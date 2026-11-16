"""
Consid Lead Intelligence Platform.
Main Application Controller & Multi-View Orchestrator.
"""
import sys
import json
import importlib
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

# Defensive reload in case database.models was cached in long-running processes (e.g. Streamlit Cloud)
if "database.models" in sys.modules and not hasattr(sys.modules["database.models"], "Consultant"):
    importlib.reload(sys.modules["database.models"])

from database.connection import init_db, SessionLocal
from database.models import Skill
from ingestion.cinode_client import (
    sync_cinode_to_database,
    get_available_consultants_from_db,
)
from analytics.trend_engine import (
    get_overview_kpis,
    get_skill_demand,
    get_location_distribution,
    get_category_distribution,
    get_top_employers,
    get_filtered_leads,
    get_pipeline_kpis,
    get_all_assignees,
    auto_archive_expired_leads,
)
from analytics.weekly_digest import build_weekly_intelligence_data
from analytics.historical_analytics import (
    get_monthly_volume_trend,
    get_top_skills_time_series,
    get_skill_growth_barometer,
    get_seasonal_pattern,
)
from analytics.forecast_engine import get_forecast_display_data
from analytics.bench_matcher import match_consultant_to_leads
from ingestion.pipeline import run_pipeline

# UI Design Tokens & View Modules
from ui.styles import (
    inject_custom_css,
    render_global_header,
    CONSID_LOGO_SVG,
)
from views.market_overview import render_market_overview
from views.opportunity_pipeline import render_opportunity_pipeline
from views.consultant_matching import render_consultant_matching
from views.forecast_trends import render_forecast_trends
from views.weekly_digest_view import render_weekly_digest

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Consid | Lead Intelligence Platform",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom typography, responsive design, and component tokens
inject_custom_css()

# ----------------- DATABASE INITIALIZATION (RUNS ONCE) -----------------
@st.cache_resource(show_spinner=False)
def setup_database(schema_version: int = 14):
    init_db()
    with SessionLocal() as s:
        auto_archive_expired_leads(s)
    try:
        from ingestion.macro_ingestion import run_macro_ingestion
        from analytics.feature_pipeline import run_feature_pipeline
        from analytics.forecast_engine import run_all_forecasts
        with SessionLocal() as s:
            sync_cinode_to_database(s)
        run_macro_ingestion()
        run_feature_pipeline()
        run_all_forecasts()
    except Exception as e:
        import logging
        logging.getLogger("DatabaseSetup").warning(f"Startup synchronization error: {e}")
    return True

setup_database(schema_version=14)
init_db()
with SessionLocal() as s:
    auto_archive_expired_leads(s)
db = SessionLocal()

# ----------------- HIGH-PERFORMANCE DATA CACHING -----------------
@st.cache_data(ttl=180, show_spinner=False)
def cached_overview_kpis():
    with SessionLocal() as s:
        return get_overview_kpis(s)

@st.cache_data(ttl=180, show_spinner=False)
def cached_skill_demand(location, source, top_n=12):
    with SessionLocal() as s:
        return get_skill_demand(s, location=location, source=source, top_n=top_n)

@st.cache_data(ttl=180, show_spinner=False)
def cached_top_employers(location, source, limit=12):
    with SessionLocal() as s:
        return get_top_employers(s, location=location, source=source, limit=limit)

@st.cache_data(ttl=180, show_spinner=False)
def cached_location_distribution(source):
    with SessionLocal() as s:
        return get_location_distribution(s, source=source)

@st.cache_data(ttl=180, show_spinner=False)
def cached_category_distribution(location, source):
    with SessionLocal() as s:
        return get_category_distribution(s, location=location, source=source)

@st.cache_data(ttl=120, show_spinner=False)
def cached_pipeline_kpis(location, hide_recruiters=True):
    with SessionLocal() as s:
        return get_pipeline_kpis(s, location=location, hide_recruiters=hide_recruiters)

@st.cache_data(ttl=300, show_spinner=False)
def cached_skills_list():
    with SessionLocal() as s:
        return [r[0] for r in s.query(Skill.name).order_by(Skill.name).all() if r[0]]

@st.cache_data(ttl=120, show_spinner=False)
def cached_assignees_list():
    with SessionLocal() as s:
        return get_all_assignees(s)

