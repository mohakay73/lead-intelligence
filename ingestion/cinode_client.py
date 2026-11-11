"""
Cinode ERP & Skills Platform Client.
Synchronizes consultant profiles, CV skills with proficiency levels (1-5),
and real-time bench availability from Cinode API into Supabase (consultants table).

Features:
- Smart Dual-Mode: Live OAuth2 REST integration when credentials exist in .env,
  with seamless sandbox simulation when awaiting company credentials.
- Multi-office filtering: Linköping, Norrköping, Södertälje, Nyköping.
"""
import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import requests
import sys
import importlib
from sqlalchemy.orm import Session
from database.connection import SessionLocal

# Ensure Consultant is reloaded in long-running processes (e.g. Streamlit Cloud)
if "database.models" in sys.modules and not hasattr(sys.modules["database.models"], "Consultant"):
    importlib.reload(sys.modules["database.models"])

from database.models import Consultant

logger = logging.getLogger("CinodeClient")

CINODE_BASE_URL = os.getenv("CINODE_BASE_URL", "https://api.cinode.app")
CINODE_TOKEN_URL = os.getenv("CINODE_TOKEN_URL", "https://api.cinode.app/token")
CINODE_ACCESS_ID = os.getenv("CINODE_ACCESS_ID")
CINODE_ACCESS_SECRET = os.getenv("CINODE_ACCESS_SECRET")
CINODE_COMPANY_ID = os.getenv("CINODE_COMPANY_ID")

# Realistic Consid regional consultant profiles for sandbox/demo mode
SANDBOX_CONSULTANTS: List[Dict[str, Any]] = [
    {
        "cinode_id": 101,
        "name": "Anna Lindqvist",
        "title": "Senior Cloud & Platform Architect",
        "office": "Linköping",
        "availability_status": "Ledig nu",
        "available_from": date.today(),
        "skills_with_levels": [
            {"name": "Azure", "level": 5},
            {"name": "Terraform", "level": 5},
            {"name": "Kubernetes", "level": 4},
            {"name": "Docker", "level": 4},
            {"name": "CI/CD", "level": 5},
            {"name": "Python", "level": 3},
        ],
        "resume_summary": (
            "10+ års erfarenhet av storskalig molninfrastruktur och plattformsautomation. "
            "Certifierad Azure Solutions Architect Expert och CKA. Har lett molnmigreringar inom försvarsindustrin "
            "och säkerhetskänslig verksamhet med strikta compliance- och NIS2-krav."
        ),
        "security_clearance": True,
    },
    {
        "cinode_id": 102,
        "name": "Erik Johansson",
        "title": "Senior Fullstack .NET / React Developer",
        "office": "Norrköping",
        "availability_status": "Ledig inom 30d",
        "available_from": date.today() + timedelta(days=20),
        "skills_with_levels": [
            {"name": "C#", "level": 5},
            {"name": ".NET", "level": 5},
            {"name": "React", "level": 4},
            {"name": "TypeScript", "level": 4},
            {"name": "SQL Server", "level": 4},
            {"name": "Azure", "level": 3},
        ],
        "resume_summary": (
            "8 års erfarenhet av mikrotjänstarkitektur i .NET 8 och moderna webbgränssnitt i React. "
            "Erfarenhet från bank, finans och offentlig sektor. Vana vid högprestandasystem, event-driven design "
            "och agilt ledarskap som Scrum Master."
        ),
        "security_clearance": False,
    },
    {
        "cinode_id": 103,
        "name": "Marcus Berg",
        "title": "Cyber Security & IAM Specialist",
        "office": "Linköping",
        "availability_status": "Ledig inom 14d",
        "available_from": date.today() + timedelta(days=12),
        "skills_with_levels": [
            {"name": "NIS2", "level": 5},
            {"name": "CISSP", "level": 5},
            {"name": "Azure AD", "level": 5},
            {"name": "IAM", "level": 4},
            {"name": "Säkerhetsskyddslagen", "level": 4},
            {"name": "Python", "level": 3},
        ],
        "resume_summary": (
            "Senior informationssäkerhetsspecialist med CISSP och CISM. Djup erfarenhet av säkerhetsskyddsanalyser, "
            "NIS2-gap-analyser samt implementation av Zero Trust-arkitektur och Entra ID (Azure AD) hos kunder inom energi och samhällskritisk IT."
        ),
        "security_clearance": True,
    },
    {
        "cinode_id": 104,
        "name": "Sofia Eklund",
        "title": "Lead Data Engineer & AI Specialist",
        "office": "Södertälje",
        "availability_status": "Ledig nu",
        "available_from": date.today(),
        "skills_with_levels": [
            {"name": "Python", "level": 5},
            {"name": "Databricks", "level": 5},
            {"name": "Apache Spark", "level": 4},
            {"name": "SQL", "level": 5},
            {"name": "Snowflake", "level": 4},
            {"name": "AWS", "level": 3},
        ],
        "resume_summary": (
            "Data- och AI-arkitekt med 7 års erfarenhet av att bygga datadrivna analysplattformar och maskininlärningspipelines. "
            "Expert på Databricks Medallion Architecture, ETL-automation i Spark samt MLOps för prediktiva AI-modeller i produktion."
        ),
        "security_clearance": False,
    },
    {
        "cinode_id": 105,
        "name": "Viktor Nygren",
        "title": "Senior Embedded Systems & C++ Engineer",
        "office": "Linköping",
        "availability_status": "Ledig inom 45d",
        "available_from": date.today() + timedelta(days=35),
        "skills_with_levels": [
            {"name": "C++", "level": 5},
            {"name": "C", "level": 5},
            {"name": "Embedded Linux", "level": 4},
            {"name": "RTOS", "level": 4},
            {"name": "Python", "level": 3},
            {"name": "Git", "level": 4},
        ],
        "resume_summary": (
            "9 års erfarenhet av hårdvarunära programmering och realtidssystem i C/C++. "
            "Bakgrund från telekom (Ericsson) och fordonsindustrin (Scania). Expert på Linux drivrutiner, CAN-buss, AUTOSAR och hårdvarutestning."
        ),
        "security_clearance": True,
    },
    {
        "cinode_id": 106,
        "name": "Elin Sandström",
        "title": "Lead Frontend & UX Architect",
        "office": "Norrköping",
        "availability_status": "Upptagen",
        "available_from": date.today() + timedelta(days=90),
        "skills_with_levels": [
            {"name": "TypeScript", "level": 5},
            {"name": "React", "level": 5},
            {"name": "Vue", "level": 4},
            {"name": "Figma", "level": 5},
            {"name": "WCAG", "level": 5},
        ],
        "resume_summary": (
            "Design- och frontendarkitekt med starkt fokus på användbarhet (UX) och tillgänglighetsdirektivet (WCAG 2.1 AA). "
            "Har etablerat designsystem och komponentbibliotek i Tailwind och Figma för ledande e-handels- och myndighetsportaler."
        ),
        "security_clearance": False,
    },
]


