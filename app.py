import os
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

from database.connection import init_db, SessionLocal
from database.models import Skill, Lead
import importlib
import analytics.trend_engine
import analytics.historical_analytics
import analytics.feature_pipeline
import analytics.forecast_engine
importlib.reload(analytics.trend_engine)
importlib.reload(analytics.historical_analytics)
importlib.reload(analytics.feature_pipeline)
importlib.reload(analytics.forecast_engine)
from analytics.trend_engine import (
    get_overview_kpis,
    get_skill_demand,
    get_location_distribution,
    get_category_distribution,
    get_top_employers,
    get_filtered_leads,
    get_pipeline_kpis,
    update_lead_status,
    get_all_assignees,
)
from analytics.pitch_generator import generate_sales_pitch
from analytics.weekly_digest import (
    build_weekly_intelligence_data,
    format_markdown_digest,
    format_html_digest,
    send_slack_notification,
    send_teams_notification,
)
from analytics.historical_analytics import (
    get_monthly_volume_trend,
    get_top_skills_time_series,
    get_skill_growth_barometer,
    get_seasonal_pattern,
)
from analytics.forecast_engine import (
    get_forecast_display_data,
    run_forecast_and_save,
)
from analytics.bench_matcher import (
    PRESET_BENCH_PROFILES,
    match_consultant_to_leads,
)
from ingestion.normalizer import extract_skills_from_text
from ingestion.pipeline import run_pipeline

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="Consid | Lead Intelligence Platform",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- CONSID BRAND ASSETS & DESIGN TOKENS -----------------
CONSID_LOGO_SVG = """<svg width="118" height="28" viewBox="0 0 128 32" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
<g clip-path="url(#consid_clip0)">
<path d="M26.2686 15.9204C26.2686 21.811 21.4925 26.5871 15.602 26.5871C9.71142 26.5871 4.9353 21.811 4.9353 15.9204C4.9353 10.0299 9.71142 5.25374 15.602 5.25374C21.4925 5.25374 26.2686 10.0299 26.2686 15.9204Z" fill="#9B2740"></path>
<path d="M15.9841 32C24.2627 32 31.0448 25.7274 31.9045 17.7035C32.7323 17.5761 33.3692 16.8756 33.3692 16.0159C33.3692 15.1562 32.7323 14.4239 31.9045 14.3284C31.0448 6.27264 24.2627 0 15.9841 0C7.16418 0 0 7.16418 0 16.0159C0 24.8358 7.16418 32 15.9841 32ZM15.9841 0.636816C23.9124 0.636816 30.408 6.62289 31.2677 14.3284C30.5035 14.4876 29.9303 15.1881 29.9303 16.0159C29.9303 16.8438 30.5035 17.5124 31.2677 17.7035C30.4398 25.409 23.9124 31.395 15.9841 31.395C7.51443 31.3632 0.636816 24.4856 0.636816 16.0159C0.636816 7.51443 7.51443 0.636816 15.9841 0.636816Z" fill="currentColor"></path>
<path d="M27.1284 21.5881H15.8249C14.7105 21.5881 13.8508 21.1741 13.2458 20.3463C12.6408 19.5184 12.3543 18.3721 12.3543 16.6209C12.3543 14.8696 12.6408 13.7234 13.2458 12.8955C13.8508 12.0677 14.7105 11.6537 15.8249 11.6537H27.1284C27.2239 11.6537 27.3513 11.6537 27.4468 11.6537C25.5364 7.32338 21.1423 4.26666 16.0797 4.26666C13.7871 4.26666 12.6408 6.08159 12.4816 7.54627C12.2269 9.93433 11.3672 11.3035 9.8707 11.6537C9.45677 11.7492 8.24682 11.9403 6.27269 11.9403C4.23488 11.9403 3.66174 15.3154 3.66174 16.5891C3.66174 17.8945 4.23488 21.2378 6.27269 21.2378C8.24682 21.2378 9.45677 21.397 9.8707 21.5244C11.3672 21.8746 12.2588 23.2119 12.4816 25.6318C12.609 27.192 13.7871 28.9751 16.0797 28.9751C21.1742 28.9751 25.5364 25.9502 27.4468 21.5881C27.3513 21.5881 27.2558 21.5881 27.1284 21.5881Z" fill="currentColor"></path>
<path d="M27.1284 20.9831H15.8249C14.7105 20.9831 13.8508 20.5692 13.2458 19.7413C12.6408 18.9134 12.3543 17.7672 12.3543 16.0159C12.3543 14.2647 12.6408 13.1184 13.2458 12.2906C13.8508 11.4627 14.7105 11.0488 15.8249 11.0488H27.1284C27.2239 11.0488 27.3513 11.0488 27.4468 11.0488C25.5364 6.71841 21.1423 3.6617 16.0797 3.6617C13.7871 3.6617 12.6408 5.47662 12.4816 6.9413C12.2269 9.32936 11.3672 10.6985 9.8707 11.0488C9.45677 11.1761 8.24682 11.3353 6.27269 11.3353C4.23488 11.3353 3.66174 14.7105 3.66174 15.9841C3.66174 17.2896 4.23488 20.6328 6.27269 20.6328C8.24682 20.6328 9.45677 20.792 9.8707 20.9194C11.3672 21.2697 12.2588 22.607 12.4816 25.0269C12.609 26.5552 13.7871 28.3383 16.0797 28.3383C21.1742 28.3383 25.5364 25.3134 27.4468 20.9513C27.3513 20.9831 27.2558 20.9831 27.1284 20.9831Z" fill="#B5223F"></path>
<path d="M71.7691 9.93433C70.3999 8.53334 68.4895 7.83284 66.0059 7.83284C63.4268 7.83284 61.389 8.56518 59.9243 10.0617C58.4596 11.5582 57.7273 13.5642 57.7273 16.1433C57.7273 18.595 58.3959 20.5373 59.7651 21.9702C61.1343 23.403 63.0447 24.1353 65.5283 24.1353C68.1392 24.1353 70.177 23.3711 71.6099 21.8109C73.0746 20.2508 73.7751 18.2129 73.7751 15.6338C73.8069 13.2458 73.1064 11.3353 71.7691 9.93433ZM70.0178 21.5244C69.1263 22.7025 67.7571 23.2756 65.9104 23.2756C64.0318 23.2756 62.5989 22.6388 61.6119 21.3333C60.6248 20.0597 60.1472 18.2129 60.1472 15.793C60.1472 13.4368 60.593 11.6537 61.4527 10.4756C62.3124 9.29752 63.6815 8.72438 65.592 8.72438C67.5661 8.72438 68.9989 9.3612 69.9542 10.603C70.9094 11.8766 71.3552 13.6597 71.3552 16.0159C71.3552 18.5313 70.9094 20.3463 70.0178 21.5244Z" fill="currentColor"></path>
<path d="M125.166 9.90248C123.861 8.72438 121.918 8.1194 119.339 8.1194C118.607 8.1194 117.906 8.15124 117.206 8.18308C116.505 8.21492 115.805 8.24676 115.073 8.24676C114.181 8.24676 113.258 8.24676 112.302 8.21492L112.334 8.69253L113.703 9.13831C113.863 9.20199 113.958 9.32935 113.958 9.52039C113.958 9.77512 113.958 10.0298 113.99 10.3483C113.99 10.6667 113.99 10.9851 113.99 11.3672V20.3781C113.99 20.8239 113.99 21.2378 113.99 21.5881C113.99 21.9383 113.99 22.2886 113.958 22.5751C113.958 22.7343 113.863 22.8617 113.672 22.9254L112.302 23.3393L112.334 23.8169C113.258 23.7851 114.181 23.7851 115.073 23.7851C115.741 23.7851 116.378 23.7851 116.919 23.8169C117.493 23.8488 118.129 23.8488 118.83 23.8488C121.441 23.8488 123.479 23.0846 124.911 21.5881C126.344 20.0597 127.077 17.9582 127.077 15.2199C127.108 12.8318 126.472 11.0806 125.166 9.90248ZM123.16 21.1741C122.141 22.3204 120.645 22.8935 118.702 22.8935C118.289 22.8935 117.875 22.8935 117.429 22.8617C117.015 22.8298 116.569 22.798 116.155 22.7343V9.17015C116.665 9.13831 117.11 9.10646 117.524 9.10646C117.938 9.10646 118.289 9.07462 118.639 9.07462C120.74 9.07462 122.269 9.61592 123.256 10.7303C124.211 11.8448 124.72 13.5642 124.72 15.8567C124.689 18.2448 124.179 20.0279 123.16 21.1741Z" fill="currentColor"></path>
<path d="M80.3343 23.7851L80.3025 23.2756L78.997 22.8935C78.8059 22.8617 78.7423 22.7343 78.7104 22.5114C78.7104 21.9383 78.6786 21.206 78.6786 20.3463V11.3672L88.6447 23.8169L89.5681 23.7214V11.3353C89.5681 10.603 89.5681 9.99802 89.6 9.48856C89.6 9.29752 89.6955 9.17015 89.8547 9.10647L91.2557 8.6607L91.2239 8.18309C90.3005 8.21493 89.5363 8.21493 88.9632 8.21493C88.39 8.21493 87.6258 8.21493 86.6706 8.18309L86.7025 8.69254L88.0079 9.07463C88.199 9.13831 88.2945 9.23384 88.2945 9.42488C88.2945 9.93433 88.3263 10.5712 88.3263 11.2716V19.805L78.9651 8.21493C78.6149 8.24677 78.2965 8.24677 77.9462 8.24677C77.405 8.24677 76.6408 8.24677 75.6855 8.21493L75.7174 8.69254L77.0865 9.13831C77.2457 9.202 77.3413 9.32936 77.3413 9.5204C77.3413 9.99802 77.3731 10.6348 77.3731 11.3672V20.3781C77.3731 21.2378 77.3731 22.002 77.3413 22.5751C77.3413 22.7343 77.2457 22.8617 77.0547 22.9254L75.6855 23.3393L75.7174 23.8169C76.6726 23.7851 77.4368 23.7851 78.0099 23.7851C78.6467 23.7532 79.3791 23.7532 80.3343 23.7851Z" fill="currentColor"></path>
<path d="M108.45 10.2846C108.45 9.96617 108.45 9.67961 108.482 9.42488C108.482 9.23384 108.577 9.13831 108.768 9.07463L110.137 8.6607L110.105 8.18309C109.15 8.21493 108.227 8.21493 107.367 8.21493C106.476 8.21493 105.584 8.21493 104.629 8.18309L104.661 8.6607L106.03 9.10647C106.189 9.17015 106.284 9.29752 106.284 9.48856C106.284 9.74329 106.285 9.99802 106.316 10.3164C106.316 10.6348 106.316 10.9532 106.316 11.3353V20.3463C106.316 20.792 106.316 21.206 106.316 21.5562C106.316 21.9065 106.316 22.2567 106.284 22.5433C106.284 22.7343 106.157 22.8299 105.998 22.8935L104.629 23.3075L104.661 23.7851C105.616 23.7532 106.507 23.7532 107.399 23.7532C108.29 23.7532 109.182 23.7532 110.137 23.7851L110.105 23.3075L108.864 22.9254C108.609 22.8617 108.482 22.7343 108.482 22.5433C108.482 22.2567 108.482 21.9065 108.45 21.5562C108.45 21.206 108.45 20.792 108.45 20.3463V11.3035C108.418 10.9532 108.45 10.603 108.45 10.2846Z" fill="currentColor"></path>
<path d="M99.7253 22.3841C99.1203 22.8617 98.2606 23.1164 97.1462 23.1164C96.3183 23.1164 95.5223 22.9572 94.7263 22.6388L93.9621 19.4866L93.4527 19.5503L92.9114 23.3075L92.9751 23.403C94.4079 23.8169 95.7134 24.008 96.8915 24.008C98.7064 24.008 100.139 23.6259 101.19 22.8299C102.209 22.0657 102.75 20.9194 102.75 19.4547C102.75 18.8498 102.623 18.2766 102.4 17.8308C102.177 17.3532 101.859 16.9711 101.477 16.6209C101.094 16.3025 100.649 15.9841 100.171 15.7612C99.6935 15.5065 99.184 15.2836 98.6746 15.0607C98.197 14.8378 97.7512 14.6468 97.3373 14.4239C96.8915 14.201 96.5094 13.9781 96.1591 13.6915C95.8089 13.405 95.5542 13.0866 95.3313 12.7363C95.1402 12.3861 95.0129 11.9403 95.0129 11.4627C95.0129 10.6348 95.2994 9.96617 95.8726 9.48856C96.4457 9.01095 97.2417 8.78806 98.197 8.78806C98.8338 8.78806 99.5661 8.91542 100.33 9.17015L101.063 11.9403L101.508 11.8766L102.177 8.40597L102.113 8.34229C100.84 8.05572 99.598 7.92836 98.4517 7.92836C96.796 7.92836 95.4586 8.31045 94.4716 9.04279C93.4845 9.77513 92.9751 10.8259 92.9751 12.1632C92.9751 12.8318 93.1024 13.405 93.3253 13.9144C93.5482 14.4239 93.8666 14.8378 94.2805 15.1881C94.6626 15.5383 95.1084 15.8249 95.6178 16.0796C96.0955 16.3343 96.6049 16.5891 97.1144 16.8119C97.5601 17.0348 98.0059 17.2259 98.4517 17.4488C98.8656 17.6716 99.2477 17.8945 99.5979 18.1493C99.9482 18.404 100.203 18.7224 100.394 19.0726C100.585 19.4229 100.681 19.8368 100.681 20.3144C100.649 21.206 100.33 21.9065 99.7253 22.3841Z" fill="currentColor"></path>
<path d="M55.8487 22.607L55.7214 22.0975C54.4159 22.5433 53.1741 22.7662 51.996 22.7662C49.8945 22.7662 48.2706 22.1294 47.0925 20.8239C45.9144 19.5503 45.3094 17.8308 45.3094 15.6657C45.3094 13.6597 45.8189 12.004 46.8696 10.7304C47.8885 9.45672 49.3214 8.8199 51.1363 8.8199C51.8686 8.8199 52.7283 8.94727 53.6199 9.17015L54.4159 12.0995L54.8617 12.0358L55.5622 8.46965L55.4985 8.37413C54.193 8.08756 52.9194 7.92836 51.6457 7.92836C49.0348 7.92836 46.9333 8.6607 45.3094 10.1572C43.6855 11.6219 42.8895 13.6279 42.8895 16.1751C42.8895 18.5632 43.6219 20.4736 45.0865 21.9383C46.5512 23.403 48.4617 24.1353 50.8497 24.1353C52.7602 24.1353 54.3841 23.6259 55.8487 22.607Z" fill="currentColor"></path>
</g>
<defs><clipPath id="consid_clip0"><rect width="127.108" height="32" fill="white"></rect></clipPath></defs>
</svg>"""

