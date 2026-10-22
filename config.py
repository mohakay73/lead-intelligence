import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

def get_secret(key: str, default: str = "") -> str:
    """Reads configuration from environment variables or Streamlit secrets."""
    val = os.getenv(key, "")
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key, "")
        except Exception:
            pass
    return str(val).strip() if val else default

# Database URL: default to SQLite for instant local runs, or PostgreSQL for Azure/Supabase
raw_db_url = get_secret("DATABASE_URL").strip('"').strip("'")
if raw_db_url.startswith("DATABASE_URL="):
    raw_db_url = raw_db_url.split("DATABASE_URL=", 1)[1].strip().strip('"').strip("'")

if not raw_db_url:
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'leads.db'}"
elif raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# JobTech API (Arbetsförmedlingen Open Data)
JOBTECH_API_URL = get_secret("JOBTECH_API_URL", "https://jobsearch.api.jobtechdev.se")
JOBTECH_API_KEY = get_secret("JOBTECH_API_KEY", "")  # Optional for basic public access

# Brainville API
BRAINVILLE_API_URL = get_secret("BRAINVILLE_API_URL", "https://api.brainville.com/api")
BRAINVILLE_API_KEY = get_secret("BRAINVILLE_API_KEY", "")

# Regional focus (Östergötland + Nyköping & Södertälje i E4-korridoren)
TARGET_REGION_CODE = "05"  # Östergötlands län
TARGET_EXTRA_MUNICIPALITY_CODES = ["0480", "0181"]  # Nyköping (0480), Södertälje (0181)

TARGET_MUNICIPALITIES = {
    "0580": "Linköping",
    "0581": "Norrköping",
    "0583": "Motala",
    "0562": "Finspång",
    "0586": "Mjölby",
    "0584": "Vadstena",
    "0582": "Söderköping",
    "0563": "Valdemarsvik",
    "0509": "Ödeshög",
    "0512": "Ydre",
    "0513": "Kinda",
    "0560": "Boxholm",
    "0561": "Åtvidaberg",
    "0480": "Nyköping",
    "0181": "Södertälje",
}

# Webhooks (Slack / Microsoft Teams)
SLACK_WEBHOOK_URL = get_secret("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL = get_secret("TEAMS_WEBHOOK_URL", "")

# JobTech Taxonomy occupation-field for IT / Data
IT_OCCUPATION_FIELD = "apaJ_2ja_LuF"