@st.cache_data(ttl=60, show_spinner=False)
def cached_filtered_leads(search_term, location, source, selected_skill, status, assigned_to, hide_recruiters, limit):
    with SessionLocal() as s:
        return get_filtered_leads(
            s,
            search_term=search_term,
            location=location,
            source=source,
            selected_skill=selected_skill,
            status=status,
            assigned_to=assigned_to,
            hide_recruiters=hide_recruiters,
            limit=limit,
        )

@st.cache_data(ttl=180, show_spinner=False)
def cached_consultant_matches(
    consultant_name,
    consultant_title,
    consultant_location,
    consultant_skills_tuple,
    clearance,
    location_filter,
    min_match_pct,
    hide_recruiters=True,
    limit=25,
    resume_summary="",
    skills_with_levels_json="",
):
    with SessionLocal() as s:
        skills_with_levels = []
        if skills_with_levels_json:
            try:
                skills_with_levels = json.loads(skills_with_levels_json)
            except Exception:
                skills_with_levels = []
        consultant_dict = {
            "name": consultant_name,
            "title": consultant_title,
            "location": consultant_location,
            "skills": list(consultant_skills_tuple),
            "skills_with_levels": skills_with_levels,
            "clearance": clearance,
            "resume_summary": resume_summary,
        }
        return match_consultant_to_leads(
            s,
            consultant=consultant_dict,
            location_filter=location_filter,
            min_match_pct=min_match_pct,
            hide_recruiters=hide_recruiters,
            limit=limit,
        )

@st.cache_data(ttl=180, show_spinner=False)
def cached_cinode_consultants(office="Alla"):
    with SessionLocal() as s:
        return get_available_consultants_from_db(s, office=office)

@st.cache_data(ttl=600, show_spinner=False)
def cached_forecast_display_data(location):
    with SessionLocal() as s:
        return get_forecast_display_data(s, location=location)

@st.cache_data(ttl=600, show_spinner=False)
def cached_latest_macro():
    with SessionLocal() as s:
        from ingestion.macro_ingestion import get_macro_indicators_df
        df = get_macro_indicators_df(s)
        if not df.empty:
            return df.iloc[-1].to_dict()
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def cached_monthly_volume_trend(location):
    with SessionLocal() as s:
        return get_monthly_volume_trend(s, location=location)

@st.cache_data(ttl=600, show_spinner=False)
def cached_seasonal_pattern(location):
    with SessionLocal() as s:
        return get_seasonal_pattern(s, location=location)

@st.cache_data(ttl=600, show_spinner=False)
def cached_top_skills_time_series(location):
    with SessionLocal() as s:
        return get_top_skills_time_series(s, location=location, top_n=6)

@st.cache_data(ttl=600, show_spinner=False)
def cached_skill_growth_barometer(location):
    with SessionLocal() as s:
        return get_skill_growth_barometer(s, location=location)

@st.cache_data(ttl=600, show_spinner=False)
def cached_weekly_digest(days_back=7):
    with SessionLocal() as s:
        return build_weekly_intelligence_data(s, days_back=days_back)

# ----------------- NAVIGATION & WORKSPACES -----------------
FUNCTION_VIEWS = [
    "Marknadsöversikt & Efterfrågan",
    "Uppdrag & Lead Pipeline",
    "Konsultmatchning & Bänkoptimering",
    "Marknadsprognos & Trender",
    "Ledningsrapport & Veckobrev",
]

if "selected_workspace_view" not in st.session_state or st.session_state.selected_workspace_view not in FUNCTION_VIEWS:
    st.session_state.selected_workspace_view = FUNCTION_VIEWS[0]