# Consid Corporate Design Tokens
CONSID_PRIMARY = "#B5223F"       # Consid Raspberry Red
CONSID_BURGUNDY = "#701131"      # Consid Dark Burgundy / Wine
CONSID_CORAL = "#F49E88"         # Consid Soft Orange / Light Coral
CONSID_TERRACOTTA = "#D86261"    # Consid Warm Terracotta
CONSID_CHARCOAL = "#1C1C1C"      # Consid Charcoal Black
CONSID_GREIGE = "#A99B94"        # Consid Greige
CONSID_MUTED = "#6C757D"         # Muted gray

# Plotly Categorical Palettes matching Consid brand system
CONSID_PALETTE = [
    "#B5223F",  # Consid Raspberry
    "#701131",  # Deep Burgundy
    "#D86261",  # Terracotta
    "#F49E88",  # Coral / Soft Orange
    "#1C1C1C",  # Charcoal
    "#A99B94",  # Greige
    "#0D9488",  # Teal Accent
    "#2563EB",  # Tech Blue
]

CONSID_GEO_PALETTE = [
    "#B5223F",  # Linköping
    "#701131",  # Norrköping
    "#D86261",  # Södertälje
    "#F49E88",  # Nyköping
    "#492A34",  # Motala
    "#A99B94",  # Finspång
    "#0D9488",  # Mjölby
    "#64748B",  # Övriga
]

