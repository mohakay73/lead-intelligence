# 🎯 Consid Lead Intelligence & Bench Optimization Platform

An enterprise market intelligence, macroeconomic forecasting, and consultant bench optimization system built for **Consid** leadership covering **Östergötland (Linköping, Norrköping, Finspång, Motala), Södertälje & Nyköping**.

The platform automates the entire consulting sales and delivery pipeline: from ingesting open market tenders, broker assignments, and macroeconomic signals, to predictive 6-month demand forecasting and automated 1-to-1 matching with available consultants from **Cinode ERP**.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│        Brainville API v2        │     │  JobTech / Arbetsförmedlingen   │     │    Cinode ERP & Skills Platform │
│ (Broker & Direct Tenders)       │     │ (Live & 2022–2026 Hist. Archive)│     │ (Bench Status, CV:s & Levels 1-5│
└────────────────┬────────────────┘     └────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │                                       │
                 └───────────────────────────────┬───────────────────────────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │      Ingestion, Pipeline & Sync Engine          │
                        │    (Scheduled Cron, Dual-Mode API Clients)      │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │        Macroeconomic Signals Engine             │
                        │  • Riksbanken Styrränta (Policy Rate API)       │
                        │  • Konjunkturinstitutet (KI IT-Barometer)       │
                        │  • SCB / Arbetsförmedlingen Varselstatistik     │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │       Database Layer (Supabase PostgreSQL)      │
                        │  • leads & skills (with M2M taxonomy)           │
                        │  • consultants (Cinode sync, levels 1-5, CV)    │
                        │  • market_features & market_forecasts           │
                        │  • macro_indicators (60-month history)          │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │           Analytics & Predictive AI             │
                        │  • Holt-Winters Damped Demand Forecaster        │
                        │  • Macro What-If Scenario Simulator             │
                        │  • Level-Weighted Bench Matcher & CV Pitcher    │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │          Consid Leadership Dashboard            │
                        │ (Streamlit, Modern Corporate Theme, High-Speed) │
                        └─────────────────────────────────────────────────┘
```

---

## 📊 Core Modules & Views

### 1. Marknadsöversikt & Aktuella Behov
* **Executive KPI Cards**: Real-time tracking of active opportunities, direct consultant tenders, unique client organizations, and recruiter agency share.
* **Kompetensranking**: Regional demand for technical stacks (.NET, Azure, C++, Python, Databricks, Cybersecurity, React, etc.).
* **Geografisk fördelning & Tekniska vertikaler**: Interactive distribution charts across Linköping, Norrköping, Södertälje, and Nyköping.
* **Topparbetsgivare**: Direct client needs (Saab, Scania, Region Östergötland, Sectra, Toyota Material Handling, IFS, etc.).

### 2. Uppdrag & Säljpipeline
* **Multi-kriterie-sök**: Filtrera på kommun, ort, tekniska krav och uppdragstyp.
* **Pipelinehantering (Kanban-status)**: Flytta uppdrag mellan `Nytt` → `Kvalificerad` → `Pitch skickad` → `Intervju bokad` → `Vunnen affär` → `Arkiverad`.
* **Kandidattilldelning**: Koppla direkt konsultchef och kandidat till varje affärsmöjlighet.
* **Snabbexport**: Exportera filtrerade leads till CSV för uppföljning i externa CRM-system.

### 3. Konsultmatchning & Bänkoptimering (Cinode ERP)
* **Cinode Live Sync**: Läser in konsulter direkt från Consids Cinode-databas med realtidsstatus (`Ledig nu`, `Ledig inom 30d`, etc.).
* **Kompetensnivåer (1–5 stjärnor)**: Cinodes kompetensgradering vägs in i matchningsgraden ($15\%–99\%$). Konsulter med nivå 4–5 i efterfrågade tekniker får en senioritetsmultiplikator.
* **CV-berikad säljpitch**: Genererar skräddarsydda B2B-säljpitchar med konsultens faktiska projektleveranser, certifieringar och säkerhetsprövning (RK3/SUA).
* **Flexibel inmatning**: Välj direkt från synkade Cinode-profiler eller klistra in ett externt CV för automatisk kompetensextraktion.

### 4. Marknadsprognos & Trender (Unified Suite)
* **Tab 1: 6-Månaders AI-Prognos**:
  * Dämpad Holt-Winters tidsserieextrapolering med kalibrerade konfidensintervall (P10–P90) tränad på 58 månaders data (2022–2026).
  * **Interaktiv What-If Scenariosimulator**: Modellera hur Riksbankens räntebana och IT-konjunkturen påverkar efterfrågan i Linköping, Norrköping, Södertälje och Nyköping.
  * **Kompetensradar & Upskilling-matris**: Identifierar växande spetsteknologier (Terraform, Kubernetes, Databricks) för att guida utbildnings- och certifieringsbudgetar.
* **Tab 2: Historik & Säsongsmönster (2022–2026)**:
  * Långsiktig efterfrågedynamik över nästan 5 år (3 800+ historiska IT-krav).
  * **Säsongsmönster (Jan–Dec)**: Synliggör årliga anställningstoppar (mars och oktober) för optimal säljtajming.
  * **Kompetenstillväxt-Barometer (%)**: Kvantifierar snabbast växande ramverk och verktyg.
* **Tab 3: Strategiskt Beslutsunderlag**:
  * Handlingsinriktade råd för resursplanering, certifieringssatsningar och säkerhetsprövningar i försvarskorridoren Linköping och fordonsklustret i Södertälje.

### 5. Ledningsrapport & Veckobrev
* **Automatiserat Veckobrev**: Formaterad executive sammanfattning av veckans marknadsläge.
* **Exportmöjligheter**: Ett klick till Markdown (`.md`) eller fristående stylad HTML-email (`.html`).
* **Webhooks**: Stöd för automatisk schemalagd utskickning till Microsoft Teams och Slack.

---

## 🛠️ Datakällor & API-integrationer

| Datakälla | Typ | Beskrivning |
| :--- | :--- | :--- |
| **Cinode ERP** | REST / OAuth2 | Konsultprofiler, CV:n, kompetensnivåer (1–5) och bänkstatus. *(Dual-mode med live API + Consid sandbox)* |
| **Brainville API** | REST / Token | Sveriges ledande öppna marknadsplats för konsultmäklare och frilansuppdrag. |
| **Arbetsförmedlingen JobTech** | Public REST | Öppna regionala IT-annonser och direkta slutkundsrekryteringar. |
| **JobTech Historical Archive** | Bulk REST | Historiskt IT-arkiv 2022–2026 för säsongs- och trendanalys (58 månader). |
| **Riksbanken** | Open REST | Sveriges styrränta (reporänta) för makroekonomisk efterfrågemodellering. |
| **Konjunkturinstitutet (KI)** | Open Data | Konjunkturbarometer för IT- och datakonsulttjänster. |
| **SCB / Arbetsförmedlingen** | Open REST | Regional varselstatistik för Östergötland och Södermanland. |

---

## 🚀 Snabbstart & Installation

### 1. Förbered miljö

```bash
# Klona repot
git clone https://github.com/mohakay73/lead-intelligence.git
cd lead-intelligence

# Skapa virtuell miljö
python -m venv .venv

# Aktivera miljö (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Aktivera miljö (macOS / Linux)
source .venv/bin/activate

# Installera beroenden
pip install -r requirements.txt
```

### 2. Konfigurera inställningar (`.env`)

Skapa eller uppdatera `.env` i rotkatalogen (se även `.env.example`):

```ini
# Databas (PostgreSQL på Supabase, eller lämna tomt för lokal SQLite leads.db)
DATABASE_URL=postgresql://postgres.xxx:xxx@aws-0-eu-west-2.pooler.supabase.com:5432/postgres

# Cinode ERP & Skills API (OAuth2 Client Credentials)
# Lämna tomt för att köra automatisk sandbox med realistiska Consid-profiler
CINODE_ACCESS_ID=
CINODE_ACCESS_SECRET=
CINODE_COMPANY_ID=
CINODE_BASE_URL=https://api.cinode.app
CINODE_TOKEN_URL=https://api.cinode.app/token

# Marknadskällor
JOBTECH_API_KEY=
BRAINVILLE_API_KEY=

# Notifikationer (Valfritt)
TEAMS_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
```

### 3. Starta applikationen

```bash
streamlit run app.py
```

*Applikationen kör automatiskt schemamigrering, synkroniserar Cinode-profiler och laddar in makro- och prognosmodeller vid första uppstart.*

---

## ⚙️ Automatiserade Bakgrundsflöden (GitHub Actions)

* **Marknadsinsamling (`.github/workflows/ingest_cron.yml`):** Hämtar dagligen kl. 07:00 CET nya marknadsuppdrag från JobTech och Brainville.
* **Veckobrev till Ledning (`.github/workflows/weekly_digest.yml`):** Sammanställer och skickar veckans marknadsrapport varje måndag kl. 07:30 CET till Teams/Slack.
* **MLOps Prognos & Makro-omträning (`.github/workflows/forecast_retrain.yml`):** Uppdaterar makroindikatorer och tränar om maskininlärningsmodellerna den 1:a och 15:e varje månad kl. 02:42 CET.

---

## 🔒 Säkerhet & Dataintegritet

* **Säkerhetsprövning (RK3/SUA)**: Inbyggd flaggning och prioritering för försvars- och säkerhetsklassade uppdrag (Linköping / Saab-klustret).
* **Inga hårdkodade hemligheter**: Alla tokens, lösenord och API-nycklar hanteras strikt via miljövariabler (`.env`) och GitHub Repository Secrets.
* **Sandbox Graceful Degradation**: Systemet degraderar sömlöst till realistisk Consid-simulering om externa API-nycklar saknas eller tjänster har driftstörning.

---

## 📄 Licens

Utvecklad för strategiskt beslutsstöd och konsultmatchning för ledningen inom Consid.
Alla rättigheter förbehållna.
