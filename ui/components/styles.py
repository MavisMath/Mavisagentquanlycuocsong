"""
ui/components/styles.py - Custom CSS injection for the Mavis Executive Life Coach UI.
"""

import streamlit as st


def inject_custom_css():
    """Nhúng toàn bộ CSS phong cách Executive, hỗ trợ Sticky Header và thẻ nhiệm vụ."""
    st.markdown(
        """
        <style>
        /* Ghim cứng (Fixed Sticky) Cụm Tiêu Đề & Thanh 4 Tab trên cùng màn hình */
        .main div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
            position: fixed !important;
            top: 2.85rem !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            z-index: 9999 !important;
            background-color: #0e1117 !important;
            border-bottom: 1px solid #262730 !important;
            padding: 0.6rem 2rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
        }
        .main div[data-testid="stTabs"] > div[data-baseweb="tab-panel"] {
            padding-top: 4.5rem !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTabs"] > div[data-baseweb="tab-list"] {
            position: static !important;
            width: auto !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTabs"] > div[data-baseweb="tab-panel"] {
            padding-top: 0 !important;
        }
        div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[role="tab"] {
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }
        .metric-card {
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 12px;
            color: #f8fafc;
        }
        .user-badge {
            background: linear-gradient(135deg, #0f766e, #134e4a);
            border: 1px solid #2dd4bf;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 14px;
            color: #f0fdfa;
        }
        .auth-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .task-card-high {
            background: #3b1812;
            border-left: 5px solid #ef4444;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-low {
            background: #142e20;
            border-left: 5px solid #10b981;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-deferred {
            background: #3b280c;
            border-left: 5px solid #f59e0b;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-habit {
            background: #0f2d38;
            border-left: 5px solid #06b6d4;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-physical {
            background: #3b1d0c;
            border-left: 5px solid #f97316;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-recovery {
            background: #0f2e29;
            border-left: 5px solid #14b8a6;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .task-card-relationship {
            background: #361022;
            border-left: 5px solid #f43f5e;
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .badge-high { color: #fca5a5; font-weight: bold; font-size: 0.8em; }
        .badge-low { color: #86efac; font-weight: bold; font-size: 0.8em; }
        .badge-deferred { color: #fde68a; font-weight: bold; font-size: 0.8em; }
        .badge-habit { color: #67e8f9; font-weight: bold; font-size: 0.8em; }
        .badge-physical { color: #fdba74; font-weight: bold; font-size: 0.8em; }
        .badge-recovery { color: #5eead4; font-weight: bold; font-size: 0.8em; }
        .badge-relationship { color: #fda4af; font-weight: bold; font-size: 0.8em; }
        </style>
        """,
        unsafe_allow_html=True,
    )
