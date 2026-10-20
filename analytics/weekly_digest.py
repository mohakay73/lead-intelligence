"""
Executive Weekly Market Digest Engine.
Compiles high-level weekly market intelligence for consulting leadership across
Östergötland & E4 Syd (Linköping, Norrköping, Södertälje, Nyköping).
Generates both Markdown (Slack/Teams) and HTML Email reports.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import os
import sys
import logging
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import init_db, SessionLocal
from database.models import Lead, Skill, lead_skills

logger = logging.getLogger("WeeklyDigest")


def build_weekly_intelligence_data(db: Session, days_back: int = 7) -> Dict[str, Any]:
    """Compiles weekly metrics and highlights from the database for active leads."""
    cutoff = datetime.now() - timedelta(days=days_back)

    total_active = db.query(func.count(Lead.id)).filter(Lead.source != "historical").scalar() or 0
    new_this_week = (
        db.query(func.count(Lead.id))
        .filter(Lead.published_at >= cutoff, Lead.source != "historical")
        .scalar()
        or 0
    )
    consultant_leads = (
        db.query(func.count(Lead.id))
        .filter(Lead.is_consultant_assignment == True, Lead.source != "historical")
        .scalar()
        or 0
    )

    # Locations (active leads)
    location_counts = (
        db.query(Lead.location, func.count(Lead.id))
        .filter(Lead.location.isnot(None), Lead.source != "historical")
        .group_by(Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(6)
        .all()
    )

    # Top skills (active leads)
    top_skills = (
        db.query(Skill.name, Skill.category, func.count(Lead.id))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.source != "historical")
        .group_by(Skill.name, Skill.category)
        .order_by(func.count(Lead.id).desc())
        .limit(6)
        .all()
    )

    # Top employers (active leads)
    top_employers = (
        db.query(Lead.company_name, Lead.location, func.count(Lead.id))
        .filter(Lead.company_name.isnot(None), Lead.source != "historical")
        .group_by(Lead.company_name, Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(6)
        .all()
    )

    # High-priority consultant assignments (direct leads)
    consultant_highlights = (
        db.query(Lead)
        .filter(Lead.is_consultant_assignment == True, Lead.source != "historical")
        .order_by(Lead.published_at.desc().nullslast())
        .limit(5)
        .all()
    )

    return {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "total_active": total_active,
        "new_this_week": new_this_week,
        "consultant_leads": consultant_leads,
        "locations": location_counts,
        "top_skills": top_skills,
        "top_employers": top_employers,
        "consultant_highlights": [
            {
                "title": l.title,
                "company": l.company_name,
                "location": l.location,
                "url": l.url,
                "skills": [s.name for s in l.skills[:4]],
            }
            for l in consultant_highlights
        ],
    }


def format_markdown_digest(data: Dict[str, Any]) -> str:
    """Formats executive intelligence as a clean, professional Markdown report for Slack/Teams."""
    loc_lines = "\n".join([f"- **{loc}**: {cnt} aktiva positioner" for loc, cnt in data["locations"]])
    skill_lines = "\n".join([f"- **{name}** ({cat}): {cnt} förfrågningar" for name, cat, cnt in data["top_skills"]])
    emp_lines = "\n".join([f"- **{comp}** ({loc}): {cnt} behov" for comp, loc, cnt in data["top_employers"]])

    consultant_lines = []
    for c in data["consultant_highlights"]:
        skills_str = ", ".join(c["skills"]) if c["skills"] else "Allmän IT"
        url_part = f" – [Länk till annons]({c['url']})" if c["url"] else ""
        consultant_lines.append(f"- **{c['title']}** ({c['company']} | {c['location']}){url_part}\n  _Kompetenser: {skills_str}_")
    consultant_block = "\n".join(consultant_lines)

    return f"""# Veckorapport: Marknadsintelligens Östergötland, Södertälje & Nyköping
**Datum:** {data['report_date']} | **Område:** Linköping, Norrköping, Södertälje, Nyköping

---

### Nyckeltal i korthet
- **Totala aktiva behov:** {data['total_active']} st
- **Direkta konsultuppdrag:** {data['consultant_leads']} st
- **Nya uppdrag senaste 7 dagarna:** {data['new_this_week']} st

---

### Geografisk fördelning
{loc_lines}

---

### Mest efterfrågade kompetenser
{skill_lines}

---

### Mest aktiva uppdragsgivare
{emp_lines}

---

### Aktuella konsultuppdrag att bemanna
{consultant_block}

