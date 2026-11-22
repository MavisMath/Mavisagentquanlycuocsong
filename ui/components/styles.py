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
        </style>
        """,
        unsafe_allow_html=True,
    )
