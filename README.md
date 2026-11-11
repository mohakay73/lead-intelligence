#  Consid Lead Intelligence & Bench Optimization Platform

An enterprise market intelligence, macroeconomic forecasting, and consultant bench optimization system built for **Consid** leadership covering **Östergötland (Linköping, Norrköping, Finspång, Motala), Södertälje, and Nyköping**.

The platform automates the entire consulting sales and delivery lifecycle: ingesting open market tenders, broker assignments, and macroeconomic signals, running predictive 6-month demand forecasting, and executing automated 1-to-1 matching with available consultants from **Cinode ERP**.

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
                        │  • Riksbanken Policy Rate (Styrränta API)       │
                        │  • Konjunkturinstitutet (KI IT Barometer)       │
                        │  • SCB / Arbetsförmedlingen Layoff Statistics   │
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

##  Core Modules & Dashboard Views

### 1. Market Overview & Active Demand
* **Executive KPI Cards**: Real-time tracking of active opportunities, direct consultant tenders, unique client organizations, and recruiter agency share.
* **Competency Ranking**: Regional demand across core technical stacks (.NET, Azure, C++, Python, Databricks, Cybersecurity, React, etc.).
* **Geographic Distribution & Technical Verticals**: Interactive visual distribution across Linköping, Norrköping, Södertälje, and Nyköping.
* **Top Hiring Organizations**: Identifies direct enterprise clients (Saab, Scania, Region Östergötland, Sectra, Toyota Material Handling, IFS, etc.).

### 2. Lead Management & Sales Pipeline
* **Multi-Criteria Search**: Filter by municipality, location, technical competencies, and assignment classification.
* **Pipeline Management (Kanban Workflow)**: Track opportunities through configurable deal stages: `New` → `Qualified` → `Pitch Sent` → `Interview Booked` → `Won` → `Archived`.
* **Consultant & Account Manager Allocation**: Directly assign account executives and consultant candidates to individual pipeline leads.
* **Rapid Data Export**: Single-click export of filtered leads to CSV for external CRM follow-up and management reporting.

### 3. Consultant Bench Matching & Pitching (Cinode ERP)
* **Cinode Live Sync**: Automatically fetches available consultants directly from Consid's Cinode database with real-time status (`Available Now`, `Available within 30d`, etc.).
* **Proficiency Level Weighting (1–5 Stars)**: Incorporates Cinode competency levels into the matching algorithm ($15\%–99\%$). Senior specialists (Levels 4–5) in required technologies receive an experience-based scoring multiplier.
* **CV-Enriched Sales Pitching**: Generates personalized B2B outreach proposals incorporating the consultant's actual project accomplishments, certifications, and security clearance status (RK3/SUA).
* **Flexible Input Modes**: Select directly from synchronized Cinode profiles or paste raw CV text for instant NLP-based skill extraction.

### 4. Predictive Market Forecast & Trends (Unified Suite)
* **Tab 1: 6-Month Predictive AI Forecast**:
  * Damped Holt-Winters time-series model with calibrated confidence intervals (P10–P90) trained on 58 months of empirical regional data (2022–2026).
  * **Interactive Macro What-If Scenario Simulator**: Simulates how shifts in Riksbanken's policy rate and IT industry sentiment impact demand across Linköping, Norrköping, Södertälje, and Nyköping.
  * **Competency Momentum & Upskilling Matrix**: Identifies accelerating high-margin technologies (Terraform, Kubernetes, Databricks) to guide talent development and training budgets.
* **Tab 2: Historical Analytics & Seasonal Dynamics (2022–2026)**:
  * Longitudinal volume trends spanning nearly 5 years (3,800+ historical IT postings).
  * **Seasonal Index (Jan–Dec)**: Reveals annual regional hiring peaks (March and October) to optimize sales outreach timing.
  * **Skill Growth Barometer (%)**: Quantifies fastest-growing frameworks, languages, and platforms.
* **Tab 3: Strategic Decision Support**:
  * Actionable executive recommendations for workforce planning, strategic certifications, and security clearance vetting in the Linköping defense corridor and Södertälje automotive cluster.

