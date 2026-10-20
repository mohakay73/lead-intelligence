"""
Executive Consulting Pitch Generator.
Generates tailored Swedish sales pitches for IT consultant assignments and recruitments.
Supports both instant algorithmic generation and optional LLM refinement.
"""
from typing import Dict, Any, Optional
import os


def generate_sales_pitch(
    lead: Dict[str, Any],
    consultant_profile: Optional[str] = None,
    consultant_name: Optional[str] = None,
    available_from: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generates an executive consulting pitch tailored to the specific lead requirements.
    
    Returns:
        dict with 'subject', 'body', and 'summary'
    """
    title = lead.get("title", "IT-uppdrag")
    company = lead.get("company_name", "Kunden")
    location = lead.get("location", "Östergötland")
    skills = lead.get("skills", [])
    is_consultant = lead.get("is_consultant", True)
    
    # Defaults
    c_name = consultant_name.strip() if consultant_name else "Vår seniorkonsult"
    c_avail = available_from.strip() if available_from else "inom 2–4 veckor"
    
    skills_formatted = ", ".join(skills[:4]) if skills else "relevant teknisk kompetens"
    
    # 1. Subject line options
    if is_consultant:
        subject = f"Konsultresurs för {title} – Tillgänglig profil ({location})"
    else:
        subject = f"Kandidatprofil & konsultlösning för {title} hos {company}"

    # 2. Body composition tailored to Swedish B2B consulting standards
    profile_desc = (
        consultant_profile.strip()
        if consultant_profile
        else f"en erfaren specialist med gedigen bakgrund inom {skills_formatted}"
    )

    body = f"""Hej {company}-teamet,

Jag såg ert aktuella behov gällande rollen som {title} i {location} och vill proaktivt presentera en stark matchning från vårt konsultteam.

Vi har {c_name}, {profile_desc}, som blir tillgänglig för nya uppdrag {c_avail}.

Nyckelkompetenser som matchar era krav:
{_format_skill_bullets(skills)}

Kort om profilen:
• Gedigen praktisk erfarenhet inom {skills_formatted}.
• Erfarenhet av komplexa leveranser, agila team och självständigt drivande i liknande projekt.
• Snabb startsträcka och god förståelse för verksamhetskritiska miljöer.

Skulle det finnas intresse av att ta del av ett anonymiserat CV eller ta en kort 10-minuters avstämning via Teams senare i veckan för att se om profilen är relevant för er?

Bästa hälsningar,
[Ditt Namn]
[Din Titel / Account Manager]
[Företagsnamn]
[Telefonnummer | E-post]"""

    return {
        "subject": subject,
        "body": body,
        "summary": f"Pitch för {title} ({company}) med fokus på {skills_formatted}",
    }


def _format_skill_bullets(skills: list) -> str:
    if not skills:
        return "• Stark systemutvecklingskompetens och modern IT-arkitektur\n• God vana av agila team och DevOps-processer"
    
    bullets = []
    for s in skills[:5]:
        bullets.append(f"• Dokumenterad erfarenhet inom {s}")
    return "\n".join(bullets)
