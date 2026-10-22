"""
Historical Market Trend & Forecasting Analytics.
Analyzes long-term trends, skill growth trajectories, and seasonal patterns
across Östergötland, Södertälje & Nyköping (2022 - present).
"""
from typing import Dict, Any, List
import pandas as pd
from sqlalchemy import func, extract, literal_column
from sqlalchemy.orm import Session
from database.models import Lead, Skill, lead_skills


def get_monthly_volume_trend(db: Session, location: str = "Alla") -> pd.DataFrame:
    """
    Returns monthly posting volume over time.
    """
    query = db.query(
        func.to_char(Lead.published_at, "YYYY-MM").label("month"),
        func.count(Lead.id).label("postings"),
    ).filter(Lead.published_at.isnot(None))

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    results = (
        query.group_by(literal_column("month"))
        .order_by(literal_column("month"))
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["month", "postings"])

    df = pd.DataFrame(results, columns=["month", "postings"])
    return df[df["month"] >= "2022-01"]


def get_top_skills_time_series(
    db: Session,
    location: str = "Alla",
    top_n: int = 5,
) -> pd.DataFrame:
    """
    Returns monthly time-series for the top N most frequent technical skills.
    """
    # 1. Identify the top N skills overall
    top_skill_query = (
        db.query(Skill.id, Skill.name, func.count(Lead.id).label("total"))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at.isnot(None))
    )
    if location and location != "Alla":
        top_skill_query = top_skill_query.filter(Lead.location.ilike(f"%{location}%"))

    top_skill_ids = [
        row[0]
        for row in top_skill_query.group_by(Skill.id, Skill.name)
        .order_by(func.count(Lead.id).desc())
        .limit(top_n)
        .all()
    ]

    if not top_skill_ids:
        return pd.DataFrame(columns=["month", "skill", "count"])

    # 2. Query monthly trend for these skills
    trend_query = (
        db.query(
            func.to_char(Lead.published_at, "YYYY-MM").label("month"),
            Skill.name.label("skill"),
            func.count(Lead.id).label("count"),
        )
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Skill.id.in_(top_skill_ids))
        .filter(Lead.published_at.isnot(None))
    )
    if location and location != "Alla":
        trend_query = trend_query.filter(Lead.location.ilike(f"%{location}%"))

    results = (
        trend_query.group_by(
            literal_column("month"),
            Skill.name,
        )
        .order_by(literal_column("month"))
        .all()
    )

    df = pd.DataFrame(results, columns=["month", "skill", "count"])
    return df[df["month"] >= "2022-01"]


def get_skill_growth_barometer(db: Session, location: str = "Alla") -> pd.DataFrame:
    """
    Calculates growth trajectories by comparing postings between two periods:
    Period 1: First half of 2024
    Period 2: Recent 6-12 months (2025 onwards)
    """
    p1_start = "2024-01-01"
    p1_end = "2024-06-30"
    p2_start = "2025-01-01"
    p2_end = "2025-06-30"

    q1 = (
        db.query(Skill.name, func.count(Lead.id).label("count_p1"))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at >= p1_start, Lead.published_at <= p1_end)
    )
    q2 = (
        db.query(Skill.name, func.count(Lead.id).label("count_p2"))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at >= p2_start, Lead.published_at <= p2_end)
    )

    if location and location != "Alla":
        q1 = q1.filter(Lead.location.ilike(f"%{location}%"))
        q2 = q2.filter(Lead.location.ilike(f"%{location}%"))

    df1 = pd.DataFrame(q1.group_by(Skill.name).all(), columns=["skill", "count_p1"])
    df2 = pd.DataFrame(q2.group_by(Skill.name).all(), columns=["skill", "count_p2"])

    if df1.empty or df2.empty:
        return pd.DataFrame(columns=["skill", "count_p1", "count_p2", "growth_pct"])

    merged = pd.merge(df1, df2, on="skill", how="inner")
    merged = merged[merged["count_p1"] >= 3]  # filter low base noise

    merged["growth_pct"] = (
        ((merged["count_p2"] - merged["count_p1"]) / merged["count_p1"]) * 100
    ).round(1)

    return merged.sort_values(by="growth_pct", ascending=False).head(10)


def get_seasonal_pattern(db: Session, location: str = "Alla") -> pd.DataFrame:
    """
    Aggregates postings by calendar month (Jan-Dec) to display regional seasonality.
    """
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Maj", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dec",
    }

    query = db.query(
        extract("month", Lead.published_at).label("month_num"),
        func.count(Lead.id).label("count"),
    ).filter(Lead.published_at.isnot(None))

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    results = (
        query.group_by(literal_column("month_num"))
        .order_by(literal_column("month_num"))
        .all()
    )
    if not results:
        return pd.DataFrame(columns=["month_name", "count"])

    data = []
    for m_num, cnt in sorted(results, key=lambda x: int(x[0])):
        data.append({"month_num": int(m_num), "month_name": month_names.get(int(m_num), str(m_num)), "count": cnt})

    return pd.DataFrame(data)

