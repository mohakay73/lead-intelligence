# 🎯 Lead Intelligence & Decision Support Platform (Östergötland)

An automated market intelligence and executive decision support system built for consulting leadership in **Östergötland (Norrköping & Linköping)**.

Ingests and unifies live IT consultant assignments and open market opportunities from:
1. **Arbetsförmedlingen JobTech API** (Public IT & tech job listings in Region Östergötland)
2. **Brainville API v2** (Consultant requests, broker assignments, direct corporate tenders)

---

## 🏛️ System Architecture

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│     Brainville API v2           │      │   JobTech / Arbetsförmedlingen  │
│  (Consultant & Broker Requests) │      │  (Public & Private IT Openings) │
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
                  │  (SQLite for Local / PostgreSQL)    │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │     Analytics & Trend Engine        │
                  │ (Skill Demand, Top Clients, Cities) │
                  └──────────────────┬──────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │    Leadership Streamlit Dashboard   │
                  │ (Executive KPIs, Lead Explorer, UI) │
                  └─────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Set Up Environment

Open a terminal in the project directory:

```bash
cd C:\Users\mohak\.gemini\antigravity\scratch\lead-intelligence
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Settings (Optional)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
- By default, it uses a local SQLite database (`leads.db`), so **zero database setup is needed to start**.
- If you have an Azure PostgreSQL or Supabase instance, simply set `DATABASE_URL=postgresql://...`.
- If you have a Brainville API key, set `BRAINVILLE_API_KEY`. If empty, realistic sample consultant assignments for Östergötland are used for demonstration.

### 3. Run Ingestion (Fetch Live Data)

Run the ingestion script to pull live postings from Arbetsförmedlingen JobTech API and Brainville:

```bash
python -m ingestion.pipeline
```

### 4. Launch the Leadership Dashboard

Start the interactive Streamlit web application:

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

---

## 📊 Features

- **Executive KPI Cards**: Instant visibility into total market opportunities, consultant assignments, and active hiring employers in Östergötland.
- **Skill Demand Matrix**: Real-time ranking of tech skills (e.g., `.NET / C#`, `Azure`, `React`, `C++ / Embedded`, `Cybersecurity / NIS2`, `Databricks`, `Power BI`).
- **Geographic Breakdown**: Compare demand between **Linköping** (tech cluster / Mjärdevi / defense) and **Norrköping** (industry, commerce, public sector).
- **Lead Explorer**: Searchable and filterable database of active leads with direct links to apply or pitch consultants.
- **On-Demand Live Sync**: Click "Kör Live-synkning" directly from the dashboard sidebar to refresh data.
- **Automated Cron Pipeline**: Ready-to-use GitHub Actions workflow (`.github/workflows/ingest_cron.yml`) to run daily refreshes.

