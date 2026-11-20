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


def _render_kanban_board(db, leads_list, pipe_kpis):
    """Renders visual 5-column Kanban board for active pipeline opportunities."""
    stages = [
        {
            "id": "Nytt",
            "title": "📥 1. Nytt",
            "color": "#64748b",
            "badge_bg": "rgba(100, 116, 139, 0.12)",
            "border": "rgba(100, 116, 139, 0.3)",
            "next_status": "Granskas",
            "next_btn": "Kvalificera ➡",
            "max_cards": 12,
        },
        {
            "id": "Granskas",
            "title": "🔍 2. Granskas",
            "color": "#d97706",
            "badge_bg": "rgba(245, 158, 11, 0.14)",
            "border": "rgba(245, 158, 11, 0.35)",
            "next_status": "Pitch skickad",
            "next_btn": "Skicka Pitch ➡",
            "max_cards": 30,
        },
        {
            "id": "Pitch skickad",
            "title": "✉️ 3. Pitch skickad",
            "color": "#B5223F",
            "badge_bg": "rgba(181, 34, 63, 0.12)",
            "border": "rgba(181, 34, 63, 0.35)",
            "next_status": "Intervju",
            "next_btn": "Boka Intervju ➡",
            "max_cards": 30,
        },
        {
            "id": "Intervju",
            "title": "🤝 4. Intervju",
            "color": "#6366f1",
            "badge_bg": "rgba(99, 102, 241, 0.14)",
            "border": "rgba(99, 102, 241, 0.35)",
            "next_status": "Vunnet",
            "next_btn": "Vinn affär 🏆",
            "max_cards": 30,
        },
        {
            "id": "Vunnet",
            "title": "🏆 5. Vunnet",
            "color": "#059669",
            "badge_bg": "rgba(16, 185, 129, 0.14)",
            "border": "rgba(16, 185, 129, 0.35)",
            "next_status": None,
            "next_btn": None,
            "max_cards": 30,
        },
    ]

    cols = st.columns(5)
    ALL_STATUSES = ["Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt", "Arkiverad"]

    for idx, stage in enumerate(stages):
        stage_id = stage["id"]
        if stage_id == "Nytt":
            stage_leads = [l for l in leads_list if l.get("status") in ("Nytt", None, "")]
        elif stage_id == "Vunnet":
            stage_leads = [l for l in leads_list if l.get("status") in ("Vunnet", "Tillsatt")]
        else:
            stage_leads = [l for l in leads_list if l.get("status") == stage_id]

        with cols[idx]:
            st.markdown(
                f"""
                <div style="background:{stage['badge_bg']}; border:1px solid {stage['border']}; border-radius:10px; padding:8px 12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.8rem; font-weight:700; color:{stage['color']}; text-transform:uppercase; letter-spacing:0.04em;">
                        {stage['title']}
                    </span>
                    <span style="font-size:0.75rem; font-weight:800; background:rgba(128,128,128,0.15); padding:2px 7px; border-radius:9999px;">
                        {len(stage_leads)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not stage_leads:
                st.markdown(
                    f"<div style='border:1px dashed {stage['border']}; border-radius:8px; padding:24px 10px; text-align:center; font-size:0.78rem; opacity:0.6; margin-bottom:12px;'>"
                    f"Inga uppdrag i detta steg"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                displayed = stage_leads[:stage["max_cards"]]
                for lead in displayed:
                    with st.container(border=True):
                        source_label = "Konsult" if lead.get("is_consultant") else "Rekrytering"
                        source_col = "#B5223F" if lead.get("is_consultant") else "#64748b"

                        st.markdown(
                            f"<div style='display:flex; justify-content:space-between; align-items:center; font-size:0.68rem; margin-bottom:4px;'>"
                            f"<span style='color:{source_col}; font-weight:700; text-transform:uppercase;'>{source_label}</span>"
                            f"<span style='opacity:0.6;'>{lead.get('published_at', '')}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                        title_text = lead['title']
                        if len(title_text) > 42:
                            title_text = title_text[:39] + "..."
                        st.markdown(f"**{html.escape(title_text)}**")

                        comp_text = f"🏢 {html.escape(lead['company_name'] or 'Konfidentiell')}"
                        loc_text = f"📍 {html.escape(lead['location'] or 'Regionen')}"
                        st.caption(f"{comp_text} • {loc_text}")

                        if lead.get("candidate_name"):
                            st.markdown(
                                f"<div style='font-size:0.75rem; color:#B5223F; font-weight:600; margin-bottom:4px;'>⭐ {html.escape(lead['candidate_name'])}</div>",
                                unsafe_allow_html=True,
                            )
                        if lead.get("assigned_to"):
                            st.markdown(
                                f"<div style='font-size:0.72rem; opacity:0.75; margin-bottom:6px;'>👤 {html.escape(lead['assigned_to'])}</div>",
                                unsafe_allow_html=True,
                            )

                        if stage["next_status"]:
                            if st.button(
                                stage["next_btn"],
                                key=f"kb_next_{stage_id}_{lead['id']}",
                                use_container_width=True,
                            ):
                                update_lead_status(db, lead_id=lead["id"], status=stage["next_status"])
                                st.toast(f"Uppdrag flyttat till {stage['next_status']}!")
                                st.cache_data.clear()
                                st.rerun()

                        with st.expander("Hantera ⚙️", expanded=False):
                            cur_st = lead.get("status") or "Nytt"
                            cur_idx = ALL_STATUSES.index(cur_st) if cur_st in ALL_STATUSES else 0
                            new_st = st.selectbox(
                                "Status",
                                ALL_STATUSES,
                                index=cur_idx,
                                key=f"kb_st_{stage_id}_{lead['id']}",
                            )
                            new_cand = st.text_input(
                                "Föreslagen konsult",
                                value=lead.get("candidate_name", ""),
                                key=f"kb_cand_{stage_id}_{lead['id']}",
                                placeholder="Konsultens namn",
                            )
                            new_ass = st.text_input(
                                "Ansvarig",
                                value=lead.get("assigned_to", ""),
                                key=f"kb_ass_{stage_id}_{lead['id']}",
                                placeholder="Konsultchef",
                            )
                            new_nt = st.text_area(
                                "Notering",
                                value=lead.get("notes", ""),
                                key=f"kb_nt_{stage_id}_{lead['id']}",
                                height=65,
                            )
                            if st.button("Spara ändringar", key=f"kb_save_{stage_id}_{lead['id']}", use_container_width=True):
                                update_lead_status(
                                    db,
                                    lead_id=lead["id"],
                                    status=new_st,
                                    assigned_to=new_ass,
                                    candidate_name=new_cand,
                                    notes=new_nt,
                                )
                                st.toast("Uppdrag sparat!")
                                st.cache_data.clear()
                                st.rerun()

                if len(stage_leads) > stage["max_cards"]:
                    st.caption(f"ℹ️ +{len(stage_leads) - stage['max_cards']} fler uppdrag. Växla till Listvy för komplett bläddring.")


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

    pipe_kpis = cached_pipeline_kpis(
        location=selected_location,
        hide_recruiters=hide_recruiters,
        source=selected_source,
    )

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

    # View Mode Switcher: List View vs. Kanban Board
    col_mode_head, col_mode_pick = st.columns([3, 2])
    with col_mode_head:
        st.markdown("###### Arbetsläge")
    with col_mode_pick:
        pipeline_view_mode = st.radio(
            "Visningsläge",
            ["📋 Listvy (Paginering)", "📊 Kanban-tavla"],
            horizontal=True,
            key="pipeline_view_mode",
            label_visibility="collapsed",
        )

    if pipeline_view_mode == "📊 Kanban-tavla":
        col_kb_search, col_kb_skill = st.columns([3, 2])
        with col_kb_search:
            kb_search = st.text_input("Sök i Kanban-tavlan", "", placeholder="Sök bolag, roll eller teknik...", key="kb_search_input")
        with col_kb_skill:
            skills_in_db = cached_skills_list()
            kb_skill = st.selectbox("Filtrera på kompetens", ["Alla"] + skills_in_db, key="kb_skill_input")

        kanban_leads = cached_filtered_leads(
            search_term=kb_search,
            location=selected_location,
            source=selected_source,
            selected_skill=kb_skill,
            status="Aktiva uppdrag",
            assigned_to=None,
            hide_recruiters=hide_recruiters,
            limit=1500,
        )
        _render_kanban_board(db, kanban_leads, pipe_kpis)
        return

    # 2. Filter & Controls
    col_search, col_status_filter, col_skill_filter, col_per_page = st.columns([2.5, 1.8, 1.8, 1])
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
    with col_per_page:
        per_page = st.selectbox(
            "Per sida",
            [15, 25, 50],
            index=1,
            help="Begränsar antalet kort som renderas samtidigt så att gränssnittet förblir blixtsnabbt.",
        )

    leads_list = cached_filtered_leads(
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        status=pipeline_status_filter,
        assigned_to=None,
        hide_recruiters=hide_recruiters,
        limit=1500,
    )

    if leads_list:
        total_leads = len(leads_list)
        total_pages = max(1, (total_leads + per_page - 1) // per_page)

        # Callback handlers for rock-solid Streamlit state sync
        def _nav_pipe_page(delta: int):
            cur = st.session_state.get("pipe_page_num", 1)
            nxt = max(1, min(cur + delta, total_pages))
            st.session_state["pipe_page_num"] = nxt
            st.session_state["pipe_page_select"] = nxt

        def _on_pipe_select_change():
            st.session_state["pipe_page_num"] = st.session_state.get("pipe_page_select", 1)

        # Reset to page 1 if search or filters changed
        current_filter_hash = (
            search_query,
            pipeline_status_filter,
            selected_skill,
            selected_location,
            selected_source,
            hide_recruiters,
            per_page,
        )
        if st.session_state.get("pipe_filter_state") != current_filter_hash:
            st.session_state["pipe_filter_state"] = current_filter_hash
            st.session_state["pipe_page_num"] = 1
            st.session_state["pipe_page_select"] = 1

        # Keep current_page within valid bounds
        current_page = st.session_state.get("pipe_page_num", 1)
        if current_page > total_pages:
            current_page = total_pages
            st.session_state["pipe_page_num"] = total_pages
            st.session_state["pipe_page_select"] = total_pages
        elif current_page < 1:
            current_page = 1
            st.session_state["pipe_page_num"] = 1
            st.session_state["pipe_page_select"] = 1

        if "pipe_page_select" not in st.session_state or st.session_state["pipe_page_select"] != current_page:
            st.session_state["pipe_page_select"] = current_page

        start_idx = (current_page - 1) * per_page
        end_idx = min(start_idx + per_page, total_leads)
        page_leads = leads_list[start_idx:end_idx]

        leads_df = pd.DataFrame(leads_list)
        csv_data = leads_df.drop(columns=["description"]).to_csv(index=False).encode("utf-8")

        col_count, col_download = st.columns([3.5, 1.5])
        with col_count:
            st.markdown(
                f"<div style='font-size:0.86rem; padding-top:6px; opacity:0.88;'>"
                f"Visar <strong>{start_idx + 1}–{end_idx}</strong> av <strong>{total_leads}</strong> matchande affärsmöjligheter "
                f"(Sida <strong>{current_page}</strong> av <strong>{total_pages}</strong>)."
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_download:
            st.download_button(
                label=f"Exportera alla {total_leads} (.csv)",
                data=csv_data,
                file_name=f"consid_lead_pipeline_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Top pagination controls if multiple pages
        if total_pages > 1:
            col_p1, col_p2, col_p3 = st.columns([1.2, 2.6, 1.2])
            with col_p1:
                st.button(
                    "⬅ Föregående sida",
                    disabled=(current_page <= 1),
                    key="btn_pipe_prev_top",
                    on_click=_nav_pipe_page,
                    args=(-1,),
                    use_container_width=True,
                )
            with col_p2:
                page_options = list(range(1, total_pages + 1))
                st.selectbox(
                    "Gå till sida",
                    page_options,
                    key="pipe_page_select",
                    on_change=_on_pipe_select_change,
                    format_func=lambda p: f"Sida {p} av {total_pages} (uppdrag {min((p-1)*per_page + 1, total_leads)}–{min(p*per_page, total_leads)})",
                    label_visibility="collapsed",
                )
            with col_p3:
                st.button(
                    "Nästa sida ➡",
                    disabled=(current_page >= total_pages),
                    key="btn_pipe_next_top",
                    on_click=_nav_pipe_page,
                    args=(1,),
                    use_container_width=True,
                )
    else:
        st.info("Inga uppdrag matchar ditt valda filter just nu.")
        page_leads = []
        total_pages = 0

    STATUS_ORDER = ["Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt", "Arkiverad"]

    for lead in page_leads:
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

    # Bottom pagination controls when scrolling reaches the bottom
    if leads_list and total_pages > 1:
        st.markdown("---")
        col_bp1, col_bp2, col_bp3 = st.columns([1.2, 2.6, 1.2])
        with col_bp1:
            st.button(
                "⬅ Föregående sida",
                disabled=(current_page <= 1),
                key="btn_pipe_prev_bottom",
                on_click=_nav_pipe_page,
                args=(-1,),
                use_container_width=True,
            )
        with col_bp2:
            st.markdown(
                f"<div style='text-align:center; padding-top:8px; font-weight:600; font-size:0.88rem; opacity:0.85;'>"
                f"Sida {current_page} av {total_pages} • Visar {start_idx + 1}–{end_idx} av {total_leads} uppdrag"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_bp3:
            st.button(
                "Nästa sida ➡",
                disabled=(current_page >= total_pages),
                key="btn_pipe_next_bottom",
                on_click=_nav_pipe_page,
                args=(1,),
                use_container_width=True,
            )
