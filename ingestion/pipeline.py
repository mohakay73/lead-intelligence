import logging
from typing import Dict, Any
from database.connection import init_db, SessionLocal
from database.models import Lead, Skill
from ingestion.jobtech_client import JobTechClient
from ingestion.brainville_client import BrainvilleClient
from ingestion.normalizer import extract_skills_from_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IngestionPipeline")


def run_pipeline() -> Dict[str, Any]:
    """
    Executes the ingestion and skill normalization pipeline for all API sources.
    Returns summary statistics.
    """
    logger.info("Starting ingestion pipeline...")
    init_db()
    db = SessionLocal()

    stats = {
        "jobtech_fetched": 0,
        "brainville_fetched": 0,
        "new_leads_saved": 0,
        "existing_leads_updated": 0,
        "skills_mapped": 0,
    }

    try:
        # 1. Fetch from JobTech API
        jobtech_client = JobTechClient()
        jobtech_leads = jobtech_client.fetch_it_leads_ostergotland()
        stats["jobtech_fetched"] = len(jobtech_leads)

        # 2. Fetch from Brainville API
        brainville_client = BrainvilleClient()
        brainville_leads = brainville_client.fetch_consultant_requests()
        stats["brainville_fetched"] = len(brainville_leads)

        all_raw_leads = jobtech_leads + brainville_leads
        logger.info(f"Total raw leads fetched across all sources: {len(all_raw_leads)}")

        # Cache existing skills to minimize DB queries
        existing_skills = {s.name: s for s in db.query(Skill).all()}

        for raw in all_raw_leads:
            source = raw["source"]
            external_id = raw["external_id"]

            lead = (
                db.query(Lead)
                .filter(Lead.source == source, Lead.external_id == external_id)
                .first()
            )

            is_new = False
            if not lead:
                lead = Lead(source=source, external_id=external_id)
                db.add(lead)
                stats["new_leads_saved"] += 1
                is_new = True
            else:
                stats["existing_leads_updated"] += 1

            lead.title = raw.get("title", lead.title)
            lead.company_name = raw.get("company_name", lead.company_name)
            lead.description = raw.get("description", lead.description)
            lead.location = raw.get("location", lead.location)
            lead.municipality_code = raw.get("municipality_code", lead.municipality_code)
            lead.region = raw.get("region", lead.region)
            lead.url = raw.get("url", lead.url)
            lead.is_consultant_assignment = raw.get(
                "is_consultant_assignment", lead.is_consultant_assignment
            )
            lead.published_at = raw.get("published_at", lead.published_at)
            lead.deadline = raw.get("deadline", lead.deadline)

            # Normalization Layer: Extract skills
            text_to_scan = f"{lead.title} {lead.description or ''}"
            detected_skills = extract_skills_from_text(text_to_scan)

            lead.skills = []
            for skill_name, category in detected_skills:
                if skill_name not in existing_skills:
                    skill_obj = Skill(name=skill_name, category=category)
                    db.add(skill_obj)
                    db.flush()
                    existing_skills[skill_name] = skill_obj
                else:
                    skill_obj = existing_skills[skill_name]

                lead.skills.append(skill_obj)
                stats["skills_mapped"] += 1

        db.commit()
        logger.info(f"Pipeline completed successfully: {stats}")
        return stats

    except Exception as e:
        db.rollback()
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()

