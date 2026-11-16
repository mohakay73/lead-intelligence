"""
Deal Economics & Bench Cost Calculator Module.
Provides financial modeling for consulting assignments:
- Revenue projection based on billable hourly rate, contract duration, and hours/month.
- Bench cost burn rate calculation (salary, 31.42% employer contributions, pension, overhead).
- Contribution margin (Täckningsbidrag, TB) and margin percentage.
- Avoided bench cost metrics for leadership ROI reporting.
"""
from typing import Dict, Any, Optional

DEFAULT_HOURS_PER_MONTH = 168  # Standard Swedish consulting month (~21 working days * 8h)

# Standard market rates and monthly employer cost benchmarks for Swedish IT consultancies
SENIORITY_BENCHMARKS = {
    "junior": {
        "hourly_rate": 900,
        "monthly_bench_cost": 65000,   # ~38k salary + 42% employer fees/pension + 11k overhead
        "label": "Junior (1–3 år)",
    },
    "mid": {
        "hourly_rate": 1050,
        "monthly_bench_cost": 80000,   # ~48k salary + 42% employer fees/pension + 12k overhead
        "label": "Mid (3–5 år)",
    },
    "senior": {
        "hourly_rate": 1200,
        "monthly_bench_cost": 95000,   # ~58k salary + 42% employer fees/pension + 13k overhead
        "label": "Senior (5–10 år)",
    },
    "lead": {
        "hourly_rate": 1350,
        "monthly_bench_cost": 110000,  # ~68k salary + 42% employer fees/pension + 14k overhead
        "label": "Lead / Arkitekt (>10 år)",
    },
}


def suggest_consultant_economics(title: str = "", seniority_hint: str = "") -> Dict[str, Any]:
    """
    Infers sensible default hourly rate and monthly bench cost based on consultant title or seniority.
    """
    text = f"{title} {seniority_hint}".lower()

    if any(k in text for k in ["lead", "arkitekt", "architect", "expert", "specialist", "principal", "chef", "manager"]):
        return SENIORITY_BENCHMARKS["lead"]
    elif any(k in text for k in ["senior", "sr", "8 år", "7 år", "9 år", "10 år"]):
        return SENIORITY_BENCHMARKS["senior"]
    elif any(k in text for k in ["junior", "jr", "trainee", "nyexad", "1 år", "2 år"]):
        return SENIORITY_BENCHMARKS["junior"]
    else:
        # Default to Senior/Mid for typical consulting bench profiles
        return SENIORITY_BENCHMARKS["senior"]


def calculate_deal_economics(
    hourly_rate: float,
    duration_months: int = 6,
    monthly_bench_cost: float = 95000.0,
    hours_per_month: int = DEFAULT_HOURS_PER_MONTH,
    allocation_pct: float = 100.0,
) -> Dict[str, Any]:
    """
    Calculates detailed financial figures for placing a consultant on an opportunity.
    
    Returns:
        Dict with total revenue, avoided bench cost, contribution margin, margin pct, etc.
    """
    alloc = max(0.1, min(1.0, allocation_pct / 100.0))
    effective_hours_per_month = hours_per_month * alloc
    total_hours = effective_hours_per_month * duration_months

    gross_revenue = round(hourly_rate * total_hours)
    monthly_revenue = round(hourly_rate * effective_hours_per_month)

    avoided_bench_cost = round(monthly_bench_cost * alloc * duration_months)
    monthly_cost = round(monthly_bench_cost * alloc)

    contribution_margin = gross_revenue - avoided_bench_cost
    monthly_margin = monthly_revenue - monthly_cost

    margin_pct = round((contribution_margin / gross_revenue) * 100, 1) if gross_revenue > 0 else 0.0

    return {
        "hourly_rate": int(hourly_rate),
        "duration_months": int(duration_months),
        "total_hours": int(total_hours),
        "gross_revenue": gross_revenue,
        "monthly_revenue": monthly_revenue,
        "avoided_bench_cost": avoided_bench_cost,
        "monthly_bench_cost": monthly_cost,
        "contribution_margin": contribution_margin,
        "monthly_margin": monthly_margin,
        "margin_pct": margin_pct,
        "formatted_revenue": f"{gross_revenue:,.0f} kr".replace(",", " "),
        "formatted_monthly_revenue": f"{monthly_revenue:,.0f} kr".replace(",", " "),
        "formatted_margin": f"{contribution_margin:,.0f} kr".replace(",", " "),
        "formatted_avoided_cost": f"{avoided_bench_cost:,.0f} kr".replace(",", " "),
    }
