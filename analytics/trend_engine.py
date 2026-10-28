from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.models import Lead, Skill, lead_skills


def get_overview_kpis(db: Session) -> Dict[str, Any]:
    """Calculates top-level executive metrics for active opportunities."""
    total_leads = db.query(func.count(Lead.id)).filter(Lead.source != "historical").scalar() or 0
    consultant_leads = (
        db.query(func.count(Lead.id))
        .filter(Lead.is_consultant_assignment == True, Lead.source != "historical")
        .scalar()
        or 0
    )
    jobtech_leads = db.query(func.count(Lead.id)).filter(Lead.source == "jobtech").scalar() or 0
    unique_employers = (
        db.query(func.count(func.distinct(Lead.company_name)))
        .filter(Lead.source != "historical")
        .scalar()
        or 0
    )

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
    else:
        query = query.filter(Lead.source != "historical")

    results = (
        query.group_by(Skill.name, Skill.category)
        .order_by(func.count(Lead.id).desc())
        .limit(top_n)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["skill", "category", "count"])

    return pd.DataFrame(results, columns=["skill", "category", "count"])


def get_location_distribution(db: Session, source: Optional[str] = None) -> pd.DataFrame:
    """Returns distribution of active leads across municipalities."""
    query = (
        db.query(
            Lead.location.label("location"),
            func.count(Lead.id).label("count"),
        )
        .filter(Lead.location.isnot(None))
    )

    if source and source != "Alla":
        query = query.filter(Lead.source == source)
    else:
        query = query.filter(Lead.source != "historical")

    results = (
        query.group_by(Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["location", "count"])

    return pd.DataFrame(results, columns=["location", "count"])


def get_category_distribution(
    db: Session,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregates demand by broader technology category for active leads."""
    query = (
        db.query(
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
    else:
        query = query.filter(Lead.source != "historical")

    results = (
        query.group_by(Skill.category)
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
    else:
        query = query.filter(Lead.source != "historical")

    results = (
        query.group_by(Lead.company_name, Lead.location)
        .order_by(func.count(Lead.id).desc())
        .limit(limit)
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["company", "location", "count"])

    return pd.DataFrame(results, columns=["company", "location", "count"])


def get_pipeline_kpis(db: Session, location: Optional[str] = None) -> Dict[str, int]:
    """Calculates lead counts across each stage of the consulting sales pipeline using fast SQL aggregation."""
    status_col = func.coalesce(Lead.status, "Nytt")
    query = (
        db.query(status_col, func.count(Lead.id))
        .filter(Lead.source != "historical")
    )
    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    results = query.group_by(status_col).all()

    kpis = {
        "total": 0,
        "nytt": 0,
        "granskas": 0,
        "pitch": 0,
        "intervju": 0,
        "vunnet": 0,
        "avböjt": 0,
    }
    for st_val, count in results:
        st = (st_val or "Nytt").strip()
        kpis["total"] += count
        if st == "Nytt":
            kpis["nytt"] += count
        elif st == "Granskas":
            kpis["granskas"] += count
        elif st == "Pitch skickad":
            kpis["pitch"] += count
        elif st == "Intervju":
            kpis["intervju"] += count
        elif st in ("Vunnet", "Tillsatt"):
            kpis["vunnet"] += count
        elif st in ("Avböjt", "Ej aktuell", "Arkiverad"):
            kpis["avböjt"] += count
        else:
            kpis["nytt"] += count
    return kpis


def update_lead_status(
    db: Session,
    lead_id: int,
    status: str,
    assigned_to: Optional[str] = None,
    candidate_name: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """Updates pipeline stage, assignee, matched candidate and sales notes for a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return False

    lead.status = status
    if assigned_to is not None:
        lead.assigned_to = assigned_to.strip() if assigned_to else None
    if candidate_name is not None:
        lead.candidate_name = candidate_name.strip() if candidate_name else None
    if notes is not None:
        lead.notes = notes.strip() if notes else None
    lead.status_updated_at = datetime.utcnow()

    db.commit()
    return True


def get_all_assignees(db: Session) -> List[str]:
    """Returns list of unique assignees in pipeline."""
    res = (
        db.query(func.distinct(Lead.assigned_to))
        .filter(Lead.assigned_to.isnot(None), Lead.assigned_to != "")
        .order_by(Lead.assigned_to.asc())
        .all()
    )
    return [r[0] for r in res if r[0]]


def get_filtered_leads(
    db: Session,
    search_term: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    selected_skill: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Returns detailed lead cards for the Lead Explorer & Pipeline views."""
    query = db.query(Lead)

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    if source and source != "Alla":
        query = query.filter(Lead.source == source)
    else:
        query = query.filter(Lead.source != "historical")

    if status and status != "Alla":
        if status == "Nytt":
            query = query.filter((Lead.status == "Nytt") | (Lead.status == None))
        else:
            query = query.filter(Lead.status == status)

    if assigned_to and assigned_to != "Alla":
        query = query.filter(Lead.assigned_to == assigned_to)

    if search_term:
        term = f"%{search_term}%"
        query = query.filter(
            (Lead.title.ilike(term))
            | (Lead.description.ilike(term))
            | (Lead.company_name.ilike(term))
            | (Lead.candidate_name.ilike(term))
            | (Lead.notes.ilike(term))
        )

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
            "status": getattr(l, "status", None) or "Nytt",
            "assigned_to": getattr(l, "assigned_to", None) or "",
            "candidate_name": getattr(l, "candidate_name", None) or "",
            "notes": getattr(l, "notes", None) or "",
            "status_updated_at": l.status_updated_at.strftime("%Y-%m-%d %H:%M") if getattr(l, "status_updated_at", None) else None,
        })
    return output
