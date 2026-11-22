import os
import sys

# Khắc phục triệt để lỗi SQLite3 cũ trên Streamlit Cloud cho ChromaDB & Vector DB
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

from datetime import datetime, timedelta, date

# Đảm bảo đường dẫn import tương thích khi chạy streamlit từ mọi thư mục (Local, Docker, Streamlit Cloud)
CURRENT_FILE = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CWD = os.path.abspath(os.getcwd())

for p in [PROJECT_ROOT, CWD, CURRENT_DIR]:
    if p and os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

# Cấu hình giao diện Streamlit (Bắt buộc chạy ngay sau import streamlit, trước mọi lệnh st.*)
st.set_page_config(
    page_title="Mavis AI Executive Life Coach - SaaS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Đồng bộ có chọn lọc các biến môi trường cần thiết từ st.secrets
try:
    if hasattr(st, "secrets"):
        _allowed_env_keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "MONGO_URI", "MONGODB_URI", "TAVILY_API_KEY"]
        for _key in _allowed_env_keys:
            if _key in st.secrets and isinstance(st.secrets[_key], str):
                os.environ[_key] = st.secrets[_key]

        if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        elif "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
            os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

        if "MONGO_URI" in os.environ and "MONGODB_URI" not in os.environ:
            os.environ["MONGODB_URI"] = os.environ["MONGO_URI"]
        elif "MONGODB_URI" in os.environ and "MONGO_URI" not in os.environ:
            os.environ["MONGO_URI"] = os.environ["MONGODB_URI"]
except Exception:
    pass

# ==========================================
# NẠP CÁC COMPONENT GIAO DIỆN & TIỆN ÍCH UI
# ==========================================
from ui.components import (
    inject_custom_css,
    render_auth_screen,
    render_sidebar,
    render_mascot_banner,
    render_tab_ceo,
    render_tab_architect,
    render_tab_scheduler,
    render_tab_retrospective,
    get_authenticator,
    get_default_redirect_uri,
    exchange_code_and_save_token,
    load_user_goals,
    load_user_profile,
    load_user_resources,
    load_user_roadmap,
    load_master_schedule,
    load_retrospective_logs,
    get_mavis_agent,
    apply_undo,
    apply_redo,
    OPENING_GREETING,
)

# Nhúng Custom CSS giao diện Executive
inject_custom_css()

# Khởi tạo Authenticator kết nối với auth_config.yaml
authenticator = get_authenticator()

# ==========================================
# BỨC TƯỜNG XÁC THỰC (LOGIN WALL)
# ==========================================
auth_status = st.session_state.get("authentication_status")
if not auth_status:
    render_auth_screen(authenticator)

# ==========================================
# KHI ĐÃ ĐĂNG NHẬP: XÁC ĐỊNH NGƯỜI DÙNG & SESSION
# ==========================================
raw_session_user = st.session_state.get("username")
if not raw_session_user or not str(raw_session_user).strip():
    raw_session_user = "mavis"
current_username = str(raw_session_user).strip().lower()
current_name = st.session_state.get("name") or current_username.capitalize()

# ------------------------------------------------------------------------------
# TỰ ĐỘNG BẮT MÃ GOOGLE CALENDAR OAUTH TỪ URL QUERY PARAMS
# ------------------------------------------------------------------------------
if "code" in st.query_params:
    auth_code = st.query_params.get("code")
    try:
        if auth_code:
            default_redir = get_default_redirect_uri()
            redir_session_key = f"active_gcal_redir_{current_username}"
            current_redir = st.session_state.get(redir_session_key, default_redir)
            res = exchange_code_and_save_token(auth_code, redirect_uri=current_redir, username=current_username)
            if bool(res):
                st.session_state[f"gcal_just_connected_{current_username}"] = True
            else:
                err_detail = getattr(res, "error", None) or "Không thể đổi mã xác thực Google Calendar."
                st.session_state[f"gcal_connect_error_{current_username}"] = err_detail
    except Exception as e:
        st.session_state[f"gcal_connect_error_{current_username}"] = f"Chi tiết lỗi Google OAuth: {e}"
    finally:
        try:
            st.query_params.clear()
        except Exception:
            try:
                del st.query_params["code"]
            except Exception:
                pass
        st.rerun()

if st.session_state.pop(f"gcal_just_connected_{current_username}", False):
    st.toast("🎉 Đã kết nối Google Calendar thành công vĩnh viễn!")
    st.success("✅ Đã kết nối Google Calendar thành công vĩnh viễn!")
if f"gcal_connect_error_{current_username}" in st.session_state:
    err_c = st.session_state.pop(f"gcal_connect_error_{current_username}")
    st.error(f"❌ {err_c}")

# Khởi tạo các biến Session State riêng biệt cho từng User
msg_key = f"messages_{current_username}"
if msg_key not in st.session_state:
    st.session_state[msg_key] = [{"role": "assistant", "content": OPENING_GREETING}]

