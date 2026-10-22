"""
Consultant Bench Matcher Module.
Matches available consultants on the bench against live market opportunities in Östergötland,
Södertälje, and Nyköping. Calculates match scores (%), highlights skill overlaps,
and prepares customized B2B consulting pitches for rapid closing.
"""
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from database.models import Lead, Skill
from ingestion.normalizer import extract_skills_from_text
from analytics.pitch_generator import generate_sales_pitch

# Preset realistic bench profiles for regional consulting leadership
PRESET_BENCH_PROFILES: List[Dict[str, Any]] = [
    {
        "id": "bench-1",
        "name": "Johan Lindqvist",
        "title": "Senior .NET & Cloud Fullstack-utvecklare",
        "seniority": "Senior (8 års erfarenhet)",
        "location": "Linköping",
        "available_from": "Omgående (På bänken)",
        "skills": [".NET / C#", "Azure", "React", "TypeScript", "SQL", "Docker"],
        "clearance": False,
        "summary": "Erfaren fullstack-utvecklare med djup profil inom C#, .NET 8, microservices i Azure och React. Van vid agila team och vård-/industrisystem.",
    },
    {
        "id": "bench-2",
        "name": "Elin Bergman",
        "title": "Cloud Platform & DevOps Arkitekt",
        "seniority": "Senior / Lead (10 års erfarenhet)",
        "location": "Linköping",
        "available_from": "Omgående (På bänken)",
        "skills": ["Kubernetes", "Terraform", "Azure", "AWS", "CI/CD & DevOps", "Docker", "Linux"],
        "clearance": False,
        "summary": "Certifierad CKA och HashiCorp Terraform Specialist. Bygger skalbara automatiseringsplattformar och molnmiljöer för industri och försvar.",
    },
    {
        "id": "bench-3",
        "name": "Mikael Ekström",
        "title": "Embedded Systems & Automotive Developer",
        "seniority": "Senior (7 års erfarenhet)",
        "location": "Södertälje / Linköping",
        "available_from": "Inom 2 veckor",
        "skills": ["C++ / Embedded", "Linux", "C", "Python"],
        "clearance": True,
        "summary": "Specialist på realtidssystem (RTOS) i C/C++ och Linux. Erfarenhet av CAN-buss, AUTOSAR och säkerhetskritiska system hos Scania och Saab. Godkänd säkerhetsprövning.",
    },
    {
        "id": "bench-4",
        "name": "Sara Almqvist",
        "title": "Data Engineer & Analytics Specialist",
        "seniority": "Mid/Senior (5 års erfarenhet)",
        "location": "Norrköping",
        "available_from": "Omgående (På bänken)",
        "skills": ["Python", "Databricks & Spark", "Power BI", "SQL", "Azure"],
        "clearance": False,
        "summary": "Bygger moderna Lakehouses i Databricks, ETL-flöden i PySpark samt ledningsrapporter i Power BI för industri- och energibolag.",
    },
    {
        "id": "bench-5",
        "name": "Alexander Holm",
        "title": "Cybersecurity & Compliance Lead (NIS2)",
        "seniority": "Lead Konsult (12 års erfarenhet)",
        "location": "Hela regionen",
        "available_from": "Inom 3 veckor",
        "skills": ["Cybersecurity", "Cloud & DevOps", "Linux", "Azure"],
        "clearance": True,
        "summary": "Säkerhetsarkitekt med spetskompetens inom NIS2, ISO 27001, risk- och gapanalyser samt härdning av molnplattformar.",
    },
]


def match_consultant_to_leads(
    db: Session,
    consultant: Dict[str, Any],
    location_filter: Optional[str] = None,
    min_match_pct: int = 30,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Scans active market leads in Supabase and ranks opportunities by match percentage.
    """
    c_skills: Set[str] = set(consultant.get("skills", []))
    c_loc = consultant.get("location", "").lower()
    c_name = consultant.get("name", "Vår seniorkonsult")
    c_title = consultant.get("title", "IT-konsult")
    c_avail = consultant.get("available_from", "inom 2–4 veckor")
    c_clearance = consultant.get("clearance", False)

    # Fetch active leads only (Lead.source != "historical")
    query = db.query(Lead).filter(Lead.source != "historical")

    if location_filter and location_filter != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location_filter}%"))

    active_leads = query.all()
    matches = []

    for lead in active_leads:
        lead_skills = set(s.name for s in lead.skills)
        matched_skills = sorted(list(c_skills.intersection(lead_skills)))
        missing_skills = sorted(list(lead_skills.difference(c_skills)))
        bonus_skills = sorted(list(c_skills.difference(lead_skills)))

        # 1. Base skill match score
        if lead_skills:
            skill_ratio = len(matched_skills) / len(lead_skills)
        else:
            # Fallback: check if lead title/description mentions any consultant skills
            lead_text = f"{lead.title} {lead.description or ''}".lower()
            detected_skills = [s for s in c_skills if s.lower() in lead_text]
            matched_skills = detected_skills
            skill_ratio = (len(detected_skills) / max(1, len(c_skills))) * 0.7

        if not matched_skills and skill_ratio < 0.15:
            continue

        raw_score = skill_ratio * 75.0  # Skills contribute up to 75 points

        # 2. Location compatibility bonus (up to 15 points)
        lead_loc = (lead.location or "").lower()
        if "hela" in c_loc or not c_loc or lead_loc in c_loc or c_loc in lead_loc:
            raw_score += 15.0
        elif ("östergötland" in lead_loc and "linköping" in c_loc) or ("östergötland" in lead_loc and "norrköping" in c_loc):
            raw_score += 10.0
        else:
            raw_score += 3.0

        # 3. Security clearance matching (Saab / Defense cluster bonus)
        lead_desc = (lead.description or "").lower()
        needs_clearance = "säkerhetspröv" in lead_desc or "medborgarskap" in lead_desc or "saab" in (lead.company_name or "").lower()
        if needs_clearance:
            if c_clearance:
                raw_score += 10.0
            else:
                raw_score -= 10.0

        # 4. Assignment type bonus: Direct consultant broker tenders get +5 priority
        if lead.is_consultant_assignment:
            raw_score += 5.0

        # Bound score between 0 and 99%
        final_score = int(min(99, max(15, round(raw_score))))

        if final_score >= min_match_pct:
            # Prepare pre-formatted pitch for this specific match
            lead_dict = {
                "id": lead.id,
                "title": lead.title,
                "company_name": lead.company_name or "Uppdragsgivaren",
                "location": lead.location or "Regionen",
                "skills": [s.name for s in lead.skills],
                "is_consultant": lead.is_consultant_assignment,
            }
            pitch = generate_sales_pitch(
                lead=lead_dict,
                consultant_profile=f"{c_title} ({consultant.get('seniority', 'Senior')}) med spetskompetens inom {', '.join(matched_skills[:4]) if matched_skills else c_title}",
                consultant_name=c_name,
                available_from=c_avail,
            )

            matches.append({
                "lead_id": lead.id,
                "title": lead.title,
                "company": lead.company_name or "Konfidentiell uppdragsgivare",
                "location": lead.location or "Östergötland",
                "is_consultant": lead.is_consultant_assignment,
                "source": lead.source,
                "url": lead.url,
                "match_score": final_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "bonus_skills": bonus_skills[:3],
                "published_at": lead.published_at.strftime("%Y-%m-%d") if lead.published_at else "Nyligen",
                "pitch_subject": pitch["subject"],
                "pitch_body": pitch["body"],
                "description": lead.description or "",
            })

    # Sort highest match score first
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:limit]