---
_Rapporten är automatiskt sammanställd via Lead Intelligence Platform för ledningsgruppen._
"""


def format_html_digest(data: Dict[str, Any]) -> str:
    """Formats executive intelligence as a modern, responsive HTML email."""
    loc_rows = "".join([f"<tr><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;'>{loc}</td><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;font-weight:600;text-align:right;'>{cnt}</td></tr>" for loc, cnt in data["locations"]])
    skill_rows = "".join([f"<tr><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;'>{name}</td><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;color:#64748b;'>{cat}</td><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;font-weight:600;text-align:right;'>{cnt}</td></tr>" for name, cat, cnt in data["top_skills"]])
    emp_rows = "".join([f"<tr><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;'>{comp}</td><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;color:#64748b;'>{loc}</td><td style='padding:6px 12px;border-bottom:1px solid #f1f5f9;font-weight:600;text-align:right;'>{cnt}</td></tr>" for comp, loc, cnt in data["top_employers"]])

    consultant_items = []
    for c in data["consultant_highlights"]:
        skills_str = ", ".join(c["skills"]) if c["skills"] else "IT"
        link_tag = f"<a href='{c['url']}' style='color:#2563eb;text-decoration:none;font-weight:600;'>Visa annons &rarr;</a>" if c["url"] else ""
        consultant_items.append(f"""
        <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:8px;'>
            <div style='font-weight:700;color:#0f172a;font-size:14px;'>{c['title']}</div>
            <div style='font-size:12px;color:#64748b;margin:3px 0 6px 0;'><strong>{c['company']}</strong> &bull; {c['location']} &bull; Nyckelkompetenser: {skills_str}</div>
            <div>{link_tag}</div>
        </div>
        """)
    consultant_html = "".join(consultant_items)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background-color:#f1f5f9;margin:0;padding:24px;color:#0f172a;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);border:1px solid #e2e8f0;">
        <div style="background:#0f172a;color:#ffffff;padding:24px 28px;">
            <div style="font-size:20px;font-weight:800;letter-spacing:-0.02em;">Ledningsrapport: Marknadsintelligens</div>
            <div style="font-size:13px;color:#94a3b8;margin-top:4px;">Östergötland, Södertälje & Nyköping &bull; {data['report_date']}</div>
        </div>
        <div style="padding:24px 28px;">
            <div style="display:flex;gap:12px;margin-bottom:24px;">
                <div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Totala Behov</div>
                    <div style="font-size:24px;font-weight:800;color:#0f172a;margin-top:2px;">{data['total_active']}</div>
                </div>
                <div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Konsultuppdrag</div>
                    <div style="font-size:24px;font-weight:800;color:#2563eb;margin-top:2px;">{data['consultant_leads']}</div>
                </div>
                <div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Nya Senaste 7d</div>
                    <div style="font-size:24px;font-weight:800;color:#059669;margin-top:2px;">{data['new_this_week']}</div>
                </div>
            </div>

            <div style="font-size:15px;font-weight:700;margin-bottom:8px;border-bottom:2px solid #e2e8f0;padding-bottom:4px;">Aktuella Konsultuppdrag att bemanna</div>
            <div style="margin-bottom:24px;">{consultant_html}</div>

            <div style="display:flex;gap:20px;margin-bottom:20px;">
                <div style="flex:1;">
                    <div style="font-size:14px;font-weight:700;margin-bottom:6px;">Geografi</div>
                    <table style="width:100%;border-collapse:collapse;font-size:12px;">{loc_rows}</table>
                </div>
                <div style="flex:1;">
                    <div style="font-size:14px;font-weight:700;margin-bottom:6px;">Toppkompetenser</div>
                    <table style="width:100%;border-collapse:collapse;font-size:12px;">{skill_rows}</table>
                </div>
            </div>

            <div style="font-size:14px;font-weight:700;margin-bottom:6px;">Mest aktiva uppdragsgivare</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px;">{emp_rows}</table>
        </div>
        <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:12px 28px;font-size:11px;color:#94a3b8;text-align:center;">
            Automatiskt sammanställd via Lead Intelligence Platform för ledningsgruppen.
        </div>
    </div>
</body>
</html>"""


def send_slack_notification(markdown_content: str, webhook_url: Optional[str] = None) -> bool:
    """Dispatches report to Slack/Teams webhook."""
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return False
    try:
        res = requests.post(url, json={"text": markdown_content}, timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Error sending webhook notification: {e}")
        return False


def run_weekly_digest() -> Dict[str, Any]:
    """Generates and dispatches the weekly digest."""
    init_db()
    db = SessionLocal()
    try:
        data = build_weekly_intelligence_data(db)
        md = format_markdown_digest(data)
        html = format_html_digest(data)
        
        # Check if Slack/Teams webhook is configured
        slack_sent = False
        if os.getenv("SLACK_WEBHOOK_URL"):
            slack_sent = send_slack_notification(md)
            logger.info(f"Webhook notification sent: {slack_sent}")
            
        return {
            "status": "success",
            "data": data,
            "markdown": md,
            "html": html,
            "slack_sent": slack_sent,
        }
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_weekly_digest()
    # Safe output for Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(result["markdown"])

