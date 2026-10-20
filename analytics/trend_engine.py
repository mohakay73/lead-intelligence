from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.models import Lead, Skill, lead_skills


def get_overview_kpis(db: Session) -> Dict[str, Any]:
    """Calculates top-level executive metrics."""
    total_leads = db.query(func.count(Lead.id)).scalar() or 0
    consultant_leads = db.query(func.count(Lead.id)).filter(Lead.is_consultant_assignment == True).scalar() or 0
    jobtech_leads = db.query(func.count(Lead.id)).filter(Lead.source == "jobtech").scalar() or 0
    unique_employers = db.query(func.count(func.distinct(Lead.company_name))).scalar() or 0

    return {
        "total_leads": total_leads,
        "consultant_leads": consultant_leads,
        "jobtech_leads": jobtech_leads,
        "unique_employers": unique_employers,
    }


def get_skill_demand(
    db: Session,
    location: Optional[str] = None,
    source: Optional[str] = None,
    top_n: int = 15,
) -> pd.DataFrame:
    """Returns top demanded skills grouped by category."""
    query = (
        db.query(
            Skill.name.label("skill"),
            Skill.category.label("category"),
            func.count(Lead.id).label("count"),
        )
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
    )

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    if source and source != "Alla":
        query = query.filter(Lead.source == source)

    results = (
        query.group_by(Skill.name, Skill.category)
        .order_by(func.count(Lead.id).desc())
        .limit(top_n)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["skill", "category", "count"])

    return pd.DataFrame(results, columns=["skill", "category", "count"])


def get_location_distribution(db: Session) -> pd.DataFrame:
    """Returns distribution of leads across Östergötland municipalities."""
    results = (
        db.query(
            Lead.location.label("location"),
            func.count(Lead.id).label("count"),
        )
        .filter(Lead.location.isnot(None))
        .group_by(Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["location", "count"])

    return pd.DataFrame(results, columns=["location", "count"])


def get_category_distribution(db: Session) -> pd.DataFrame:
    """Aggregates demand by broader technology category."""
    results = (
        db.query(
            Skill.category.label("category"),
            func.count(Lead.id).label("count"),
        )
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .group_by(Skill.category)
        .order_by(func.count(Lead.id).desc())
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["category", "count"])

    return pd.DataFrame(results, columns=["category", "count"])


def get_top_employers(
    db: Session,
    location: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 15,
) -> pd.DataFrame:
    """Returns the most active hiring organizations and brokers in the region."""
    query = (
        db.query(
            Lead.company_name.label("company"),
            Lead.location.label("location"),
            func.count(Lead.id).label("count"),
        )
        .filter(Lead.company_name.isnot(None))
    )

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    if source and source != "Alla":
        query = query.filter(Lead.source == source)

    results = (
        query.group_by(Lead.company_name, Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(limit)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["company", "location", "count"])

    return pd.DataFrame(results, columns=["company", "location", "count"])


def get_filtered_leads(
    db: Session,
    search_term: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    selected_skill: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Returns detailed lead cards for the Lead Explorer view."""
    query = db.query(Lead)

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    if source and source != "Alla":
        query = query.filter(Lead.source == source)

    if search_term:
        term = f"%{search_term}%"
        query = query.filter((Lead.title.ilike(term)) | (Lead.description.ilike(term)) | (Lead.company_name.ilike(term)))

    if selected_skill and selected_skill != "Alla":
        query = query.join(lead_skills).join(Skill).filter(Skill.name == selected_skill)

    leads = query.order_by(Lead.published_at.desc().nullslast(), Lead.id.desc()).limit(limit).all()

    output = []
    for l in leads:
        output.append({
            "id": l.id,
            "source": l.source,
            "title": l.title,
            "company_name": l.company_name,
            "location": l.location,
            "published_at": l.published_at.strftime("%Y-%m-%d") if l.published_at else "Nyligen",
            "deadline": l.deadline.strftime("%Y-%m-%d") if l.deadline else "Löpande",
            "url": l.url,
            "is_consultant": l.is_consultant_assignment,
            "skills": [s.name for s in l.skills],
            "description": l.description,
        })
    return output
