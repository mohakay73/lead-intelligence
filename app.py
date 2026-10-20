import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database.connection import init_db, SessionLocal
from database.models import Skill
from analytics.trend_engine import (
    get_overview_kpis,
    get_skill_demand,
    get_location_distribution,
    get_category_distribution,
    get_top_employers,
    get_filtered_leads,
)
from ingestion.pipeline import run_pipeline

# Configure Streamlit page
st.set_page_config(
    page_title="Marknadsintelligens & Beslutsstöd | Östergötland",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    .badge-brainville {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }
    .badge-jobtech {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .badge-skill {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize database
init_db()
db = SessionLocal()

# ----------------- SIDEBAR -----------------
st.sidebar.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
st.sidebar.title("Ledningsstöd Östergötland")
st.sidebar.caption("Norrköping & Linköping Marknadsöversikt")

st.sidebar.markdown("---")
selected_location = st.sidebar.selectbox(
    "📍 Välj Ort / Område",
    ["Alla", "Linköping", "Norrköping", "Motala", "Finspång"],
)

selected_source = st.sidebar.selectbox(
    "🔌 Datakälla",
    ["Alla", "brainville", "jobtech"],
    format_func=lambda x: "Alla källor" if x == "Alla" else ("Brainville (Konsult)" if x == "brainville" else "JobTech (Publika jobb)"),
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Datainsamling")
if st.sidebar.button("Kör Live-synkning (APIs)", use_container_width=True):
    with st.spinner("Hämtar data från Arbetsförmedlingen JobTech och Brainville API..."):
        try:
            stats = run_pipeline()
            st.sidebar.success(
                f"Klar! Nya leads: {stats['new_leads_saved']}, Uppdaterade: {stats['existing_leads_updated']}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Ett fel uppstod vid synkning: {e}")

st.sidebar.info(
    "💡 **Tips:** Kör synkningen för att automatiskt hämta färska uppdrag från Östergötland."
)

# ----------------- TOP METRICS -----------------
st.title("🎯 Automatisering & Intelligenta Underlag för Ledning")
st.markdown(
    "*Beslutsunderlag för bemanning, rekrytering och säljmöjligheter i Östergötland.*"
)

kpis = get_overview_kpis(db)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Totala Aktiva Leads", kpis["total_leads"], help="Alla unika identifierade uppdrag och jobb i regionen")
with col2:
    st.metric("Konsultuppdrag (Brainville)", kpis["consultant_leads"], help="Direkta konsultförfrågningar och mäklaruppdrag")
with col3:
    st.metric("Arbetsmarknadsleads (JobTech)", kpis["jobtech_leads"], help="Publika IT-tjänster från Arbetsförmedlingen")
with col4:
    st.metric("Aktiva Uppdragsgivare", kpis["unique_employers"], help="Unika företag/organisationer med behov")

st.markdown("---")

# If no data in DB yet, show helper message
if kpis["total_leads"] == 0:
    st.warning("⚠️ Databasen är tom. Klicka på **'Kör Live-synkning (APIs)'** i vänstermenyn för att hämta live-uppdrag!")

# ----------------- TABS -----------------
tab_market, tab_leads, tab_strategy = st.tabs([
    "📊 Marknad & Kompetensefterfrågan",
    "💼 Affärsmöjligheter & Lead Explorer",
    "📈 Strategiskt Beslutsstöd & Trender",
])

# ----- TAB 1: MARKNAD -----
with tab_market:
    st.subheader("🔥 Mest Efterfrågade Kompetenser i Regionen")
    
    skill_df = get_skill_demand(db, location=selected_location, source=selected_source, top_n=15)
    
    col_chart, col_geo = st.columns([3, 2])
    
    with col_chart:
        if not skill_df.empty:
            fig = px.bar(
                skill_df,
                x="count",
                y="skill",
                orientation="h",
                color="category",
                title=f"Toppkompetenser ({selected_location})",
                labels={"count": "Antal förfrågningar", "skill": "Kompetens", "category": "Kategori"},
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450, margin=dict(l=20, r=20, t=40, b=20))
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
                title="Geografisk Fördelning (Östergötland)",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_loc.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("Ingen ortsdata tillgänglig.")

    st.markdown("---")
    st.subheader("🏢 Mest Aktiva Uppdragsgivare & Kunder")
    top_emp_df = get_top_employers(db, limit=8)
    if not top_emp_df.empty:
        fig_emp = px.bar(
            top_emp_df,
            x="company",
            y="count",
            color="location",
            title="Arbetsgivare/Uppdragsgivare med flest öppna behov",
            labels={"company": "Företag / Organisation", "count": "Antal behov", "location": "Ort"},
        )
        fig_emp.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_emp, use_container_width=True)


# ----- TAB 2: LEADS EXPLORER -----
with tab_leads:
    st.subheader("🔍 Sök & Filtrera Uppdrag och Tjänster")
    
    col_search, col_skill_filter = st.columns([3, 2])
    with col_search:
        search_query = st.text_input("Fritextsökning (roll, företag, teknik...)", "")
    
    with col_skill_filter:
        skills_in_db = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        selected_skill = st.selectbox("Filtrera på specifik kompetens", ["Alla"] + skills_in_db)

    leads_list = get_filtered_leads(
        db,
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        limit=40,
    )

    st.write(f"Visar **{len(leads_list)}** matchande affärsmöjligheter:")

    for lead in leads_list:
        with st.container():
            source_badge = (
                f'<span class="badge badge-brainville">⚡ Brainville (Konsult)</span>'
                if lead["is_consultant"]
                else f'<span class="badge badge-jobtech">🏢 JobTech (Rekrytering)</span>'
            )
            
            skill_badges = "".join([f'<span class="badge badge-skill">{s}</span>' for s in lead["skills"]])
            
            st.markdown(
                f"""
                <div class="metric-card" style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0 0 6px 0; color: #0f172a;">{lead['title']}</h4>
                            <p style="margin: 0 0 8px 0; color: #475569; font-size: 0.9rem;">
                                <strong>{lead['company_name']}</strong> • 📍 {lead['location']} • Publicerad: {lead['published_at']} • Deadline: {lead['deadline']}
                            </p>
                        </div>
                        <div>{source_badge}</div>
                    </div>
                    <div style="margin-top: 6px; margin-bottom: 8px;">{skill_badges}</div>
                    <p style="color: #64748b; font-size: 0.85rem; margin: 0 0 8px 0;">
                        {lead['description'][:240] + '...' if lead['description'] else 'Ingen beskrivning angiven.'}
                    </p>
                    {f'<a href="{lead["url"]}" target="_blank" style="font-size: 0.85rem; text-decoration: none; font-weight: bold; color: #2563eb;">🔗 Öppna uppdragsannons &rarr;</a>' if lead["url"] else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ----- TAB 3: STRATEGISKT BESLUTSSTÖD -----
with tab_strategy:
    st.subheader("📈 Strategiskt Beslutsstöd för Kontorsledningen")
    
    col_cat, col_insights = st.columns([2, 3])
    
    with col_cat:
        cat_df = get_category_distribution(db)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                values="count",
                names="category",
                title="Fördelning per Kompetensområde",
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
    with col_insights:
        st.markdown("#### 🎯 Insikter & Riktningar för Östergötland")
        st.markdown(
            """
            Baserat på aggregerad marknadsdata för Linköping och Norrköping:
            
            1. **Moln & Infrastruktur (Azure & DevOps):**
               - Fortsatt stark efterfrågan inom både privat industri och offentlig sektor i regionen.
               - *Rekommendation:* Säkerställ hög certifieringsgrad inom Azure och Terraform bland konsulterna.
               
            2. **Systemnära och Inbyggda System (.NET, C++, Embedded):**
               - Särskilt framträdande i Linköping (Mjärdevi & försvars-/industriklustret).
               - *Rekommendation:* Fokusera rekrytering på seniora C++ och .NET-utvecklare med säkerhetsklassningspotential.
               
            3. **Cybersäkerhet & Informationssäkerhet (NIS2):**
               - Tydlig ökning i förfrågningar kopplat till regulatoriska krav och NIS2.
               - *Rekommendation:* Proaktiv kunddialog kring gapanalyser och rådgivning.
               
            4. **Data & AI (Databricks, Power BI, LLM):**
               - Kunder rör sig från enskilda BI-rapporter till samlade dataplattformar.
               - *Rekommendation:* Paketera erbjudanden kring modern data-stack.
            """
        )

db.close()

