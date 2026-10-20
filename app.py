import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database.connection import init_db, SessionLocal
from database.models import Skill, Lead
from analytics.trend_engine import (
    get_overview_kpis,
    get_skill_demand,
    get_location_distribution,
    get_category_distribution,
    get_top_employers,
    get_filtered_leads,
)
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

# ----------------- SIDEBAR -----------------
st.sidebar.markdown(
    """
    <div style="padding-bottom: 12px; margin-bottom: 16px; border-bottom: 1px solid rgba(128,128,128,0.2);">
        <div style="font-size: 0.95rem; font-weight: 700; color: inherit;">Lead Intelligence</div>
        <div style="font-size: 0.78rem; opacity: 0.7; color: inherit;">Beslutsstöd Region Östergötland</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("**Filter**")

selected_location = st.sidebar.selectbox(
    "Kommun / Ort",
    ["Alla", "Linköping", "Norrköping", "Motala", "Finspång", "Mjölby"],
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
    <div style="background: rgba(128, 128, 128, 0.06); border: 1px solid rgba(128, 128, 128, 0.16); border-radius: 6px; padding: 12px; margin-top: 16px; font-size: 0.75rem; opacity: 0.8; color: inherit; line-height: 1.4;">
        <div style="font-weight: 600; margin-bottom: 2px;">Automatiserad drift</div>
        GitHub Actions uppdaterar denna databas schemalagt varje vardagsmorgon kl. 07:00 CET.
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
            <div class="header-subtitle">IT- och teknikmarknaden i Östergötland (Linköping, Norrköping)</div>
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
            <div class="metric-detail">Östergötlands samlade marknad</div>
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

# ----------------- MAIN TABS -----------------
tab_market, tab_leads, tab_strategy = st.tabs([
    "Marknadsöversikt & Kompetenser",
    "Uppdrag & Lead Pipeline",
    "Strategiskt Beslutsunderlag",
])

# ----------------- TAB 1: MARKNADSÖVERSIKT -----------------
with tab_market:
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
                height=460,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
        else:
            st.info("Ingen kompetensdata tillgänglig för det valda filtret.")

    with col_geo:
        loc_df = get_location_distribution(db)
        if not loc_df.empty:
            fig_loc = px.pie(
                loc_df,
                values="count",
                names="location",
                title="Geografisk fördelning i länet",
                hole=0.55,
                color_discrete_sequence=["#3b82f6", "#60a5fa", "#93c5fd", "#06b6d4", "#a5f3fc"],
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
        top_emp_df = get_top_employers(db, limit=10)
        if not top_emp_df.empty:
            fig_emp = px.bar(
                top_emp_df,
                x="count",
                y="company",
                orientation="h",
                color="location",
                title="Organisationer med flest öppna förfrågningar",
                labels={"company": "Organisation", "count": "Antal behov", "location": "Ort"},
                color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"],
            )
            fig_emp.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=380,
                font={"family": "Inter, sans-serif"},
                margin=dict(l=10, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_emp, use_container_width=True, theme="streamlit")
            
    with col_cat:
        st.markdown("##### Fördelning per teknikområde")
        cat_df = get_category_distribution(db)
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

# ----------------- TAB 2: LEAD PIPELINE -----------------
with tab_leads:
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

# ----------------- TAB 3: STRATEGISKT BESLUTSUNDERLAG -----------------
with tab_strategy:
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
        """,
        unsafe_allow_html=True,
    )

db.close()
