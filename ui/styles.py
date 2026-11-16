"""
Consid Lead Intelligence Platform - UI Design Tokens, CSS, and Theme Helpers.
"""
import streamlit as st

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

CONSID_PRIMARY = "#B5223F"       # Consid Raspberry Red
CONSID_BURGUNDY = "#701131"      # Consid Dark Burgundy / Wine
CONSID_CORAL = "#F49E88"         # Consid Soft Orange / Light Coral
CONSID_TERRACOTTA = "#D86261"    # Consid Warm Terracotta
CONSID_CHARCOAL = "#1C1C1C"      # Consid Charcoal Black
CONSID_GREIGE = "#A99B94"        # Consid Greige
CONSID_MUTED = "#6C757D"         # Muted gray

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


def inject_custom_css():
    """Injects Consid brand typography, colors, and layout stylesheet into Streamlit."""
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


def style_chart(fig, height=380, show_legend=True):
    """Applies standardized typography, colors, and layout to Plotly figures."""
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
    """Applies standardized styling for donut/pie charts."""
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
    """Returns styled HTML pill for a CRM pipeline lead status."""
    st_val = (status_val or "Nytt").strip()
    if st_val == "Granskas":
        return '<span class="status-pill status-granskas">🔍 Granskas</span>'
    elif st_val == "Pitch skickad":
        return '<span class="status-pill status-pitch">✉️ Pitch skickad</span>'
    elif st_val == "Intervju":
        return '<span class="status-pill status-intervju">🤝 Intervju</span>'
    elif st_val in ("Vunnet", "Tillsatt"):
        return '<span class="status-pill status-vunnet">🏆 Vunnet</span>'
    elif st_val == "Arkiverad":
        return '<span class="status-pill" style="background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;">📁 Arkiverad</span>'
    elif st_val in ("Avböjt", "Ej aktuell"):
        return '<span class="status-pill status-avböjt">✖ Avböjt</span>'
    else:
        return '<span class="status-pill status-nytt">📥 Nytt</span>'


def render_html(html_str: str):
    """Safely renders HTML without Markdown interpreting indented lines as code blocks."""
    clean = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


def render_global_header(current_view: str, sync_time_str: str, new_today_html: str):
    """Renders the top title and active view breadcrumb."""
    render_html(
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
            <span style="font-size: 0.76rem; opacity: 0.85;">🕒 Senaste datainsamling: <strong>{sync_time_str}</strong>{new_today_html}</span>
        </div>
        """
    )
