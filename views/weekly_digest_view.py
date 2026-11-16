"""
View 5: Ledningsrapport & Veckobrev (Executive Weekly Intelligence Digest)
"""
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

from analytics.weekly_digest import (
    format_markdown_digest,
    format_html_digest,
    send_teams_notification,
)
from config import get_secret


def render_weekly_digest(cached_weekly_digest, base_dir: Path):
    """Renders the executive weekly intelligence report with export and Microsoft Teams webhook integration."""
    st.markdown("##### Veckorapport: Marknadsintelligens för ledningen")
    st.caption("Aggregerad sammanställning av den senaste veckans uppdragsflöde, heta leads och kompetenstrender.")

    digest_data = cached_weekly_digest(days_back=7)
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

    current_env_webhook = get_secret("TEAMS_WEBHOOK_URL", "").strip()

    with col_btn_teams:
        if st.button("Skicka rapport till Microsoft Teams nu", use_container_width=True):
            target_url = st.session_state.get("custom_teams_url") or current_env_webhook
            if target_url and send_teams_notification(digest_md, webhook_url=target_url):
                st.success("Veckorapporten har skickats till din Microsoft Teams-kanal!")
            else:
                st.warning("Kunde inte skicka. Kontrollera att din TEAMS_WEBHOOK_URL är konfigurerad nedan.")

    # Expandable Microsoft Teams Webhook Configuration box
    with st.expander("Koppla & Konfigurera Microsoft Teams Webhook", expanded=not bool(current_env_webhook)):
        if current_env_webhook:
            st.success("Microsoft Teams Webhook är kopplad i `.env`.")
        else:
            st.info("Koppla ihop valfri kanal i Microsoft Teams för automatiserade rapporter varje måndag.")

        st.markdown(
            """
            1. **I Teams:** Gå till kanalen där du vill få rapporterna -> Klicka på `...` -> Välj **Arbetsflöden (Workflows)**.
            2. Sök efter mallen **"webhook"** och välj *"Send webhook alerts to a channel"* (eller *"Skicka webhook-aviseringar till en kanal"*).
            3. Kopiera den genererade webhook-länken och klistra in den nedan.
            """
        )
        custom_teams_url = st.text_input(
            "Teams Webhook URL",
            value=st.session_state.get("custom_teams_url", current_env_webhook),
            key="custom_teams_url_input",
            placeholder="https://...powerplatform.com:443/powerautomate/automations/... eller logic.azure.com",
        )
        if custom_teams_url:
            st.session_state["custom_teams_url"] = custom_teams_url.strip()

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            if st.button("Skicka testmeddelande till denna Teams-länk"):
                active_url = custom_teams_url.strip() or current_env_webhook
                if active_url:
                    if send_teams_notification(digest_md, webhook_url=active_url):
                        st.success("Testrapporten levererades till Microsoft Teams! Kontrollera din kanal nu.")
                    else:
                        st.error("Kunde inte skicka. Kontrollera att länken är komplett kopierad från Teams.")
                else:
                    st.warning("Klistra in en Teams Webhook URL i rutan först.")
        with col_t2:
            if st.button("Spara till .env-filen"):
                if custom_teams_url.strip():
                    try:
                        env_path = base_dir / ".env"
                        env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
                        if "TEAMS_WEBHOOK_URL=" in env_content:
                            lines = env_content.splitlines()
                            new_lines = []
                            for l in lines:
                                if l.strip().startswith("TEAMS_WEBHOOK_URL="):
                                    new_lines.append(f"TEAMS_WEBHOOK_URL={custom_teams_url.strip()}")
                                else:
                                    new_lines.append(l)
                            env_path.write_text("\n".join(new_lines), encoding="utf-8")
                        else:
                            env_path.write_text(env_content + f"\nTEAMS_WEBHOOK_URL={custom_teams_url.strip()}\n", encoding="utf-8")
                        load_dotenv(override=True)
                        st.success("Webhook-länken sparades permanent i .env!")
                    except Exception as ex:
                        st.error(f"Kunde inte spara till .env: {ex}")
                else:
                    st.warning("Ange en länk att spara.")

    st.markdown("##### Förhandsgranskning av veckorapporten")
    st.markdown(digest_md)