### 5. Executive Intelligence Report & Weekly Briefing
* **Automated Weekly Briefing**: Structured executive intelligence report summarizing regional market shifts, emerging demand clusters, and pipeline health.
* **Multi-Format Export**: Single-click export to Markdown (`.md`) or standalone styled HTML email (`.html`).
* **Webhook Integrations**: Automated dispatch support for Microsoft Teams and Slack channels.

---

##  Data Sources & API Integrations

| Data Source | Protocol | Description |
| :--- | :--- | :--- |
| **Cinode ERP** | REST / OAuth2 | Consultant profiles, CV accomplishments, proficiency ratings (1–5), and real-time bench availability. *(Dual-mode: live API + realistic Consid sandbox)* |
| **Brainville API** | REST / Token | Sweden's leading marketplace for consulting brokers, freelance opportunities, and enterprise tenders. |
| **Arbetsförmedlingen JobTech** | Public REST | Active regional IT postings and direct corporate hiring initiatives. |
| **JobTech Historical Archive** | Bulk REST | Historical IT dataset (2022–2026) powering time-series and seasonal analytics (58 months). |
| **Riksbanken** | Open REST | Sweden's central bank policy rate (reporänta) for macroeconomic demand forecasting. |
| **National Institute of Economic Research (KI)** | Open Data | Business tendency survey (Konjunkturbarometer) for IT and consulting services. |
| **Statistics Sweden (SCB) / Arbetsförmedlingen** | Open REST | Regional layoff notices (varselstatistik) for Östergötland and Södermanland. |

---

##  Quickstart & Setup Guide

### 1. Environment Preparation

```bash
# Clone the repository
git clone https://github.com/mohakay73/lead-intelligence.git
cd lead-intelligence

# Create a virtual environment
python -m venv .venv

# Activate the environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate the environment (macOS / Linux)
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)

Create or update `.env` in the root directory (see `.env.example` for reference):

```ini
# Database (PostgreSQL on Supabase, or leave empty for local SQLite leads.db)
DATABASE_URL=postgresql://postgres.xxx:xxx@aws-0-eu-west-2.pooler.supabase.com:5432/postgres

# Cinode ERP & Skills API (OAuth2 Client Credentials)
# Leave empty to run in automatic sandbox mode with realistic Consid profiles
CINODE_ACCESS_ID=
CINODE_ACCESS_SECRET=
CINODE_COMPANY_ID=
CINODE_BASE_URL=https://api.cinode.app
CINODE_TOKEN_URL=https://api.cinode.app/token

# Market Data Sources
JOBTECH_API_KEY=
BRAINVILLE_API_KEY=

# Executive Notifications (Optional)
TEAMS_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
```

### 3. Launch the Application

```bash
streamlit run app.py
```

*Upon initial startup, the platform automatically applies database migrations, synchronizes Cinode consultant profiles, and computes baseline macroeconomic indicators and predictive models.*

---

##  Automated Workflows (GitHub Actions)

* **Market Ingestion (`.github/workflows/ingest_cron.yml`):** Runs every weekday at 07:00 CET to ingest and normalize active market leads from JobTech and Brainville.
* **Executive Weekly Briefing (`.github/workflows/weekly_digest.yml`):** Compiles and dispatches the weekly intelligence brief every Monday at 07:30 CET via Microsoft Teams and Slack webhooks.
* **MLOps Forecast & Macro Retraining (`.github/workflows/forecast_retrain.yml`):** Re-extracts macroeconomic features and retrains time-series prediction models on the 1st and 15th of every month at 02:42 CET.

---
##  Security & Data Integrity

* **Security Clearance Alignment (RK3/SUA)**: Built-in classification and priority weighting for defense and public sector requirements (Linköping / Saab defense ecosystem).
* **Zero Hardcoded Secrets**: All authentication tokens, database credentials, and API secrets are strictly managed via environment variables (`.env`) and GitHub Repository Secrets.
* **Graceful Sandbox Degradation**: The platform falls back seamlessly to realistic offline Consid simulations if external APIs are unreachable or pending enterprise access provisioning.

---

##  License

Developed for strategic decision support, market forecasting, and bench optimization at Consid.
All rights reserved.
