"""
Market Forecasting Engine for Consulting Leadership.
Trains predictive time-series models on engineered features in Supabase (market_features),
generates 6-month forward market forecasts with confidence intervals,
computes skill momentum trajectories, and persists results to market_forecasts.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import MarketFeature, MarketForecast, Skill, Lead, lead_skills

logger = logging.getLogger("ForecastEngine")


def get_training_features(db: Session, location: str = "Alla") -> pd.DataFrame:
    """Retrieves feature table for location from Supabase."""
    query = (
        db.query(MarketFeature)
        .filter(MarketFeature.location == location)
        .order_by(MarketFeature.period.asc())
    )
    records = query.all()
    if not records:
        return pd.DataFrame()

    data = []
    for r in records:
        data.append({
            "period": r.period,
            "total_postings": r.total_postings,
            "lag_1m": r.lag_1m,
            "lag_2m": r.lag_2m,
            "lag_3m": r.lag_3m,
            "lag_12m": r.lag_12m,
            "rolling_mean_3m": r.rolling_mean_3m,
            "rolling_mean_6m": r.rolling_mean_6m,
            "month_num": r.month_num,
            "quarter": r.quarter,
        })
    df = pd.DataFrame(data)
    return df


def train_and_forecast_volume(
    df: pd.DataFrame,
    horizon_months: int = 6,
) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """
    Fits Exponential Smoothing (Holt-Winters with damped trend & 12-month seasonality),
    and generates non-explosive, calibrated multi-step forecasts with confidence intervals.
    """
    if len(df) < 15:
        return [], {}

    series = df["total_postings"].values.astype(float)

    try:
        # Fit Holt-Winters with additive damped trend and 12-month seasonality
        model = ExponentialSmoothing(
            series,
            seasonal_periods=12,
            trend="add",
            seasonal="add",
            damped_trend=True,
            initialization_method="estimated",
        ).fit()
        raw_preds = model.forecast(horizon_months)
        residuals = model.resid
        mae = float(mean_absolute_error(series[12:], model.fittedvalues[12:]))
        rmse = float(root_mean_squared_error(series[12:], model.fittedvalues[12:]))
        residual_std = float(np.std(residuals))
    except Exception as e:
        logger.warning(f"Holt-Winters fallback due to: {e}")
        # Robust linear trend fallback
        t = np.arange(len(series))
        p = np.polyfit(t, series, 1)
        raw_preds = np.polyval(p, np.arange(len(series), len(series) + horizon_months))
        residuals = series - np.polyval(p, t)
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        residual_std = float(np.std(residuals))

    forecasts = []
    last_period = df["period"].iloc[-1]  # e.g. "2026-10"
    last_year, last_month = map(int, last_period.split("-"))
    prev_val = float(series[-1])

    current_year = last_year
    current_month = last_month

    for step, p_val in enumerate(raw_preds):
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

        forecast_period = f"{current_year}-{current_month:02d}"

        pred_val = float(max(5.0, round(p_val, 1)))

        # 80% Confidence Interval: ~1.28 * std * sqrt(1 + 0.08 * step)
        step_uncertainty = float(1.28 * residual_std * np.sqrt(1 + 0.08 * step))
        ci_lower = float(max(2.0, round(pred_val - step_uncertainty, 1)))
        ci_upper = float(round(pred_val + step_uncertainty, 1))

        # Growth MoM
        growth_mom = float(round(((pred_val - prev_val) / prev_val) * 100, 1)) if prev_val > 0 else 0.0

        forecasts.append({
            "forecast_month": forecast_period,
            "predicted_volume": pred_val,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "growth_mom_pct": growth_mom,
        })

        prev_val = pred_val

    metrics = {"mae": round(mae, 2), "rmse": round(rmse, 2), "residual_std": round(residual_std, 2)}
    return forecasts, metrics


def compute_skill_momentum_forecast(db: Session, location: str = "Alla") -> List[Dict[str, Any]]:
    """
    Computes velocity and trajectory of technical skills.
    Compares recent 6 months with prior period and labels actionable leadership focus.
    """
    # Period 1: 2025-05 to 2025-10
    # Period 2: 2026-05 to 2026-10
    dt_p1_start = datetime(2025, 5, 1)
    dt_p1_end = datetime(2025, 10, 31, 23, 59, 59)
    dt_p2_start = datetime(2026, 5, 1)
    dt_p2_end = datetime(2026, 10, 31, 23, 59, 59)

    q1 = (
        db.query(Skill.name, Skill.category, func.count(Lead.id).label("count_p1"))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at >= dt_p1_start, Lead.published_at <= dt_p1_end)
    )
    q2 = (
        db.query(Skill.name, Skill.category, func.count(Lead.id).label("count_p2"))
        .join(lead_skills, Skill.id == lead_skills.c.skill_id)
        .join(Lead, Lead.id == lead_skills.c.lead_id)
        .filter(Lead.published_at >= dt_p2_start, Lead.published_at <= dt_p2_end)
    )

    if location and location != "Alla":
        q1 = q1.filter(Lead.location.ilike(f"%{location}%"))
        q2 = q2.filter(Lead.location.ilike(f"%{location}%"))

    df1 = pd.DataFrame(q1.group_by(Skill.name, Skill.category).all(), columns=["skill", "category", "count_p1"])
    df2 = pd.DataFrame(q2.group_by(Skill.name, Skill.category).all(), columns=["skill", "category", "count_p2"])

    if df1.empty or df2.empty:
        return []

    merged = pd.merge(df1, df2, on=["skill", "category"], how="outer").fillna(0)
    merged = merged[(merged["count_p1"] + merged["count_p2"]) >= 4]  # filter low volume noise

    merged["growth_pct"] = np.where(
        merged["count_p1"] > 0,
        ((merged["count_p2"] - merged["count_p1"]) / merged["count_p1"]) * 100,
        100.0,
    ).round(1)

    merged["momentum_score"] = (merged["count_p2"] * 0.6 + merged["growth_pct"] * 0.4).round(1)

    # Classify into strategic focus:
    # 1. Investera / Certifiera: Strong positive growth (> 15%)
    # 2. Etablerad kassako: High volume (>= 15), stable
    # 3. Minskat fokus: Negative growth
    def label_strategy(row):
        if row["growth_pct"] >= 20.0 and row["count_p2"] >= 5:
            return "Investera & Certifiera (Hög expansion)"
        elif row["count_p2"] >= 15:
            return "Etablerad kassako (Hög stabil volym)"
        elif row["growth_pct"] <= -15.0:
            return "Avtagande (Minska utbildningsfokus)"
        else:
            return "Stabil efterfrågan"

    merged["action_label"] = merged.apply(label_strategy, axis=1)
    sorted_skills = merged.sort_values(by="momentum_score", ascending=False)

    output = []
    for _, r in sorted_skills.head(20).iterrows():
        output.append({
            "skill": r["skill"],
            "category": r["category"],
            "current_volume": int(r["count_p2"]),
            "growth_pct": float(r["growth_pct"]),
            "momentum_score": float(r["momentum_score"]),
            "action": r["action_label"],
        })
    return output


def run_forecast_and_save(db: Session, location: str = "Alla") -> Dict[str, Any]:
    """
    Fits model, generates 6-month forecast and skill momentum,
    and updates market_forecasts table in Supabase.
    """
    feature_df = get_training_features(db, location=location)
    if feature_df.empty or len(feature_df) < 15:
        logger.warning(f"Insufficient feature data for location '{location}'")
        return {"status": "skipped", "reason": "insufficient data"}

    forecasts, metrics = train_and_forecast_volume(feature_df, horizon_months=6)
    trending_skills = compute_skill_momentum_forecast(db, location=location)
    trending_skills_json = json.dumps(trending_skills)

    for fc in forecasts:
        f_month = fc["forecast_month"]
        existing = (
            db.query(MarketForecast)
            .filter(MarketForecast.forecast_month == f_month, MarketForecast.location == location)
            .first()
        )

        if not existing:
            rec = MarketForecast(
                forecast_month=f_month,
                location=location,
                predicted_volume=float(fc["predicted_volume"]),
                ci_lower=float(fc["ci_lower"]),
                ci_upper=float(fc["ci_upper"]),
                growth_mom_pct=float(fc["growth_mom_pct"]) if fc["growth_mom_pct"] is not None else None,
                model_version="Ridge-v1.0",
                trending_skills=trending_skills_json,
            )
            db.add(rec)
        else:
            existing.predicted_volume = float(fc["predicted_volume"])
            existing.ci_lower = float(fc["ci_lower"])
            existing.ci_upper = float(fc["ci_upper"])
            existing.growth_mom_pct = float(fc["growth_mom_pct"]) if fc["growth_mom_pct"] is not None else None
            existing.model_version = "Ridge-v1.0"
            existing.trending_skills = trending_skills_json

    db.commit()
    logger.info(f"Saved {len(forecasts)} forecast months for location='{location}'. Metrics: {metrics}")
    return {"status": "success", "location": location, "forecasts": forecasts, "metrics": metrics}


def run_all_forecasts() -> Dict[str, Any]:
    """Runs forecast engine across all key regional corridors."""
    db = SessionLocal()
    try:
        locations = ["Alla", "Linköping", "Norrköping", "Södertälje", "Nyköping"]
        results = {}
        for loc in locations:
            results[loc] = run_forecast_and_save(db, location=loc)
        return {"status": "completed", "results": results}
    finally:
        db.close()


# ---------------- Query functions for Streamlit UI ----------------

def get_forecast_display_data(db: Session, location: str = "Alla") -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
    """
    Returns (history_df, forecast_df, trending_skills_list) for dashboard plotting.
    """
    # 1. Historical postings
    hist_feats = (
        db.query(MarketFeature.period, MarketFeature.total_postings)
        .filter(MarketFeature.location == location)
        .order_by(MarketFeature.period.asc())
        .all()
    )
    hist_df = pd.DataFrame(hist_feats, columns=["period", "total_postings"]) if hist_feats else pd.DataFrame(columns=["period", "total_postings"])

    # 2. Forecasts
    fcs = (
        db.query(
            MarketForecast.forecast_month.label("period"),
            MarketForecast.predicted_volume,
            MarketForecast.ci_lower,
            MarketForecast.ci_upper,
            MarketForecast.growth_mom_pct,
            MarketForecast.trending_skills,
        )
        .filter(MarketForecast.location == location)
        .order_by(MarketForecast.forecast_month.asc())
        .all()
    )

    if not fcs:
        return hist_df, pd.DataFrame(), []

    fc_df = pd.DataFrame(fcs, columns=["period", "predicted_volume", "ci_lower", "ci_upper", "growth_mom_pct", "trending_skills"])

    trending_skills = []
    if not fc_df.empty and fc_df["trending_skills"].iloc[0]:
        try:
            trending_skills = json.loads(fc_df["trending_skills"].iloc[0])
        except Exception:
            trending_skills = []

    return hist_df, fc_df.drop(columns=["trending_skills"]), trending_skills


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = run_all_forecasts()
    print("Forecast execution completed:", res["status"])
