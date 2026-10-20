import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Database URL: default to SQLite for instant local runs, or PostgreSQL for Azure/Supabase
raw_db_url = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
if raw_db_url.startswith("DATABASE_URL="):
    raw_db_url = raw_db_url.split("DATABASE_URL=", 1)[1].strip().strip('"').strip("'")

if not raw_db_url:
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'leads.db'}"
elif raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# JobTech API (Arbetsförmedlingen Open Data)
JOBTECH_API_URL = os.getenv("JOBTECH_API_URL", "https://jobsearch.api.jobtechdev.se")
JOBTECH_API_KEY = os.getenv("JOBTECH_API_KEY", "")  # Optional for basic public access

# Brainville API
BRAINVILLE_API_URL = os.getenv("BRAINVILLE_API_URL", "https://api.brainville.com/api")
BRAINVILLE_API_KEY = os.getenv("BRAINVILLE_API_KEY", "")

# Regional focus (Östergötland)
TARGET_REGION_CODE = "05"  # Östergötlands län
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
}

# JobTech Taxonomy occupation-field for IT / Data
IT_OCCUPATION_FIELD = "apaJ_2ja_LuF"