# ----------------- SIDEBAR -----------------
st.sidebar.markdown(
    f"""
    <div style="padding-bottom: 14px; margin-bottom: 16px; border-bottom: 1px solid rgba(181, 34, 63, 0.2);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            {CONSID_LOGO_SVG}
            <span style="font-size: 0.62rem; font-weight: 700; background: rgba(181, 34, 63, 0.12); color: #B5223F; border: 1px solid rgba(181, 34, 63, 0.25); border-radius: 9999px; padding: 2px 7px; text-transform: uppercase; letter-spacing: 0.06em;">Intelligence</span>
        </div>
        <div style="font-size: 0.76rem; opacity: 0.72; color: inherit; line-height: 1.35; margin-top: 5px;">Östergötland, Södertälje & Nyköping</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("**Arbetsvy**")
current_view = st.sidebar.radio(
    "Arbetsvy",
    FUNCTION_VIEWS,
    key="selected_workspace_view",
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

overview_kpis = cached_overview_kpis()
sync_time_str = "Nyligen"
if overview_kpis.get("latest_sync_at"):
    dt = overview_kpis["latest_sync_at"]
    cet_dt = dt + timedelta(hours=1)
    if cet_dt.date() == (datetime.utcnow() + timedelta(hours=1)).date():
        sync_time_str = f"Idag kl. {cet_dt.strftime('%H:%M')} CET"
    else:
        sync_time_str = cet_dt.strftime("%Y-%m-%d %H:%M CET")

new_today_count = overview_kpis.get("new_today", 0)
new_today_html = f' • <span style="color:#16a34a; font-weight:700;">+{new_today_count} nya idag</span>' if new_today_count > 0 else ""

st.sidebar.markdown("---")
st.sidebar.markdown("**Datainsamling**")
st.sidebar.markdown(
    f"""
    <div style="font-size:0.78rem; opacity:0.85; margin-bottom:8px; line-height:1.4;">
        🕒 Senaste insamling: <strong>{sync_time_str}</strong>{new_today_html}<br>
        📊 Aktiva marknadsbehov: <strong>{overview_kpis.get('total_leads', 0)} st</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("🔄 Uppdatera vy", use_container_width=True, help="Tömmer webbappens minnescache och hämtar senaste data direkt från databasen."):
        st.cache_data.clear()
        st.rerun()
with col_sb2:
    if st.button("Hämta nytt nu", use_container_width=True, help="Kör manuell insamling mot källorna omedelbart."):
        with st.spinner("Ansluter till källor och uppdaterar databas..."):
            try:
                stats = run_pipeline()
                st.sidebar.success(
                    f"Klar. Nya poster: {stats['new_leads_saved']}, Uppdaterade: {stats['existing_leads_updated']}"
                )
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Synkroniseringsfel: {e}")

st.sidebar.markdown(
    """
    <div style="background: rgba(181, 34, 63, 0.04); border: 1px solid rgba(181, 34, 63, 0.16); border-radius: 8px; padding: 12px; margin-top: 14px; font-size: 0.75rem; opacity: 0.85; color: inherit; line-height: 1.5;">
        <div style="font-weight: 700; color: #B5223F; margin-bottom: 4px;">Automatiserad drift (GitHub Actions)</div>
        • Datainsamling: Sön kl. 21:35 & vardagsnätter kl. 01:35 CET<br>
        • Veckorapport (Teams): Måndag natt kl. 02:17 CET (klar till morgonen)<br>
        • ML-modellträning: 1:a & 15:e i månaden
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- GLOBAL HEADER -----------------
render_global_header(current_view, sync_time_str, new_today_html)

# ----------------- VIEW DISPATCH ROUTER -----------------
if current_view == "Marknadsöversikt & Efterfrågan":
    render_market_overview(
        kpis=overview_kpis,
        selected_location=selected_location,
        selected_source=selected_source,
        cached_skill_demand=cached_skill_demand,
        cached_top_employers=cached_top_employers,
        cached_location_distribution=cached_location_distribution,
        cached_category_distribution=cached_category_distribution,
    )

elif current_view == "Uppdrag & Lead Pipeline":
    render_opportunity_pipeline(
        db=db,
        selected_location=selected_location,
        selected_source=selected_source,
        cached_pipeline_kpis=cached_pipeline_kpis,
        cached_skills_list=cached_skills_list,
        cached_filtered_leads=cached_filtered_leads,
    )

elif current_view == "Konsultmatchning & Bänkoptimering":
    render_consultant_matching(
        db=db,
        selected_location=selected_location,
        cached_cinode_consultants=cached_cinode_consultants,
        cached_skills_list=cached_skills_list,
        cached_consultant_matches=cached_consultant_matches,
    )

elif current_view == "Marknadsprognos & Trender":
    render_forecast_trends(
        db=db,
        selected_location=selected_location,
        cached_forecast_display_data=cached_forecast_display_data,
        cached_latest_macro=cached_latest_macro,
        cached_monthly_volume_trend=cached_monthly_volume_trend,
        cached_seasonal_pattern=cached_seasonal_pattern,
        cached_top_skills_time_series=cached_top_skills_time_series,
        cached_skill_growth_barometer=cached_skill_growth_barometer,
    )

elif current_view == "Ledningsrapport & Veckobrev":
    render_weekly_digest(
        cached_weekly_digest=cached_weekly_digest,
        base_dir=BASE_DIR,
    )

db.close()
