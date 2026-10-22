import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database.connection import init_db, SessionLocal
from database.models import Skill, Lead
import importlib
import analytics.trend_engine
importlib.reload(analytics.trend_engine)
from analytics.trend_engine import (
    get_overview_kpis,
    get_skill_demand,
    get_location_distribution,
    get_category_distribution,
    get_top_employers,
    get_filtered_leads,
)
from analytics.pitch_generator import generate_sales_pitch
from analytics.weekly_digest import (
    build_weekly_intelligence_data,
    format_markdown_digest,
    format_html_digest,
    send_slack_notification,
    send_teams_notification,
)
from analytics.historical_analytics import (
    get_monthly_volume_trend,
    get_top_skills_time_series,
    get_skill_growth_barometer,
    get_seasonal_pattern,
)
from analytics.forecast_engine import (
    get_forecast_display_data,
    run_forecast_and_save,
)
from analytics.bench_matcher import (
    PRESET_BENCH_PROFILES,
    match_consultant_to_leads,
)
from ingestion.normalizer import extract_skills_from_text
from ingestion.pipeline import run_pipeline

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Lead Intelligence Platform | Östergötland",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- THEME-AWARE EXECUTIVE CSS (DARK & LIGHT) -----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Minimalist Header Container */
    .header-container {
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 18px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        flex-wrap: wrap;
        gap: 16px;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: inherit;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 0.9rem;
        opacity: 0.72;
        color: inherit;
        margin-top: 4px;
        font-weight: 400;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #0d9488;
        background: rgba(13, 148, 136, 0.12);
        border: 1px solid rgba(13, 148, 136, 0.25);
        padding: 4px 10px;
        border-radius: 4px;
    }
    .status-indicator {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #0d9488;
    }

    /* Metric Boxes (Adaptive Backgrounds) */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 26px;
    }
    .metric-box {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 8px;
        padding: 18px 20px;
    }
    .metric-caption {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.7;
        color: inherit;
        margin-bottom: 6px;
    }
    .metric-number {
        font-size: 1.9rem;
        font-weight: 700;
        color: inherit;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .metric-detail {
        font-size: 0.78rem;
        opacity: 0.6;
        color: inherit;
        margin-top: 6px;
    }

    /* Lead Item Card */
    .lead-row {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.16);
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 12px;
        transition: border-color 0.15s ease;
    }
    .lead-row:hover {
        border-color: rgba(59, 130, 246, 0.4);
    }
    .lead-title-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: inherit;
        margin: 0 0 6px 0;
    }
    .lead-attributes {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        font-size: 0.82rem;
        opacity: 0.78;
        color: inherit;
        margin-bottom: 10px;
    }
    .lead-attr-strong {
        font-weight: 600;
        opacity: 1;
        color: inherit;
    }

    /* Badges */
    .tag-source {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .source-consultant {
        background: rgba(37, 99, 235, 0.15);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .source-recruitment {
        background: rgba(128, 128, 128, 0.12);
        color: inherit;
        border: 1px solid rgba(128, 128, 128, 0.22);
    }
    .skill-tag {
        display: inline-block;
        background: rgba(128, 128, 128, 0.1);
        color: inherit;
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 2px 7px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .link-action {
        display: inline-block;
        font-size: 0.82rem;
        font-weight: 600;
        color: #3b82f6;
        text-decoration: none;
    }
    .link-action:hover {
        text-decoration: underline;
    }

    /* Bench Matcher Tags */
    .skill-matched {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 7px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .skill-missing {
        display: inline-block;
        background: rgba(128, 128, 128, 0.08);
        color: inherit;
        opacity: 0.7;
        border: 1px dashed rgba(128, 128, 128, 0.25);
        border-radius: 4px;
        font-size: 0.75rem;
        padding: 2px 7px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .skill-bonus {
        display: inline-block;
        background: rgba(37, 99, 235, 0.1);
        color: #2563eb;
        border: 1px solid rgba(37, 99, 235, 0.25);
        border-radius: 4px;
        font-size: 0.75rem;
        padding: 2px 7px;
        margin-right: 5px;
        margin-bottom: 5px;
    }

    /* Strategic Notes */
    .strategy-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .strategy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .strategy-name {
        font-size: 1rem;
        font-weight: 600;
        color: inherit;
    }
    .priority-pill {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .p-high { background: rgba(239, 68, 68, 0.15); color: #f87171; }
    .p-growth { background: rgba(16, 185, 129, 0.15); color: #34d399; }
    .p-strategic { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
    .p-stable { background: rgba(128, 128, 128, 0.15); color: inherit; opacity: 0.8; }

    .action-note {
        background: rgba(37, 99, 235, 0.08);
        border-left: 3px solid #3b82f6;
        border-radius: 0 6px 6px 0;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.84rem;
        color: inherit;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- DATABASE INITIALIZATION -----------------
init_db()
db = SessionLocal()

# ----------------- VIEW STATE & SYNC -----------------
FUNCTION_VIEWS = [
    "Marknadsöversikt & Aktuella Behov",
    "Uppdrag & Lead Pipeline",
    "Konsultmatchning & Bänkoptimering",
    "Prediktiv Prognos & Kompetensradar",
    "Historiska Trender (2022–2026)",
    "Strategiskt Beslutsunderlag",
    "Ledningsrapport & Veckobrev",
]

if "app_view" not in st.session_state:
    st.session_state.app_view = FUNCTION_VIEWS[0]
if "sidebar_view_choice" not in st.session_state:
    st.session_state.sidebar_view_choice = FUNCTION_VIEWS[0]
if "top_nav_select" not in st.session_state:
    st.session_state.top_nav_select = FUNCTION_VIEWS[0]

def sync_view_from_sidebar():
    st.session_state.app_view = st.session_state.sidebar_view_choice
    st.session_state.top_nav_select = st.session_state.sidebar_view_choice

def sync_view_from_top():
    st.session_state.app_view = st.session_state.top_view_choice
    st.session_state.sidebar_view_choice = st.session_state.top_view_choice

# ----------------- SIDEBAR -----------------
st.sidebar.markdown(
    """
    <div style="padding-bottom: 12px; margin-bottom: 14px; border-bottom: 1px solid rgba(128,128,128,0.2);">
        <div style="font-size: 1.05rem; font-weight: 700; color: inherit;">Lead Intelligence</div>
        <div style="font-size: 0.78rem; opacity: 0.7; color: inherit;">Östergötland, Södertälje & Nyköping</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("**Funktion & Arbetsvy**")
st.sidebar.selectbox(
    "Välj funktion (Rullgardinsmeny)",
    FUNCTION_VIEWS,
    index=FUNCTION_VIEWS.index(st.session_state.app_view),
    key="sidebar_view_choice",
    on_change=sync_view_from_sidebar,
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Filter**")

selected_location = st.sidebar.selectbox(
    "Kommun / Ort",
    ["Alla", "Linköping", "Norrköping", "Södertälje", "Nyköping", "Motala", "Finspång", "Mjölby"],
)

selected_source = st.sidebar.selectbox(
    "Uppdragstyp",
    ["Alla", "brainville", "jobtech"],
    format_func=lambda x: "Alla källor" if x == "Alla" else ("Konsultuppdrag (Brainville)" if x == "brainville" else "Rekryteringsannonser (JobTech)"),
)

consultant_only = st.sidebar.checkbox("Endast externa konsultuppdrag", value=False)
if consultant_only:
    selected_source = "brainville"

st.sidebar.markdown("---")
st.sidebar.markdown("**Datainsamling**")

if st.sidebar.button("Synkronisera data nu", use_container_width=True):
    with st.spinner("Ansluter till källor och uppdaterar databas..."):
        try:
            stats = run_pipeline()
            st.sidebar.success(
                f"Klar. Nya poster: {stats['new_leads_saved']}, Uppdaterade: {stats['existing_leads_updated']}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Synkroniseringsfel: {e}")

st.sidebar.markdown(
    """
    <div style="background: rgba(128, 128, 128, 0.06); border: 1px solid rgba(128, 128, 128, 0.16); border-radius: 6px; padding: 12px; margin-top: 16px; font-size: 0.75rem; opacity: 0.8; color: inherit; line-height: 1.5;">
        <div style="font-weight: 600; margin-bottom: 4px;">Automatiserad drift (GitHub Actions)</div>
        • Marknadssynkning: Vardagar kl. 07:00 CET<br>
        • Veckorapport: Måndagar kl. 07:30 CET<br>
        • ML-modellträning: 1:a & 15:e i månaden
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- HEADER -----------------
kpis = get_overview_kpis(db)

st.markdown(
    """
    <div class="header-container">
        <div>
            <div class="header-title">Marknadsintelligens & Beslutsstöd</div>
            <div class="header-subtitle">IT- och teknikmarknaden i Östergötland, Södertälje & Nyköping</div>
        </div>
        <div>
            <div class="status-badge">
                <span class="status-indicator"></span>
                <span>Databas ansluten • PostgreSQL</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- METRIC CARDS -----------------
st.markdown(
    f"""
    <div class="metrics-grid">
        <div class="metric-box">
            <div class="metric-caption">Totala aktiva behov</div>
            <div class="metric-number">{kpis['total_leads']}</div>
            <div class="metric-detail">Östergötland, Södertälje & Nyköping</div>
        </div>
        <div class="metric-box">
            <div class="metric-caption">Konsultförfrågningar</div>
            <div class="metric-number">{kpis['consultant_leads']}</div>
            <div class="metric-detail">Brainville och mäklaruppdrag</div>
        </div>
        <div class="metric-box">
            <div class="metric-caption">Rekryteringsannonser</div>
            <div class="metric-number">{kpis['jobtech_leads']}</div>
            <div class="metric-detail">Arbetsförmedlingen JobTech</div>
        </div>
        <div class="metric-box">
            <div class="metric-caption">Aktiva organisationer</div>
            <div class="metric-number">{kpis['unique_employers']}</div>
            <div class="metric-detail">Unika uppdragsgivare & företag</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- MAIN VIEW SELECTOR (ROLL-UP MENU) -----------------
current_view = st.session_state.app_view

col_nav_bar1, col_nav_bar2 = st.columns([3, 2])
with col_nav_bar1:
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 8px; padding-top: 5px;">
            <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 600; opacity: 0.6; letter-spacing: 0.05em;">Aktiv funktion:</span>
            <span style="font-size: 1.25rem; font-weight: 700; color: inherit; letter-spacing: -0.01em;">{current_view}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_nav_bar2:
    st.selectbox(
        "Byt vy (Rullgardinsmeny)",
        FUNCTION_VIEWS,
        index=FUNCTION_VIEWS.index(current_view),
        key="top_nav_select",
        on_change=sync_view_from_top,
        label_visibility="collapsed",
    )

st.markdown("""<div style="border-bottom: 1px solid rgba(128, 128, 128, 0.18); margin-top: 4px; margin-bottom: 24px;"></div>""", unsafe_allow_html=True)

# ----------------- VIEW 1: MARKNADSÖVERSIKT -----------------
if current_view == "Marknadsöversikt & Aktuella Behov":
    st.markdown("##### Efterfrågan per kompetens och geografi")
    
    col_chart, col_geo = st.columns([3, 2])
    
    with col_chart:
        skill_df = get_skill_demand(db, location=selected_location, source=selected_source, top_n=12)
        if not skill_df.empty:
            fig = px.bar(
                skill_df,
                x="count",
                y="skill",
                orientation="h",
                color="category",
                title=f"Mest efterfrågade tekniska kompetenser ({selected_location})",
                labels={"count": "Antal förfrågningar", "skill": "Kompetens", "category": "Kategori"},
                color_discrete_sequence=["#3b82f6", "#10b981", "#6366f1", "#06b6d4", "#f59e0b", "#ec4899"],
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=480,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=50, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
            )
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        else:
            st.info("Ingen kompetensdata tillgänglig för det valda filtret.")

    with col_geo:
        loc_df = get_location_distribution(db, source=selected_source)
        if not loc_df.empty:
            fig_loc = px.pie(
                loc_df,
                values="count",
                names="location",
                title="Geografisk fördelning (Östergötland, Södertälje & Nyköping)",
                hole=0.55,
                color_discrete_sequence=["#2563eb", "#3b82f6", "#10b981", "#06b6d4", "#f59e0b", "#8b5cf6", "#ec4899", "#cbd5e1"],
            )
            fig_loc.update_traces(textposition="inside", textinfo="percent+label")
            fig_loc.update_layout(
                height=460,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=10, t=40, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_loc, use_container_width=True, theme="streamlit")
        else:
            st.info("Ingen ortsdata tillgänglig.")

    st.markdown("---")
    
    col_emp, col_cat = st.columns([3, 2])
    
    with col_emp:
        st.markdown("##### Mest aktiva uppdragsgivare")
        top_emp_df = get_top_employers(db, location=selected_location, source=selected_source, limit=15)
        if not top_emp_df.empty:
            loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
            fig_emp = px.bar(
                top_emp_df,
                x="count",
                y="company",
                orientation="h",
                color="location",
                title=f"Organisationer med flest öppna förfrågningar ({loc_label})",
                labels={"company": "Organisation", "count": "Antal behov", "location": "Ort"},
                color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"],
            )
            fig_emp.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=420,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_emp, use_container_width=True, theme="streamlit")
        else:
            st.info("Inga arbetsgivare matchar det valda filtret.")
            
    with col_cat:
        st.markdown("##### Fördelning per teknikområde")
        cat_df = get_category_distribution(db, location=selected_location, source=selected_source)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                values="count",
                names="category",
                title="Tekniska vertikaler",
                hole=0.55,
                color_discrete_sequence=["#2563eb", "#059669", "#7c3aed", "#d97706", "#db2777"],
            )
            fig_cat.update_layout(
                height=380,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=10, t=40, b=20),
            )
            st.plotly_chart(fig_cat, use_container_width=True, theme="streamlit")

# ----------------- VIEW 2: LEAD PIPELINE -----------------
elif current_view == "Uppdrag & Lead Pipeline":
    st.markdown("##### Marknadsförfrågningar och uppdragsflöde")
    
    col_search, col_skill_filter, col_limit = st.columns([3, 2, 1])
    with col_search:
        search_query = st.text_input("Sök i uppdragsbeskrivningar", "", placeholder="Sök roll, teknik eller bolagsnamn...")
    with col_skill_filter:
        skills_in_db = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        selected_skill = st.selectbox("Filtrera på kompetens", ["Alla"] + skills_in_db)
    with col_limit:
        max_leads = st.selectbox("Max antal", [25, 50, 100], index=1)

    leads_list = get_filtered_leads(
        db,
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        limit=max_leads,
    )

    if leads_list:
        leads_df = pd.DataFrame(leads_list)
        csv_data = leads_df.drop(columns=["description"]).to_csv(index=False).encode("utf-8")
        
        col_count, col_download = st.columns([4, 1])
        with col_count:
            st.caption(f"Visar {len(leads_list)} matchande uppdrag i urvalet.")
        with col_download:
            st.download_button(
                label="Exportera data (.csv)",
                data=csv_data,
                file_name=f"lead_intelligence_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    for lead in leads_list:
        source_class = "source-consultant" if lead["is_consultant"] else "source-recruitment"
        source_text = "Konsult" if lead["is_consultant"] else "Rekrytering"
        
        skill_tags = "".join([f'<span class="skill-tag">{s}</span>' for s in lead["skills"]])
        
        link_html = (
            f'<a href="{lead["url"]}" target="_blank" class="link-action">Visa fullständig annons →</a>'
            if lead["url"]
            else '<span style="opacity:0.6; font-size:0.8rem;">Länk saknas</span>'
        )

        st.markdown(
            f"""
            <div class="lead-row">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
                    <div class="lead-title-text">{lead['title']}</div>
                    <div><span class="tag-source {source_class}">{source_text}</span></div>
                </div>
                <div class="lead-attributes">
                    <span>Organisation: <span class="lead-attr-strong">{lead['company_name']}</span></span>
                    <span>Ort: <span class="lead-attr-strong">{lead['location']}</span></span>
                    <span>Publicerad: {lead['published_at']}</span>
                    <span>Deadline: {lead['deadline']}</span>
                </div>
                <div style="margin-bottom: 10px;">{skill_tags}</div>
                <div style="opacity: 0.8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 12px;">
                    {lead['description'][:260] + '...' if lead['description'] else 'Detaljerad information finns i källsystemet.'}
                </div>
                <div>{link_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"Skapa konsultpitch & säljmejl ({lead['company_name']})"):
            col_p1, col_p2 = st.columns([3, 2])
            with col_p1:
                default_profile = f"Senior specialist inom {', '.join(lead['skills'][:3]) if lead['skills'] else 'systemutveckling'}"
                c_role = st.text_input(
                    "Konsultprofil / Erfarenhetsinriktning",
                    value=default_profile,
                    key=f"role_{lead['id']}",
                )
            with col_p2:
                c_avail = st.text_input(
                    "Tillgänglig från",
                    value="inom 2–4 veckor",
                    key=f"avail_{lead['id']}",
                )

            pitch = generate_sales_pitch(lead, consultant_profile=c_role, available_from=c_avail)
            st.text_input("Föreslagen ämnesrad", value=pitch["subject"], key=f"subj_{lead['id']}")
            st.text_area("Färdigt säljmejl (redigerbart)", value=pitch["body"], height=190, key=f"body_{lead['id']}")

# ----------------- VIEW: KONSULTMATCHNING & BÄNKOPTIMERING -----------------
elif current_view == "Konsultmatchning & Bänkoptimering":
    st.markdown("##### Konsultmatchning & Bänkoptimering")
    st.caption("Matcha tillgängliga konsulter mot regionens 144 aktiva IT- och teknikkrav. Systemet analyserar kompetensöverlapp, geografi och förbereder skräddarsydda säljmejl.")

    # 1. Profile Selection Section
    profile_options = [f"{p['name']} – {p['title']} ({p['location']})" for p in PRESET_BENCH_PROFILES]
    profile_options.append("➕ Skapa egen konsultprofil / Klistra in CV")

    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        chosen_profile_label = st.selectbox(
            "Välj konsultprofil på bänken",
            profile_options,
            index=0,
        )
    with col_sel2:
        min_score = st.slider("Lägsta matchningsgrad (%)", min_value=20, max_value=80, value=30, step=5)

    is_custom = "Skapa egen" in chosen_profile_label

    if not is_custom:
        selected_prof_idx = profile_options.index(chosen_profile_label)
        active_consultant = PRESET_BENCH_PROFILES[selected_prof_idx]

        # Consultant summary card
        skills_pills = "".join([f'<span class="skill-tag">{s}</span>' for s in active_consultant["skills"]])
        clearance_text = " • Säkerhetsprövad (RK3/SUA)" if active_consultant.get("clearance") else ""
        
        st.markdown(
            f"""
            <div style="background: rgba(128, 128, 128, 0.04); border: 1px solid rgba(128, 128, 128, 0.18); border-radius: 8px; padding: 18px 20px; margin-bottom: 22px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: inherit;">{active_consultant['name']}</div>
                        <div style="font-size: 0.86rem; opacity: 0.8; margin-top: 2px;">{active_consultant['title']} • {active_consultant['seniority']} • {active_consultant['location']}{clearance_text}</div>
                    </div>
                    <div class="priority-pill p-growth">{active_consultant['available_from']}</div>
                </div>
                <div style="font-size: 0.85rem; opacity: 0.85; line-height: 1.5; margin-bottom: 12px;">{active_consultant['summary']}</div>
                <div>{skills_pills}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("###### Egen konsultprofil")
        col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
        with col_c1:
            c_name_input = st.text_input("Konsultens namn", value="Anna Andersson")
            c_role_input = st.text_input("Rollextitel", value="Senior Fullstack-utvecklare")
        with col_c2:
            c_loc_input = st.selectbox("Ort / Primärt område", ["Linköping", "Norrköping", "Södertälje", "Nyköping", "Hela regionen"])
            c_avail_input = st.text_input("Tillgänglig från", value="Omgående")
        with col_c3:
            c_clear_input = st.checkbox("Säkerhetsprövad", value=False)
            c_seniority_input = st.selectbox("Erfarenhet", ["Junior (1–3 år)", "Mid (3–5 år)", "Senior (5–10 år)", "Lead (>10 år)"], index=2)

        raw_cv_text = st.text_area(
            "Klistra in konsultens profil, CV-sammanfattning eller tekniska nyckelord",
            height=110,
            placeholder="T.ex: Erfaren utvecklare med stark bakgrund inom C#, .NET 8, React, Azure, Docker, Kubernetes och REST API...",
        )

        detected_custom_skills = [s[0] for s in extract_skills_from_text(raw_cv_text)] if raw_cv_text else []
        all_skills = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        
        custom_selected_skills = st.multiselect(
            "Kompetenser (extraherade automatiskt ur texten, lägg till eller justera vid behov)",
            all_skills,
            default=[s for s in detected_custom_skills if s in all_skills],
        )

        active_consultant = {
            "name": c_name_input,
            "title": c_role_input,
            "seniority": c_seniority_input,
            "location": c_loc_input,
            "available_from": c_avail_input,
            "clearance": c_clear_input,
            "skills": custom_selected_skills,
            "summary": raw_cv_text[:300] if raw_cv_text else f"{c_role_input} baserad i {c_loc_input}.",
        }

    # 2. Run Matcher against active market leads
    matched_leads = match_consultant_to_leads(
        db,
        consultant=active_consultant,
        location_filter=selected_location if selected_location != "Alla" else None,
        min_match_pct=min_score,
        limit=25,
    )

    # 3. Match Statistics Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Matchade Uppdrag", f"{len(matched_leads)} st")
    with col_m2:
        top_match_score = f"{matched_leads[0]['match_score']}%" if matched_leads else "0%"
        st.metric("Bästa Matchning", top_match_score)
    with col_m3:
        direct_consultant_count = sum(1 for m in matched_leads if m["is_consultant"])
        st.metric("Direkta Konsultuppdrag", f"{direct_consultant_count} st")
    with col_m4:
        strong_matches_count = sum(1 for m in matched_leads if m["match_score"] >= 75)
        st.metric("Hög Prioritet (>=75%)", f"{strong_matches_count} st")

    st.markdown("---")

    # 4. Render Matched Leads Cards
    if matched_leads:
        st.markdown(f"###### Relevanta affärsmöjligheter för {active_consultant['name']} (Sorterat efter matchningsgrad)")

        for lead in matched_leads:
            score = lead["match_score"]
            if score >= 75:
                score_pill = f'<span class="priority-pill p-growth">{score}% Match</span>'
            elif score >= 55:
                score_pill = f'<span class="priority-pill p-strategic">{score}% Match</span>'
            else:
                score_pill = f'<span class="priority-pill p-stable">{score}% Match</span>'

            source_tag = (
                '<span class="tag-source source-consultant">Konsultuppdrag</span>'
                if lead["is_consultant"]
                else '<span class="tag-source source-recruitment">Rekryteringsannons</span>'
            )

            matched_tags = "".join([f'<span class="skill-matched">✓ {s}</span>' for s in lead["matched_skills"]])
            missing_tags = "".join([f'<span class="skill-missing">{s}</span>' for s in lead["missing_skills"][:4]])
            bonus_tags = "".join([f'<span class="skill-bonus">+ {s}</span>' for s in lead["bonus_skills"]])

            link_html = (
                f'<a href="{lead["url"]}" target="_blank" class="link-action">Visa fullständig annons →</a>'
                if lead["url"]
                else '<span style="opacity:0.6; font-size:0.8rem;">Länk saknas</span>'
            )

            st.markdown(
                f"""
                <div class="lead-row">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                        <div>
                            {score_pill} {source_tag}
                            <div class="lead-title-text" style="margin-top: 6px;">{lead['title']}</div>
                        </div>
                        <div>
                            {link_html}
                        </div>
                    </div>
                    <div class="lead-attributes">
                        <span>Beställare: <span class="lead-attr-strong">{lead['company']}</span></span>
                        <span>Ort: <span class="lead-attr-strong">{lead['location']}</span></span>
                        <span>Publicerad: <span>{lead['published_at']}</span></span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.8rem;">
                        <div style="margin-bottom: 4px;"><strong>Matchade krav:</strong> {matched_tags if matched_tags else '<span style=\"opacity:0.6;\">Inga direkta teknikkrav</span>'}</div>
                        {f'<div style=\"margin-bottom: 4px;\"><strong style=\"opacity:0.7;\">Övriga krav i annons:</strong> {missing_tags}</div>' if missing_tags else ''}
                        {f'<div><strong style=\"color:#2563eb;\">Konsultens mervärde:</strong> {bonus_tags}</div>' if bonus_tags else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Generera säljpitch för {active_consultant['name']} till {lead['company']}"):
                col_sp1, col_sp2 = st.columns([3, 1])
                with col_sp1:
                    st.text_input("Föreslagen ämnesrad", value=lead["pitch_subject"], key=f"pitch_sub_{lead['lead_id']}_{active_consultant['name']}")
                with col_sp2:
                    st.caption("Färdigt att kopiera & skicka")
                st.text_area("Säljmejl (redigerbart)", value=lead["pitch_body"], height=190, key=f"pitch_body_{lead['lead_id']}_{active_consultant['name']}")
    else:
        st.info("Inga uppdrag nådde den valda lägsta matchningsgraden. Prova att sänka matchningströskeln ovan.")

# ----------------- VIEW 3: PREDIKTIV PROGNOS & KOMPETENSRADAR -----------------
elif current_view == "Prediktiv Prognos & Kompetensradar":
    st.markdown("##### Prediktiv Marknadsprognos & Kompetensradar (6 Månader Framåt)")
    st.caption("AI/ML-tidsserieprognos med Holt-Winters säsongsmodell & momentum-analys tränad på 58 månaders data (2022–2026) sparad i Supabase.")

    hist_df, fc_df, trending_skills = get_forecast_display_data(db, location=selected_location)

    if not fc_df.empty:
        avg_fc_vol = fc_df["predicted_volume"].mean()
        peak_month_row = fc_df.loc[fc_df["predicted_volume"].idxmax()]
        top_growth_skill = trending_skills[0] if trending_skills else None

        col_fc1, col_fc2, col_fc3 = st.columns(3)
        with col_fc1:
            st.metric(
                "Prognosticerad Snittvolym (Kommande 6 mån)",
                f"{avg_fc_vol:.0f} st/mån",
                delta=f"{fc_df['growth_mom_pct'].iloc[0]:+.1f}% startmånad",
            )
        with col_fc2:
            st.metric(
                "Förväntad Efterfrågetopp",
                f"{peak_month_row['predicted_volume']:.0f} st",
                help=f"Toppmånad: {peak_month_row['period']}",
            )
        with col_fc3:
            if top_growth_skill:
                st.metric(
                    "Starkast Kompetenstillväxt",
                    f"{top_growth_skill['skill']}",
                    delta=f"+{top_growth_skill['growth_pct']:.0f}% momentum",
                )
            else:
                st.metric("Kompetenstillväxt", "Beräknad", delta="Normal")

        st.markdown("---")

        # Forecast Line Chart with Confidence Interval
        st.markdown("###### Volymutveckling & 6-månaders framtidsprognos (med konfidensintervall)")
        
        hist_subset = hist_df.tail(18).copy()
        
        fig_fc = go.Figure()

        # Add Historical Line
        fig_fc.add_trace(go.Scatter(
            x=hist_subset["period"],
            y=hist_subset["total_postings"],
            mode="lines+markers",
            name="Historisk volym (Utfall)",
            line=dict(color="#2563eb", width=2.5),
            marker=dict(size=6),
        ))

        # Bridge point: connect last historical point to first forecast point
        bridge_x = [hist_subset["period"].iloc[-1]] + list(fc_df["period"])
        bridge_y = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["predicted_volume"])
        bridge_lower = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["ci_lower"])
        bridge_upper = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["ci_upper"])

        # Confidence Interval (Upper bound)
        fig_fc.add_trace(go.Scatter(
            x=bridge_x,
            y=bridge_upper,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Confidence Interval (Lower bound filled to upper)
        fig_fc.add_trace(go.Scatter(
            x=bridge_x,
            y=bridge_lower,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(37, 99, 235, 0.12)",
            name="80% Konfidensintervall (P10–P90)",
            hoverinfo="skip",
        ))

        # Forecast Line
        fig_fc.add_trace(go.Scatter(
            x=bridge_x,
            y=bridge_y,
            mode="lines+markers",
            name="Maskininlärningsprognos",
            line=dict(color="#10b981", width=3, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        ))

        loc_label = selected_location if selected_location != "Alla" else "Hela regionen (Östergötland, Södertälje & Nyköping)"
        fig_fc.update_layout(
            title=f"Marknadsprognos & Efterfrågebana ({loc_label})",
            xaxis_title="Period (Månad)",
            yaxis_title="Antal IT-behov / Uppdrag",
            height=420,
            font={"family": "Inter, sans-serif"},
            margin=dict(l=10, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
            hovermode="x unified",
        )
        st.plotly_chart(fig_fc, use_container_width=True, theme="streamlit")

        st.markdown("---")

        # Competency Momentum & Upskilling Matrix
        st.markdown("###### Framtida Kompetensbehov & Vidareutbildningsrekommendationer (Upskilling Matrix)")
        st.caption("Sorterat efter efterfrågeacceleration och tillväxt mellan perioderna. Ger ledningen direkt underlag för vilka certifieringar konsulter ska prioriteras inom.")

        if trending_skills:
            col_u1, col_u2 = st.columns([3, 2])
            with col_u1:
                skills_table_df = pd.DataFrame(trending_skills)
                display_table = skills_table_df[["skill", "category", "current_volume", "growth_pct", "action"]].copy()
                display_table.columns = ["Kompetens", "Kategori", "Aktuella behov (6m)", "Tillväxt (%)", "Strategisk Rekommendation"]
                st.dataframe(
                    display_table,
                    use_container_width=True,
                    hide_index=True,
                )

            with col_u2:
                st.markdown(
                    """
                    <div style="background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.15); border-radius: 8px; padding: 16px; font-size: 0.88rem; line-height: 1.6;">
                        <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 8px;">Ledningsåtgärder för konsultteamet:</div>
                        <strong>1. Investera & Certifiera:</strong> Konsulter på bänken eller med ledig tid bör omedelbart styras mot certifieringar inom <em>Terraform, Kubernetes (CKA) och Databricks</em>.<br>
                        <strong>2. Rekryteringsfokus:</strong> Styr kravprofiler för seniorrekrytering mot Cloud Architecture och NIS2-säkerhet där tillväxttakten är som högst.<br>
                        <strong>3. Kassakor:</strong> Bibehåll senior leverans inom etablerad systemutveckling (.NET, C#, C++, Python) som står för den stabila basvolymen.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        col_btn_retrain, col_btn_info = st.columns([1, 3])
        with col_btn_retrain:
            if st.button("Kör om ML-prognos nu", use_container_width=True):
                with st.spinner("Tränar om tidsserie- och momentummodeller..."):
                    run_forecast_and_save(db, location=selected_location)
                    st.success("Modell omtränad och prognos uppdaterad!")
                    st.rerun()
        with col_btn_info:
            st.caption("Modellen tränas automatiskt varannan vecka via GitHub Actions. Klicka ovan för att manuellt framtvinga en omedelbar omräkning.")
    else:
        st.info("Ingen förberäknad prognos tillgänglig för det valda filtret. Klicka på knappen nedan för att generera den.")
        if st.button("Generera prognos nu"):
            with st.spinner("Tränar modell..."):
                run_forecast_and_save(db, location=selected_location)
                st.rerun()

# ----------------- VIEW 4: HISTORISKA TRENDER -----------------
elif current_view == "Historiska Trender (2022–2026)":
    st.markdown("##### Historisk marknadsutveckling (2022–2026)")
    st.caption("Djupanalys baserad på över 3 800 historiska IT-annonser i Östergötland, Södertälje och Nyköping.")

    # 1. Top row: Monthly volume trend + Seasonality
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        vol_df = get_monthly_volume_trend(db, location=selected_location)
        if not vol_df.empty:
            loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
            fig_vol = px.line(
                vol_df,
                x="month",
                y="postings",
                title=f"Volymtrend månad för månad ({loc_label})",
                labels={"month": "Månad", "postings": "Antal annonserade IT-positioner"},
                markers=True,
                color_discrete_sequence=["#2563eb"],
            )
            fig_vol.update_layout(
                height=380,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_vol, use_container_width=True, theme="streamlit")
            st.caption("Månatlig volym från JobTech Historical API (2024–2026-09) samt dagsaktuellt realtidsflöde för pågående månad (2026-10).")
        else:
            st.info("Ingen historisk volymdata tillgänglig för valt filter.")

    with col_t2:
        season_df = get_seasonal_pattern(db, location=selected_location)
        if not season_df.empty:
            fig_season = px.bar(
                season_df,
                x="month_name",
                y="count",
                title="Säsongsmönster: När rekryterar kunderna som mest?",
                labels={"month_name": "Kalendermånad", "count": "Sammanlagd volym"},
                color="count",
                color_continuous_scale="Blues",
            )
            fig_season.update_layout(
                height=380,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=10, t=40, b=20),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_season, use_container_width=True, theme="streamlit")

    st.markdown("---")

    # 2. Second row: Skill evolution over time + Growth Barometer
    col_t3, col_t4 = st.columns([3, 2])
    with col_t3:
        skills_ts_df = get_top_skills_time_series(db, location=selected_location, top_n=6)
        if not skills_ts_df.empty:
            fig_ts = px.line(
                skills_ts_df,
                x="month",
                y="count",
                color="skill",
                title="Kompetensutveckling över tid: Topp 6 teknologier",
                labels={"month": "Månad", "count": "Efterfrågan (annonser)", "skill": "Kompetens"},
                color_discrete_sequence=["#2563eb", "#10b981", "#6366f1", "#f59e0b", "#ec4899", "#06b6d4"],
            )
            fig_ts.update_layout(
                height=420,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_ts, use_container_width=True, theme="streamlit")
        else:
            st.info("Ingen kompetenshistorik tillgänglig.")

    with col_t4:
        growth_df = get_skill_growth_barometer(db, location=selected_location)
        if not growth_df.empty:
            fig_growth = px.bar(
                growth_df,
                x="growth_pct",
                y="skill",
                orientation="h",
                title="Tillväxtbarometer: Snabbast växande kompetenser (%)",
                labels={"growth_pct": "Tillväxt (%)", "skill": "Kompetens"},
                color="growth_pct",
                color_continuous_scale=["#93c5fd", "#2563eb", "#1d4ed8"],
            )
            fig_growth.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=420,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_growth, use_container_width=True, theme="streamlit")

    st.markdown("---")

    # 3. Third row: Strategic Foresight Note for Leadership
    st.markdown(
        """
        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">Strategisk Marknadsspaning & Prognos</span>
                <span class="priority-pill p-strategic">Ledningsanalys</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.82; line-height: 1.6;">
                1. <strong>Cybersäkerhet & Plattform (+62% till +100% tillväxt):</strong> Den starkaste tillväxtvektorn i regionen. Drivs av regulatoriska EU-direktiv (NIS2/DORA) samt industriell modernisering mot microservices.<br>
                2. <strong>Försvar & Fordon (C++ / Embedded +35.7%):</strong> Linköpings flyg- och försvarskluster (Saab Gripen) och Södertäljes fordonskluster (Scania elektrifiering) uppvisar en strukturell tillväxt som är oberoende av allmänna konjunktursvängningar.<br>
                3. <strong>Säsongseffekter för säljteamet:</strong> Efterfrågan toppar historiskt kraftigt i <strong>oktober och mars</strong>. Resursplanering och konsultpitchar bör intensifieras 3–4 veckor före dessa toppar (i slutet av augusti och i februari) för att maximera beläggningen.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------- VIEW 5: STRATEGISKT BESLUTSUNDERLAG -----------------
elif current_view == "Strategiskt Beslutsunderlag":
    st.markdown("##### Strategiska prioriteringar för ledningen")
    st.caption("Sammanfattande marknadsanalys och affärsrekommendationer baserat på aggregerade data.")
    
    st.markdown(
        """
        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">1. Molninfrastruktur & DevOps (Azure, Terraform, Kubernetes)</span>
                <span class="priority-pill p-high">Hög prioritet</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                Azure och automation fortsätter att vara det dominerande teknikbehovet i regionen, framförallt inom industri och offentlig förvaltning med bas i Linköping och Norrköping.
            </div>
            <div class="action-note">
                <strong>Ledningsåtgärd:</strong> Prioritera certifiering av befintliga konsulter (Azure Solutions Architect, DevOps Engineer) och inrikta senior rekrytering mot plattformsarkitektur.
            </div>
        </div>

        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">2. Inbyggda och säkerhetskritiska system (C++, Linux, Försvarssektorn)</span>
                <span class="priority-pill p-growth">Tillväxtsegment</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                Linköpings starka försvars- och säkerhetskluster uppvisar en ihållande hög efterfrågan på systemnära utvecklare. Uppdragen ställer regelmässigt krav på svenskt medborgarskap och godkänd säkerhetsprövning.
            </div>
            <div class="action-note">
                <strong>Ledningsåtgärd:</strong> Etablera dedikerade kandidatpooler med förhandskontrollerad säkerhetsstatus inför kommande ramavtalstilldelningar.
            </div>
        </div>

        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">3. Informationssäkerhet & Compliance (NIS2, ISO 27001)</span>
                <span class="priority-pill p-strategic">Strategisk rådgivning</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                Implementeringen av NIS2-direktivet driver en kraftigt ökad efterfrågan på rådgivning och gapanalyser hos både kommunala bolag och samhällsviktiga leverantörer.
            </div>
            <div class="action-note">
                <strong>Ledningsåtgärd:</strong> Paketera proaktiva rådgivningsinsatser mot ledningsgrupper i medelstora regionala bolag för att öppna dörrar till bredare IT-uppdrag.
            </div>
        </div>

        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">4. Data Analytics & Dataplattformar (Databricks, Power BI, Python)</span>
                <span class="priority-pill p-stable">Etablerat behov</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                Flera ledande industrier i Norrköping konsoliderar sin datainfrastruktur mot moderna Data Lakehouses för att möjliggöra avancerad analys och maskininlärning.
            </div>
            <div class="action-note">
                <strong>Ledningsåtgärd:</strong> Positionera erbjudandet kring helhetslösningar inom data engineering snarare än enskilda rapportbyggen.
            </div>
        </div>

        <div class="strategy-card">
            <div class="strategy-header">
                <span class="strategy-name">5. Fordonselektrifiering & Life Science (Södertälje & Nyköping)</span>
                <span class="priority-pill p-growth">Expansionsområde</span>
            </div>
            <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                Scania- och AstraZeneca-klustren i Södertälje samt industrin kring Nyköping skapar stor efterfrågan inom fordonsprogramvara (AUTOSAR, C++, diagnostik, Linux) och validerade Life Science-molnplattformar.
            </div>
            <div class="action-note">
                <strong>Ledningsåtgärd:</strong> Rikta konsultbearbetning mot fordons- och automationsbolag i Södertälje- och Nyköpingsregionen som komplement till Mjärdevi- och SAAB-affärerna.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------- VIEW 6: VECKORAPPORT & LEDNINGSBREV -----------------
elif current_view == "Ledningsrapport & Veckobrev":
    st.markdown("##### Veckorapport: Marknadsintelligens för ledningen")
    st.caption("Aggregerad sammanställning av den senaste veckans uppdragsflöde, heta leads och kompetenstrender.")

    digest_data = build_weekly_intelligence_data(db, days_back=7)
    digest_md = format_markdown_digest(digest_data)
    digest_html = format_html_digest(digest_data)

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("Totala Aktiva Behov", f"{digest_data['total_active']} st")
    with col_d2:
        st.metric("Direkta Konsultuppdrag", f"{digest_data['consultant_leads']} st")
    with col_d3:
        st.metric("Nya Poster Senaste 7 Dagar", f"{digest_data['new_this_week']} st")

    st.markdown("---")

    col_btn_md, col_btn_html, col_btn_teams = st.columns([1, 1, 2])
    with col_btn_md:
        st.download_button(
            label="Ladda ner Markdown (.md)",
            data=digest_md,
            file_name=f"marknadsrapport_{digest_data['report_date']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_btn_html:
        st.download_button(
            label="Ladda ner HTML-brev (.html)",
            data=digest_html,
            file_name=f"marknadsbrev_{digest_data['report_date']}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_btn_teams:
        if st.button("Skicka rapport till Microsoft Teams nu", use_container_width=True):
            if send_teams_notification(digest_md):
                st.success("Veckorapporten har skickats till din Microsoft Teams-kanal!")
            else:
                st.warning("Kunde inte skicka. Kontrollera att din TEAMS_WEBHOOK_URL är konfigurerad nedan.")

    # Expandable Microsoft Teams Webhook Configuration box
    with st.expander("Koppla & Konfigurera Microsoft Teams Webhook"):
        st.markdown(
            """
            Koppla ihop valfri kanal i Microsoft Teams för automatiserade rapporter varje måndag:
            1. **I Teams:** Gå till den kanal där du vill få rapporterna -> Klicka på `...` -> Välj **Arbetsflöden (Workflows)**.
            2. Välj mallen *"Publicera i en kanal när en webhook-begäran tas emot"* (Post to a channel when a webhook request is received).
            3. Kopiera den genererade webhook-länken och klistra in den nedan.
            """
        )
        current_env_webhook = os.getenv("TEAMS_WEBHOOK_URL", "")
        custom_teams_url = st.text_input(
            "Teams Webhook URL",
            value=current_env_webhook,
            placeholder="https://prod-xx.westeurope.logic.azure.com:443/workflows/... eller https://outlook.office.com/webhook/...",
        )
        if st.button("Skicka testmeddelande till denna Teams-länk"):
            if custom_teams_url.strip():
                if send_teams_notification(digest_md, webhook_url=custom_teams_url.strip()):
                    st.success("Testrapporten levererades till Microsoft Teams! Kontrollera din kanal nu.")
                else:
                    st.error("Kunde inte skicka. Kontrollera att länken är komplett kopierad från Teams.")
            else:
                st.warning("Klistra in en Teams Webhook URL i rutan först.")

    st.markdown("##### Förhandsgranskning av veckorapporten")
    st.markdown(digest_md)

db.close()