energy_key = f"energy_{current_username}"
if energy_key not in st.session_state:
    st.session_state[energy_key] = "high"

emotion_key = f"emotion_{current_username}"
if emotion_key not in st.session_state:
    st.session_state[emotion_key] = "neutral"

intent_key = f"intent_{current_username}"
if intent_key not in st.session_state:
    st.session_state[intent_key] = "chat"

plan_key = f"plan_{current_username}"
if plan_key not in st.session_state:
    st.session_state[plan_key] = []

rag_key = f"rag_{current_username}"
if rag_key not in st.session_state:
    st.session_state[rag_key] = None

pending_goal_key = f"pending_goal_{current_username}"
if pending_goal_key not in st.session_state:
    st.session_state[pending_goal_key] = None

awaiting_confirmation_key = f"awaiting_confirmation_{current_username}"
if awaiting_confirmation_key not in st.session_state:
    st.session_state[awaiting_confirmation_key] = False

profile_key = f"profile_{current_username}"
if profile_key not in st.session_state:
    try:
        saved_prof = load_user_profile(current_username)
    except Exception:
        saved_prof = {}
    if saved_prof and isinstance(saved_prof, dict) and saved_prof.get("is_onboarded"):
        st.session_state[profile_key] = saved_prof
    else:
        st.session_state[profile_key] = {
            "current_situation": "",
            "financial_status": "",
            "time_constraints": "",
            "is_onboarded": False,
            "coaching_stage": "interviewing",
            "obstacles": [],
        }

stage_key = f"stage_{current_username}"
if stage_key not in st.session_state:
    st.session_state[stage_key] = st.session_state[profile_key].get("coaching_stage", "interviewing")

obstacles_key = f"obstacles_{current_username}"
if obstacles_key not in st.session_state:
    st.session_state[obstacles_key] = st.session_state[profile_key].get("obstacles", [])

thread_ver_key = f"thread_ver_{current_username}"
if thread_ver_key not in st.session_state:
    st.session_state[thread_ver_key] = 1

goals_key = f"goals_{current_username}"
if goals_key not in st.session_state:
    st.session_state[goals_key] = load_user_goals(current_username)

user_goals_loaded = st.session_state[goals_key]
goal_profile_key = f"goal_profile_{current_username}"
if not user_goals_loaded:
    st.session_state[goal_profile_key] = {}
    st.session_state[profile_key] = {
        "current_situation": "Chưa có mục tiêu",
        "financial_status": "",
        "time_constraints": "0h/ngày",
        "is_onboarded": False,
        "coaching_stage": "interviewing",
        "obstacles": [],
    }
elif goal_profile_key not in st.session_state or not st.session_state.get(goal_profile_key):
    st.session_state[goal_profile_key] = user_goals_loaded[0]

resources_key = f"resources_{current_username}"
if resources_key not in st.session_state:
    st.session_state[resources_key] = load_user_resources(current_username)

roadmap_key = f"roadmap_{current_username}"
if roadmap_key not in st.session_state:
    st.session_state[roadmap_key] = load_user_roadmap(current_username)

chat_ceo_key = f"chat_ceo_{current_username}"
if chat_ceo_key not in st.session_state:
    st.session_state[chat_ceo_key] = [
        {
            "role": "assistant",
            "content": (
                f"Xin chào **{current_name}**! Tôi là **Mavis CEO Coach** — người đồng hành chiến lược cao cấp của bạn.\n\n"
                "Tôi sẽ đánh giá tính khả thi, phân tích quỹ thời gian và tối ưu hóa nhịp sinh học năng lượng đỉnh cao cho các mục tiêu bạn theo đuổi.\n\n"
                "👉 Hãy chia sẻ mục tiêu bạn đang ấp ủ (VD: *'Tôi muốn học IELTS 7.0 trong 3 tháng, mỗi ngày 2 tiếng'*)..."
            ),
        }
    ]

chat_arch_key = f"chat_arch_{current_username}"
if chat_arch_key not in st.session_state:
    st.session_state[chat_arch_key] = [
        {
            "role": "assistant",
            "content": (
                f"Chào **{current_name}**! Tôi là **Strategy & Roadmap Architect** (Chuyên trách Giai đoạn 1).\n\n"
                "Tôi chịu trách nhiệm phân tích chiến lược, đề xuất phương pháp tối ưu và phân rã mục tiêu thành lộ trình 4 tầng (**Năm ➔ Quý ➔ Tháng ➔ Tuần**).\n\n"
                "👉 Hãy chọn mục tiêu ở bảng điều khiển bên cạnh để bắt đầu thảo luận phương pháp hoặc tinh chỉnh lộ trình!"
            ),
        }
    ]

