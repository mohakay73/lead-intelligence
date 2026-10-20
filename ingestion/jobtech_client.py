import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from config import (
    JOBTECH_API_KEY,
    JOBTECH_API_URL,
    IT_OCCUPATION_FIELD,
    TARGET_REGION_CODE,
    TARGET_EXTRA_MUNICIPALITY_CODES,
)

logger = logging.getLogger(__name__)


class JobTechClient:
    """Client for Arbetsförmedlingen JobTech JobSearch API."""

    def __init__(self, base_url: str = JOBTECH_API_URL, api_key: str = JOBTECH_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "LeadIntelligencePlatform/1.0",
        }
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def fetch_it_leads_ostergotland(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches live IT/Data job postings in Östergötland (Linköping, Norrköping, etc.)
        as well as key regional extension hubs (Nyköping and Södertälje).
        """
        endpoint = f"{self.base_url}/search"
        headers = self._get_headers()
        all_hits = []
        seen_ids = set()

        # 1. Fetch Östergötlands län (05)
        try:
            params_region = {
                "occupation-field": IT_OCCUPATION_FIELD,
                "region": TARGET_REGION_CODE,
                "limit": limit,
            }
            res = requests.get(endpoint, params=params_region, headers=headers, timeout=15)
            res.raise_for_status()
            region_hits = res.json().get("hits", [])
            for h in region_hits:
                hid = h.get("id")
                if hid and hid not in seen_ids:
                    seen_ids.add(hid)
                    all_hits.append(h)
            logger.info(f"Fetched {len(region_hits)} hits from JobTech API for Östergötland.")
        except Exception as e:
            logger.error(f"Error fetching JobTech data for Östergötland: {e}")

        # 2. Fetch additional target municipalities (e.g. Nyköping, Södertälje)
        for muni_code in TARGET_EXTRA_MUNICIPALITY_CODES:
            try:
                params_muni = {
                    "occupation-field": IT_OCCUPATION_FIELD,
                    "municipality": muni_code,
                    "limit": limit,
                }
                res = requests.get(endpoint, params=params_muni, headers=headers, timeout=15)
                res.raise_for_status()
                muni_hits = res.json().get("hits", [])
                new_count = 0
                for h in muni_hits:
                    hid = h.get("id")
                    if hid and hid not in seen_ids:
                        seen_ids.add(hid)
                        all_hits.append(h)
                        new_count += 1
                logger.info(f"Fetched {new_count} additional hits for municipality code {muni_code}.")
            except Exception as e:
                logger.error(f"Error fetching JobTech data for municipality {muni_code}: {e}")

        logger.info(f"Total unified JobTech hits fetched: {len(all_hits)}")
        return self._standardize_hits(all_hits)

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Handle ISO formats: 2026-02-15T09:00:00 or with timezone
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def _standardize_hits(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        leads = []
        for hit in hits:
            workplace = hit.get("workplace_address") or {}
            employer = hit.get("employer") or {}
            desc = hit.get("description") or {}

            location = workplace.get("municipality") or "Östergötland"
            muni_code = workplace.get("municipality_code")

            lead = {
                "source": "jobtech",
                "external_id": str(hit.get("id")),
                "title": hit.get("headline", "Namnlös roll"),
                "company_name": employer.get("name", "Okänd arbetsgivare"),
                "description": desc.get("text", ""),
                "location": location,
                "municipality_code": muni_code,
                "region": workplace.get("region", "Östergötlands län"),
                "url": hit.get("webpage_url"),
                "is_consultant_assignment": False,
                "published_at": self._parse_date(hit.get("publication_date")),
                "deadline": self._parse_date(hit.get("application_deadline")),
            }
            leads.append(lead)
        return leads
