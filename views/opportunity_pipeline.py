"""
View 2: Uppdrag & Lead Pipeline (CRM & Pipeline Management)
"""
import html
from datetime import datetime
import pandas as pd
import streamlit as st

from analytics.trend_engine import update_lead_status
from analytics.pitch_generator import generate_sales_pitch
from ui.styles import render_html, get_status_badge_html


def render_opportunity_pipeline(
    db,
    selected_location: str,
    selected_source: str,
    cached_pipeline_kpis,
    cached_skills_list,
    cached_filtered_leads,
):
    """Renders the CRM Lead Pipeline with status updates and pitch generators."""
    col_head_title, col_rec_toggle = st.columns([3, 2])
    with col_head_title:
        st.markdown("##### Säljpipeline & Uppdragsflöde (Lead Pipeline CRM)")
        st.caption("Aktiv uppföljning och statusstyrning för regionala affärsmöjligheter från identifiering till tillsatt uppdrag.")
    with col_rec_toggle:
        include_recruiters = st.checkbox(
            "Inkludera rekryteringsbolag",
            value=False,
            help="Som standard döljs bemannings- och rekryteringsföretag (t.ex. Academic Work, Randstad) så att ni enbart ser direkta slutkunder och konsultuppdrag.",
        )
    hide_recruiters = not include_recruiters

    pipe_kpis = cached_pipeline_kpis(location=selected_location, hide_recruiters=hide_recruiters)

    # 1. Pipeline Funnel Summary Bar
    col_pk1, col_pk2, col_pk3, col_pk4, col_pk5, col_pk6 = st.columns(6)
    with col_pk1:
        render_html(
            f"""
            <div class="funnel-metric-card">
                <div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;">1. Nya Leads</div>
                <div style="font-size:1.45rem;font-weight:800;color:inherit;line-height:1.2;">{pipe_kpis['nytt']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Ohanterade</div>
            </div>
            """
        )
    with col_pk2:
        render_html(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(245,158,11,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#d97706;text-transform:uppercase;">2. Granskas</div>
                <div style="font-size:1.45rem;font-weight:800;color:#d97706;line-height:1.2;">{pipe_kpis['granskas']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Matchning pågår</div>
            </div>
            """
        )
    with col_pk3:
        render_html(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(181,34,63,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#B5223F;text-transform:uppercase;">3. Pitch skickad</div>
                <div style="font-size:1.45rem;font-weight:800;color:#B5223F;line-height:1.2;">{pipe_kpis['pitch']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Konsult presenterad</div>
            </div>
            """
        )
    with col_pk4:
        render_html(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(99,102,241,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#6366f1;text-transform:uppercase;">4. Intervju</div>
                <div style="font-size:1.45rem;font-weight:800;color:#6366f1;line-height:1.2;">{pipe_kpis['intervju']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Kundmöte bokat</div>
            </div>
            """
        )
    with col_pk5:
        render_html(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(16,185,129,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#059669;text-transform:uppercase;">5. Vunnet</div>
                <div style="font-size:1.45rem;font-weight:800;color:#059669;line-height:1.2;">{pipe_kpis['vunnet']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Tillsatt uppdrag</div>
            </div>
            """
        )
    with col_pk6:
        render_html(
            f"""
            <div class="funnel-metric-card">
                <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;">Arkiv / Avböjt</div>
                <div style="font-size:1.45rem;font-weight:800;color:#94a3b8;line-height:1.2;">{pipe_kpis['avböjt']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Avslutade & Arkiverade</div>
            </div>
            """
        )

    st.markdown("---")

    # 2. Filter & Controls
    col_search, col_status_filter, col_skill_filter, col_limit = st.columns([2.5, 1.8, 1.8, 1])
    with col_search:
        search_query = st.text_input("Sök i pipeline & uppdrag", "", placeholder="Sök roll, teknik, bolag, konsult...")
    with col_status_filter:
        pipeline_status_filter = st.selectbox(
            "Pipeline-status",
            ["Aktiva uppdrag", "Alla", "Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt", "Arkiverad"],
            index=0,
        )
    with col_skill_filter:
        skills_in_db = cached_skills_list()
        selected_skill = st.selectbox("Filtrera på kompetens", ["Alla"] + skills_in_db)
    with col_limit:
        max_leads = st.selectbox("Max antal", [25, 50, 100], index=1)

    leads_list = cached_filtered_leads(
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        status=pipeline_status_filter,
        assigned_to=None,
        hide_recruiters=hide_recruiters,
        limit=max_leads,
    )

    if leads_list:
        leads_df = pd.DataFrame(leads_list)
        csv_data = leads_df.drop(columns=["description"]).to_csv(index=False).encode("utf-8")

        col_count, col_download = st.columns([4, 1])
        with col_count:
            st.caption(f"Visar {len(leads_list)} matchande affärsmöjligheter i pipelinen.")
        with col_download:
            st.download_button(
                label="Exportera pipeline (.csv)",
                data=csv_data,
                file_name=f"consid_lead_pipeline_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Inga uppdrag matchar ditt valda filter just nu.")

    STATUS_ORDER = ["Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt", "Arkiverad"]

    for lead in leads_list:
        source_class = "source-consultant" if lead["is_consultant"] else "source-recruitment"
        source_text = "Konsultuppdrag" if lead["is_consultant"] else "Rekryteringsannons"
        recruiter_tag = '<span class="tag-source" style="background:rgba(239, 68, 68, 0.12);color:#dc2626;border:1px solid rgba(239, 68, 68, 0.35);font-size:0.7rem;">⚠️ Rekryteringsbolag</span>' if lead.get("is_recruiter") else ""
        status_html = get_status_badge_html(lead["status"])

        skill_tags = "".join([f'<span class="skill-tag">{html.escape(s)}</span>' for s in lead["skills"]])

        link_html = (
            f'<a href="{lead["url"]}" target="_blank" class="link-action">Visa källannons →</a>'
            if lead["url"]
            else '<span style="opacity:0.6; font-size:0.8rem;">Länk saknas</span>'
        )

        crm_meta_items = []
        if lead["assigned_to"]:
            crm_meta_items.append(f'<span>Ansvarig: <span class="pipeline-assignee">👤 {html.escape(lead["assigned_to"])}</span></span>')
        if lead["candidate_name"]:
            crm_meta_items.append(f'<span>Föreslagen konsult: <strong style="color:#B5223F;">⭐ {html.escape(lead["candidate_name"])}</strong></span>')
        crm_meta_html = " • ".join(crm_meta_items) if crm_meta_items else ""

        notes_html = f'<div class="pipeline-notes-box"><strong>Intern säljnotering:</strong> {html.escape(lead["notes"])}</div>' if lead["notes"] else ""
        desc_snippet = html.escape(lead["description"][:240]) + "..." if lead["description"] else "Detaljerad information finns i källsystemet."

        card_html = f"""
        <div class="lead-row">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        {status_html}
                        <span class="tag-source {source_class}">{source_text}</span>
                        {recruiter_tag}
                    </div>
                    <div class="lead-title-text">{html.escape(lead['title'])}</div>
                </div>
                <div>{link_html}</div>
            </div>
            <div class="lead-attributes">
                <span>Beställare: <span class="lead-attr-strong">{html.escape(lead['company_name'] or 'Konfidentiell')}</span></span>
                <span>Ort: <span class="lead-attr-strong">{html.escape(lead['location'] or 'Östergötland')}</span></span>
                <span>Publicerad: {html.escape(str(lead['published_at']))}</span>
                <span>Deadline: {html.escape(str(lead['deadline']))}</span>
            </div>
            {f'<div style="margin-bottom: 8px; font-size: 0.82rem;">{crm_meta_html}</div>' if crm_meta_html else ''}
            <div style="margin-bottom: 10px;">{skill_tags}</div>
            <div style="opacity: 0.8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 10px;">
                {desc_snippet}
            </div>
            {notes_html}
        </div>
        """
        render_html(card_html)

        # Action Hub: Pipeline Management & Sales Pitch
        col_act1, col_act2 = st.columns([1, 1])

        with col_act1:
            with st.expander(f"🎯 Uppdatera Pipeline & Status ({lead['company_name']})"):
                cur_idx = STATUS_ORDER.index(lead["status"]) if lead["status"] in STATUS_ORDER else 0
                new_status = st.selectbox(
                    "Ny pipeline-status",
                    STATUS_ORDER,
                    index=cur_idx,
                    key=f"pipe_status_{lead['id']}",
                )

                col_cm1, col_cm2 = st.columns(2)
                with col_cm1:
                    new_assignee = st.text_input(
                        "Ansvarig konsultchef/säljare",
                        value=lead["assigned_to"],
                        key=f"pipe_ass_{lead['id']}",
                        placeholder="T.ex. Erik S / Konsultchef Öst",
                    )
                with col_cm2:
                    new_candidate = st.text_input(
                        "Matchad konsult / kandidat",
                        value=lead["candidate_name"],
                        key=f"pipe_cand_{lead['id']}",
                        placeholder="T.ex. Anna A (Senior Fullstack)",
                    )

                new_notes = st.text_area(
                    "Säljanteckningar & kunddialog",
                    value=lead["notes"],
                    key=f"pipe_notes_{lead['id']}",
                    height=85,
                    placeholder="T.ex. Kontaktat kund via LinkedIn. Söker 1 senior konsult, intervjuer nästa tisdag...",
                )

                if st.button("Spara pipeline-ändringar", key=f"btn_save_pipe_{lead['id']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["id"],
                        status=new_status,
                        assigned_to=new_assignee,
                        candidate_name=new_candidate,
                        notes=new_notes,
                    )
                    st.toast("Pipeline sparad!")
                    st.cache_data.clear()
                    st.rerun()

        with col_act2:
            with st.expander(f"✉️ Skapa & Kopiera Säljpitch ({lead['company_name']})"):
                c_role_def = f"Senior specialist inom {', '.join(lead['skills'][:3]) if lead['skills'] else 'systemutveckling'}"
                c_role = st.text_input(
                    "Konsultens profil",
                    value=lead["candidate_name"] if lead["candidate_name"] else c_role_def,
                    key=f"role_{lead['id']}",
                )
                c_avail = st.text_input(
                    "Tillgänglig från",
                    value="inom 2–4 veckor",
                    key=f"avail_{lead['id']}",
                )

                pitch = generate_sales_pitch(lead, consultant_profile=c_role, available_from=c_avail)
                st.text_input("Ämnesrad", value=pitch["subject"], key=f"subj_{lead['id']}")
                st.text_area("Säljmejl", value=pitch["body"], height=130, key=f"body_{lead['id']}")

                if st.button("Markera som 'Pitch skickad' direkt", key=f"btn_fast_pitch_{lead['id']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["id"],
                        status="Pitch skickad",
                        candidate_name=c_role,
                        notes=f"Säljpitch genererad & skickad: {pitch['subject']}",
                    )
                    st.toast(f"Uppdraget flyttat till 'Pitch skickad' för {c_role}!")
                    st.cache_data.clear()
                    st.rerun()