chat_sched_key = f"chat_sched_{current_username}"
if chat_sched_key not in st.session_state:
    st.session_state[chat_sched_key] = [
        {
            "role": "assistant",
            "content": (
                f"Chào **{current_name}**! Tôi là **AI Master Scheduler** (Chuyên trách Giai đoạn 2).\n\n"
                "Tôi gom toàn bộ các mục tiêu Active để xếp lịch không trùng lặp (Sáng học nặng, Chiều thực hành, Tối ôn tập nhẹ).\n\n"
                "👉 Nếu bạn có việc bận đột xuất hoặc muốn dời task, hãy nhắn cho tôi ngay nhé!"
            ),
        }
    ]

chat_retro_key = f"chat_retro_{current_username}"
if chat_retro_key not in st.session_state:
    st.session_state[chat_retro_key] = [
        {
            "role": "assistant",
            "content": (
                f"Chào **{current_name}**! Tôi là **AI Retrospective Coach** (Chuyên trách Giai đoạn 3).\n\n"
                "Cuối ngày hoặc cuối tuần, chúng ta hãy ngồi lại đánh giá các task chưa hoàn thành, lắng nghe cảm xúc của bạn và tự động đề xuất điều chỉnh ngược lại Thiết lập để bạn luôn duy trì phong độ bền bỉ!"
            ),
        }
    ]

master_schedule_key = f"master_schedule_{current_username}"
if master_schedule_key not in st.session_state:
    st.session_state[master_schedule_key] = load_master_schedule(current_username)

retro_logs_key = f"retro_logs_{current_username}"
if retro_logs_key not in st.session_state:
    st.session_state[retro_logs_key] = load_retrospective_logs(current_username)

# Phục hồi State từ MongoDB vào Ram Checkpointer
mavis_agent = get_mavis_agent()
if mavis_agent and hasattr(mavis_agent, "ensure_user_state_loaded"):
    try:
        mavis_agent.ensure_user_state_loaded(current_username)
    except Exception:
        pass

# ==========================================
# SIDEBAR BẢNG ĐIỀU KHIỂN
# ==========================================
render_sidebar(current_username, current_name, authenticator)

# ==========================================
# MAIN PANEL: HEADER & 4 GIAI ĐOẠN KHÉP KÍN
# ==========================================
with st.container():
    col_hdr_text, col_hdr_undo, col_hdr_redo = st.columns([0.76, 0.12, 0.12], vertical_alignment="center")
    with col_hdr_text:
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 2px solid #E5E5E5; border-bottom: 4px solid #E5E5E5; padding: 0.65rem 1.1rem; border-radius: 18px; margin-bottom: 0.5rem; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                <div style="font-size: 1.55rem; font-weight: 800; color: #3C3C3C; margin-bottom: 2px;">⚡ Mavis AI Executive & Life Coach</div>
                <div style="font-size: 0.88rem; color: #777777; font-weight: 600;"><b>Không gian làm việc:</b> <code style="color: #1CB0F6; font-weight: 800; background: #EBF8FF; padding: 2px 8px; border-radius: 8px; border: 1px solid #BAE3FF;">{current_name}</code> (<code>@{current_username}</code>) | Mô hình CEO điều phối 3 giai đoạn khép kín • Tối ưu nhịp sinh học • Đồng bộ Cloud MongoDB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_hdr_undo:
        undo_cnt = len(st.session_state.get(f"undo_stack_{current_username}", []))
        if st.button(f"↩️ Undo ({undo_cnt})", key=f"btn_undo_top_{current_username}", disabled=(undo_cnt == 0), use_container_width=True, help="Hoàn tác thao tác trước đó (Ctrl+Z)"):
            if apply_undo(current_username):
                st.toast("↩️ Đã hoàn tác thao tác vừa rồi!")
                st.rerun()
    with col_hdr_redo:
        redo_cnt = len(st.session_state.get(f"redo_stack_{current_username}", []))
        if st.button(f"↪️ Redo ({redo_cnt})", key=f"btn_redo_top_{current_username}", disabled=(redo_cnt == 0), use_container_width=True, help="Làm lại thao tác vừa hoàn tác (Ctrl+Y)"):
            if apply_redo(current_username):
                st.toast("↪️ Đã làm lại thao tác!")
                st.rerun()

# 4 Tab Chuyên biệt theo Chu trình Điều hành Mavis CEO
tab_ceo, tab_arch, tab_sched, tab_retro = st.tabs([
    "🎙️ Tổng Hành Dinh (CEO Coach)",
    "📐 Giai đoạn 1: Thiết Lập Mục Tiêu",
    "📅 Giai đoạn 2: Thực Thi & Lịch Trình",
    "📊 Giai đoạn 3: Tổng Kết & Cải Thiện",
])

with tab_ceo:
    render_tab_ceo(current_username, current_name)

with tab_arch:
    render_tab_architect(current_username, current_name)

with tab_sched:
    render_tab_scheduler(current_username, current_name)

with tab_retro:
    render_tab_retrospective(current_username, current_name)
