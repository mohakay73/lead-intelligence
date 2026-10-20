# 🎯 Lead Intelligence & Decision Support Platform

An automated market intelligence, historical forecasting, and executive decision support system built for consulting leadership covering **Östergötland (Linköping, Norrköping, Finspång, Mjölby, Motala), Södertälje & Nyköping**.

Ingests, aggregates, and analyzes live IT consultant assignments, open market tenders, and historical trends (2024–2026) from:
1. **Arbetsförmedlingen JobTech API** (Public & enterprise IT listings in the region)
2. **JobTech Historical Archive API** (2,000+ historical IT job postings from 2024–2026 for longitudinal market intelligence)
3. **Brainville API v2** (Consultant requests, broker assignments, direct corporate tenders)

---

## 🏛️ System Architecture

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│     Brainville API v2           │      │   JobTech / Arbetsförmedlingen  │
│  (Consultant & Broker Requests) │      │  (Live & Historical IT Archive) │
└────────────────┬────────────────┘      └────────────────┬────────────────┘
                 │                                        │
                 └───────────────────┬────────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │    Ingestion & Pipeline Engine      │
                  │   (Scheduled Python / GitHub Cron)  │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │   Taxonomy & Skill Normalization    │
                  │  (Maps variants: .NET, Azure, etc.) │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │          Database Layer             │
                  │ (PostgreSQL Supabase / IPv4 Pooler) │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │     Analytics & Trend Engines       │
                  │  (Live KPIs, Growth Barometer, AI)  │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │    Leadership Streamlit Dashboard   │
                  │ (5 Executive Tabs, Pitch Gen, HTML) │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │  Automated Executive Weekly Digest  │
                  │   (Markdown / HTML Email / Slack)   │
                  └─────────────────────────────────────┘
```

---

## 📊 Core Modules & Dashboard Tabs

1. **Marknadsöversikt & Aktuella Behov:**
   - Real-time executive KPIs (Total active leads, direct broker/consultant assignments, unique employers).
   - Regional skill demand ranking (.NET, Azure, C++, Python, Cybersecurity, React, etc.).
   - Interactive geographic distribution and technical verticals donut charts.
   - Most active hiring organizations (Saab, Scania, Region Östergötland, Sectra, Toyota Material Handling, etc.).

2. **Uppdrag & Lead Pipeline:**
   - Multi-criteria lead search and filter by municipality, technical skill, and assignment type.
   - One-click export to CSV for sales and recruitment follow-up.
   - **AI Consulting Pitch Generator:** Generates tailored, ready-to-send Swedish sales pitch emails with customizable consultant seniority and availability.

3. **Historiska Trender & Framtidsutsikter (2024–2026):**
   - Monthly volume trendline tracking demand dynamics over 2.5 years.
   - Multi-skill evolution over time showing shifting technology stacks.
   - **Kompetenstillväxt-Barometer (%):** Quantifies fastest-growing skills (e.g. Cybersecurity, Microservices, Cloud).
   - **Säsongsmönster (Jan–Dec):** Reveals annual regional hiring peaks (March and October) to optimize sales timing.

4. **Strategiskt Beslutsunderlag:**
   - Actionable executive recommendations for resource planning, certifications, and security clearance vetting in the Linköping defense corridor and Södertälje automotive sector.

5. **Ledningsrapport & Veckobrev:**
   - Formatted executive intelligence brief.
   - One-click export to Markdown (`.md`) or standalone styled HTML email (`.html`).
   - Webhook integration for automated Slack / Microsoft Teams delivery.

---

## 🚀 Quickstart Guide

### 1. Set Up Environment

Open a terminal in the project directory:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Settings

Create or update `.env`:

```ini
DATABASE_URL=postgresql://postgres.xxx:xxx@aws-0-eu-west-2.pooler.supabase.com:5432/postgres
JOBTECH_API_KEY=
BRAINVILLE_API_KEY=
SLACK_WEBHOOK_URL=
```

### 3. Run Ingestion (Live & Historical)

- Ingest live active listings:
  ```bash
  python -m ingestion.pipeline
  ```
- Ingest historical archive data (2024–2026):
  ```bash
  python -m ingestion.historical_ingestion
  ```

### 4. Launch the Dashboard

```bash
streamlit run app.py
```

---

## ⚙️ Automated GitHub Actions

- **Daily Live Sync (`.github/workflows/ingest_cron.yml`):** Runs every weekday at 07:00 CET to fetch new market leads.
- **Weekly Executive Digest (`.github/workflows/weekly_digest.yml`):** Compiles and dispatches the weekly intelligence brief every Monday at 07:30 CET.
