"""
Feature Engineering Pipeline for Market Intelligence.
Aggregates raw leads into monthly time-series features (lags, rolling averages, seasonality)
and tracks skill momentum over time. Persists features into Supabase (market_features).
"""
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Lead, Skill, lead_skills, MarketFeature

logger = logging.getLogger("FeaturePipeline")


def extract_monthly_time_series(db: Session, location: str = "Alla") -> pd.DataFrame:
    """
    Extracts chronological monthly posting counts from leads database.
    """
    query = db.query(
        func.to_char(Lead.published_at, "YYYY-MM").label("period"),
        func.count(Lead.id).label("total_postings"),
    ).filter(Lead.published_at.isnot(None))

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    results = (
        query.group_by(func.to_char(Lead.published_at, "YYYY-MM"))
        .order_by(func.to_char(Lead.published_at, "YYYY-MM"))
        .all()
    )

    if not results:
        return pd.DataFrame(columns=["period", "total_postings"])

    df = pd.DataFrame(results, columns=["period", "total_postings"])
    df = df[df["period"] >= "2022-01"]
    return df


def compute_skill_distribution_per_month(db: Session, location: str = "Alla") -> Dict[str, Dict[str, int]]:
    """
    Computes count of top skills mentioned in each month.
    """
    query = (
        db.query(
            func.to_char(Lead.published_at, "YYYY-MM").label("period"),
            Skill.name.label("skill"),
            func.count(Lead.id).label("count"),
        )
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at.isnot(None))
    )

    if location and location != "Alla":
        query = query.filter(Lead.location.ilike(f"%{location}%"))

    results = (
        query.group_by(func.to_char(Lead.published_at, "YYYY-MM"), Skill.name)
        .order_by(func.to_char(Lead.published_at, "YYYY-MM"))
        .all()
    )

    period_skills: Dict[str, Dict[str, int]] = {}
    for p, s, c in results:
        if p not in period_skills:
            period_skills[p] = {}
        period_skills[p][s] = int(c)
    return period_skills


def build_and_save_market_features(db: Session, location: str = "Alla") -> int:
    """
    Computes lag features, rolling windows, and seasonality indicators,
    then upserts them into the market_features table in Supabase.
    """
    df = extract_monthly_time_series(db, location=location)
    if df.empty:
        logger.warning(f"No time series data found for location {location}")
        return 0

    df["total_postings"] = df["total_postings"].astype(int)

    # 1. Temporal & Calendar features
    df["month_num"] = df["period"].apply(lambda p: int(p.split("-")[1]))
    df["quarter"] = df["month_num"].apply(lambda m: (m - 1) // 3 + 1)

    # 2. Lag features
    df["lag_1m"] = df["total_postings"].shift(1)
    df["lag_2m"] = df["total_postings"].shift(2)
    df["lag_3m"] = df["total_postings"].shift(3)
    df["lag_12m"] = df["total_postings"].shift(12)  # YoY seasonal lag

    # 3. Rolling window features (strictly historical: shifted by 1 to prevent data leakage)
    df["rolling_mean_3m"] = df["total_postings"].shift(1).rolling(window=3, min_periods=1).mean().round(2)
    df["rolling_mean_6m"] = df["total_postings"].shift(1).rolling(window=6, min_periods=1).mean().round(2)

    # 4. Monthly skill distribution
    skill_dist = compute_skill_distribution_per_month(db, location=location)

    # 5. Save/Upsert into database
    records_saved = 0
    for _, row in df.iterrows():
        period = row["period"]
        existing = (
            db.query(MarketFeature)
            .filter(MarketFeature.period == period, MarketFeature.location == location)
            .first()
        )

        skills_json = json.dumps(skill_dist.get(period, {}))

        if not existing:
            feature_record = MarketFeature(
                period=period,
                location=location,
                total_postings=int(row["total_postings"]),
                lag_1m=int(row["lag_1m"]) if pd.notna(row["lag_1m"]) else None,
                lag_2m=int(row["lag_2m"]) if pd.notna(row["lag_2m"]) else None,
                lag_3m=int(row["lag_3m"]) if pd.notna(row["lag_3m"]) else None,
                lag_12m=int(row["lag_12m"]) if pd.notna(row["lag_12m"]) else None,
                rolling_mean_3m=float(row["rolling_mean_3m"]) if pd.notna(row["rolling_mean_3m"]) else None,
                rolling_mean_6m=float(row["rolling_mean_6m"]) if pd.notna(row["rolling_mean_6m"]) else None,
                month_num=int(row["month_num"]),
                quarter=int(row["quarter"]),
                skill_distribution=skills_json,
            )
            db.add(feature_record)
        else:
            existing.total_postings = int(row["total_postings"])
            existing.lag_1m = int(row["lag_1m"]) if pd.notna(row["lag_1m"]) else None
            existing.lag_2m = int(row["lag_2m"]) if pd.notna(row["lag_2m"]) else None
            existing.lag_3m = int(row["lag_3m"]) if pd.notna(row["lag_3m"]) else None
            existing.lag_12m = int(row["lag_12m"]) if pd.notna(row["lag_12m"]) else None
            existing.rolling_mean_3m = float(row["rolling_mean_3m"]) if pd.notna(row["rolling_mean_3m"]) else None
            existing.rolling_mean_6m = float(row["rolling_mean_6m"]) if pd.notna(row["rolling_mean_6m"]) else None
            existing.month_num = int(row["month_num"])
            existing.quarter = int(row["quarter"])
            existing.skill_distribution = skills_json

        records_saved += 1

    db.commit()
    logger.info(f"Saved {records_saved} feature periods for location='{location}'.")
    return records_saved


def run_feature_pipeline() -> Dict[str, Any]:
    """Runs feature extraction for region overall and primary corridors."""
    db = SessionLocal()
    try:
        locations_to_process = ["Alla", "Linköping", "Norrköping", "Södertälje", "Nyköping"]
        total = 0
        for loc in locations_to_process:
            total += build_and_save_market_features(db, location=loc)
        return {"status": "success", "feature_records_processed": total}
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = run_feature_pipeline()
    print("Feature Pipeline Completed:", res)