# ----------------- CONSID THEME CSS -----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Minimalist Header Container */
    .header-container {
        border-bottom: 1px solid rgba(181, 34, 63, 0.18);
        padding-bottom: 16px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        flex-wrap: wrap;
        gap: 12px;
    }
    .consid-brand-badge {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #B5223F;
        margin-bottom: 3px;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: inherit;
        letter-spacing: -0.025em;
        margin: 0;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 0.88rem;
        opacity: 0.75;
        color: inherit;
        margin-top: 4px;
        font-weight: 400;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #B5223F;
        background: rgba(181, 34, 63, 0.08);
        border: 1px solid rgba(181, 34, 63, 0.22);
        padding: 5px 12px;
        border-radius: 9999px;
    }
    .status-indicator {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #B5223F;
        box-shadow: 0 0 8px rgba(181, 34, 63, 0.6);
    }

    /* Metric Boxes - Consid Rounded-XL */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .metric-box {
        background: rgba(181, 34, 63, 0.02);
        border: 1px solid rgba(181, 34, 63, 0.12);
        border-radius: 12px;
        padding: 16px 18px;
        transition: all 0.2s ease;
    }
    .metric-box:hover {
        border-color: rgba(181, 34, 63, 0.35);
        box-shadow: 0 4px 18px rgba(181, 34, 63, 0.08);
    }
    .metric-caption {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #B5223F;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    .metric-number {
        font-size: 1.85rem;
        font-weight: 700;
        color: inherit;
        line-height: 1.1;
        letter-spacing: -0.025em;
    }
    .metric-detail {
        font-size: 0.78rem;
        opacity: 0.62;
        color: inherit;
        margin-top: 5px;
    }

    /* Lead Item Card - Consid Rounded-XL */
    .lead-row {
        background: rgba(128, 128, 128, 0.03);
        border: 1px solid rgba(128, 128, 128, 0.14);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .lead-row:hover {
        border-color: rgba(181, 34, 63, 0.4);
        box-shadow: 0 4px 20px rgba(181, 34, 63, 0.06);
    }
    .lead-title-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: inherit;
        margin: 0 0 6px 0;
    }
    .lead-attributes {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        font-size: 0.82rem;
        opacity: 0.78;
        color: inherit;
        margin-bottom: 10px;
    }
    .lead-attr-strong {
        font-weight: 600;
        opacity: 1;
        color: inherit;
    }

    /* Badges & Pills - Consid Signature Pill Design */
    .tag-source {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .source-consultant {
        background: rgba(181, 34, 63, 0.1);
        color: #B5223F;
        border: 1px solid rgba(181, 34, 63, 0.28);
    }
    .source-recruitment {
        background: rgba(128, 128, 128, 0.1);
        color: inherit;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .skill-tag {
        display: inline-block;
        background: rgba(181, 34, 63, 0.04);
        color: inherit;
        border: 1px solid rgba(181, 34, 63, 0.14);
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 3px 9px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .link-action {
        display: inline-block;
        font-size: 0.82rem;
        font-weight: 600;
        color: #B5223F;
        text-decoration: none;
        transition: color 0.15s ease;
    }
    .link-action:hover {
        color: #701131;
        text-decoration: underline;
    }

    /* Pipeline Status Pills & CRM styles */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .status-nytt {
        background: rgba(148, 163, 184, 0.15);
        color: #475569;
        border: 1px solid rgba(148, 163, 184, 0.35);
    }
    .status-granskas {
        background: rgba(245, 158, 11, 0.14);
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .status-pitch {
        background: rgba(181, 34, 63, 0.12);
        color: #B5223F;
        border: 1px solid rgba(181, 34, 63, 0.35);
    }
    .status-intervju {
        background: rgba(99, 102, 241, 0.14);
        color: #6366f1;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }
    .status-vunnet {
        background: rgba(16, 185, 129, 0.15);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .status-avböjt {
        background: rgba(100, 116, 139, 0.1);
        color: #94a3b8;
        border: 1px solid rgba(100, 116, 139, 0.2);
    }
    .pipeline-assignee {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(181, 34, 63, 0.06);
        color: #B5223F;
        padding: 2px 8px;
        border-radius: 9999px;
        border: 1px solid rgba(181, 34, 63, 0.18);
    }
    .pipeline-notes-box {
        background: rgba(128, 128, 128, 0.04);
        border-left: 3px solid #B5223F;
        border-radius: 0 6px 6px 0;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 0.8rem;
        line-height: 1.45;
    }
    .funnel-metric-card {
        background: rgba(181, 34, 63, 0.02);
        border: 1px solid rgba(181, 34, 63, 0.12);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
        transition: all 0.2s ease;
    }
    .funnel-metric-card:hover {
        border-color: rgba(181, 34, 63, 0.35);
        box-shadow: 0 2px 10px rgba(181, 34, 63, 0.06);
    }

    /* Bench Matcher Tags */
    .skill-matched {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 9px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .skill-missing {
        display: inline-block;
        background: rgba(128, 128, 128, 0.08);
        color: inherit;
        opacity: 0.7;
        border: 1px dashed rgba(128, 128, 128, 0.25);
        border-radius: 9999px;
        font-size: 0.75rem;
        padding: 3px 9px;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .skill-bonus {
        display: inline-block;
        background: rgba(244, 158, 136, 0.18);
        color: #D86261;
        border: 1px solid rgba(216, 98, 97, 0.3);
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 9px;
        margin-right: 5px;
        margin-bottom: 5px;
    }

    /* Strategic Notes */
    .strategy-card {
        background: rgba(181, 34, 63, 0.02);
        border: 1px solid rgba(181, 34, 63, 0.14);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }
    .strategy-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .strategy-name {
        font-size: 1rem;
        font-weight: 600;
        color: inherit;
    }
    .priority-pill {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .p-high { background: rgba(181, 34, 63, 0.15); color: #B5223F; }
    .p-growth { background: rgba(16, 185, 129, 0.15); color: #059669; }
    .p-strategic { background: rgba(112, 17, 49, 0.15); color: #701131; }
    .p-stable { background: rgba(169, 155, 148, 0.2); color: #495057; }

    .action-note {
        background: rgba(181, 34, 63, 0.06);
        border-left: 3px solid #B5223F;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 0.84rem;
        color: inherit;
    }

    /* Consid Buttons - Pill Shaped */
    .stButton > button {
        border-radius: 9999px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
    }
    .stButton > button:hover {
        border-color: #B5223F !important;
        color: #B5223F !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #B5223F !important;
        color: #ffffff !important;
        border-color: #B5223F !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #701131 !important;
        border-color: #701131 !important;
        color: #ffffff !important;
    }
    .stDownloadButton > button {
        border-radius: 9999px !important;
        font-weight: 600 !important;
    }

    /* Clean Sidebar Radio Navigation - Consid Highlight */
    div[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 4px;
        display: flex;
        flex-direction: column;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.12);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 0;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(181, 34, 63, 0.05);
        border-color: rgba(181, 34, 63, 0.25);
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: rgba(181, 34, 63, 0.1) !important;
        border-color: #B5223F !important;
        color: #B5223F !important;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- PLOTLY STYLING HELPERS -----------------
def style_chart(fig, height=380, show_legend=True):
    fig.update_layout(
        height=height,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=10, b=25),
        showlegend=show_legend,
    )
    if show_legend:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                title=None,
                font=dict(size=11),
            ),
            margin=dict(l=10, r=20, t=32, b=25),
        )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.12)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.12)", zeroline=False)
    return fig

def style_pie(fig, height=360):
    fig.update_layout(
        height=height,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=15, b=20),
        showlegend=False,
    )
    return fig

def get_status_badge_html(status_val: str) -> str:
    st_val = (status_val or "Nytt").strip()
    if st_val == "Granskas":
        return '<span class="status-pill status-granskas">🔍 Granskas</span>'
    elif st_val == "Pitch skickad":
        return '<span class="status-pill status-pitch">✉️ Pitch skickad</span>'
    elif st_val == "Intervju":
        return '<span class="status-pill status-intervju">🤝 Intervju</span>'
    elif st_val in ("Vunnet", "Tillsatt"):
        return '<span class="status-pill status-vunnet">🏆 Vunnet</span>'
    elif st_val in ("Avböjt", "Ej aktuell", "Arkiverad"):
        return '<span class="status-pill status-avböjt">✖ Avböjt</span>'
    else:
        return '<span class="status-pill status-nytt">📥 Nytt</span>'

# ----------------- DATABASE INITIALIZATION -----------------
init_db()
db = SessionLocal()

# ----------------- NAVIGATION & WORKSPACES -----------------
FUNCTION_VIEWS = [
    "Marknadsöversikt & Efterfrågan",
    "Uppdrag & Lead Pipeline",
    "Konsultmatchning & Bänkoptimering",
    "Marknadsprognos & Trender",
    "Ledningsrapport & Veckobrev",
]

if "selected_workspace_view" not in st.session_state or st.session_state.selected_workspace_view not in FUNCTION_VIEWS:
    st.session_state.selected_workspace_view = FUNCTION_VIEWS[0]

# ----------------- SIDEBAR -----------------
st.sidebar.markdown(
    f"""
    <div style="padding-bottom: 14px; margin-bottom: 16px; border-bottom: 1px solid rgba(181, 34, 63, 0.2);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            {CONSID_LOGO_SVG}
            <span style="font-size: 0.62rem; font-weight: 700; background: rgba(181, 34, 63, 0.12); color: #B5223F; border: 1px solid rgba(181, 34, 63, 0.25); border-radius: 9999px; padding: 2px 7px; text-transform: uppercase; letter-spacing: 0.06em;">Intelligence</span>
        </div>
        <div style="font-size: 0.76rem; opacity: 0.72; color: inherit; line-height: 1.35; margin-top: 5px;">Östergötland, Södertälje & Nyköping</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("**Arbetsvy**")
current_view = st.sidebar.radio(
    "Arbetsvy",
    FUNCTION_VIEWS,
    key="selected_workspace_view",
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Filter**")

selected_location = st.sidebar.selectbox(
    "Kommun / Ort",
    ["Alla", "Linköping", "Norrköping", "Södertälje", "Nyköping", "Motala", "Finspång", "Mjölby"],
)

selected_source = st.sidebar.selectbox(
    "Uppdragstyp",
    ["Alla", "brainville", "jobtech"],
    format_func=lambda x: "Alla källor" if x == "Alla" else ("Konsultuppdrag (Brainville)" if x == "brainville" else "Rekryteringsannonser (JobTech)"),
)

consultant_only = st.sidebar.checkbox("Endast externa konsultuppdrag", value=False)
if consultant_only:
    selected_source = "brainville"

st.sidebar.markdown("---")
st.sidebar.markdown("**Datainsamling**")

if st.sidebar.button("Synkronisera data nu", use_container_width=True):
    with st.spinner("Ansluter till källor och uppdaterar databas..."):
        try:
            stats = run_pipeline()
            st.sidebar.success(
                f"Klar. Nya poster: {stats['new_leads_saved']}, Uppdaterade: {stats['existing_leads_updated']}"
            )
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Synkroniseringsfel: {e}")

st.sidebar.markdown(
    """
    <div style="background: rgba(181, 34, 63, 0.04); border: 1px solid rgba(181, 34, 63, 0.16); border-radius: 8px; padding: 12px; margin-top: 14px; font-size: 0.75rem; opacity: 0.85; color: inherit; line-height: 1.5;">
        <div style="font-weight: 700; color: #B5223F; margin-bottom: 4px;">Automatiserad drift (GitHub Actions)</div>
        • Daglig synkning: Vardagar kl. 06:20 CET<br>
        • Veckorapport (Teams): Måndagar kl. 06:45 CET<br>
        • ML-modellträning: 1:a & 15:e i månaden
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- GLOBAL HEADER -----------------
st.markdown(
    f"""
    <div class="header-container">
        <div>
            <div class="consid-brand-badge">CONSID LEAD INTELLIGENCE</div>
            <div class="header-title">Marknadsintelligens & Beslutsstöd</div>
            <div class="header-subtitle">Regional efterfrågeanalys och konsultmatchning • Östergötland & E4 Syd</div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="status-badge">
                <span class="status-indicator"></span>
                <span>Consid Intelligence Node • Aktiv</span>
            </div>
        </div>
    </div>
    <div style="margin-top: -6px; margin-bottom: 22px; padding-bottom: 10px; border-bottom: 1px solid rgba(181, 34, 63, 0.15); display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div>
            <span style="font-size: 0.72rem; text-transform: uppercase; font-weight: 600; opacity: 0.6; letter-spacing: 0.06em;">Aktiv arbetsvy:</span>
            <span style="font-size: 1.18rem; font-weight: 700; color: inherit; letter-spacing: -0.01em; margin-left: 6px;">{current_view}</span>
        </div>
        <span style="font-size: 0.74rem; opacity: 0.65;">Uppdateras i realtid via Supabase & Schemalagd sync</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------- VIEW 1: MARKNADSÖVERSIKT & EFTERFRÅGAN -----------------
if current_view == "Marknadsöversikt & Efterfrågan":
    kpis = get_overview_kpis(db)

    # Macro KPI Grid
    st.markdown(
        f"""
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-caption">Totala aktiva behov</div>
                <div class="metric-number">{kpis['total_leads']}</div>
                <div class="metric-detail">Östergötland, Södertälje & Nyköping</div>
            </div>
            <div class="metric-box">
                <div class="metric-caption">Konsultförfrågningar</div>
                <div class="metric-number">{kpis['consultant_leads']}</div>
                <div class="metric-detail">Brainville och mäklaruppdrag</div>
            </div>
            <div class="metric-box">
                <div class="metric-caption">Rekryteringsannonser</div>
                <div class="metric-number">{kpis['jobtech_leads']}</div>
                <div class="metric-detail">Arbetsförmedlingen JobTech</div>
            </div>
            <div class="metric-box">
                <div class="metric-caption">Aktiva organisationer</div>
                <div class="metric-number">{kpis['unique_employers']}</div>
                <div class="metric-detail">Unika uppdragsgivare & företag</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Row 1: Competencies (left) & Top Employers (right) - Balanced Bar Charts
    col_skills, col_emp = st.columns(2)
    with col_skills:
        loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
        st.markdown(f"###### Mest efterfrågade kompetenser ({loc_label})")
        skill_df = get_skill_demand(db, location=selected_location, source=selected_source, top_n=12)
        if not skill_df.empty:
            fig_skills = px.bar(
                skill_df,
                x="count",
                y="skill",
                orientation="h",
                color="category",
                labels={"count": "Behov", "skill": "Kompetens", "category": "Kategori"},
                color_discrete_sequence=CONSID_PALETTE,
            )
            fig_skills.update_layout(yaxis={"categoryorder": "total ascending"})
            style_chart(fig_skills, height=390, show_legend=True)
            st.plotly_chart(fig_skills, use_container_width=True)
        else:
            st.info("Ingen kompetensdata tillgänglig för det valda filtret.")

    with col_emp:
        loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
        st.markdown(f"###### Mest aktiva uppdragsgivare ({loc_label})")
        top_emp_df = get_top_employers(db, location=selected_location, source=selected_source, limit=12)
        if not top_emp_df.empty:
            fig_emp = px.bar(
                top_emp_df,
                x="count",
                y="company",
                orientation="h",
                color="location",
                labels={"company": "Organisation", "count": "Behov", "location": "Ort"},
                color_discrete_sequence=CONSID_GEO_PALETTE,
            )
            fig_emp.update_layout(yaxis={"categoryorder": "total ascending"})
            style_chart(fig_emp, height=390, show_legend=True)
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.info("Inga arbetsgivare matchar det valda filtret.")

    st.markdown("---")

    # Row 2: Geography (left) & Technical Verticals (right) - Balanced Donut Charts
    col_geo, col_cat = st.columns(2)
    with col_geo:
        st.markdown("###### Geografisk fördelning av uppdrag")
        loc_df = get_location_distribution(db, source=selected_source)
        if not loc_df.empty:
            fig_loc = px.pie(
                loc_df,
                values="count",
                names="location",
                hole=0.55,
                color_discrete_sequence=CONSID_GEO_PALETTE,
            )
            fig_loc.update_traces(textposition="inside", textinfo="percent+label")
            style_pie(fig_loc, height=350)
            st.plotly_chart(fig_loc, use_container_width=True)
        else:
            st.info("Ingen ortsdata tillgänglig.")

    with col_cat:
        st.markdown("###### Fördelning per tekniskt område")
        cat_df = get_category_distribution(db, location=selected_location, source=selected_source)
        if not cat_df.empty:
            fig_cat = px.pie(
                cat_df,
                values="count",
                names="category",
                hole=0.55,
                color_discrete_sequence=CONSID_PALETTE,
            )
            fig_cat.update_traces(textposition="inside", textinfo="percent+label")
            style_pie(fig_cat, height=350)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Ingen kategoridata tillgänglig.")

# ----------------- VIEW 2: UPPDRAG & LEAD PIPELINE -----------------
elif current_view == "Uppdrag & Lead Pipeline":
    st.markdown("##### Säljpipeline & Uppdragsflöde (Lead Pipeline CRM)")
    st.caption("Aktiv uppföljning och statusstyrning för regionala affärsmöjligheter från identifiering till tillsatt uppdrag.")

    pipe_kpis = get_pipeline_kpis(db, location=selected_location)

    # 1. Pipeline Funnel Summary Bar
    col_pk1, col_pk2, col_pk3, col_pk4, col_pk5, col_pk6 = st.columns(6)
    with col_pk1:
        st.markdown(
            f"""
            <div class="funnel-metric-card">
                <div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;">1. Nya Leads</div>
                <div style="font-size:1.45rem;font-weight:800;color:inherit;line-height:1.2;">{pipe_kpis['nytt']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Ohanterade</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pk2:
        st.markdown(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(245,158,11,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#d97706;text-transform:uppercase;">2. Granskas</div>
                <div style="font-size:1.45rem;font-weight:800;color:#d97706;line-height:1.2;">{pipe_kpis['granskas']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Matchning pågår</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pk3:
        st.markdown(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(181,34,63,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#B5223F;text-transform:uppercase;">3. Pitch skickad</div>
                <div style="font-size:1.45rem;font-weight:800;color:#B5223F;line-height:1.2;">{pipe_kpis['pitch']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Konsult presenterad</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pk4:
        st.markdown(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(99,102,241,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#6366f1;text-transform:uppercase;">4. Intervju</div>
                <div style="font-size:1.45rem;font-weight:800;color:#6366f1;line-height:1.2;">{pipe_kpis['intervju']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Kundmöte bokat</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pk5:
        st.markdown(
            f"""
            <div class="funnel-metric-card" style="border-color: rgba(16,185,129,0.3);">
                <div style="font-size:0.68rem;font-weight:700;color:#059669;text-transform:uppercase;">5. Vunnet</div>
                <div style="font-size:1.45rem;font-weight:800;color:#059669;line-height:1.2;">{pipe_kpis['vunnet']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Tillsatt uppdrag</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_pk6:
        st.markdown(
            f"""
            <div class="funnel-metric-card">
                <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;">Avböjt</div>
                <div style="font-size:1.45rem;font-weight:800;color:#94a3b8;line-height:1.2;">{pipe_kpis['avböjt']}</div>
                <div style="font-size:0.68rem;opacity:0.6;">Arkiverade</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 2. Filter & Controls
    col_search, col_status_filter, col_skill_filter, col_limit = st.columns([2.5, 1.8, 1.8, 1])
    with col_search:
        search_query = st.text_input("Sök i pipeline & uppdrag", "", placeholder="Sök roll, teknik, bolag, konsult...")
    with col_status_filter:
        pipeline_status_filter = st.selectbox(
            "Pipeline-status",
            ["Alla", "Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt"],
            index=0,
        )
    with col_skill_filter:
        skills_in_db = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        selected_skill = st.selectbox("Filtrera på kompetens", ["Alla"] + skills_in_db)
    with col_limit:
        max_leads = st.selectbox("Max antal", [25, 50, 100], index=1)

    leads_list = get_filtered_leads(
        db,
        search_term=search_query,
        location=selected_location,
        source=selected_source,
        selected_skill=selected_skill,
        status=pipeline_status_filter if pipeline_status_filter != "Alla" else None,
        limit=max_leads,
    )

    if leads_list:
        leads_df = pd.DataFrame(leads_list)
        csv_data = leads_df.drop(columns=["description"]).to_csv(index=False).encode("utf-8")

        col_count, col_download = st.columns([4, 1])
        with col_count:
            st.caption(f"Visar {len(leads_list)} matchande affärsmöjligheter i pipelinen.")
        with col_download:
            st.download_button(
                label="Exportera pipeline (.csv)",
                data=csv_data,
                file_name=f"consid_lead_pipeline_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Inga uppdrag matchar ditt valda filter just nu.")

    STATUS_ORDER = ["Nytt", "Granskas", "Pitch skickad", "Intervju", "Vunnet", "Avböjt"]

    for lead in leads_list:
        source_class = "source-consultant" if lead["is_consultant"] else "source-recruitment"
        source_text = "Konsultuppdrag" if lead["is_consultant"] else "Rekryteringsannons"
        status_html = get_status_badge_html(lead["status"])

        skill_tags = "".join([f'<span class="skill-tag">{s}</span>' for s in lead["skills"]])

        link_html = (
            f'<a href="{lead["url"]}" target="_blank" class="link-action">Visa källannons →</a>'
            if lead["url"]
            else '<span style="opacity:0.6; font-size:0.8rem;">Länk saknas</span>'
        )

        crm_meta_items = []
        if lead["assigned_to"]:
            crm_meta_items.append(f'<span>Ansvarig: <span class="pipeline-assignee">👤 {lead["assigned_to"]}</span></span>')
        if lead["candidate_name"]:
            crm_meta_items.append(f'<span>Föreslagen konsult: <strong style="color:#B5223F;">⭐ {lead["candidate_name"]}</strong></span>')
        crm_meta_html = " • ".join(crm_meta_items) if crm_meta_items else ""

        notes_html = f'<div class="pipeline-notes-box"><strong>Intern säljnotering:</strong> {lead["notes"]}</div>' if lead["notes"] else ""

        st.markdown(
            f"""
            <div class="lead-row">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            {status_html}
                            <span class="tag-source {source_class}">{source_text}</span>
                        </div>
                        <div class="lead-title-text">{lead['title']}</div>
                    </div>
                    <div>{link_html}</div>
                </div>
                <div class="lead-attributes">
                    <span>Beställare: <span class="lead-attr-strong">{lead['company_name']}</span></span>
                    <span>Ort: <span class="lead-attr-strong">{lead['location']}</span></span>
                    <span>Publicerad: {lead['published_at']}</span>
                    <span>Deadline: {lead['deadline']}</span>
                </div>
                {f'<div style="margin-bottom: 8px; font-size: 0.82rem;">{crm_meta_html}</div>' if crm_meta_html else ''}
                <div style="margin-bottom: 10px;">{skill_tags}</div>
                <div style="opacity: 0.8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 10px;">
                    {lead['description'][:240] + '...' if lead['description'] else 'Detaljerad information finns i källsystemet.'}
                </div>
                {notes_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action Hub: Pipeline Management & Sales Pitch
        col_act1, col_act2 = st.columns([1, 1])

        with col_act1:
            with st.expander(f"🎯 Uppdatera Pipeline & Status ({lead['company_name']})"):
                cur_idx = STATUS_ORDER.index(lead["status"]) if lead["status"] in STATUS_ORDER else 0
                new_status = st.selectbox(
                    "Ny pipeline-status",
                    STATUS_ORDER,
                    index=cur_idx,
                    key=f"pipe_status_{lead['id']}",
                )

                col_cm1, col_cm2 = st.columns(2)
                with col_cm1:
                    new_assignee = st.text_input(
                        "Ansvarig konsultchef/säljare",
                        value=lead["assigned_to"],
                        key=f"pipe_ass_{lead['id']}",
                        placeholder="T.ex. Erik S / Konsultchef Öst",
                    )
                with col_cm2:
                    new_candidate = st.text_input(
                        "Matchad konsult / kandidat",
                        value=lead["candidate_name"],
                        key=f"pipe_cand_{lead['id']}",
                        placeholder="T.ex. Anna A (Senior Fullstack)",
                    )

                new_notes = st.text_area(
                    "Säljanteckningar & kunddialog",
                    value=lead["notes"],
                    key=f"pipe_notes_{lead['id']}",
                    height=85,
                    placeholder="T.ex. Kontaktat kund via LinkedIn. Söker 1 senior konsult, intervjuer nästa tisdag...",
                )

                if st.button("Spara pipeline-ändringar", key=f"btn_save_pipe_{lead['id']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["id"],
                        status=new_status,
                        assigned_to=new_assignee,
                        candidate_name=new_candidate,
                        notes=new_notes,
                    )
                    st.toast("Pipeline sparad!")
                    st.rerun()

        with col_act2:
            with st.expander(f"✉️ Skapa & Kopiera Säljpitch ({lead['company_name']})"):
                c_role_def = f"Senior specialist inom {', '.join(lead['skills'][:3]) if lead['skills'] else 'systemutveckling'}"
                c_role = st.text_input(
                    "Konsultens profil",
                    value=lead["candidate_name"] if lead["candidate_name"] else c_role_def,
                    key=f"role_{lead['id']}",
                )
                c_avail = st.text_input(
                    "Tillgänglig från",
                    value="inom 2–4 veckor",
                    key=f"avail_{lead['id']}",
                )

                pitch = generate_sales_pitch(lead, consultant_profile=c_role, available_from=c_avail)
                st.text_input("Ämnesrad", value=pitch["subject"], key=f"subj_{lead['id']}")
                st.text_area("Säljmejl", value=pitch["body"], height=130, key=f"body_{lead['id']}")

                if st.button("Markera som 'Pitch skickad' direkt", key=f"btn_fast_pitch_{lead['id']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["id"],
                        status="Pitch skickad",
                        candidate_name=c_role,
                        notes=f"Säljpitch genererad & skickad: {pitch['subject']}",
                    )
                    st.toast(f"Uppdraget flyttat till 'Pitch skickad' för {c_role}!")
                    st.rerun()

# ----------------- VIEW 3: KONSULTMATCHNING & BÄNKOPTIMERING -----------------
elif current_view == "Konsultmatchning & Bänkoptimering":
    st.markdown("##### Konsultmatchning & Bänkoptimering")
    st.caption("Matcha tillgängliga konsulter mot regionens aktiva IT-krav med viktad poängberäkning och automatiska säljpitchar.")

    profile_options = [f"{p['name']} – {p['title']} ({p['location']})" for p in PRESET_BENCH_PROFILES]
    profile_options.append("➕ Skapa egen konsultprofil / Klistra in CV")

    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        chosen_profile_label = st.selectbox(
            "Välj konsultprofil på bänken",
            profile_options,
            index=0,
        )
    with col_sel2:
        min_score = st.slider("Lägsta matchningsgrad (%)", min_value=20, max_value=80, value=30, step=5)

    is_custom = "Skapa egen" in chosen_profile_label

    if not is_custom:
        selected_prof_idx = profile_options.index(chosen_profile_label)
        active_consultant = PRESET_BENCH_PROFILES[selected_prof_idx]

        skills_pills = "".join([f'<span class="skill-tag">{s}</span>' for s in active_consultant["skills"]])
        clearance_text = " • Säkerhetsprövad (RK3/SUA)" if active_consultant.get("clearance") else ""
        
        st.markdown(
            f"""
            <div style="background: rgba(128, 128, 128, 0.04); border: 1px solid rgba(128, 128, 128, 0.18); border-radius: 8px; padding: 18px 20px; margin-bottom: 22px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: inherit;">{active_consultant['name']}</div>
                        <div style="font-size: 0.86rem; opacity: 0.8; margin-top: 2px;">{active_consultant['title']} • {active_consultant['seniority']} • {active_consultant['location']}{clearance_text}</div>
                    </div>
                    <div class="priority-pill p-growth">{active_consultant['available_from']}</div>
                </div>
                <div style="font-size: 0.85rem; opacity: 0.85; line-height: 1.5; margin-bottom: 12px;">{active_consultant['summary']}</div>
                <div>{skills_pills}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("###### Egen konsultprofil")
        col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
        with col_c1:
            c_name_input = st.text_input("Konsultens namn", value="Anna Andersson")
            c_role_input = st.text_input("Rollextitel", value="Senior Fullstack-utvecklare")
        with col_c2:
            c_loc_input = st.selectbox("Ort / Primärt område", ["Linköping", "Norrköping", "Södertälje", "Nyköping", "Hela regionen"])
            c_avail_input = st.text_input("Tillgänglig från", value="Omgående")
        with col_c3:
            c_clear_input = st.checkbox("Säkerhetsprövad", value=False)
            c_seniority_input = st.selectbox("Erfarenhet", ["Junior (1–3 år)", "Mid (3–5 år)", "Senior (5–10 år)", "Lead (>10 år)"], index=2)

        raw_cv_text = st.text_area(
            "Klistra in konsultens profil, CV-sammanfattning eller tekniska nyckelord",
            height=110,
            placeholder="T.ex: Erfaren utvecklare med stark bakgrund inom C#, .NET 8, React, Azure, Docker, Kubernetes och REST API...",
        )

        detected_custom_skills = [s[0] for s in extract_skills_from_text(raw_cv_text)] if raw_cv_text else []
        all_skills = [s.name for s in db.query(Skill).order_by(Skill.name).all()]
        
        custom_selected_skills = st.multiselect(
            "Kompetenser (extraherade automatiskt ur texten, justera vid behov)",
            all_skills,
            default=[s for s in detected_custom_skills if s in all_skills],
        )

        active_consultant = {
            "name": c_name_input,
            "title": c_role_input,
            "seniority": c_seniority_input,
            "location": c_loc_input,
            "available_from": c_avail_input,
            "clearance": c_clear_input,
            "skills": custom_selected_skills,
            "summary": raw_cv_text[:300] if raw_cv_text else f"{c_role_input} baserad i {c_loc_input}.",
        }

    matched_leads = match_consultant_to_leads(
        db,
        consultant=active_consultant,
        location_filter=selected_location if selected_location != "Alla" else None,
        min_match_pct=min_score,
        limit=25,
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Matchade Uppdrag", f"{len(matched_leads)} st")
    with col_m2:
        top_match_score = f"{matched_leads[0]['match_score']}%" if matched_leads else "0%"
        st.metric("Bästa Matchning", top_match_score)
    with col_m3:
        direct_consultant_count = sum(1 for m in matched_leads if m["is_consultant"])
        st.metric("Direkta Konsultuppdrag", f"{direct_consultant_count} st")
    with col_m4:
        strong_matches_count = sum(1 for m in matched_leads if m["match_score"] >= 75)
        st.metric("Hög Prioritet (>=75%)", f"{strong_matches_count} st")

    st.markdown("---")

    if matched_leads:
        st.markdown(f"###### Relevanta affärsmöjligheter för {active_consultant['name']} (Sorterat efter matchningsgrad)")

        for lead in matched_leads:
            score = lead["match_score"]
            if score >= 75:
                score_pill = f'<span class="priority-pill p-growth">{score}% Match</span>'
            elif score >= 55:
                score_pill = f'<span class="priority-pill p-strategic">{score}% Match</span>'
            else:
                score_pill = f'<span class="priority-pill p-stable">{score}% Match</span>'

            source_tag = (
                '<span class="tag-source source-consultant">Konsultuppdrag</span>'
                if lead["is_consultant"]
                else '<span class="tag-source source-recruitment">Rekryteringsannons</span>'
            )

            matched_tags = "".join([f'<span class="skill-matched">✓ {s}</span>' for s in lead["matched_skills"]])
            missing_tags = "".join([f'<span class="skill-missing">{s}</span>' for s in lead["missing_skills"][:4]])
            bonus_tags = "".join([f'<span class="skill-bonus">+ {s}</span>' for s in lead["bonus_skills"]])

            link_html = (
                f'<a href="{lead["url"]}" target="_blank" class="link-action">Visa fullständig annons →</a>'
                if lead["url"]
                else '<span style="opacity:0.6; font-size:0.8rem;">Länk saknas</span>'
            )

            status_badge = get_status_badge_html(lead.get("status", "Nytt"))

            st.markdown(
                f"""
                <div class="lead-row">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                        <div>
                            {score_pill} {source_tag} {status_badge}
                            <div class="lead-title-text" style="margin-top: 6px;">{lead['title']}</div>
                        </div>
                        <div>
                            {link_html}
                        </div>
                    </div>
                    <div class="lead-attributes">
                        <span>Beställare: <span class="lead-attr-strong">{lead['company']}</span></span>
                        <span>Ort: <span class="lead-attr-strong">{lead['location']}</span></span>
                        <span>Publicerad: <span>{lead['published_at']}</span></span>
                        {f'<span>Kandidat: <span class="lead-attr-strong">{lead["candidate_name"]}</span></span>' if lead.get("candidate_name") else ''}
                        {f'<span>Ansvarig: <span class="lead-attr-strong">{lead["assigned_to"]}</span></span>' if lead.get("assigned_to") else ''}
                    </div>
                    <div style="margin-top: 8px; font-size: 0.8rem;">
                        <div style="margin-bottom: 4px;"><strong>Matchade krav:</strong> {matched_tags if matched_tags else '<span style=\"opacity:0.6;\">Inga direkta teknikkrav</span>'}</div>
                        {f'<div style=\"margin-bottom: 4px;\"><strong style=\"opacity:0.7;\">Övriga krav i annons:</strong> {missing_tags}</div>' if missing_tags else ''}
                        {f'<div><strong style=\"color:#B5223F;\">Konsultens mervärde:</strong> {bonus_tags}</div>' if bonus_tags else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Generera säljpitch för {active_consultant['name']} till {lead['company']}"):
                col_sp1, col_sp2 = st.columns([3, 1])
                with col_sp1:
                    custom_sub = st.text_input("Föreslagen ämnesrad", value=lead["pitch_subject"], key=f"pitch_sub_{lead['lead_id']}_{active_consultant['name']}")
                with col_sp2:
                    st.caption("Färdigt att kopiera & skicka")
                custom_body = st.text_area("Säljmejl (redigerbart)", value=lead["pitch_body"], height=190, key=f"pitch_body_{lead['lead_id']}_{active_consultant['name']}")

                if st.button(f"🚀 Spara pitch & flytta till 'Pitch skickad'", key=f"pipe_save_{lead['lead_id']}_{active_consultant['name']}", use_container_width=True):
                    update_lead_status(
                        db,
                        lead_id=lead["lead_id"],
                        status="Pitch skickad",
                        assigned_to=active_consultant.get("location", "Konsultchef"),
                        candidate_name=active_consultant["name"],
                        notes=f"Matchad med {active_consultant['name']} ({lead['match_score']}% match).\nÄmne: {custom_sub}",
                    )
                    st.toast(f"Uppdraget har sparats och flyttats till Säljpipeline som 'Pitch skickad' för {active_consultant['name']}!")
                    st.rerun()
    else:
        st.info("Inga uppdrag nådde den valda lägsta matchningsgraden. Prova att sänka matchningströskeln ovan.")

# ----------------- VIEW 4: MARKNADSPROGNOS & TRENDER (UNIFIED SUITE) -----------------
elif current_view == "Marknadsprognos & Trender":
    tab_forecast, tab_history, tab_strategy = st.tabs([
        "6-Månaders AI-Prognos",
        "Historik & Säsongsmönster (2022–2026)",
        "Strategiskt Beslutsunderlag",
    ])

    with tab_forecast:
        st.markdown("##### Prediktiv Efterfrågeprognos (6 Månader Framåt)")
        st.caption("Maskininlärningsprognos (Holt-Winters säsongsextrapolering & momentum) tränad på 58 månaders data (2022–2026) sparad i Supabase.")

        hist_df, fc_df, trending_skills = get_forecast_display_data(db, location=selected_location)

        if not fc_df.empty:
            avg_fc_vol = fc_df["predicted_volume"].mean()
            peak_month_row = fc_df.loc[fc_df["predicted_volume"].idxmax()]
            top_growth_skill = trending_skills[0] if trending_skills else None

            col_fc1, col_fc2, col_fc3 = st.columns(3)
            with col_fc1:
                st.metric(
                    "Prognosticerad Snittvolym (Kommande 6 mån)",
                    f"{avg_fc_vol:.0f} st/mån",
                    delta=f"{fc_df['growth_mom_pct'].iloc[0]:+.1f}% startmånad",
                )
            with col_fc2:
                st.metric(
                    "Förväntad Efterfrågetopp",
                    f"{peak_month_row['predicted_volume']:.0f} st",
                    help=f"Toppmånad: {peak_month_row['period']}",
                )
            with col_fc3:
                if top_growth_skill:
                    st.metric(
                        "Starkast Kompetenstillväxt",
                        f"{top_growth_skill['skill']}",
                        delta=f"+{top_growth_skill['growth_pct']:.0f}% momentum",
                    )
                else:
                    st.metric("Kompetenstillväxt", "Beräknad", delta="Normal")

            st.markdown("---")

            # Forecast Line Chart with Confidence Interval
            hist_subset = hist_df.tail(18).copy()
            fig_fc = go.Figure()

            # Add Historical Line
            fig_fc.add_trace(go.Scatter(
                x=hist_subset["period"],
                y=hist_subset["total_postings"],
                mode="lines+markers",
                name="Historisk volym (Utfall)",
                line=dict(color="#1C1C1C", width=2.5),
                marker=dict(size=6, color="#1C1C1C"),
            ))

            # Bridge point
            bridge_x = [hist_subset["period"].iloc[-1]] + list(fc_df["period"])
            bridge_y = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["predicted_volume"])
            bridge_lower = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["ci_lower"])
            bridge_upper = [hist_subset["total_postings"].iloc[-1]] + list(fc_df["ci_upper"])

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_upper,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(181, 34, 63, 0.12)",
                name="80% Konfidensintervall (P10–P90)",
                hoverinfo="skip",
            ))

            fig_fc.add_trace(go.Scatter(
                x=bridge_x,
                y=bridge_y,
                mode="lines+markers",
                name="Maskininlärningsprognos",
                line=dict(color="#B5223F", width=3, dash="dash"),
                marker=dict(size=7, color="#B5223F", symbol="diamond"),
            ))

            loc_label = selected_location if selected_location != "Alla" else "Hela regionen (Östergötland, Södertälje & Nyköping)"
            st.markdown(f"###### Marknadsprognos & Efterfrågebana ({loc_label})")
            fig_fc.update_layout(
                xaxis_title="Period (Månad)",
                yaxis_title="Antal IT-behov / Uppdrag",
                hovermode="x unified",
            )
            style_chart(fig_fc, height=390, show_legend=True)
            st.plotly_chart(fig_fc, use_container_width=True)

            st.markdown("---")

            # Upskilling Matrix
            st.markdown("###### Framtida Kompetensbehov & Vidareutbildningsrekommendationer (Upskilling Matrix)")
            st.caption("Sorterat efter efterfrågeacceleration och tillväxt mellan perioderna.")

            if trending_skills:
                col_u1, col_u2 = st.columns([3, 2])
                with col_u1:
                    skills_table_df = pd.DataFrame(trending_skills)
                    display_table = skills_table_df[["skill", "category", "current_volume", "growth_pct", "action"]].copy()
                    display_table.columns = ["Kompetens", "Kategori", "Aktuella behov (6m)", "Tillväxt (%)", "Strategisk Rekommendation"]
                    st.dataframe(
                        display_table,
                        use_container_width=True,
                        hide_index=True,
                    )

                with col_u2:
                    st.markdown(
                        """
                        <div style="background: rgba(128, 128, 128, 0.04); border: 1px solid rgba(128, 128, 128, 0.16); border-radius: 8px; padding: 16px; font-size: 0.88rem; line-height: 1.6;">
                            <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 8px;">Ledningsåtgärder för konsultteamet:</div>
                            <strong>1. Investera & Certifiera:</strong> Konsulter på bänken bör prioriteras mot certifieringar inom <em>Terraform, Kubernetes (CKA) och Databricks</em>.<br>
                            <strong>2. Rekryteringsfokus:</strong> Styr kravprofiler för seniorrekrytering mot Cloud Architecture och NIS2-säkerhet där tillväxttakten är som högst.<br>
                            <strong>3. Kassakor:</strong> Bibehåll senior leverans inom etablerad systemutveckling (.NET, C#, C++, Python) som står för den stabila basvolymen.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            col_btn_retrain, col_btn_info = st.columns([1, 3])
            with col_btn_retrain:
                if st.button("Kör om ML-prognos nu", use_container_width=True):
                    with st.spinner("Tränar om tidsserie- och momentummodeller..."):
                        run_forecast_and_save(db, location=selected_location)
                        st.success("Modell omtränad och prognos uppdaterad!")
                        st.rerun()
            with col_btn_info:
                st.caption("Modellen tränas automatiskt varannan vecka via GitHub Actions. Klicka ovan för att framtvinga en omedelbar omräkning.")
        else:
            st.info("Ingen förberäknad prognos tillgänglig för det valda filtret. Klicka på knappen nedan för att generera den.")
            if st.button("Generera prognos nu"):
                with st.spinner("Tränar modell..."):
                    run_forecast_and_save(db, location=selected_location)
                    st.rerun()

    with tab_history:
        st.markdown("##### Historisk Marknadsutveckling (2022–2026)")
        st.caption("Djupanalys baserad på över 3 800 historiska IT-annonser i Östergötland, Södertälje och Nyköping.")

        # Row 1: Monthly Trend (left) & Seasonality (right) - Balanced
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            loc_label = selected_location if selected_location != "Alla" else "Hela regionen"
            st.markdown(f"###### Volymtrend månad för månad ({loc_label})")
            try:
                vol_df = get_monthly_volume_trend(db, location=selected_location)
                if not vol_df.empty:
                    fig_vol = px.line(
                        vol_df,
                        x="month",
                        y="postings",
                        labels={"month": "Månad", "postings": "Annonserade IT-positioner"},
                        markers=True,
                        color_discrete_sequence=["#B5223F"],
                    )
                    style_chart(fig_vol, height=360, show_legend=False)
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.info("Ingen historisk volymdata tillgänglig för valt filter.")
            except Exception as e:
                st.warning(f"Kunde inte läsa volymtrend just nu: {e}")

        with col_t2:
            st.markdown("###### Säsongsmönster: När rekryterar kunderna som mest?")
            try:
                season_df = get_seasonal_pattern(db, location=selected_location)
                if not season_df.empty:
                    fig_season = px.bar(
                        season_df,
                        x="month_name",
                        y="count",
                        labels={"month_name": "Kalendermånad", "count": "Sammanlagd volym"},
                        color="count",
                        color_continuous_scale=["#FBD8CF", "#F49E88", "#B5223F"],
                    )
                    style_chart(fig_season, height=360, show_legend=False)
                    fig_season.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_season, use_container_width=True)
                else:
                    st.info("Ingen säsongsdata tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa säsongsmönster: {e}")

        st.markdown("---")

        # Row 2: Top 6 Tech Time Series (left) & Growth Barometer (right) - Balanced
        col_t3, col_t4 = st.columns(2)
        with col_t3:
            st.markdown("###### Kompetensutveckling över tid: Topp 6 teknologier")
            try:
                skills_ts_df = get_top_skills_time_series(db, location=selected_location, top_n=6)
                if not skills_ts_df.empty:
                    fig_ts = px.line(
                        skills_ts_df,
                        x="month",
                        y="count",
                        color="skill",
                        labels={"month": "Månad", "count": "Efterfrågan (annonser)", "skill": "Kompetens"},
                        color_discrete_sequence=CONSID_PALETTE[:6],
                    )
                    style_chart(fig_ts, height=360, show_legend=True)
                    fig_ts.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5, title=None))
                    st.plotly_chart(fig_ts, use_container_width=True)
                else:
                    st.info("Ingen kompetenshistorik tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa kompetensutveckling: {e}")

        with col_t4:
            st.markdown("###### Tillväxtbarometer: Snabbast växande kompetenser (%)")
            try:
                growth_df = get_skill_growth_barometer(db, location=selected_location)
                if not growth_df.empty:
                    fig_growth = px.bar(
                        growth_df,
                        x="growth_pct",
                        y="skill",
                        orientation="h",
                        labels={"growth_pct": "Tillväxt (%)", "skill": "Kompetens"},
                        color="growth_pct",
                        color_continuous_scale=["#FBD8CF", "#F49E88", "#D86261", "#B5223F"],
                    )
                    fig_growth.update_layout(yaxis={"categoryorder": "total ascending"})
                    style_chart(fig_growth, height=360, show_legend=False)
                    fig_growth.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_growth, use_container_width=True)
                else:
                    st.info("Ingen tillväxtdata tillgänglig.")
            except Exception as e:
                st.warning(f"Kunde inte läsa tillväxtbarometer: {e}")

        st.markdown("---")

        # Strategic Foresight Note
        st.markdown(
            """
            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">Strategisk Marknadsspaning för Ledningsgruppen</span>
                    <span class="priority-pill p-strategic">Ledningsanalys</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.82; line-height: 1.6;">
                    1. <strong>Cybersäkerhet & Plattform (+62% till +100% tillväxt):</strong> Den starkaste tillväxtvektorn i regionen. Drivs av regulatoriska EU-direktiv (NIS2/DORA) samt industriell modernisering mot mikrotjänster.<br>
                    2. <strong>Försvar & Fordon (C++ / Embedded +35.7%):</strong> Linköpings flyg- och försvarskluster (Saab Gripen) och Södertäljes fordonskluster (Scania elektrifiering) uppvisar en strukturell tillväxt som är stabil över konjunkturcykler.<br>
                    3. <strong>Säsongseffekter för säljteamet:</strong> Efterfrågan toppar historiskt kraftigt i <strong>oktober och mars</strong>. Resursplanering och konsultpitchar bör intensifieras 3–4 veckor före dessa toppar för att maximera beläggningen.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_strategy:
        st.markdown("##### Strategiska Prioriteringar för Ledningen")
        st.caption("Sammanfattande marknadsanalys och konkreta affärsrekommendationer för ledningsgruppen.")

        st.markdown(
            """
            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">1. Molninfrastruktur & DevOps (Azure, Terraform, Kubernetes)</span>
                    <span class="priority-pill p-high">Hög prioritet</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                    Azure och automation fortsätter att vara det dominerande teknikbehovet i regionen, framförallt inom industri och offentlig förvaltning med bas i Linköping och Norrköping.
                </div>
                <div class="action-note">
                    <strong>Ledningsåtgärd:</strong> Prioritera certifiering av befintliga konsulter (Azure Solutions Architect, DevOps Engineer) och inrikta senior rekrytering mot plattformsarkitektur.
                </div>
            </div>

            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">2. Inbyggda och säkerhetskritiska system (C++, Linux, Försvarssektorn)</span>
                    <span class="priority-pill p-growth">Tillväxtsegment</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                    Linköpings starka försvars- och säkerhetskluster uppvisar en ihållande hög efterfrågan på systemnära utvecklare. Uppdragen ställer regelmässigt krav på svenskt medborgarskap och godkänd säkerhetsprövning.
                </div>
                <div class="action-note">
                    <strong>Ledningsåtgärd:</strong> Etablera dedikerade kandidatpooler med förhandskontrollerad säkerhetsstatus inför kommande ramavtalstilldelningar.
                </div>
            </div>

            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">3. Informationssäkerhet & Compliance (NIS2, ISO 27001)</span>
                    <span class="priority-pill p-strategic">Strategisk rådgivning</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                    Implementeringen av NIS2-direktivet driver en kraftigt ökad efterfrågan på rådgivning och gapanalyser hos både kommunala bolag och samhällsviktiga leverantörer.
                </div>
                <div class="action-note">
                    <strong>Ledningsåtgärd:</strong> Paketera proaktiva rådgivningsinsatser mot ledningsgrupper i medelstora regionala bolag för att öppna dörrar till bredare IT-uppdrag.
                </div>
            </div>

            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">4. Data Analytics & Dataplattformar (Databricks, Power BI, Python)</span>
                    <span class="priority-pill p-stable">Etablerat behov</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                    Flera ledande industrier i Norrköping konsoliderar sin datainfrastruktur mot moderna Data Lakehouses för att möjliggöra avancerad analys och maskininlärning.
                </div>
                <div class="action-note">
                    <strong>Ledningsåtgärd:</strong> Positionera erbjudandet kring helhetslösningar inom data engineering snarare än enskilda rapportbyggen.
                </div>
            </div>

            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">5. Fordonselektrifiering & Life Science (Södertälje & Nyköping)</span>
                    <span class="priority-pill p-growth">Expansionsområde</span>
                </div>
                <div style="font-size: 0.88rem; opacity: 0.8; line-height: 1.5;">
                    Scania- och AstraZeneca-klustren i Södertälje samt industrin kring Nyköping skapar stor efterfrågan inom fordonsprogramvara (AUTOSAR, C++, diagnostik, Linux) och validerade Life Science-molnplattformar.
                </div>
                <div class="action-note">
                    <strong>Ledningsåtgärd:</strong> Rikta konsultbearbetning mot fordons- och automationsbolag i Södertälje- och Nyköpingsregionen som komplement till Mjärdevi- och SAAB-affärerna.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------- VIEW 5: LEDNINGSRAPPORT & VECKOBREV -----------------
elif current_view == "Ledningsrapport & Veckobrev":
    st.markdown("##### Veckorapport: Marknadsintelligens för ledningen")
    st.caption("Aggregerad sammanställning av den senaste veckans uppdragsflöde, heta leads och kompetenstrender.")

    digest_data = build_weekly_intelligence_data(db, days_back=7)
    digest_md = format_markdown_digest(digest_data)
    digest_html = format_html_digest(digest_data)

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("Totala Aktiva Behov", f"{digest_data['total_active']} st")
    with col_d2:
        st.metric("Direkta Konsultuppdrag", f"{digest_data['consultant_leads']} st")
    with col_d3:
        st.metric("Nya Poster Senaste 7 Dagar", f"{digest_data['new_this_week']} st")

    st.markdown("---")

    col_btn_md, col_btn_html, col_btn_teams = st.columns([1, 1, 2])
    with col_btn_md:
        st.download_button(
            label="Ladda ner Markdown (.md)",
            data=digest_md,
            file_name=f"marknadsrapport_{digest_data['report_date']}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_btn_html:
        st.download_button(
            label="Ladda ner HTML-brev (.html)",
            data=digest_html,
            file_name=f"marknadsbrev_{digest_data['report_date']}.html",
            mime="text/html",
            use_container_width=True,
        )

    current_env_webhook = os.getenv("TEAMS_WEBHOOK_URL", "").strip()

    with col_btn_teams:
        if st.button("Skicka rapport till Microsoft Teams nu", use_container_width=True):
            target_url = st.session_state.get("custom_teams_url") or current_env_webhook
            if target_url and send_teams_notification(digest_md, webhook_url=target_url):
                st.success("Veckorapporten har skickats till din Microsoft Teams-kanal!")
            else:
                st.warning("Kunde inte skicka. Kontrollera att din TEAMS_WEBHOOK_URL är konfigurerad nedan.")

    # Expandable Microsoft Teams Webhook Configuration box
    with st.expander("Koppla & Konfigurera Microsoft Teams Webhook", expanded=not bool(current_env_webhook)):
        if current_env_webhook:
            st.success("Microsoft Teams Webhook är kopplad i `.env`.")
        else:
            st.info("Koppla ihop valfri kanal i Microsoft Teams för automatiserade rapporter varje måndag.")

        st.markdown(
            """
            1. **I Teams:** Gå till kanalen där du vill få rapporterna -> Klicka på `...` -> Välj **Arbetsflöden (Workflows)**.
            2. Sök efter mallen **"webhook"** och välj *"Send webhook alerts to a channel"* (eller *"Skicka webhook-aviseringar till en kanal"*).
            3. Kopiera den genererade webhook-länken och klistra in den nedan.
            """
        )
        custom_teams_url = st.text_input(
            "Teams Webhook URL",
            value=st.session_state.get("custom_teams_url", current_env_webhook),
            key="custom_teams_url_input",
            placeholder="https://...powerplatform.com:443/powerautomate/automations/... eller logic.azure.com",
        )
        if custom_teams_url:
            st.session_state["custom_teams_url"] = custom_teams_url.strip()

        col_t1, col_t2 = st.columns([1, 1])
        with col_t1:
            if st.button("Skicka testmeddelande till denna Teams-länk"):
                active_url = custom_teams_url.strip() or current_env_webhook
                if active_url:
                    if send_teams_notification(digest_md, webhook_url=active_url):
                        st.success("Testrapporten levererades till Microsoft Teams! Kontrollera din kanal nu.")
                    else:
                        st.error("Kunde inte skicka. Kontrollera att länken är komplett kopierad från Teams.")
                else:
                    st.warning("Klistra in en Teams Webhook URL i rutan först.")
        with col_t2:
            if st.button("Spara till .env-filen"):
                if custom_teams_url.strip():
                    try:
                        env_path = BASE_DIR / ".env"
                        env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
                        if "TEAMS_WEBHOOK_URL=" in env_content:
                            lines = env_content.splitlines()
                            new_lines = []
                            for l in lines:
                                if l.strip().startswith("TEAMS_WEBHOOK_URL="):
                                    new_lines.append(f"TEAMS_WEBHOOK_URL={custom_teams_url.strip()}")
                                else:
                                    new_lines.append(l)
                            env_path.write_text("\n".join(new_lines), encoding="utf-8")
                        else:
                            env_path.write_text(env_content + f"\nTEAMS_WEBHOOK_URL={custom_teams_url.strip()}\n", encoding="utf-8")
                        load_dotenv(override=True)
                        st.success("Webhook-länken sparades permanent i .env!")
                    except Exception as ex:
                        st.error(f"Kunde inte spara till .env: {ex}")
                else:
                    st.warning("Ange en länk att spara.")

    st.markdown("##### Förhandsgranskning av veckorapporten")
    st.markdown(digest_md)

db.close()
