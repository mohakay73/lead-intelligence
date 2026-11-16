"""
Deal Economics & Bench Cost Calculator Module.
Provides financial modeling for consulting assignments:
- Revenue projection based on billable hourly rate, contract duration, and hours/month.
- Bench cost burn rate calculation (salary, 31.42% employer contributions, pension, overhead).
- Granular consultant cost adjustment (by monthly salary OR direct hourly cost / subconsultant rate).
- Contribution margin (Täckningsbidrag, TB) and margin percentage.
- Avoided bench cost metrics for leadership ROI reporting.
"""
from typing import Dict, Any, Optional

DEFAULT_HOURS_PER_MONTH = 168  # Standard Swedish consulting month (~21 working days * 8h)

# Standard market rates and monthly employer cost benchmarks for Swedish IT consultancies
SENIORITY_BENCHMARKS = {
    "junior": {
        "hourly_rate": 900,
        "monthly_salary": 38000,
        "monthly_bench_cost": 65000,   # ~38k salary + 42% employer fees/pension + 11k overhead (~387 kr/h)
        "hourly_cost": 387,
        "label": "Junior (1–3 år)",
    },
    "mid": {
        "hourly_rate": 1050,
        "monthly_salary": 48000,
        "monthly_bench_cost": 80000,   # ~48k salary + 42% employer fees/pension + 12k overhead (~476 kr/h)
        "hourly_cost": 476,
        "label": "Mid (3–5 år)",
    },
    "senior": {
        "hourly_rate": 1200,
        "monthly_salary": 58000,
        "monthly_bench_cost": 95000,   # ~58k salary + 42% employer fees/pension + 13k overhead (~565 kr/h)
        "hourly_cost": 565,
        "label": "Senior (5–10 år)",
    },
    "lead": {
        "hourly_rate": 1350,
        "monthly_salary": 68000,
        "monthly_bench_cost": 110000,  # ~68k salary + 42% employer fees/pension + 14k overhead (~655 kr/h)
        "hourly_cost": 655,
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
    hourly_cost: Optional[float] = None,
    monthly_salary: Optional[float] = None,
    monthly_bench_cost: Optional[float] = None,
    hours_per_month: int = DEFAULT_HOURS_PER_MONTH,
    allocation_pct: float = 100.0,
    include_overhead: bool = True,
) -> Dict[str, Any]:
    """
    Calculates detailed financial figures for placing a consultant on an opportunity.
    Supports either direct hourly cost (subconsultant / exact cost/h) or monthly salary.
    
    Returns:
        Dict with total revenue, total cost, contribution margin, margin pct, hourly profit, etc.
    """
    alloc = max(0.1, min(1.0, allocation_pct / 100.0))
    effective_hours_per_month = hours_per_month * alloc
    total_hours = effective_hours_per_month * duration_months

    # Determine effective hourly cost & monthly cost
    if hourly_cost is not None and hourly_cost > 0:
        eff_hourly_cost = float(hourly_cost)
        eff_monthly_cost = eff_hourly_cost * effective_hours_per_month
        cost_source = "hourly"
    elif monthly_salary is not None and monthly_salary > 0:
        # Swedish employer fees (31.42%) + ITP pension (8.0%) = 39.42%
        overhead_amount = 12000.0 if include_overhead else 0.0
        eff_monthly_cost = (monthly_salary * 1.3942 + overhead_amount) * alloc
        eff_hourly_cost = eff_monthly_cost / effective_hours_per_month
        cost_source = "salary"
    elif monthly_bench_cost is not None and monthly_bench_cost > 0:
        eff_monthly_cost = monthly_bench_cost * alloc
        eff_hourly_cost = eff_monthly_cost / effective_hours_per_month
        cost_source = "benchmark"
    else:
        eff_monthly_cost = 95000.0 * alloc
        eff_hourly_cost = eff_monthly_cost / effective_hours_per_month
        cost_source = "default"

    gross_revenue = round(hourly_rate * total_hours)
    monthly_revenue = round(hourly_rate * effective_hours_per_month)

    total_cost = round(eff_monthly_cost * duration_months)
    avoided_bench_cost = total_cost

    contribution_margin = gross_revenue - total_cost
    monthly_margin = monthly_revenue - round(eff_monthly_cost)
    hourly_profit = round(hourly_rate - eff_hourly_cost)

    margin_pct = round((contribution_margin / gross_revenue) * 100, 1) if gross_revenue > 0 else 0.0

    return {
        "hourly_rate": int(hourly_rate),
        "hourly_cost": int(round(eff_hourly_cost)),
        "hourly_profit": hourly_profit,
        "duration_months": int(duration_months),
        "total_hours": int(total_hours),
        "gross_revenue": gross_revenue,
        "monthly_revenue": monthly_revenue,
        "total_cost": total_cost,
        "avoided_bench_cost": avoided_bench_cost,
        "monthly_bench_cost": round(eff_monthly_cost),
        "contribution_margin": contribution_margin,
        "monthly_margin": monthly_margin,
        "margin_pct": margin_pct,
        "cost_source": cost_source,
        "formatted_revenue": f"{gross_revenue:,.0f} kr".replace(",", " "),
        "formatted_monthly_revenue": f"{monthly_revenue:,.0f} kr".replace(",", " "),
        "formatted_cost": f"{total_cost:,.0f} kr".replace(",", " "),
        "formatted_margin": f"{contribution_margin:,.0f} kr".replace(",", " "),
        "formatted_avoided_cost": f"{avoided_bench_cost:,.0f} kr".replace(",", " "),
    }
