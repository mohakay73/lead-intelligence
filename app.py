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
    page_title="Executive Lead Intelligence | Östergötland",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- CUSTOM EXECUTIVE CSS -----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Executive Top Banner */
    .executive-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .executive-title {
        color: #f8fafc;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .executive-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 6px 0 0 0;
        font-weight: 400;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }

    /* Modern KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .kpi-blue::before { background: linear-gradient(90deg, #2563eb, #3b82f6); }
    .kpi-indigo::before { background: linear-gradient(90deg, #4f46e5, #6366f1); }
    .kpi-amber::before { background: linear-gradient(90deg, #d97706, #f59e0b); }
    .kpi-emerald::before { background: linear-gradient(90deg, #059669, #10b981); }

    .kpi-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .kpi-meta {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Lead Item Card */
    .lead-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease-in-out;
    }
    .lead-card:hover {
        border-color: #93c5fd;
        box-shadow: 0 6px 14px -3px rgba(37, 99, 235, 0.08);
    }
    .lead-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
        flex-wrap: wrap;
    }
    .lead-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 6px 0;
    }
    .lead-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 12px;
    }
    .lead-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }
    .badge-brainville {
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }
    .badge-jobtech {
        background-color: #fefce8;
        color: #854d0e;
        border: 1px solid #fef08a;
    }
    .badge-skill {
        background-color: #f8fafc;
        color: #334155;
        border: 1px solid #e2e8f0;
        margin-right: 6px;
        margin-bottom: 6px;
        font-size: 0.75rem;
        padding: 3px 9px;
        border-radius: 6px;
    }
    .action-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 8px;
        background: #2563eb;
        color: #ffffff !important;
        font-size: 0.82rem;
        font-weight: 600;
        text-decoration: none;
        transition: background 0.15s ease;
    }
    .action-btn:hover {
        background: #1d4ed8;
    }

    /* Strategy Insight Cards */
    .insight-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
        border-left: 4px solid #2563eb;
    }
    .insight-card.priority-high {
        border-left-color: #ef4444;
    }
    .insight-card.priority-growth {
        border-left-color: #10b981;
    }
    .insight-card.priority-strategic {
        border-left-color: #8b5cf6;
    }
    .insight-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 8px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .insight-body {
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.5;
        margin: 0;
    }
    .insight-rec {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.85rem;
        color: #1e293b;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- DATABASE INITIALIZATION -----------------
init_db()
db = SessionLocal()

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
        <div style="background: #2563eb; border-radius: 10px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.25rem; font-weight: bold;">
            🎯
        </div>
        <div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; line-height: 1.2;">Lead Intelligence</div>
            <div style="font-size: 0.75rem; color: #64748b;">Östergötland Ledningsstöd</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🎛️ Filtrera Underlag")

selected_location = st.sidebar.selectbox(
    "📍 Ort / Kommun",
    ["Alla", "Linköping", "Norrköping", "Motala", "Finspång", "Mjölby"],
    help="Filtrera mellan orter i Östergötlands län.",
)

selected_source = st.sidebar.selectbox(
    "🔌 Datakälla",
    ["Alla", "brainville", "jobtech"],
    format_func=lambda x: "Alla Källor" if x == "Alla" else ("⚡ Brainville (Konsult)" if x == "brainville" else "🏢 JobTech (Rekrytering)"),
    help="Välj om du vill se konsultuppdrag eller fasta rekryteringsbehov.",
)

consultant_only = st.sidebar.checkbox("Endast direkta konsultuppdrag", value=False)
if consultant_only:
    selected_source = "brainville"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Datainsamling & Sync")

if st.sidebar.button("⚡ Kör Live-synkning (APIs)", use_container_width=True):
    with st.spinner("Hämtar färsk data från Arbetsförmedlingen JobTech & Brainville..."):
        try:
            stats = run_pipeline()
            st.sidebar.success(
                f"Synkning klar! Nya leads: {stats['new_leads_saved']}, Uppdaterade: {stats['existing_leads_updated']}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Ett fel uppstod vid synkning: {e}")

st.sidebar.markdown(
    """
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-top: 12px; font-size: 0.75rem; color: #64748b;">
        <div style="font-weight: 600; color: #334155; margin-bottom: 4px;">☁️ Molnautomatisering</div>
        GitHub Actions uppdaterar denna databas helautomatiskt varje vardagsmorgon kl. 07:00.
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- EXECUTIVE HEADER BANNER -----------------
kpis = get_overview_kpis(db)
now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

st.markdown(
    f"""
    <div class="executive-header">
        <div>
            <div class="executive-title">
                🎯 Marknadsintelligens & Beslutsstöd
            </div>
            <div class="executive-subtitle">
                Realtidsanalys av IT-kompetenser, konsultförfrågningar och affärsmöjligheter i <strong>Linköping & Norrköping</strong>
            </div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <div class="status-pill">
                <span class="status-dot"></span>
                <span>Supabase PostgreSQL • Online</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- MODERN EXECUTIVE KPI CARDS -----------------
st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-card kpi-blue">
            <div class="kpi-label">Totala Aktiva Leads</div>
            <div class="kpi-value">{kpis['total_leads']}</div>
            <div class="kpi-meta">📊 Östergötlands IT-marknad</div>
        </div>
        <div class="kpi-card kpi-indigo">
            <div class="kpi-label">Konsultuppdrag (Brainville)</div>
            <div class="kpi-value">{kpis['consultant_leads']}</div>
            <div class="kpi-meta">⚡ Förfrågningar & Mäklaruppdrag</div>
        </div>
        <div class="kpi-card kpi-amber">
            <div class="kpi-label">Rekryteringsleads (JobTech)</div>
            <div class="kpi-value">{kpis['jobtech_leads']}</div>
            <div class="kpi-meta">🏢 Offentliga & privata arbetsgivare</div>
        </div>
        <div class="kpi-card kpi-emerald">
            <div class="kpi-label">Aktiva Uppdragsgivare</div>
            <div class="kpi-value">{kpis['unique_employers']}</div>
            <div class="kpi-meta">🤝 Unika företag & organisationer</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- MAIN NAVIGATION TABS -----------------
tab_market, tab_leads, tab_strategy = st.tabs([
    "📊 Marknadsanalys & Kompetensefterfrågan",
    "💼 Affärsmöjligheter & Lead Explorer",
    "🎯 Strategiska Ledningsbeslut",
])

# ----------------- TAB 1: MARKNADSANALYS -----------------
with tab_market:
    st.markdown("#### 🔥 Kompetens- och Marknadsdynamik i Östergötland")
    
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
                title=f"Topp 12 mest efterfrågade kompetenser ({selected_location})",
                labels={"count": "Antal förfrågningar / annonser", "skill": "Kompetens", "category": "Kategori"},
                color_discrete_sequence=["#2563eb", "#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899"],
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=480,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"family": "Plus Jakarta Sans, sans-serif"},
                margin=dict(l=10, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            )
            fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ingen kompetensdata tillgänglig för det valda filtret.")

    with col_geo:
        loc_df = get_location_distribution(db)
        if not loc_df.empty:
            fig_loc = px.pie(
                loc_df,
                values="count",
                names="location",
                title="Geografisk fördelning (Östergötland)",
                hole=0.5,
                color_discrete_sequence=["#1e40af", "#3b82f6", "#60a5fa", "#93c5fd", "#cbd5e1"],
            )
            fig_loc.update_traces(textposition="inside", textinfo="percent+label")
            fig_loc.update_layout(
                height=480,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"family": "Plus Jakarta Sans, sans-serif"},
                margin=dict(l=10, r=10, t=50, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("Ingen ortsdata tillgänglig.")

    st.markdown("---")
    
    col_emp, col_cat = st.columns([3, 2])
    
    with col_emp:
        st.markdown("#### 🏢 Mest aktiva uppdragsgivare i regionen")
        top_emp_df = get_top_employers(db, limit=10)
        if not top_emp_df.empty:
            fig_emp = px.bar(
                top_emp_df,
                x="count",
                y="company",
                orientation="h",
                color="location",
                title="Arbetsgivare och mäklare med flest öppna förfrågningar",
                labels={"company": "Företag / Uppdragsgivare", "count": "Aktiva behov", "location": "Ort"},
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_emp.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"family": "Plus Jakarta Sans, sans-serif"},
                margin=dict(l=10, r=20, t=50, b=20),
            )
            fig_emp.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
            st.plotly_chart(fig_emp, use_container_width=True)
            
    with col_cat:
        st.markdown("#### 🧩 Efterfrågan per teknikområde")
        cat_df = get_category_distribution(db)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                values="count",
                names="category",
                title="Fördelning per kompetensvertikal",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_cat.update_layout(
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"family": "Plus Jakarta Sans, sans-serif"},
                margin=dict(l=10, r=10, t=50, b=20),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

# ----------------- TAB 2: LEAD EXPLORER -----------------
with tab_leads:
    st.markdown("#### 💼 Affärsmöjligheter & Lead Pipeline")
    st.caption("Filtrera, sök och granska kundbehov för snabb kontakt eller konsultpitch.")
    
    col_search, col_skill_filter, col_limit = st.columns([3, 2, 1])
    with col_search:
        search_query = st.text_input("🔍 Fritextsökning", "", placeholder="T.ex. .NET, Azure, Saab, säkerhet, DevOps...")
    with col_skill_filter:
        skills_in_db = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        selected_skill = st.selectbox("🎯 Filtrera på specifik kompetens", ["Alla"] + skills_in_db)
    with col_limit:
        max_leads = st.selectbox("Visa antal", [20, 50, 100], index=1)

    leads_list = get_filtered_leads(
        db,
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        limit=max_leads,
    )

    # Export to CSV action
    if leads_list:
        leads_df = pd.DataFrame(leads_list)
        csv_data = leads_df.drop(columns=["description"]).to_csv(index=False).encode("utf-8")
        
        col_count, col_download = st.columns([4, 1])
        with col_count:
            st.markdown(f"Visar **{len(leads_list)}** matchande affärsmöjligheter:")
        with col_download:
            st.download_button(
                label="📥 Exportera till Excel/CSV",
                data=csv_data,
                file_name=f"leads_ostergotland_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    for lead in leads_list:
        source_badge = (
            '<span class="badge badge-brainville">⚡ Brainville • Konsultförfrågan</span>'
            if lead["is_consultant"]
            else '<span class="badge badge-jobtech">🏢 JobTech • Rekryteringslead</span>'
        )
        
        skill_badges = "".join([f'<span class="badge badge-skill">{s}</span>' for s in lead["skills"]])
        
        url_button = (
            f'<a href="{lead["url"]}" target="_blank" class="action-btn">Granska & Ansök ↗</a>'
            if lead["url"]
            else '<span style="color:#94a3b8; font-size:0.8rem;">Ingen extern länk</span>'
        )

        st.markdown(
            f"""
            <div class="lead-card">
                <div class="lead-header">
                    <div>
                        <div class="lead-title">{lead['title']}</div>
                        <div class="lead-meta">
                            <span class="lead-meta-item">🏢 <strong>{lead['company_name']}</strong></span>
                            <span class="lead-meta-item">📍 {lead['location']}</span>
                            <span class="lead-meta-item">📅 Publicerad: {lead['published_at']}</span>
                            <span class="lead-meta-item">⏳ Deadline: {lead['deadline']}</span>
                        </div>
                    </div>
                    <div>{source_badge}</div>
                </div>
                <div style="margin-bottom: 12px;">{skill_badges}</div>
                <div style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin-bottom: 14px;">
                    {lead['description'][:280] + '...' if lead['description'] else 'Kravprofil finns i originalannonsen.'}
                </div>
                <div style="display: flex; justify-content: flex-end;">
                    {url_button}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------- TAB 3: STRATEGISKA BESLUT -----------------
with tab_strategy:
    st.markdown("#### 🎯 Strategiskt Ledningsunderlag för Östergötland")
    st.caption("Handlingsplaner och prioriteringar baserade på aggregerad marknadsdata.")
    
    st.markdown(
        """
        <div class="insight-card priority-high">
            <div class="insight-title">
                <span>1. Molntjänster & Modern Plattform (Azure & DevOps)</span>
                <span style="font-size: 0.75rem; background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 6px;">HÖG PRIORITET</span>
            </div>
            <p class="insight-body">
                Azure och tillhörande DevOps-verktyg (Terraform, CI/CD, Kubernetes) dominerar både Linköping och Norrköping. Detta drivs av att såväl industri som offentlig förvaltning accelererar sin migration.
            </p>
            <div class="insight-rec">
                👉 <strong>Ledningsåtgärd:</strong> Säkerställ certifieringsmål inom Azure (AZ-104/AZ-204/AZ-400) bland befintliga konsulter och prioritera seniora Cloud Engineers vid nyrekrytering.
            </div>
        </div>

        <div class="insight-card priority-growth">
            <div class="insight-title">
                <span>2. Inbyggda System & Systemnära Utveckling (C++, Linux, Försvar)</span>
                <span style="font-size: 0.75rem; background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 6px;">TILLVÄXTOMRÅDE</span>
            </div>
            <p class="insight-body">
                Linköpings starka ställning inom försvar och flygindustri (Saab, Sectra, Combitech-ekosystemet) skapar en konstant efterfrågan på C++ och realtidssystem med krav på svenskt medborgarskap och säkerhetsprövning.
            </p>
            <div class="insight-rec">
                👉 <strong>Ledningsåtgärd:</strong> Bygg ett nischat erbjudande inom säkerhetsklassade uppdrag och upprätta förhandskontroller inför kommande ramavtalsupphandlingar.
            </div>
        </div>

        <div class="insight-card priority-strategic">
            <div class="insight-title">
                <span>3. Informationssäkerhet & Regulatoriska Krav (NIS2 & ISO 27001)</span>
                <span style="font-size: 0.75rem; background: #ede9fe; color: #5b21b6; padding: 3px 8px; border-radius: 6px;">STRATEGISK RÅDGIVNING</span>
            </div>
            <p class="insight-body">
                Med det nya NIS2-direktivet söker både kommuner, regioner och industriella leverantörer specialistkompetens inom riskhantering, säkerhetsarkitektur och efterlevnad.
            </p>
            <div class="insight-rec">
                👉 <strong>Ledningsåtgärd:</strong> Paketera ett <em>"NIS2 Gap Analysis & Compliance Package"</em> för direktförsäljning till medelstora bolag och offentliga beställare i Norrköping/Linköping.
            </div>
        </div>

        <div class="insight-card">
            <div class="insight-title">
                <span>4. Dataplattformar & Analytics (Databricks, Power BI, Python)</span>
                <span style="font-size: 0.75rem; background: #e0f2fe; color: #075985; padding: 3px 8px; border-radius: 6px;">ETABLERAD EFTERFRÅGAN</span>
            </div>
            <p class="insight-body">
                Företag rör sig snabbt bort från fragmenterade Excel-ark mot enhetliga datalager (Data Lakehouse) för att möjliggöra framtida AI-initiativ.
            </p>
            <div class="insight-rec">
                👉 <strong>Ledningsåtgärd:</strong> Etablera partnerskap kring Databricks och Microsoft Fabric samt positionera konsulter som Data Platform Engineers snarare än traditionella rapportbyggare.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

db.close()
