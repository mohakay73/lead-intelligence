"""
View 1: Marknadsöversikt & Efterfrågan (Market Overview & Demand)
"""
import streamlit as st
import plotly.express as px
from ui.styles import (
    render_html,
    style_chart,
    style_pie,
    CONSID_PALETTE,
    CONSID_GEO_PALETTE,
)


def render_market_overview(
    kpis: dict,
    selected_location: str,
    selected_source: str,
    cached_skill_demand,
    cached_top_employers,
    cached_location_distribution,
    cached_category_distribution,
):
    """Renders regional market demand overview and distribution dashboards."""
    # Macro KPI Grid
    render_html(
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
        """
    )

    if kpis.get("archived_leads", 0) > 0:
        st.markdown(
            f"""
            <div style="font-size:0.75rem; color:#64748b; margin-top:8px; margin-bottom:18px;">
                📁 <b>Automatisk livscykelhantering:</b> <b>{kpis['archived_leads']}</b> utgångna eller avslutade uppdrag är arkiverade. De räknas bort från aktiva behov men bevaras i databasen för historik och AI-trendanalys.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Row 1: Competencies (left) & Top Employers (right) - Balanced Bar Charts
    col_skills, col_emp = st.columns(2)
    with col_skills:
        loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
        st.markdown(f"###### Mest efterfrågade kompetenser ({loc_label})")
        skill_df = cached_skill_demand(location=selected_location, source=selected_source, top_n=12)
        if not skill_df.empty:
            fig_skills = px.bar(
                skill_df,
                x="count",
                y="skill",
                orientation="h",
                color="category",
                labels={"count": "Behov", "skill": "Kompetens", "category": "Kategori"},
                color_discrete_sequence=CONSID_PALETTE,
            )
            fig_skills.update_layout(yaxis={"categoryorder": "total ascending"})
            style_chart(fig_skills, height=390, show_legend=True)
            st.plotly_chart(fig_skills, use_container_width=True)
        else:
            st.info("Ingen kompetensdata tillgänglig för det valda filtret.")

    with col_emp:
        loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
        st.markdown(f"###### Mest aktiva uppdragsgivare ({loc_label})")
        top_emp_df = cached_top_employers(location=selected_location, source=selected_source, limit=12)
        if not top_emp_df.empty:
            fig_emp = px.bar(
                top_emp_df,
                x="count",
                y="company",
                orientation="h",
                color="location",
                labels={"company": "Organisation", "count": "Behov", "location": "Ort"},
                color_discrete_sequence=CONSID_GEO_PALETTE,
            )
            fig_emp.update_layout(yaxis={"categoryorder": "total ascending"})
            style_chart(fig_emp, height=390, show_legend=True)
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.info("Inga arbetsgivare matchar det valda filtret.")

    st.markdown("---")

    # Row 2: Geography (left) & Technical Verticals (right) - Balanced Donut Charts
    col_geo, col_cat = st.columns(2)
    with col_geo:
        st.markdown("###### Geografisk fördelning av uppdrag")
        loc_df = cached_location_distribution(source=selected_source)
        if not loc_df.empty:
            fig_loc = px.pie(
                loc_df,
                values="count",
                names="location",
                hole=0.55,
                color_discrete_sequence=CONSID_GEO_PALETTE,
            )
            fig_loc.update_traces(textposition="inside", textinfo="percent+label")
            style_pie(fig_loc, height=350)
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("Ingen ortsdata tillgänglig.")

    with col_cat:
        st.markdown("###### Fördelning per tekniskt område")
        cat_df = cached_category_distribution(location=selected_location, source=selected_source)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                values="count",
                names="category",
                hole=0.55,
                color_discrete_sequence=CONSID_PALETTE,
            )
            fig_cat.update_traces(textposition="inside", textinfo="percent+label")
            style_pie(fig_cat, height=350)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Ingen kategoridata tillgänglig.")