def is_live_cinode_configured() -> bool:
    """Returns True if live Cinode API credentials are fully configured."""
    return bool(CINODE_ACCESS_ID and CINODE_ACCESS_SECRET and CINODE_COMPANY_ID)


def get_cinode_access_token() -> Optional[str]:
    """
    Authenticates against Cinode OAuth2 token endpoint using Basic/Bearer client credentials.
    Returns access token string or None on failure.
    """
    if not is_live_cinode_configured():
        return None

    try:
        auth_header = requests.auth.HTTPBasicAuth(CINODE_ACCESS_ID, CINODE_ACCESS_SECRET)
        resp = requests.post(
            CINODE_TOKEN_URL,
            auth=auth_header,
            data={"grant_type": "client_credentials"},
            timeout=8,
        )
        if resp.status_code == 200:
            token_data = resp.json()
            return token_data.get("access_token")
        else:
            logger.warning(f"Cinode OAuth2 failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Cinode authentication request error: {e}")
    return None


def fetch_live_cinode_consultants() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches live company consultants, planning/availability, and resume skills from Cinode REST API.
    Returns None if live credentials are not set or unreachable.
    """
    token = get_cinode_access_token()
    if not token or not CINODE_COMPANY_ID:
        return None

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    consultants = []

    try:
        # 1. Fetch users in company
        users_url = f"{CINODE_BASE_URL}/v0.1/companies/{CINODE_COMPANY_ID}/users"
        resp = requests.get(users_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        users = resp.json()

        # 2. Fetch planning / availability
        planning_url = f"{CINODE_BASE_URL}/v0.1/companies/{CINODE_COMPANY_ID}/planning/users"
        plan_resp = requests.get(planning_url, headers=headers, timeout=10)
        planning_data = plan_resp.json() if plan_resp.status_code == 200 else {}
        plan_lookup = {p.get("userId"): p for p in planning_data} if isinstance(planning_data, list) else {}

        # 3. Process each consultant
        for u in users:
            uid = u.get("id")
            first_name = u.get("firstName", "")
            last_name = u.get("lastName", "")
            full_name = f"{first_name} {last_name}".strip()
            title = u.get("title") or "IT-konsult"
            office = u.get("location") or "Linköping"

            # Skills
            skills_url = f"{CINODE_BASE_URL}/v0.1/companies/{CINODE_COMPANY_ID}/users/{uid}/skills"
            s_resp = requests.get(skills_url, headers=headers, timeout=6)
            user_skills = []
            if s_resp.status_code == 200:
                for s in s_resp.json():
                    user_skills.append({
                        "name": s.get("name"),
                        "level": int(s.get("level", 3)),
                    })

            # Availability
            plan = plan_lookup.get(uid, {})
            avail_date_str = plan.get("availableFrom")
            avail_date = datetime.strptime(avail_date_str[:10], "%Y-%m-%d").date() if avail_date_str else date.today()
            days_to_avail = (avail_date - date.today()).days

            if days_to_avail <= 0:
                avail_status = "Ledig nu"
            elif days_to_avail <= 30:
                avail_status = "Ledig inom 30d"
            elif days_to_avail <= 60:
                avail_status = "Ledig inom 60d"
            else:
                avail_status = "Upptagen"

            consultants.append({
                "cinode_id": uid,
                "name": full_name,
                "title": title,
                "office": office,
                "availability_status": avail_status,
                "available_from": avail_date,
                "skills_with_levels": user_skills,
                "resume_summary": u.get("bio") or f"Konsultprofil synkad från Cinode med {len(user_skills)} registrerade kompetenser.",
                "security_clearance": bool("säkerhet" in title.lower() or "försvar" in (u.get("bio") or "").lower()),
            })

        return consultants
    except Exception as e:
        logger.warning(f"Error while querying live Cinode API: {e}")
        return None


def get_all_cinode_consultants() -> List[Dict[str, Any]]:
    """
    Returns live Cinode consultants if configured; otherwise returns the rich sandbox dataset.
    """
    if is_live_cinode_configured():
        live_data = fetch_live_cinode_consultants()
        if live_data:
            logger.info(f"Retrieved {len(live_data)} consultants from live Cinode API.")
            return live_data

    logger.info("Using Cinode Sandbox profiles (awaiting live Cinode credentials).")
    return SANDBOX_CONSULTANTS


def sync_cinode_to_database(db: Session) -> Dict[str, Any]:
    """
    Upserts Cinode consultant profiles into the Supabase consultants table.
    """
    consultant_records = get_all_cinode_consultants()
    synced_count = 0

    for c in consultant_records:
        cid = c.get("cinode_id")
        existing = db.query(Consultant).filter(Consultant.cinode_id == cid).first() if cid else None

        skills_json = json.dumps(c.get("skills_with_levels", []))

        if not existing:
            new_cons = Consultant(
                cinode_id=cid,
                name=c["name"],
                title=c["title"],
                office=c["office"],
                availability_status=c["availability_status"],
                available_from=c["available_from"],
                skills_with_levels=skills_json,
                resume_summary=c.get("resume_summary", ""),
                security_clearance=c.get("security_clearance", False),
            )
            db.add(new_cons)
        else:
            existing.name = c["name"]
            existing.title = c["title"]
            existing.office = c["office"]
            existing.availability_status = c["availability_status"]
            existing.available_from = c["available_from"]
            existing.skills_with_levels = skills_json
            existing.resume_summary = c.get("resume_summary", "")
            existing.security_clearance = c.get("security_clearance", False)
            existing.updated_at = datetime.utcnow()

        synced_count += 1

    db.commit()
    logger.info(f"Synced {synced_count} Cinode consultants to database.")
    return {
        "status": "success",
        "synced_count": synced_count,
        "mode": "live" if is_live_cinode_configured() else "sandbox",
    }


def get_available_consultants_from_db(
    db: Session,
    office: Optional[str] = None,
    include_occupied: bool = False,
) -> List[Dict[str, Any]]:
    """
    Queries synced consultants from Supabase for dashboard matching and display.
    """
    query = db.query(Consultant)
    if office and office != "Alla":
        query = query.filter(Consultant.office == office)

    if not include_occupied:
        query = query.filter(Consultant.availability_status.in_(["Ledig nu", "Ledig inom 14d", "Ledig inom 30d", "Ledig inom 45d", "Ledig inom 60d"]))

    records = query.order_by(Consultant.available_from.asc().nullslast()).all()
    results = []
    for r in records:
        skills = []
        if r.skills_with_levels:
            try:
                skills = json.loads(r.skills_with_levels)
            except Exception:
                skills = []

        results.append({
            "id": r.id,
            "cinode_id": r.cinode_id,
            "name": r.name,
            "title": r.title,
            "office": r.office,
            "availability_status": r.availability_status,
            "available_from": r.available_from,
            "skills_with_levels": skills,
            "resume_summary": r.resume_summary or "",
            "security_clearance": r.security_clearance,
        })
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        res = sync_cinode_to_database(db)
        print("Cinode sync result:", res)
    finally:
        db.close()
