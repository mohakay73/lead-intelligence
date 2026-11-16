"""
View 3: Konsultmatchning & Bänkoptimering (Bench Matching & Deal Economics)
"""
import html
import json
import streamlit as st

from database.connection import SessionLocal
from ingestion.cinode_client import is_live_cinode_configured, sync_cinode_to_database
from analytics.bench_matcher import PRESET_BENCH_PROFILES
from ingestion.normalizer import extract_skills_from_text
from analytics.deal_economics import suggest_consultant_economics, calculate_deal_economics
from analytics.trend_engine import update_lead_status
from ui.styles import render_html, get_status_badge_html


def render_consultant_matching(
    db,
    selected_location: str,
    cached_cinode_consultants,
    cached_skills_list,
    cached_consultant_matches,
):
    """Renders consultant matching from Cinode and deal economics calculator."""
    col_v3_h1, col_v3_h2 = st.columns([3, 1])
    with col_v3_h1:
        st.markdown("##### Konsultmatchning & Bänkoptimering (Cinode)")
        st.caption("Matcha tillgängliga konsulter från Cinode mot regionens aktiva IT-krav med kompetensnivåer (1–5), CV-highlights och automatiska säljpitchar.")
    with col_v3_h2:
        cinode_mode = "Live API" if is_live_cinode_configured() else "Sandbox (Consid)"
        st.caption(f"Källa: **Cinode** ({cinode_mode})")
        if st.button("🔄 Synka med Cinode", key="btn_sync_cinode", use_container_width=True):
            with st.spinner("Hämtar profiler och CV-kompetenser från Cinode..."):
                with SessionLocal() as sync_db:
                    sync_res = sync_cinode_to_database(sync_db)
                st.cache_data.clear()
                st.toast(f"Synkroniserat {sync_res.get('synced_count', 0)} konsulter från Cinode!")
                st.rerun()

    # Load synchronized Cinode consultants from database
    db_consultants = cached_cinode_consultants(office="Alla")

    profile_options = []
    profile_dict_map = {}

    if db_consultants:
        for c in db_consultants:
            label = f"👤 {c['name']} – {c['title']} ({c['office']}) • [{c['availability_status']}]"
            profile_options.append(label)
            profile_dict_map[label] = {
                "name": c["name"],
                "title": c["title"],
                "office": c["office"],
                "location": c["office"],
                "availability_status": c["availability_status"],
                "available_from": str(c["available_from"]) if c["available_from"] else c["availability_status"],
                "skills": [s["name"] for s in c.get("skills_with_levels", [])],
                "skills_with_levels": c.get("skills_with_levels", []),
                "resume_summary": c.get("resume_summary", ""),
                "summary": c.get("resume_summary", ""),
                "security_clearance": c.get("security_clearance", False),
                "clearance": c.get("security_clearance", False),
                "is_cinode": True,
            }
    else:
        for p in PRESET_BENCH_PROFILES:
            label = f"{p['name']} – {p['title']} ({p['location']})"
            profile_options.append(label)
            profile_dict_map[label] = p

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
        active_consultant = profile_dict_map[chosen_profile_label]

        skills_pills_list = []
        if active_consultant.get("skills_with_levels"):
            for s in active_consultant["skills_with_levels"]:
                lvl = s.get("level", 3)
                stars = "★" * lvl + "☆" * (5 - lvl)
                skills_pills_list.append(f'<span class="skill-tag" title="Cinode-nivå {lvl}/5">{html.escape(s["name"])} <span style="font-size:0.75rem; color:#f59e0b;">{stars}</span></span>')
        else:
            for s in active_consultant.get("skills", []):
                skills_pills_list.append(f'<span class="skill-tag">{html.escape(s)}</span>')
        skills_pills = "".join(skills_pills_list)

        clearance_text = " • 🛡️ Säkerhetsprövad (RK3/SUA)" if active_consultant.get("clearance") or active_consultant.get("security_clearance") else ""
        avail_badge = active_consultant.get("availability_status") or active_consultant.get("available_from") or "Tillgänglig"

        cinode_badge = '<span style="font-size:0.75rem; font-weight:600; background:rgba(181,34,63,0.12); color:#B5223F; padding:2px 8px; border-radius:12px; margin-left:6px;">Cinode-profil</span>' if active_consultant.get("is_cinode") else ""

        cv_excerpt = active_consultant.get("resume_summary") or active_consultant.get("summary") or ""
        cv_html = f'<div style="font-size: 0.85rem; opacity: 0.88; line-height: 1.5; margin-bottom: 12px; background: rgba(0,0,0,0.02); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #B5223F;"><strong>CV-utdrag:</strong> {html.escape(cv_excerpt)}</div>' if cv_excerpt else ""

        consultant_econ = suggest_consultant_economics(active_consultant.get("title", ""), active_consultant.get("seniority", ""))
        bench_cost_str = f"{consultant_econ['monthly_bench_cost']:,} kr/mån".replace(",", " ")

        render_html(
            f"""
            <div style="background: rgba(128, 128, 128, 0.04); border: 1px solid rgba(128, 128, 128, 0.18); border-radius: 8px; padding: 18px 20px; margin-bottom: 22px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: inherit;">{html.escape(active_consultant['name'])}{cinode_badge}</div>
                        <div style="font-size: 0.86rem; opacity: 0.8; margin-top: 2px;">{html.escape(active_consultant['title'])} • {html.escape(active_consultant.get('office') or active_consultant.get('location', 'Regionen'))}{html.escape(clearance_text)}</div>
                        <div style="font-size: 0.78rem; opacity: 0.72; margin-top: 3px;">💼 Riktpris: ~{consultant_econ['hourly_rate']} kr/h • Uppskattad bänkkostnad: ~{bench_cost_str}</div>
                    </div>
                    <div class="priority-pill p-growth">{html.escape(avail_badge)}</div>
                </div>
                {cv_html}
                <div>{skills_pills}</div>
            </div>
            """
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
        all_skills = cached_skills_list()

        custom_selected_skills = st.multiselect(
            "Kompetenser (extraherade automatiskt ur texten, justera vid behov)",
            all_skills,
            default=[s for s in detected_custom_skills if s in all_skills],
        )

        active_consultant = {
            "name": c_name_input,
            "title": c_role_input,
            "seniority": c_seniority_input,
            "office": c_loc_input,
            "location": c_loc_input,
            "availability_status": c_avail_input,
            "available_from": c_avail_input,
            "security_clearance": c_clear_input,
            "clearance": c_clear_input,
            "skills": custom_selected_skills,
            "skills_with_levels": [{"name": s, "level": 3} for s in custom_selected_skills],
            "resume_summary": raw_cv_text[:400] if raw_cv_text else f"{c_role_input} baserad i {c_loc_input}.",
            "summary": raw_cv_text[:400] if raw_cv_text else f"{c_role_input} baserad i {c_loc_input}.",
            "is_cinode": False,
        }

    skills_levels_json = json.dumps(active_consultant.get("skills_with_levels", []))

    matched_leads = cached_consultant_matches(
        consultant_name=active_consultant["name"],
        consultant_title=active_consultant["title"],
        consultant_location=active_consultant.get("office") or active_consultant.get("location", "Regionen"),
        consultant_skills_tuple=tuple(active_consultant["skills"]),
        clearance=active_consultant.get("security_clearance") or active_consultant.get("clearance", False),
        location_filter=selected_location if selected_location != "Alla" else None,
        min_match_pct=min_score,
        hide_recruiters=True,
        limit=25,
        resume_summary=active_consultant.get("resume_summary") or active_consultant.get("summary", ""),
        skills_with_levels_json=skills_levels_json,
    )

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

            status_badge = get_status_badge_html(lead.get("status", "Nytt"))

            cand_info = f'<span>Kandidat: <span class="lead-attr-strong">{html.escape(lead["candidate_name"])}</span></span>' if lead.get("candidate_name") else ''
            resp_info = f'<span>Ansvarig: <span class="lead-attr-strong">{html.escape(lead["assigned_to"])}</span></span>' if lead.get("assigned_to") else ''

            card_html = f"""
            <div class="lead-row">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        {score_pill} {source_tag} {status_badge}
                        <div class="lead-title-text" style="margin-top: 6px;">{html.escape(lead['title'])}</div>
                    </div>
                    <div>
                        {link_html}
                    </div>
                </div>
                <div class="lead-attributes">
                    <span>Beställare: <span class="lead-attr-strong">{html.escape(lead['company'] or 'Konfidentiell')}</span></span>
                    <span>Ort: <span class="lead-attr-strong">{html.escape(lead['location'] or 'Östergötland')}</span></span>
                    <span>Publicerad: <span>{html.escape(str(lead['published_at']))}</span></span>
                    {cand_info}
                    {resp_info}
                </div>
                <div style="margin-top: 8px; font-size: 0.8rem;">
                    <div style="margin-bottom: 4px;"><strong>Matchade krav:</strong> {matched_tags if matched_tags else '<span style="opacity:0.6;">Inga direkta teknikkrav</span>'}</div>
                    {f'<div style="margin-bottom: 4px;"><strong style="opacity:0.7;">Övriga krav i annons:</strong> {missing_tags}</div>' if missing_tags else ''}
                    {f'<div><strong style="color:#B5223F;">Konsultens mervärde:</strong> {bonus_tags}</div>' if bonus_tags else ''}
                </div>
            </div>
            """
            render_html(card_html)

            with st.expander(f"🎯 Säljpitch & Affärskalkylator ({active_consultant['name']} → {lead['company']})"):
                tab_pitch, tab_deal = st.tabs(["✉️ Säljpitch", "💰 Affärsvärde & Bänkkalkylator"])

                # --- Tab 2: Deal Economics ---
                with tab_deal:
                    consultant_econ = suggest_consultant_economics(active_consultant.get("title", ""), active_consultant.get("seniority", ""))
                    col_ec1, col_ec2 = st.columns(2)
                    with col_ec1:
                        deal_rate = st.slider(
                            "Debiterbart timarvode till kund (kr/h)",
                            min_value=750,
                            max_value=2000,
                            value=int(consultant_econ["hourly_rate"]),
                            step=25,
                            key=f"deal_rate_{lead['lead_id']}_{active_consultant['name']}",
                            help="Priset kunden betalar per timme. Standard baseras på konsultens roll och marknadsnivå.",
                        )
                    with col_ec2:
                        deal_months = st.slider(
                            "Uppskattad uppdragslängd (månader)",
                            min_value=1,
                            max_value=12,
                            value=6,
                            step=1,
                            key=f"deal_months_{lead['lead_id']}_{active_consultant['name']}",
                            help="Kontraktets beräknade löptid.",
                        )

                    st.markdown("**Konsultens lön & kostnad (justera för att få exakt vinst):**")
                    col_cost_type, col_cost_val = st.columns([1.6, 2.4])
                    with col_cost_type:
                        cost_mode = st.radio(
                            "Kostnadsmetod",
                            ["Månadslön (Fast anställd)", "Timkostnad (kr/h / Underkonsult)"],
                            key=f"cost_mode_{lead['lead_id']}_{active_consultant['name']}",
                            label_visibility="collapsed",
                        )
                    with col_cost_val:
                        if "Månadslön" in cost_mode:
                            def_salary = consultant_econ.get("monthly_salary", 58000)
                            c_salary = st.number_input(
                                "Månadslön (kr/mån)",
                                min_value=25000,
                                max_value=130000,
                                value=int(def_salary),
                                step=1000,
                                key=f"salary_{lead['lead_id']}_{active_consultant['name']}",
                                help="Konsultens fasta bruttomånadslön. Systemet lägger automatiskt till lagstadgad arbetsgivaravgift (31,42%), ITP-tjänstepension (8,0%) samt overhead."
                            )
                            deal_res = calculate_deal_economics(
                                hourly_rate=deal_rate,
                                duration_months=deal_months,
                                monthly_salary=c_salary,
                            )
                        else:
                            def_hourly_cost = consultant_econ.get("hourly_cost", 565)
                            c_hourly_cost = st.number_input(
                                "Intern timkostnad (kr/h)",
                                min_value=200,
                                max_value=1600,
                                value=int(def_hourly_cost),
                                step=25,
                                key=f"hourly_cost_{lead['lead_id']}_{active_consultant['name']}",
                                help="Konsultens direkta kostnad eller inköpspris per timme. Perfekt för underkonsulter och frilansare."
                            )
                            deal_res = calculate_deal_economics(
                                hourly_rate=deal_rate,
                                duration_months=deal_months,
                                hourly_cost=c_hourly_cost,
                            )

                    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                    with col_met1:
                        st.metric("Kontraktsvärde", deal_res["formatted_revenue"])
                    with col_met2:
                        st.metric("Konsultens Kostnad", f"{deal_res['hourly_cost']} kr/h")
                    with col_met3:
                        st.metric("Exakt Vinst (TB)", deal_res["formatted_margin"], delta=f"+{deal_res['hourly_profit']} kr/h")
                    with col_met4:
                        st.metric("Vinstmarginal", f"{deal_res['margin_pct']}%")

                    cost_info_detail = (
                        f"Månadslön {c_salary:,} kr + 31,42% soc + 8% ITP-pension + overhead = {deal_res['monthly_bench_cost']:,} kr/mån (~{deal_res['hourly_cost']} kr/h)."
                        if "Månadslön" in cost_mode
                        else f"Direkt timkostnad: {c_hourly_cost} kr/h (totalt {deal_res['formatted_cost']} under uppdraget)."
                    ).replace(",", " ")

                    st.caption(
                        f"💡 Vinst per debiterad timme: **+{deal_res['hourly_profit']} kr/h**. {cost_info_detail}"
                    )

                # --- Tab 1: Pitch ---
                with tab_pitch:
                    col_sp1, col_sp2 = st.columns([3, 1])
                    with col_sp1:
                        custom_sub = st.text_input("Föreslagen ämnesrad", value=lead["pitch_subject"], key=f"pitch_sub_{lead['lead_id']}_{active_consultant['name']}")
                    with col_sp2:
                        st.caption("Färdigt att kopiera & skicka")
                    custom_body = st.text_area("Säljmejl (redigerbart)", value=lead["pitch_body"], height=190, key=f"pitch_body_{lead['lead_id']}_{active_consultant['name']}")

                deal_note_snippet = f"Affärsvärde: {deal_res['formatted_revenue']} ({deal_rate} kr/h x {deal_months} mån, TB: {deal_res['formatted_margin']})"

                if st.button(f"🚀 Spara pitch & flytta till 'Pitch skickad'", key=f"pipe_save_{lead['lead_id']}_{active_consultant['name']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["lead_id"],
                        status="Pitch skickad",
                        assigned_to=active_consultant.get("office") or active_consultant.get("location", "Konsultchef"),
                        candidate_name=active_consultant["name"],
                        notes=f"Matchad med {active_consultant['name']} ({lead['match_score']}% match).\n{deal_note_snippet}\nÄmne: {custom_sub}",
                    )
                    st.toast(f"Uppdraget har sparats och flyttats till Säljpipeline som 'Pitch skickad' för {active_consultant['name']}!")
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("Inga uppdrag nådde den valda lägsta matchningsgraden. Prova att sänka matchningströskeln ovan.")
