import re
from typing import Dict, List, Tuple

# Comprehensive taxonomy for Swedish IT & Tech consulting market
TAXONOMY: Dict[str, Dict[str, any]] = {
    # Backend
    ".NET / C#": {
        "aliases": [r"\.net", r"\bc#\b", r"c-sharp", r"dotnet", r"asp\.net", r"\.net core"],
        "category": "Backend",
    },
    "Java": {
        "aliases": [r"\bjava\b", r"\bspring boot\b", r"\bspring\b", r"\bquarkus\b"],
        "category": "Backend",
    },
    "Python": {
        "aliases": [r"\bpython\b", r"\bdjango\b", r"\bfastapi\b", r"\bflask\b"],
        "category": "Backend",
    },
    "Node.js": {
        "aliases": [r"\bnode(?:\.js)?\b", r"\bexpress(?:\.js)?\b", r"\bnestjs\b"],
        "category": "Backend",
    },
    "C++ / Embedded": {
        "aliases": [r"\bc\+\+\b", r"\bembedded\b", r"\binbyggda system\b", r"\brtos\b", r"\bautosar\b"],
        "category": "Embedded & Systems",
    },
    "C": {
        "aliases": [r"\bansi c\b", r"\bc-programmering\b"],
        "category": "Embedded & Systems",
    },
    "Go / Golang": {
        "aliases": [r"\bgolang\b", r"\bgo-utvecklare\b"],
        "category": "Backend",
    },

    # Frontend
    "React": {
        "aliases": [r"\breact(?:\.js)?\b", r"\breact native\b", r"\bnext(?:\.js)?\b"],
        "category": "Frontend",
    },
    "Angular": {
        "aliases": [r"\bangular(?:\.js)?\b"],
        "category": "Frontend",
    },
    "Vue.js": {
        "aliases": [r"\bvue(?:\.js)?\b", r"\bnuxt(?:\.js)?\b"],
        "category": "Frontend",
    },
    "TypeScript": {
        "aliases": [r"\btypescript\b", r"\bts\b"],
        "category": "Frontend",
    },
    "JavaScript": {
        "aliases": [r"\bjavascript\b", r"\bjs\b"],
        "category": "Frontend",
    },

    # Cloud & DevOps
    "Azure": {
        "aliases": [r"\bazure\b", r"\bmicrosoft azure\b"],
        "category": "Cloud & DevOps",
    },
    "AWS": {
        "aliases": [r"\baws\b", r"\bamazon web services\b"],
        "category": "Cloud & DevOps",
    },
    "Google Cloud (GCP)": {
        "aliases": [r"\bgcp\b", r"\bgoogle cloud\b"],
        "category": "Cloud & DevOps",
    },
    "Kubernetes": {
        "aliases": [r"\bkubernetes\b", r"\bk8s\b"],
        "category": "Cloud & DevOps",
    },
    "Docker": {
        "aliases": [r"\bdocker\b", r"\bcontainers\b"],
        "category": "Cloud & DevOps",
    },
    "Terraform": {
        "aliases": [r"\bterraform\b", r"\biac\b", r"infrastructure as code"],
        "category": "Cloud & DevOps",
    },
    "CI/CD & DevOps": {
        "aliases": [r"\bci/cd\b", r"\bdevops\b", r"\bgithub actions\b", r"\bgitlab\b", r"\bjenkins\b"],
        "category": "Cloud & DevOps",
    },

    # Data & AI
    "SQL / Relational DB": {
        "aliases": [r"\bsql\b", r"\bpostgresql\b", r"\bpostgres\b", r"\bmysql\b", r"\bsql server\b"],
        "category": "Data & AI",
    },
    "Power BI": {
        "aliases": [r"\bpower bi\b", r"\bpowerbi\b", r"\bdax\b"],
        "category": "Data & AI",
    },
    "Databricks & Spark": {
        "aliases": [r"\bdatabricks\b", r"\bapache spark\b", r"\bspark\b", r"\bpyspark\b"],
        "category": "Data & AI",
    },
    "Snowflake": {
        "aliases": [r"\bsnowflake\b"],
        "category": "Data & AI",
    },
    "Machine Learning & AI": {
        "aliases": [r"\bmachine learning\b", r"\bmaskininlärning\b", r"\bllm\b", r"\bgenerative ai\b", r"\bartificiell intelligens\b", r"\bdata science\b"],
        "category": "Data & AI",
    },

    # Security
    "Cybersecurity & Security": {
        "aliases": [r"\bcybersecurity\b", r"\bit-säkerhet\b", r"\binformationssäkerhet\b", r"\bsäkerhetsskydd\b", r"\bnis2\b", r"\biso 27001\b", r"\bsoc\b"],
        "category": "Security",
    },

    # Architecture & Roles
    "Solution & Cloud Architecture": {
        "aliases": [r"\barki?tekt\b", r"\bsolution architect\b", r"\bmolnarkitekt\b", r"\bsystemarkitekt\b", r"\benterprisearkitekt\b"],
        "category": "Architecture",
    },
    "Agile / Scrum / Lead": {
        "aliases": [r"\bscrum master\b", r"\bproduktägare\b", r"\bproduct owner\b", r"\bagile coach\b", r"\bsafe\b", r"\bprojektledare\b"],
        "category": "Management & Agile",
    },
    "QA & Test Automation": {
        "aliases": [r"\btestautomatisering\b", r"\bqa\b", r"\btestledare\b", r"\btestare\b", r"\bcypress\b", r"\bplaywright\b", r"\bselenium\b"],
        "category": "Testing & QA",
    },
}

# Precompile patterns for high-speed scanning
COMPILED_TAXONOMY = []
for standard_name, info in TAXONOMY.items():
    combined_pattern = re.compile(r"|".join(info["aliases"]), re.IGNORECASE)
    COMPILED_TAXONOMY.append((standard_name, info["category"], combined_pattern))


def extract_skills_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Scans text (e.g. job headline + description) and returns a list of unique 
    normalized (skill_name, category) tuples.
    """
    if not text:
        return []

    found = []
    seen = set()
    for name, category, pattern in COMPILED_TAXONOMY:
        if pattern.search(text):
            if name not in seen:
                seen.add(name)
                found.append((name, category))
    return found

