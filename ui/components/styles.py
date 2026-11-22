"""
ui/components/styles.py - Custom CSS injection for the Mavis Executive Life Coach UI (Duolingo Style).
"""

import streamlit as st


def inject_custom_css():
    """Nhúng toàn bộ CSS phong cách Duolingo tươi sáng, vui nhộn, nút 3D và thẻ bo tròn."""
    st.markdown(
        """
        <style>
        /* 1. GOOGLE FONT NUNITO TOÀN DIỆN */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;0,900;1,400;1,700&display=swap');

        html, body, [class*="css"], .stApp, button, input, select, textarea, div {
            font-family: 'Nunito', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* 2. NỀN SÁNG DỊU DUOLINGO */
        .stApp {
            background-color: #F7F9FC !important;
            color: #3C3C3C !important;
        }

        /* 3. SIDEBAR DUOLINGO */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 2px solid #E5E5E5 !important;
        }
        section[data-testid="stSidebar"] div.stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
            color: #3C3C3C !important;
        }

        /* 4. GHIM CỨNG (FIXED STICKY) CỤM TIÊU ĐỀ & THANH 4 TAB TRÊN CÙNG */
        .main div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
            position: fixed !important;
            top: 2.85rem !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            z-index: 9999 !important;
            background-color: #FFFFFF !important;
            border-bottom: 3px solid #E5E5E5 !important;
            padding: 0.65rem 2rem !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
            gap: 10px !important;
        }
        .main div[data-testid="stTabs"] > div[data-baseweb="tab-panel"] {
            padding-top: 5.2rem !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
            position: static !important;
            width: auto !important;
            padding: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
            border-bottom: none !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTabs"] > div[data-baseweb="tab-panel"] {
            padding-top: 0 !important;
        }
        div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[role="tab"] {
            font-weight: 800 !important;
            font-size: 0.95rem !important;
            border-radius: 14px !important;
            padding: 0.5rem 1.1rem !important;
            color: #777777 !important;
            background-color: #F7F9FC !important;
            border: 2px solid #E5E5E5 !important;
            border-bottom: 3px solid #D5D5D5 !important;
            transition: all 0.15s ease !important;
        }
        div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[role="tab"]:hover {
            color: #1CB0F6 !important;
            background-color: #F0F9FF !important;
            border-color: #BAE3FF !important;
        }
        div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] {
            color: #1CB0F6 !important;
            background-color: #EBF8FF !important;
            border-color: #1CB0F6 !important;
            border-bottom: 4px solid #1899D6 !important;
        }

        /* 5. NÚT BẤM 3D DUOLINGO (st.button, st.download_button) */
        div.stButton > button, div.stDownloadButton > button, div[data-testid*="BaseButton"] {
            font-family: 'Nunito', sans-serif !important;
            font-weight: 800 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.3px !important;
            border-radius: 16px !important;
            border: 2px solid #E5E5E5 !important;
            border-bottom: 4px solid #CECECE !important;
            background-color: #FFFFFF !important;
            color: #4B4B4B !important;
            padding: 0.45rem 1.15rem !important;
            transition: all 0.1s ease !important;
            box-shadow: none !important;
            text-transform: none !important;
        }
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: #F7F7F7 !important;
            border-color: #D5D5D5 !important;
            color: #1B1B1B !important;
        }
        div.stButton > button:active, div.stDownloadButton > button:active {
            transform: translateY(2px) !important;
            border-bottom: 2px solid #CECECE !important;
        }

        /* Primary Button: Xanh lá tươi sáng #58CC02 */
        div.stButton > button[kind="primary"], div[data-testid="baseButton-primary"] {
            background-color: #58CC02 !important;
            color: #FFFFFF !important;
            border: 2px solid #58CC02 !important;
            border-bottom: 4px solid #46A302 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #61E002 !important;
            border-color: #61E002 !important;
            color: #FFFFFF !important;
        }
        div.stButton > button[kind="primary"]:active {
            transform: translateY(2px) !important;
            border-bottom: 2px solid #46A302 !important;
        }

        /* 6. KHUNG CARD, EXPANDER, CONTAINERS BO TRÒN 16PX VIỀN 2PX */
        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 2px solid #E5E5E5 !important;
            border-bottom: 4px solid #E5E5E5 !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            margin-bottom: 14px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 800 !important;
            color: #3C3C3C !important;
            padding: 0.75rem 1rem !important;
        }
        div[data-testid="stExpander"] summary:hover {
            background-color: #F7F9FC !important;
            color: #1CB0F6 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 16px !important;
            border: 2px solid #E5E5E5 !important;
            border-bottom: 4px solid #E5E5E5 !important;
            background-color: #FFFFFF !important;
        }

        /* 7. METRIC CARDS & USER BADGES */
        .metric-card {
            background: #FFFFFF;
            border: 2px solid #E5E5E5;
            border-bottom: 4px solid #E5E5E5;
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            color: #3C3C3C;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        }
        .user-badge {
            background: #EBF8FF;
            border: 2px solid #BAE3FF;
            border-bottom: 4px solid #99D5FF;
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 14px;
            color: #0284C7;
            font-weight: 700;
        }
        .auth-card {
            background: #FFFFFF;
            border: 2px solid #E5E5E5;
            border-bottom: 4px solid #D5D5D5;
            border-radius: 20px;
            padding: 28px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
        }

        /* 8. THẺ NHIỆM VỤ (TASK CARDS) BẢNG MÀU DUOLINGO */
        .task-card-high {
            background: #FFF2F2;
            border: 2px solid #FFD1D1;
            border-left: 6px solid #FF4B4B;
            border-bottom: 4px solid #FFA8A8;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #991B1B;
        }
        .task-card-low {
            background: #F3FBF0;
            border: 2px solid #DCF5D0;
            border-left: 6px solid #58CC02;
            border-bottom: 4px solid #B8ECA0;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #166534;
        }
        .task-card-deferred {
            background: #FFFDF0;
            border: 2px solid #FFF0BA;
            border-left: 6px solid #FFC800;
            border-bottom: 4px solid #FFE480;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #854D0E;
        }
        .task-card-habit {
            background: #F0F9FF;
            border: 2px solid #BAE3FF;
            border-left: 6px solid #1CB0F6;
            border-bottom: 4px solid #85CEFF;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #0369A1;
        }
        .task-card-physical {
            background: #FFF7ED;
            border: 2px solid #FFD9B3;
            border-left: 6px solid #FF9600;
            border-bottom: 4px solid #FFC280;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #9A3412;
        }
        .task-card-recovery {
            background: #F0FDF4;
            border: 2px solid #BBF7D0;
            border-left: 6px solid #2DD4BF;
            border-bottom: 4px solid #86EFAC;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #115E59;
        }
        .task-card-relationship {
            background: #FDF2F8;
            border: 2px solid #FBCFE8;
            border-left: 6px solid #F43F5E;
            border-bottom: 4px solid #F9A8D4;
            padding: 12px 16px;
            border-radius: 16px;
            margin-bottom: 12px;
            color: #9F1239;
        }

        /* 9. BADGES MÀU RÕ NÉT */
        .badge-high { color: #DC2626; font-weight: 800; font-size: 0.85em; }
        .badge-low { color: #16A34A; font-weight: 800; font-size: 0.85em; }
        .badge-deferred { color: #D97706; font-weight: 800; font-size: 0.85em; }
        .badge-habit { color: #0284C7; font-weight: 800; font-size: 0.85em; }
        .badge-physical { color: #EA580C; font-weight: 800; font-size: 0.85em; }
        .badge-recovery { color: #0D9488; font-weight: 800; font-size: 0.85em; }
        .badge-relationship { color: #E11D48; font-weight: 800; font-size: 0.85em; }

        /* 10. INPUT FIELDS, TEXTAREA, SELECT */
        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > textarea, div[data-baseweb="select"] > div {
            border-radius: 14px !important;
            border: 2px solid #E5E5E5 !important;
            font-family: 'Nunito', sans-serif !important;
        }
        div[data-baseweb="input"]:focus-within > div, div[data-baseweb="textarea"]:focus-within > textarea, div[data-baseweb="select"]:focus-within > div {
            border-color: #1CB0F6 !important;
            box-shadow: 0 0 0 2px rgba(28, 176, 246, 0.2) !important;
        }

        /* 11. PROGRESS BARS */
        div[data-testid="stProgress"] > div > div {
            border-radius: 12px !important;
            background-color: #58CC02 !important;
        }

        /* 12. DUOLINGO MASCOT BANNER */
        .mavis-mascot-banner {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            background-color: #FFFFFF;
            border: 2px solid #E5E5E5;
            border-bottom: 4px solid #E5E5E5;
            border-radius: 20px;
            padding: 16px 22px;
            margin-bottom: 1.25rem;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
            gap: 16px;
        }
        .mascot-left-section {
            display: flex;
            align-items: center;
            gap: 16px;
            flex: 1 1 420px;
            min-width: 300px;
        }
        .mascot-avatar-container {
            width: 88px;
            height: 88px;
            min-width: 88px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: linear-gradient(135deg, #FFF9FA 0%, #FFF0F5 100%);
            border: 3px solid #FFE0EB;
            border-bottom: 4px solid #FFB8D2;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(255, 138, 163, 0.2);
            animation: float 3.5s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }
        .mascot-img-floating {
            animation: float 3.5s ease-in-out infinite;
        }
        .mascot-speech-bubble {
            position: relative;
            background-color: #FFFDF7;
            border: 2px solid #E5E5E5;
            border-bottom: 4px solid #D5D5D5;
            border-radius: 18px;
            padding: 12px 18px;
            color: #3C3C3C;
            flex: 1;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
        }
        .bubble-arrow {
            position: absolute;
            left: -12px;
            top: 50%;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            border-right: 12px solid #E5E5E5;
        }
        .bubble-arrow::after {
            content: '';
            position: absolute;
            left: 2px;
            top: -7px;
            width: 0;
            height: 0;
            border-top: 7px solid transparent;
            border-bottom: 7px solid transparent;
            border-right: 11px solid #FFFDF7;
        }
        .bubble-title {
            font-size: 0.8rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #1CB0F6;
            margin-bottom: 3px;
        }
        .bubble-message {
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.4;
            color: #3C3C3C;
        }
        .mascot-right-section {
            display: flex;
            flex-direction: column;
            gap: 10px;
            flex: 1 1 360px;
            min-width: 280px;
        }
        .mascot-badges-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .badge-streak {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: #FFF4E5;
            border: 2px solid #FFD8A8;
            border-bottom: 4px solid #FFA94D;
            border-radius: 14px;
            padding: 6px 14px;
            color: #D9480F;
            font-weight: 800;
        }
        .badge-xp {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: #EBF8FF;
            border: 2px solid #BAE3FF;
            border-bottom: 4px solid #74C0FC;
            border-radius: 14px;
            padding: 6px 14px;
            color: #1971C2;
            font-weight: 800;
        }
        .mascot-progress-container {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .progress-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.86rem;
            font-weight: 800;
            color: #4B4B4B;
        }
        .progress-percent {
            color: #58CC02;
            font-weight: 900;
        }
        .progress-track {
            height: 16px;
            background-color: #E5E5E5;
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid #D5D5D5;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(180deg, #68D912 0%, #58CC02 100%);
            border-radius: 8px;
            transition: width 0.4s ease;
            box-shadow: inset 0 2px 0 rgba(255, 255, 255, 0.4), inset 0 -2px 0 rgba(0, 0, 0, 0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
