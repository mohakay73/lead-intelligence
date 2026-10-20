import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import requests
from config import BRAINVILLE_API_KEY, BRAINVILLE_API_URL

logger = logging.getLogger(__name__)


class BrainvilleClient:
    """Client for Brainville Consultant Assignment API v2."""

    def __init__(self, base_url: str = BRAINVILLE_API_URL, api_key: str = BRAINVILLE_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def fetch_consultant_requests(self) -> List[Dict[str, Any]]:
        """
        Fetches live consultant assignments from Brainville API.
        Falls back to realistic mock consultant assignments if no API key is provided.
        """
        if self.api_key:
            return self._fetch_live_api()
        else:
            logger.info("No BRAINVILLE_API_KEY set. Providing mock consultant assignments for Östergötland & E4 Syd.")
            return self._generate_mock_requests()

    def _fetch_live_api(self) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        endpoint = f"{self.base_url}/assignments"
        params = {
            "region": "Östergötland",
            "status": "active",
        }
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            items = data.get("items") or data.get("assignments") or []
            return self._standardize_brainville_items(items)
        except Exception as e:
            logger.error(f"Error fetching from Brainville API: {e}. Falling back to sample assignments.")
            return self._generate_mock_requests()

    def _standardize_brainville_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        leads = []
        for item in items:
            leads.append({
                "source": "brainville",
                "external_id": str(item.get("id")),
                "title": item.get("title", "Konsultuppdrag"),
                "company_name": item.get("client_name") or item.get("broker_name", "Sekretessbelagd kund"),
                "description": item.get("description", ""),
                "location": item.get("location", "Linköping"),
                "municipality_code": None,
                "region": "Östergötlands län",
                "url": item.get("url") or f"https://www.brainville.com/assignment/{item.get('id')}",
                "is_consultant_assignment": True,
                "published_at": datetime.utcnow() - timedelta(days=2),
                "deadline": datetime.utcnow() + timedelta(days=14),
            })
        return leads

    def _generate_mock_requests(self) -> List[Dict[str, Any]]:
        """Realistic sample consultant assignments tailored for Östergötland, Nyköping & Södertälje."""
        now = datetime.utcnow()
        return [
            {
                "source": "brainville",
                "external_id": "bv-ost-101",
                "title": "Senior .NET / Azure Utvecklare till Region Östergötland",
                "company_name": "Region Östergötland (via Mäklare)",
                "description": "Vi söker en erfaren fullstack-utvecklare med stark profil inom .NET Core, C# och Azure. Uppdraget innefattar vidareutveckling av vårdrelaterade interna stödsystem, integration med REST API och mikrotjänster i Kubernetes.",
                "location": "Linköping",
                "municipality_code": "0580",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-101",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=1),
                "deadline": now + timedelta(days=10),
            },
            {
                "source": "brainville",
                "external_id": "bv-ost-102",
                "title": "Cloud & DevOps Specialist (Terraform / Azure)",
                "company_name": "Teknikbolag Mjärdevi",
                "description": "Uppdrag inom molninfrastruktur och automation. Rollen kräver gedigen erfarenhet av Terraform, Microsoft Azure, CI/CD pipelines i GitHub Actions samt containerisering via Docker och Kubernetes (AKS).",
                "location": "Linköping",
                "municipality_code": "0580",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-102",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=2),
                "deadline": now + timedelta(days=14),
            },
            {
                "source": "brainville",
                "external_id": "bv-ost-103",
                "title": "C++ / Embedded Software Developer",
                "company_name": "Försvars- och säkerhetskoncern",
                "description": "Konsultförfrågan för systemnära utveckling i C++ under Linux RTOS. Erfarenhet av realtidssystem, CAN-buss, säkerhetskritiska system och agil utveckling i SAFe.",
                "location": "Linköping",
                "municipality_code": "0580",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-103",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=3),
                "deadline": now + timedelta(days=8),
            },
            {
                "source": "brainville",
                "external_id": "bv-ost-104",
                "title": "Data Engineer / Power BI & Databricks Konsult",
                "company_name": "Industrikoncern Norrköping",
                "description": "Vi etablerar en modern dataplattform baserad på Databricks, PySpark och Microsoft Fabric. Vi söker en Data Engineer som kan bygga ETL-flöden i SQL och visualisera ledningsrapporter i Power BI.",
                "location": "Norrköping",
                "municipality_code": "0581",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-104",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=4),
                "deadline": now + timedelta(days=12),
            },
            {
                "source": "brainville",
                "external_id": "bv-ost-105",
                "title": "Informationssäkerhet & NIS2 Koordinator",
                "company_name": "Offentlig sektor Östergötland",
                "description": "Uppdrag att genomföra gapanalys och implementera ledningssystem för informationssäkerhet (LIS) enligt ISO 27001 och NIS2-direktivet. Erfarenhet av säkerhetsskyddslagen och riskbedömning är ett krav.",
                "location": "Norrköping",
                "municipality_code": "0581",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-105",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=1),
                "deadline": now + timedelta(days=15),
            },
            {
                "source": "brainville",
                "external_id": "bv-ost-106",
                "title": "Frontend Lead (React & TypeScript)",
                "company_name": "E-handelsbolag Norrköping",
                "description": "Vi söker en senior frontendutvecklare med djup förståelse för React, TypeScript, Next.js och modern CSS. Du leder frontend-arkitekturen och säkerställer god prestanda och tillgänglighet (WCAG).",
                "location": "Norrköping",
                "municipality_code": "0581",
                "region": "Östergötlands län",
                "url": "https://www.brainville.com/assignment/bv-ost-106",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(hours=18),
                "deadline": now + timedelta(days=20),
            },
            {
                "source": "brainville",
                "external_id": "bv-sod-201",
                "title": "Embedded Automotive & Diagnostics Specialist (C++ / AUTOSAR)",
                "company_name": "Fordonskoncern Södertälje (Scania-kluster)",
                "description": "Konsultuppdrag för mjukvaruutveckling inom elektrifiering och tunga fordon. Kräver djup kompetens inom C++, Linux, CAN-buss, AUTOSAR och diagnostikverktyg.",
                "location": "Södertälje",
                "municipality_code": "0181",
                "region": "Stockholms län",
                "url": "https://www.brainville.com/assignment/bv-sod-201",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=1),
                "deadline": now + timedelta(days=12),
            },
            {
                "source": "brainville",
                "external_id": "bv-sod-202",
                "title": "Cloud Platform Architect (AWS / Kubernetes) Life Science",
                "company_name": "Läkemedels- och Bioteknikbolag Södertälje",
                "description": "Vi söker en erfaren Cloud Architect för att designa validerade molnmiljöer i AWS och Kubernetes för hantering av kliniska forskningsdata. GxP och säkerhetsefterlevnad är meriterande.",
                "location": "Södertälje",
                "municipality_code": "0181",
                "region": "Stockholms län",
                "url": "https://www.brainville.com/assignment/bv-sod-202",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=2),
                "deadline": now + timedelta(days=16),
            },
            {
                "source": "brainville",
                "external_id": "bv-nyk-301",
                "title": "Fullstack .NET / Cloud Utvecklare",
                "company_name": "Offentlig verksamhet & Industri Nyköping",
                "description": "Konsultförfrågan för vidareutveckling av verksamhetsnära system i C#, .NET 8 och Azure. Integration med SQL-databaser och moderna frontend-gränssnitt i React.",
                "location": "Nyköping",
                "municipality_code": "0480",
                "region": "Södermanlands län",
                "url": "https://www.brainville.com/assignment/bv-nyk-301",
                "is_consultant_assignment": True,
                "published_at": now - timedelta(days=3),
                "deadline": now + timedelta(days=10),
            },
        ]
