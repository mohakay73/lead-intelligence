"""
Historical Ingestion Module for JobTech Archive Data (2024 - 2025).
Fetches historical IT ads across Östergötland, Södertälje, and Nyköping to power
market trend analysis, skill evolution tracking, and seasonal forecasting.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List
import requests
from config import IT_OCCUPATION_FIELD, TARGET_REGION_CODE, TARGET_EXTRA_MUNICIPALITY_CODES
from database.connection import init_db, SessionLocal
from database.models import Lead, Skill
from ingestion.normalizer import extract_skills_from_text

logger = logging.getLogger("HistoricalIngestion")

HISTORICAL_API_URL = "https://historical.api.jobtechdev.se/search"


def fetch_historical_month_slice(
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetches historical IT job postings from JobTech Historical API for a specific date slice
    across Östergötland, Nyköping, and Södertälje.
    """
    headers = {"User-Agent": "LeadIntelligencePlatform/1.0", "Accept": "application/json"}
    all_hits = []
    seen_ids = set()

    # 1. Östergötland region
    try:
        params_region = {
            "occupation-field": IT_OCCUPATION_FIELD,
            "region": TARGET_REGION_CODE,
            "historical-from": f"{start_date}T00:00:00",
            "historical-to": f"{end_date}T23:59:59",
            "limit": limit,
        }
        res = requests.get(HISTORICAL_API_URL, params=params_region, headers=headers, timeout=20)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            for h in hits:
                hid = h.get("id")
                if hid and hid not in seen_ids:
                    seen_ids.add(hid)
                    all_hits.append(h)
    except Exception as e:
        logger.error(f"Error fetching historical data for Östergötland ({start_date} to {end_date}): {e}")

    # 2. Key corridors: Södertälje and Nyköping
    for muni in TARGET_EXTRA_MUNICIPALITY_CODES:
        try:
            params_muni = {
                "occupation-field": IT_OCCUPATION_FIELD,
                "municipality": muni,
                "historical-from": f"{start_date}T00:00:00",
                "historical-to": f"{end_date}T23:59:59",
                "limit": min(limit, 25),
            }
            res = requests.get(HISTORICAL_API_URL, params=params_muni, headers=headers, timeout=20)
            if res.status_code == 200:
                hits = res.json().get("hits", [])
                for h in hits:
                    hid = h.get("id")
                    if hid and hid not in seen_ids:
                        seen_ids.add(hid)
                        all_hits.append(h)
        except Exception as e:
            logger.error(f"Error fetching historical data for muni {muni}: {e}")

    return all_hits


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def run_historical_pipeline(
    start_year: int = 2024,
    end_year: int = 2026,
    end_month: int = 9,
    samples_per_month: int = 40,
) -> Dict[str, Any]:
    """
    Ingests monthly slices from start_year through end_year into the database with source='historical'.
    """
    init_db()
    db = SessionLocal()

    total_saved = 0
    total_skills = 0

    existing_skills = {s.name: s for s in db.query(Skill).all()}

    logger.info(f"Starting historical pipeline for {start_year} - {end_year}...")

    # Month by month iteration
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > end_month:
                break

            # Format month start and end
            start_date = f"{year}-{month:02d}-01"
            if month in [1, 3, 5, 7, 8, 10, 12]:
                end_day = 31
            elif month in [4, 6, 9, 11]:
                end_day = 30
            else:
                end_day = 29 if year % 4 == 0 else 28
            end_date = f"{year}-{month:02d}-{end_day}"

            hits = fetch_historical_month_slice(start_date, end_date, limit=samples_per_month)
            logger.info(f"Month {start_date[:7]}: Fetched {len(hits)} historical hits.")

            for hit in hits:
                ext_id = str(hit.get("id"))
                existing = db.query(Lead).filter(Lead.source == "historical", Lead.external_id == ext_id).first()
                if existing:
                    continue

                workplace = hit.get("workplace_address") or {}
                employer = hit.get("employer") or {}
                desc = hit.get("description") or {}

                location = workplace.get("municipality") or "Östergötland"
                pub_date = parse_date(hit.get("publication_date") or start_date)

                lead = Lead(
                    source="historical",
                    external_id=ext_id,
                    title=hit.get("headline", "Namnlös roll"),
                    company_name=employer.get("name", "Okänd arbetsgivare"),
                    description=desc.get("text", "")[:2000],  # trim very long text
                    location=location,
                    municipality_code=workplace.get("municipality_code"),
                    region=workplace.get("region", "Östergötlands län"),
                    url=hit.get("webpage_url"),
                    is_consultant_assignment=False,
                    published_at=pub_date,
                    deadline=parse_date(hit.get("application_deadline") or end_date),
                )
                db.add(lead)

                # Skill normalization
                text_to_scan = f"{lead.title} {lead.description or ''}"
                detected = extract_skills_from_text(text_to_scan)
                lead.skills = []
                for skill_name, category in detected:
                    if skill_name not in existing_skills:
                        skill_obj = Skill(name=skill_name, category=category)
                        db.add(skill_obj)
                        db.flush()
                        existing_skills[skill_name] = skill_obj
                    else:
                        skill_obj = existing_skills[skill_name]
                    lead.skills.append(skill_obj)
                    total_skills += 1

                total_saved += 1

            db.commit()

    db.close()
    logger.info(f"Historical pipeline complete. Saved {total_saved} historical leads with {total_skills} skill connections.")
    return {"saved_leads": total_saved, "mapped_skills": total_skills}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_historical_pipeline(start_year=2024, end_year=2025, samples_per_month=35)

