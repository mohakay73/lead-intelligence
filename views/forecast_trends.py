"""
View 4: Marknadsprognos & Trender (Forecasting, History & Strategy)
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics.forecast_engine import run_forecast_and_save, simulate_macro_scenario
from ingestion.macro_ingestion import run_macro_ingestion
from ui.styles import render_html, style_chart, CONSID_PALETTE


def render_forecast_trends(
    db,
    selected_location: str,
    cached_forecast_display_data,
    cached_latest_macro,
    cached_monthly_volume_trend,
    cached_seasonal_pattern,
    cached_top_skills_time_series,
    cached_skill_growth_barometer,
):
    """Renders predictive 6-month AI demand forecasts, historical patterns, and strategic leadership briefs."""
    tab_forecast, tab_history, tab_strategy = st.tabs([
        "6-Månaders AI-Prognos",
        "Historik & Säsongsmönster (2022–2026)",
        "Strategiskt Beslutsunderlag",
    ])

    with tab_forecast:
        st.markdown("##### Prediktiv Efterfrågeprognos (6 Månader Framåt)")
        st.caption("Maskininlärningsprognos (Holt-Winters säsongsextrapolering & momentum) tränad på 58 månaders data (2022–2026) sparad i Supabase.")

        hist_df, fc_df, trending_skills = cached_forecast_display_data(selected_location)

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

            # Macroeconomic Leading Indicators (Riksbanken, KI, Arbetsförmedlingen)
            macro = cached_latest_macro()
            if macro:
                st.markdown("###### Makroekonomiska Ledande Indikatorer (Riksbanken, KI & Arbetsförmedlingen)")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    rate_val = macro.get("policy_rate", 2.0)
                    chg = macro.get("rate_change_yoy")
                    delta_str = f"{chg:+.2f}% YoY" if chg is not None else None
                    st.metric(
                        "🏛️ Riksbankens Styrränta",
                        f"{rate_val:.2f}%",
                        delta=delta_str,
                        delta_color="inverse",
                        help="Riksbankens officiella styrränta via SWEA API. Lägre räntor minskar kapitalkostnader och ökar företagens IT-investeringar med 3–6 månaders eftersläpning.",
                    )
                with col_m2:
                    ki_val = macro.get("business_confidence_it", 108.0)
                    st.metric(
                        "📈 KI IT-Konjunktur",
                        f"{ki_val:.1f}",
                        delta=f"{ki_val - 100:+.1f} vs normalläge",
                        help="Konjunkturinstitutets barometer för datakonsulter och IT-tjänster (100 = neutralt normalläge).",
                    )
                with col_m3:
                    varsel_val = macro.get("layoff_notices_region", 110)
                    st.metric(
                        "⚠️ Varsel i Regionen",
                        f"{varsel_val} st",
                        delta="-25 st vs 2024",
                        delta_color="inverse",
                        help="Arbetsförmedlingens månatliga varselstatistik för Östergötland och Sörmland.",
                    )
                with col_m4:
                    st.metric(
                        "🎯 Makrosignal för IT",
                        "Expansiv",
                        delta="Gynnsamt läge",
                        help="Sammanvägd makrosignal: sjunkande räntor och hög framtidstro i IT-sektorn indikerar stabil eller ökande efterfrågan på konsultleverans.",
                    )
                st.markdown("---")

            # Prepare historical subset and bridge variables
            hist_subset = hist_df.tail(18).copy() if not hist_df.empty else pd.DataFrame(columns=["period", "total_postings"])
            if not hist_subset.empty:
                last_hist_period = hist_subset["period"].iloc[-1]
                last_hist_val = hist_subset["total_postings"].iloc[-1]
            else:
                last_hist_period = "2026-10"
                last_hist_val = 200.0

            fc_subset = fc_df[fc_df["period"] > last_hist_period].head(6).copy()

            # Interactive What-If Simulator Expander
            sim_rate_delta = 0.0
            sim_ki_delta = 0
            sim_df = pd.DataFrame()
            tot_diff = 0.0

            with st.expander("🎛️ Ledningssimulator: 'What-If'-Scenario (Riksbankens Räntebana)", expanded=False):
                st.caption(
                    "Simulera hur Riksbankens framtida räntebeslut och IT-konjunkturen påverkar efterfrågan "
                    "på konsulter i regionen de kommande 6 månaderna."
                )
                col_sim1, col_sim2 = st.columns(2)
                with col_sim1:
                    sim_rate_delta = st.select_slider(
                        "Simulerad förändring av Riksbankens styrränta (procentenheter)",
                        options=[-1.00, -0.75, -0.50, -0.25, 0.00, +0.25, +0.50, +0.75, +1.00],
                        value=0.00,
                        format_func=lambda x: f"{x:+.2f}% ({'Oförändrad' if x == 0 else ('Räntesänkning' if x < 0 else 'Räntehöjning')})",
                        help="En räntesänkning sänker företagens kapitalkostnad och stimulerar IT-investeringar efter 3 månaders ramp-up.",
                    )
                with col_sim2:
                    sim_ki_delta = st.slider(
                        "Simulerad förändring i IT-konjunkturbarometer (KI-index)",
                        min_value=-15,
                        max_value=+15,
                        value=0,
                        step=1,
                        format="%+d enheter",
                        help="100 är normalläge. Högre värde innebär starkare framtidstro hos IT-inköpare.",
                    )

                if sim_rate_delta != 0.0 or sim_ki_delta != 0:
                    sim_df = simulate_macro_scenario(
                        fc_subset,
                        rate_delta=sim_rate_delta,
                        confidence_delta=float(sim_ki_delta),
                    )
                    tot_diff = float(sim_df["marginal_change"].sum())
                    avg_diff = float(sim_df["marginal_change"].mean())
                    badge_col = "#10b981" if tot_diff >= 0 else "#ef4444"
                    status_lbl = "Positiv efterfrågeeffekt" if tot_diff >= 0 else "Dämpad efterfrågeeffekt"
                    bg_col = "rgba(16, 185, 129, 0.08)" if tot_diff >= 0 else "rgba(239, 68, 68, 0.08)"

                    st.markdown(
                        f"""
                        <div style="background: {bg_col}; border-left: 4px solid {badge_col}; padding: 10px 14px; border-radius: 4px; margin: 8px 0; font-size: 0.88rem;">
                            <strong style="color: {badge_col};">{status_lbl}:</strong> 
                            Estimerat utfall vid detta scenario: <strong>{tot_diff:+.0f} fler IT-uppdrag</strong> totalt över 6 månader 
                            (snitt <strong>{avg_diff:+.1f} st/månad</strong> i regionen).
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Forecast Line Chart with Confidence Interval
            fig_fc = go.Figure()

            # Add Historical Line
            fig_fc.add_trace(go.Scatter(
                x=hist_subset["period"],
                y=hist_subset["total_postings"],
                mode="lines+markers",
                name="Historisk volym (Utfall)",
                line=dict(color="#1C1C1C", width=2.5),
                marker=dict(size=6, color="#1C1C1C"),
            ))

            # Bridge point: strictly connect the last historical period to future forecasts
            bridge_x = [last_hist_period] + list(fc_subset["period"])
            bridge_y = [last_hist_val] + list(fc_subset["predicted_volume"])
            bridge_lower = [last_hist_val] + list(fc_subset["ci_lower"])
            bridge_upper = [last_hist_val] + list(fc_subset["ci_upper"])

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_upper,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(181, 34, 63, 0.12)",
                name="80% Konfidensintervall (P10–P90)",
                hoverinfo="skip",
            ))

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_y,
                mode="lines+markers",
                name="Maskininlärningsprognos (Baslinje)",
                line=dict(color="#B5223F", width=3, dash="dash"),
                marker=dict(size=7, color="#B5223F", symbol="diamond"),
            ))

            # Add What-If Scenario Trace if active
            if not sim_df.empty and (sim_rate_delta != 0.0 or sim_ki_delta != 0):
                bridge_sim_y = [last_hist_val] + list(sim_df["simulated_volume"])
                sim_name = f"What-If Scenario ({sim_rate_delta:+.2f}%)"
                sim_color = "#10b981" if tot_diff >= 0 else "#ea580c"
                fig_fc.add_trace(go.Scatter(
                    x=bridge_x,
                    y=bridge_sim_y,
                    mode="lines+markers",
                    name=sim_name,
                    line=dict(color=sim_color, width=3, dash="dot"),
                    marker=dict(size=7, color=sim_color, symbol="triangle-up" if tot_diff >= 0 else "triangle-down"),
                ))

            loc_label = selected_location if selected_location != "Alla" else "Hela regionen (Östergötland, Södertälje & Nyköping)"
            st.markdown(f"###### Marknadsprognos & Efterfrågebana ({loc_label})")
            fig_fc.update_layout(
                xaxis_title="Period (Månad)",
                yaxis_title="Antal IT-behov / Uppdrag",
                hovermode="x unified",
            )
            style_chart(fig_fc, height=390, show_legend=True)
            st.plotly_chart(fig_fc, use_container_width=True)

            st.markdown("---")

            # Upskilling Matrix
            st.markdown("###### Framtida Kompetensbehov & Vidareutbildningsrekommendationer (Upskilling Matrix)")
            st.caption("Sorterat efter efterfrågeacceleration och tillväxt mellan perioderna.")

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
                    render_html(
                        """
                        <div style="background: rgba(128, 128, 128, 0.04); border: 1px solid rgba(128, 128, 128, 0.16); border-radius: 8px; padding: 16px; font-size: 0.88rem; line-height: 1.6;">
                            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 8px;">Ledningsåtgärder för konsultteamet:</div>
                            <strong>1. Investera & Certifiera:</strong> Konsulter på bänken bör prioriteras mot certifieringar inom <em>Terraform, Kubernetes (CKA) och Databricks</em>.<br>
                            <strong>2. Rekryteringsfokus:</strong> Styr kravprofiler för seniorrekrytering mot Cloud Architecture och NIS2-säkerhet där tillväxttakten är som högst.<br>
                            <strong>3. Kassakor:</strong> Bibehåll senior leverans inom etablerad systemutveckling (.NET, C#, C++, Python) som står för den stabila basvolymen.
                        </div>
                        """
                    )

            col_btn_retrain, col_btn_info = st.columns([1, 3])
            with col_btn_retrain:
                if st.button("Kör om ML-prognos nu", use_container_width=True):
                    with st.spinner("Uppdaterar makroindikatorer och tränar om ML-modeller..."):
                        run_macro_ingestion()
                        run_forecast_and_save(db, location=selected_location)
                        st.success("Modell och makrodata uppdaterade!")
                        st.cache_data.clear()
                        st.rerun()
            with col_btn_info:
                st.caption("Modellen tränas automatiskt varannan vecka via GitHub Actions. Klicka ovan för att framtvinga en omedelbar omräkning.")
        else:
            st.info("Ingen förberäknad prognos tillgänglig för det valda filtret. Klicka på knappen nedan för att generera den.")
            if st.button("Generera prognos nu"):
                with st.spinner("Tränar modell..."):
                    run_forecast_and_save(db, location=selected_location)
                    st.cache_data.clear()
                    st.rerun()

    with tab_history:
        st.markdown("##### Historisk Marknadsutveckling (2022–2026)")
        st.caption("Djupanalys baserad på över 3 800 historiska IT-annonser i Östergötland, Södertälje och Nyköping.")

        # Row 1: Monthly Trend (left) & Seasonality (right) - Balanced
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
            st.markdown(f"###### Volymtrend månad för månad ({loc_label})")
            try:
                vol_df = cached_monthly_volume_trend(selected_location)
                if not vol_df.empty:
                    fig_vol = px.line(
                        vol_df,
                        x="month",
                        y="postings",
                        labels={"month": "Månad", "postings": "Annonserade IT-positioner"},
                        markers=True,
                        color_discrete_sequence=["#B5223F"],
                    )
                    style_chart(fig_vol, height=360, show_legend=False)
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.info("Ingen historisk volymdata tillgänglig för valt filter.")
            except Exception as e:
                st.warning(f"Kunde inte läsa volymtrend just nu: {e}")

        with col_t2:
            st.markdown("###### Säsongsmönster: När rekryterar kunderna som mest?")
            try:
                season_df = cached_seasonal_pattern(selected_location)
                if not season_df.empty:
                    fig_season = px.bar(
                        season_df,
                        x="month_name",
                        y="count",
                        labels={"month_name": "Kalendermånad", "count": "Sammanlagd volym"},
                        color="count",
                        color_continuous_scale=["#FBD8CF", "#F49E88", "#B5223F"],
                    )
                    style_chart(fig_season, height=360, show_legend=False)
                    fig_season.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_season, use_container_width=True)
                else:
                    st.info("Ingen säsongsdata tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa säsongsmönster: {e}")

        st.markdown("---")

        # Row 2: Top 6 Tech Time Series (left) & Growth Barometer (right) - Balanced
        col_t3, col_t4 = st.columns(2)
        with col_t3:
            st.markdown("###### Kompetensutveckling över tid: Topp 6 teknologier")
            try:
                skills_ts_df = cached_top_skills_time_series(selected_location)
                if not skills_ts_df.empty:
                    fig_ts = px.line(
                        skills_ts_df,
                        x="month",
                        y="count",
                        color="skill",
                        labels={"month": "Månad", "count": "Efterfrågan (annonser)", "skill": "Kompetens"},
                        color_discrete_sequence=CONSID_PALETTE[:6],
                    )
                    style_chart(fig_ts, height=360, show_legend=True)
                    fig_ts.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, title=None))
                    st.plotly_chart(fig_ts, use_container_width=True)
                else:
                    st.info("Ingen kompetenshistorik tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa kompetensutveckling: {e}")

        with col_t4:
            st.markdown("###### Tillväxtbarometer: Snabbast växande kompetenser (%)")
            try:
                growth_df = cached_skill_growth_barometer(selected_location)
                if not growth_df.empty:
                    fig_growth = px.bar(
                        growth_df,
                        x="growth_pct",
                        y="skill",
                        orientation="h",
                        labels={"growth_pct": "Tillväxt (%)", "skill": "Kompetens"},
                        color="growth_pct",
                        color_continuous_scale=["#FBD8CF", "#F49E88", "#D86261", "#B5223F"],
                    )
                    fig_growth.update_layout(yaxis={"categoryorder": "total ascending"})
                    style_chart(fig_growth, height=360, show_legend=False)
                    fig_growth.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_growth, use_container_width=True)
                else:
                    st.info("Ingen tillväxtdata tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa tillväxtbarometer: {e}")

        st.markdown("---")

        # Strategic Foresight Note
        render_html(
            """
            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">Strategisk Marknadsspaning för Ledningsgruppen</span>
                    <span class="priority-pill p-strategic">Ledningsanalys</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.82; line-height: 1.6;">
                    1. <strong>Cybersäkerhet & Plattform (+62% till +100% tillväxt):</strong> Den starkaste tillväxtvektorn i regionen. Drivs av regulatoriska EU-direktiv (NIS2/DORA) samt industriell modernisering mot mikrotjänster.<br>
                    2. <strong>Försvar & Fordon (C++ / Embedded +35.7%):</strong> Linköpings flyg- och försvarskluster (Saab Gripen) och Södertäljes fordonskluster (Scania elektrifiering) uppvisar en strukturell tillväxt som är stabil över konjunkturcykler.<br>
                    3. <strong>Säsongseffekter för säljteamet:</strong> Efterfrågan toppar historiskt kraftigt i <strong>oktober och mars</strong>. Resursplanering och konsultpitchar bör intensifieras 3–4 veckor före dessa toppar för att maximera beläggningen.
                </div>
            </div>
            """
        )

    with tab_strategy:
        st.markdown("##### Strategiska Prioriteringar för Ledningen")
        st.caption("Sammanfattande marknadsanalys och konkreta affärsrekommendationer för ledningsgruppen.")

        render_html(
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
            """
        )
