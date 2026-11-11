import sys
import importlib

# Defensive reload in case database.models was cached in long-running processes (e.g. Streamlit Cloud)
if "database.models" in sys.modules and not hasattr(sys.modules["database.models"], "Consultant"):
    importlib.reload(sys.modules["database.models"])

from database.models import (
    Base,
    Skill,
    Lead,
    lead_skills,
    MarketFeature,
    MarketForecast,
    MacroIndicator,
    Consultant,
)
from database.connection import init_db, SessionLocal, get_db

__all__ = [
    "Base",
    "Skill",
    "Lead",
    "lead_skills",
    "MarketFeature",
    "MarketForecast",
    "MacroIndicator",
    "Consultant",
    "init_db",
    "SessionLocal",
    "get_db",
]
