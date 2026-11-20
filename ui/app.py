import os
import sys

# Khắc phục triệt để lỗi SQLite3 cũ trên Streamlit Cloud cho ChromaDB & Vector DB
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

import json
import uuid
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Đảm bảo đường dẫn import tương thích khi chạy streamlit từ mọi thư mục
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

# Tự động đồng bộ hóa secrets từ Streamlit Cloud vào biến môi trường hệ thống
try:
    if hasattr(st, "secrets"):
        for _k, _v in st.secrets.items():
            if isinstance(_v, str):
                os.environ[_k] = _v
                if _k == "GEMINI_API_KEY" and "GOOGLE_API_KEY" not in os.environ:
                    os.environ["GOOGLE_API_KEY"] = _v
except Exception:
    pass

from langchain_core.messages import HumanMessage, AIMessage

# Khởi tạo an toàn Agent Graph với cơ chế báo lỗi trực quan trên Cloud
try:
    from agents.graph import build_graph, mavis_agent
except Exception as _graph_import_err:
    import traceback
    st.error(f"⚠️ Phát hiện cảnh báo khi khởi tạo Multi-Agent Graph: {_graph_import_err}")
    with st.expander("Chi tiết kỹ thuật lỗi khởi tạo (Technical Traceback)"):
        st.code(traceback.format_exc())

    class FallbackAgent:
        def invoke(self, state, config=None):
            return {
                "messages": [
                    AIMessage(
                        content="⚠️ Hệ thống đang đồng bộ cấu hình trên Cloud. Vui lòng kiểm tra lại API Key hoặc liên hệ Quản trị viên."
                    )
                ]
            }

    def build_graph(checkpointer=None):
        return FallbackAgent()

    mavis_agent = FallbackAgent()

from memory.goals import (
    load_goals,
    save_goals,
    add_goal,
    update_goal,
    CATEGORY_LABELS,
    load_historical_insights,
    save_historical_insights,
    load_user_profile,
    save_user_profile,
    load_user_goal_profile,
    save_user_goal_profile,
    load_user_goals,
    save_user_goals,
    load_user_resources,
    save_user_resources,
    load_user_roadmap,
    save_user_roadmap,
    load_categorized_goals,
    save_categorized_goals,
)
from memory.auth import get_authenticator, register_user
from memory.mongodb import is_mongodb_available, db_update_user_state

try:
    from agents.brain import chat_node
except Exception:
    chat_node = None


def safe_dict(val: Any) -> Dict[str, Any]:
    """Chuyển đổi an toàn mọi giá trị sang dict, tránh lỗi AttributeError khi parse JSON từ LLM."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def safe_list(val: Any) -> List[Any]:
    """Chuyển đổi an toàn mọi giá trị sang list, tránh lỗi khi lặp hoặc parse JSON."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return []


def generate_gcal_link(task_title: str, time_slot: str, duration_minutes: int = 120, resource_info: str = "") -> str:
    """Tạo liên kết mở trực tiếp Google Calendar Web để thêm sự kiện 1 chạm."""
    now = datetime.now()
    now_str = now.strftime("%Y%m%d")
    start_h = 20
    start_m = 0
    t_slot_lower = str(time_slot).lower()
    if "sáng" in t_slot_lower or "08" in t_slot_lower:
        start_h = 8
    elif "06" in t_slot_lower:
        start_h = 6

    end_total_m = start_h * 60 + start_m + int(duration_minutes or 120)
    end_h = (end_total_m // 60) % 24
    end_m = end_total_m % 60

    dates_str = f"{now_str}T{start_h:02d}{start_m:02d}00/{now_str}T{end_h:02d}{end_m:02d}00"
    params = {
        "action": "TEMPLATE",
        "text": f"🎯 Mavis Coach: {task_title}",
        "dates": dates_str,
        "details": f"Lịch hành động từ Mavis Executive Coach.\nKhung giờ: {time_slot} ({duration_minutes} phút)\nTài liệu: {resource_info}",
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"


def generate_ics_calendar(roadmap: Dict[str, Any], goal_name: str, preferred_slots: str) -> str:
    """Tạo file lịch chuẩn .ics (iCalendar) tải về để import một chạm vào Google Calendar, Outlook, Apple Calendar."""
    now = datetime.now()
    now_str = now.strftime("%Y%m%d")
    events = []
    weekly_ms = safe_list(roadmap.get("weekly_milestones", []))
    day_count = 0

    for w in weekly_ms[:2]:
        w_dict = safe_dict(w)
        daily_tasks = safe_list(w_dict.get("daily_tasks", []))
        for t in daily_tasks:
            t_dict = safe_dict(t)
            t_title = t_dict.get("task_title", f"Học tập {goal_name}")
            t_duration = t_dict.get("duration_minutes", 120)
            t_slot = t_dict.get("time_slot", preferred_slots)
            t_res = t_dict.get("attached_resource", "")

            event_date = (now + timedelta(days=day_count)).strftime("%Y%m%d")
            day_count += 1

            start_h = 20
            start_m = 0
            if "sáng" in str(t_slot).lower() or "08" in str(t_slot):
                start_h = 8
            elif "06" in str(t_slot):
                start_h = 6

            end_tot = start_h * 60 + start_m + int(t_duration or 120)
            end_h = (end_tot // 60) % 24
            end_m = end_tot % 60

            uid = f"mavis_{uuid.uuid4().hex[:8]}@maviscoach.ai"
            events.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_str}T000000Z",
                f"DTSTART:{event_date}T{start_h:02d}{start_m:02d}00",
                f"DTEND:{event_date}T{end_h:02d}{end_m:02d}00",
                f"SUMMARY:🎯 Mavis: {t_title}",
                f"DESCRIPTION:Khung giờ: {t_slot} | Thời lượng: {t_duration} phút | Tài liệu: {t_res}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])

    if not events:
        uid = f"mavis_{uuid.uuid4().hex[:8]}@maviscoach.ai"
        events.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}T000000Z",
            f"DTSTART:{now_str}T200000",
            f"DTEND:{now_str}T220000",
            f"SUMMARY:🎯 Mavis: Bắt đầu mục tiêu {goal_name}",
            f"DESCRIPTION:Khung giờ học tập tối ưu nhịp sinh học cùng Mavis Coach",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mavis Executive Life Coach//VN",
        "CALSCALE:GREGORIAN",
        *events,
        "END:VCALENDAR",
    ]
    return "\r\n".join(ics_content)


def extract_text_from_content(content: Any) -> str:
    """Đảm bảo trích xuất chuỗi văn bản sạch từ content của AIMessage hoặc LLM response."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", ""))
            elif hasattr(part, "text"):
                parts.append(getattr(part, "text", ""))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def load_categorized_goals(username: str = "mavis") -> Dict[str, Any]:
    """
    Truy xuất vào đúng nhánh dữ liệu của tài khoản đó từ memory/goals_ledger.json (Phase 8 Multi-Tenant).
    Ví dụ: return data.get(username, {})
    """
    username = (username or "mavis").strip().lower()
    ledger_file = os.path.join(PROJECT_ROOT, "memory", "goals_ledger.json")

    try:
        if os.path.exists(ledger_file):
            import json
            with open(ledger_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Truy xuất trực tiếp nhánh dữ liệu của username
            user_branch = data.get(username, {})
            if user_branch:
                result = {}
                for root in ["career", "relationships", "health", "beauty"]:
                    node = user_branch.get(root, {})
                    children = node.get("children", []) if isinstance(node, dict) else (node if isinstance(node, list) else [])
                    result[root] = children
                return result
    except Exception as e:
        print(f"Lỗi khi đọc file goals_ledger.json: {e}")

    # Fallback qua memory.goals
    try:
        return load_categorized_goals(username=username)
    except Exception:
        return {}

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Mavis AI Executive Life Coach - SaaS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS để giao diện trông hiện đại, mang phong cách Executive
st.markdown(
    """
    <style>
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

# Khởi tạo Authenticator kết nối với auth_config.yaml
authenticator = get_authenticator()


# ==========================================
# 2. BỨC TƯỜNG XÁC THỰC (LOGIN WALL) - PHASE 8
# ==========================================
# Khi người dùng chưa đăng nhập, chỉ hiển thị Form Đăng nhập / Đăng ký
auth_status = st.session_state.get("authentication_status")

if not auth_status:
    col_l, col_center, col_r = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px; margin-bottom: 25px;">
                <h1 style="color: #38bdf8; margin-bottom: 4px;">⚡ MAVIS EXECUTIVE AI</h1>
                <p style="color: #94a3b8; font-size: 1.1em;">Nền tảng SaaS Quản trị Hiệu suất & Nhịp sinh học Đa người dùng</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["🔑 Đăng Nhập", "📝 Đăng Ký Tài Khoản"])

        with tab_login:
            try:
                authenticator.login(location="main", key="login_widget")
            except Exception as e:
                st.error(f"Lỗi xác thực: {e}")

            if st.session_state.get("authentication_status") is False:
                st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng thử lại!")
            elif st.session_state.get("authentication_status") is None:
                st.info("💡 Vui lòng nhập thông tin để đăng nhập vào không gian làm việc của bạn.")

        with tab_register:
            st.markdown("#### 📝 Đăng ký thành viên SaaS mới")
            with st.form("reg_form", clear_on_submit=True):
                new_user = st.text_input("Tên đăng nhập (Username)", placeholder="vd: alex_tran").strip().lower()
                new_name = st.text_input("Họ và Tên", placeholder="vd: Alex Tran")
                new_email = st.text_input("Email", placeholder="vd: alex@company.com")
                new_pass = st.text_input("Mật khẩu", type="password")
                new_pass_confirm = st.text_input("Xác nhận Mật khẩu", type="password")
                submit_reg = st.form_submit_button("🚀 Hoàn Tất Đăng Ký", use_container_width=True)

                if submit_reg:
                    if not new_user or not new_pass:
                        st.warning("⚠️ Vui lòng điền đầy đủ Tên đăng nhập và Mật khẩu!")
                    elif new_pass != new_pass_confirm:
                        st.error("❌ Mật khẩu xác nhận không khớp!")
                    else:
                        success = register_user(
                            username=new_user,
                            name=new_name,
                            email=new_email,
                            password=new_pass,
                        )
                        if success:
                            st.success(f"🎉 Chúc mừng! Tài khoản **{new_user}** đã được khởi tạo thành công. Bạn có thể chuyển sang tab **Đăng Nhập** ngay bây giờ!")
                        else:
                            st.error(f"❌ Tên đăng nhập '{new_user}' đã tồn tại trong hệ thống. Vui lòng chọn tên khác!")

    # Chặn hoàn toàn không hiển thị Sidebar hay Main App khi chưa đăng nhập thành công
    st.stop()


# ==========================================
# 3. KHI ĐĂNG NHẬP THÀNH CÔNG: PHÂN TÁCH DỮ LIỆU
# ==========================================
raw_session_user = st.session_state.get("username")
if not raw_session_user or not str(raw_session_user).strip():
    raw_session_user = "mavis"
current_username = str(raw_session_user).strip().lower()
current_name = st.session_state.get("name") or current_username.capitalize()

# Khởi tạo các biến Session State riêng biệt cho từng User
msg_key = f"messages_{current_username}"
OPENING_GREETING = (
    "Chào bạn! Tôi là Elite Executive & Life Coach độc quyền của bạn. "
    "Hiện tại hồ sơ chiến lược của bạn đang hoàn toàn trống. "
    "Bạn muốn chúng ta bắt đầu bằng việc xây dựng khía cạnh nào trước (Sự nghiệp, Sức khỏe, Tài chính...), và mục tiêu lớn nhất hiện tại của bạn là gì?"
)
if msg_key not in st.session_state:
    st.session_state[msg_key] = [
        {
            "role": "assistant",
            "content": OPENING_GREETING,
        }
    ]

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

goal_profile_key = f"goal_profile_{current_username}"
if goal_profile_key not in st.session_state:
    st.session_state[goal_profile_key] = load_user_goal_profile(current_username)

resources_key = f"resources_{current_username}"
if resources_key not in st.session_state:
    st.session_state[resources_key] = load_user_resources(current_username)

roadmap_key = f"roadmap_{current_username}"
if roadmap_key not in st.session_state:
    st.session_state[roadmap_key] = load_user_roadmap(current_username)

# Khởi tạo graph = build_graph() trong st.session_state duy nhất 1 lần
if "mavis_graph" not in st.session_state:
    st.session_state["mavis_graph"] = build_graph()
mavis_agent = st.session_state["mavis_graph"]


# ==========================================
# 4. SIDEBAR: BẢNG ĐIỀU KHIỂN RIÊNG BIỆT CỦA USER
# ==========================================
with st.sidebar:
    st.markdown("## ⚡ Executive Control Center")
    st.caption("Bảng chỉ huy nhịp sinh học & kế hoạch hành động")

    # Hiển thị thông tin định danh người dùng & nút Logout
    st.markdown(
        f"""
        <div class="user-badge">
            <div style="font-size:0.8em; text-transform:uppercase; letter-spacing:1px; opacity:0.8;">Tài khoản đăng nhập</div>
            <div style="font-size:1.15em; font-weight:bold; margin-top:2px;">{current_name}</div>
            <div style="font-size:0.85em; opacity:0.9;"><code>@{current_username}</code> | SaaS Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        authenticator.logout(button_name="🚪 Đăng Xuất (Logout)", location="sidebar", key="sidebar_logout_btn")
    except Exception as e:
        if st.sidebar.button("🚪 Đăng Xuất (Fallback)", key="fallback_logout"):
            st.session_state["authentication_status"] = None
            st.session_state["username"] = None
            st.session_state["name"] = None
            st.rerun()

    st.markdown("---")

    # Hồ sơ mục tiêu có cấu trúc (Goal Profile - Phase 11 Multi-Agent)
    current_gp = safe_dict(st.session_state.get(goal_profile_key))
    with st.expander("🎯 Hồ Sơ Mục Tiêu (Real-time)", expanded=True):
        if current_gp.get("goal_name"):
            st.markdown(f"**Mục tiêu:** `{current_gp.get('goal_name')}`")
            st.markdown(f"**Vạch xuất phát:** {current_gp.get('current_level') or 'Chưa rõ'}")
            st.markdown(f"**Thời hạn:** {current_gp.get('duration_days') or 'N/A'} ngày")
            st.markdown(f"**Quỹ thời gian:** {current_gp.get('daily_hours') or 'N/A'}h/ngày")
            st.markdown(f"**Khung giờ:** {current_gp.get('preferred_slots') or 'Linh hoạt'}")

            if current_gp.get("is_complete"):
                st.success("✅ **ĐÃ CHỐT HOÀN THIỆN**")
            else:
                missing = []
                if not current_gp.get("goal_name"): missing.append("Mục tiêu")
                if not current_gp.get("current_level"): missing.append("Trình độ hiện tại")
                if not current_gp.get("duration_days"): missing.append("Thời gian thực hiện")
                if not current_gp.get("daily_hours"): missing.append("Số giờ rảnh mỗi ngày")
                if not current_gp.get("preferred_slots"): missing.append("Khung giờ học")
                st.warning(f"⚠️ **Đang thiếu:** {', '.join(missing)}")
        else:
            st.caption("Chưa có hồ sơ mục tiêu. Nhập vào ô chat để bắt đầu!")

    # Kho tài liệu (resources) trên Sidebar
    current_res = safe_list(st.session_state.get(resources_key))
    if current_res:
        with st.expander("📚 Kho Tài Liệu (Link nhanh)", expanded=False):
            for r in current_res:
                r_dict = safe_dict(r)
                title = r_dict.get("title", "Tài liệu")
                url = r_dict.get("url", "#")
                rtype = r_dict.get("type", "Tài liệu")
                st.markdown(f"- 🔗 [{title}]({url}) *({rtype})*")

    # Hồ sơ cá nhân đa khía cạnh (User Profile)
    user_prof = st.session_state[profile_key]
    if user_prof.get("is_onboarded"):
        with st.expander("👤 Hồ Sơ Chiến Lược Cá Nhân", expanded=False):
            st.markdown(f"**Tình trạng:** {user_prof.get('current_situation', 'N/A')}")
            st.markdown(f"**Thời gian:** {user_prof.get('time_constraints', 'N/A')}")
            st.markdown(f"**Tài chính:** {user_prof.get('financial_status', 'N/A')}")
            if user_prof.get("obstacles"):
                obs_list = user_prof.get("obstacles")
                obs_disp = ", ".join(obs_list) if isinstance(obs_list, list) else str(obs_list)
                st.markdown(f"**Rào cản:** {obs_disp}")
            st.markdown(f"**Giai đoạn:** `{user_prof.get('coaching_stage', 'action').upper()}`")
    else:
        st.warning("⚠️ Chưa hoàn thành Onboarding! Hãy chat để hoàn thiện hồ sơ.")

    # Bảng điều khiển năng lượng
    st.subheader("🔋 Bảng điều khiển Năng lượng")
    energy = st.session_state[energy_key]

    if energy == "high":
        st.success("🟢 **NĂNG LƯỢNG ĐỈNH CAO (HIGH)**")
        st.markdown(
            """
            * **Khung giờ vàng:** 08:00 - 10:00 Sáng
            * **Trạng thái:** Tối ưu tải nhận thức cao
            * **Ưu tiên:** Giải đề thi, tư duy logic, nghiên cứu thuật toán
            """
        )
    else:
        st.warning("🟠 **NĂNG LƯỢNG GIẢM / HẠ TẢI (LOW)**")
        st.markdown(
            """
            * **Khung giờ:** Buổi chiều (sau 14:00) hoặc phát hiện quá tải
            * **Trạng thái:** Cần nghỉ ngơi hoặc tác vụ nhẹ
            * **Hành động:** Pomodoro 15 phút, review tài liệu nhẹ
            """
        )

    # Hiển thị cảm xúc và ý định nhận diện
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:0.85em; color:#94a3b8;">CẢM XÚC NHẬN DIỆN</div>
            <div style="font-size:1.1em; font-weight:bold; margin-top:4px;">{st.session_state[emotion_key].upper()}</div>
            <div style="font-size:0.85em; color:#94a3b8; margin-top:8px;">Ý ĐỊNH XỬ LÝ (INTENT)</div>
            <div style="font-size:1.0em; font-weight:600; color:#38bdf8;">{st.session_state[intent_key].upper()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Lịch trình dự kiến (Scheduled Plan)
    st.subheader("📅 Lịch trình dự kiến")
    current_plan = st.session_state[plan_key]
    if not current_plan:
        st.info("Chưa có task nào được lập. Hãy chat yêu cầu ôn tập để Coach tự động phân rã vào giờ vàng!")
    else:
        for idx, task in enumerate(current_plan, 1):
            is_deferred = task.get("status") == "deferred_to_tomorrow"
            cog_load = str(task.get("cognitive_load", "")).lower()
            category = str(task.get("category", "")).lower()
            t_title = str(task.get("title", "")).lower()
            is_habit = cog_load == "habit_stacking" or bool(task.get("combined_with"))
            is_high = cog_load == "high"

            if is_deferred:
                card_class = "task-card-deferred"
                badge_class = "badge-deferred"
                badge_text = "⏸️ DỜI SANG MAI (BẢO VỆ NĂNG LƯỢNG)"
            elif cog_load in ["recovery_buffer", "recovery"]:
                card_class = "task-card-recovery"
                badge_class = "badge-recovery"
                badge_text = "🍃 RECOVERY BUFFER (PHỤC HỒI)"
            elif cog_load in ["physical", "cardio", "workout"] or "chạy bộ" in t_title:
                card_class = "task-card-physical"
                badge_class = "badge-physical"
                badge_text = "🏃 THỂ CHẤT & VÓC DÁNG (CARDIO 30P)"
            elif category == "relationships" or "gia đình" in t_title or "cơm tối" in t_title:
                card_class = "task-card-relationship"
                badge_class = "badge-relationship"
                badge_text = "🤝 GIA ĐÌNH & MỐI QUAN HỆ"
            elif is_habit:
                card_class = "task-card-habit"
                badge_class = "badge-habit"
                badge_text = "🎧 HABIT STACKING (KẾT HỢP SINH HOẠT)"
            elif is_high:
                card_class = "task-card-high"
                badge_class = "badge-high"
                badge_text = "🔥 HIGH LOAD (GIỜ VÀNG)"
            else:
                card_class = "task-card-low"
                badge_class = "badge-low"
                badge_text = "🍃 LOW LOAD (HẠ NHIỆT)"

            platform = task.get("platform_or_resource") or "Hệ thống"
            combined_html = f"<div style='font-size:0.8em; color:#a5f3fc; margin-top:2px;'>🧺 Kết hợp: {task.get('combined_with')}</div>" if task.get("combined_with") else ""
            note_html = f"<div style='font-size:0.75em; opacity:0.8; font-style:italic; margin-top:2px;'>💡 {task.get('note')}</div>" if task.get("note") else ""

            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="{badge_class}">{badge_text} | {task.get('time_slot', 'N/A')}</div>
                    <div style="font-weight:bold; font-size:1.0em; margin-top:4px;">{task.get('title', 'Task')}</div>
                    <div style="font-size:0.8em; opacity:0.8; margin-top:2px;">📍 Nền tảng: {platform}</div>
                    {combined_html}
                    {note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Ngữ cảnh RAG đã tải lên (Knowledge Base Context)
    if st.session_state.get(rag_key):
        with st.expander("📚 Tri thức RAG Tải lên (Knowledge Base)", expanded=False):
            st.markdown(st.session_state[rag_key])

    # BỘ NHỚ THÍCH NGHI (ADAPTIVE MEMORY - PHASE 10)
    user_insights = load_historical_insights(username=current_username)
    failed_methods = user_insights.get("failed_methods", [])
    effective_methods = user_insights.get("effective_methods", [])
    productivity_patterns = user_insights.get("productivity_patterns", [])
    has_insights = bool(failed_methods or effective_methods or productivity_patterns)

    with st.expander("🧠 Bộ Nhớ Thích Nghi (Adaptive Memory)", expanded=has_insights):
        st.caption("AI Life Coach học hỏi từ trải nghiệm thực tế để cá nhân hóa chiến lược trọn đời:")
        
        st.markdown("**❌ Phương pháp đã thất bại / Bỏ cuộc (failed_methods):**")
        if failed_methods:
            for f in failed_methods:
                st.markdown(f"- 🛑 <span style='color:#fca5a5;'>{f}</span>", unsafe_allow_html=True)
        else:
            st.caption("*(Chưa ghi nhận thất bại - Hệ thống đang quan sát)*")

        st.markdown("**✅ Phương pháp hiệu quả cao (effective_methods):**")
        if effective_methods:
            for e in effective_methods:
                st.markdown(f"- ⭐ <span style='color:#86efac;'>{e}</span>", unsafe_allow_html=True)
        else:
            st.caption("*(Chưa ghi nhận)*")

        st.markdown("**⚡ Quy luật Năng suất Sinh học (productivity_patterns):**")
        if productivity_patterns:
            for p in productivity_patterns:
                st.markdown(f"- ⏰ <span style='color:#38bdf8;'>{p}</span>", unsafe_allow_html=True)
        else:
            st.caption("*(Chưa ghi nhận)*")

    # Kho Mục Tiêu & Tài Nguyên CỦA RIÊNG USER ĐANG ĐĂNG NHẬP (Tree Hierarchy)
    st.subheader(f"🎯 Mục Tiêu Của {current_name}")
    categorized_goals = load_categorized_goals(username=current_username)

    tabs = st.tabs(["💼 Sự Nghiệp", "🤝 Mối Quan Hệ", "🧘 Sức Khỏe", "✨ Sắc Vóc"])
    category_keys = ["career", "relationships", "health", "beauty"]

    for tab, cat_key in zip(tabs, category_keys):
        with tab:
            goals_in_cat = categorized_goals.get(cat_key, [])
            if isinstance(goals_in_cat, dict):
                goals_in_cat = goals_in_cat.get("children", [])
            if not goals_in_cat:
                st.caption("Chưa có mục tiêu trong Root Node này.")
            else:
                for g in goals_in_cat:
                    if not isinstance(g, dict):
                        continue
                    g_st = g.get("status", "in_progress")
                    if g_st == "in_progress":
                        status_badge = "🟢"
                    elif g_st == "paused_until_ielts_done":
                        status_badge = "⏸️ [Tạm hoãn chờ IELTS]"
                    elif g_st == "completed":
                        status_badge = "✅"
                    else:
                        status_badge = "⏳"

                    score_info = f" • Khả thi: {g.get('feasibility_score')}/100" if g.get("feasibility_score") else ""
                    prio_info = f" • {g.get('priority')}" if g.get("priority") else ""

                    with st.expander(f"{status_badge} {g.get('title')}{score_info}", expanded=False):
                        st.caption(f"⏱️ Deadline: **{g.get('deadline')}**{prio_info} | Trạng thái: `{g_st}`")
                        if g.get("total_estimated_hours"):
                            st.caption(f"⏳ Dự toán: **{g.get('total_estimated_hours')} giờ** *(Cam kết: {g.get('recommended_hours_per_week', 6)}h/tuần)*")

                        if g.get("feasibility_analysis"):
                            st.markdown(f"> 🔍 *Nhận định:* {g.get('feasibility_analysis')}")

                        leaf_nodes = g.get("leaf_nodes") or g.get("milestones", [])
                        if leaf_nodes:
                            st.markdown("**🌿 Cột mốc Leaf Nodes & Ràng buộc (Dependencies):**")
                            for idx, leaf in enumerate(leaf_nodes, 1):
                                l_st = leaf.get("status", "pending")
                                if l_st == "in_progress":
                                    m_status = "🟢"
                                elif l_st == "paused_until_ielts_done":
                                    m_status = "⏸️ [Hoãn]"
                                elif l_st == "completed":
                                    m_status = "✅"
                                else:
                                    m_status = "⏳"
                                m_title = leaf.get("title") or leaf.get("milestone", f"Cột mốc {idx}")
                                m_time = leaf.get("deadline") or leaf.get("timeline", "N/A")
                                m_hours = f" ({leaf.get('estimated_hours')}h)" if leaf.get("estimated_hours") else ""
                                m_dep = f" *[🔗 Ràng buộc: {', '.join(leaf.get('dependencies', []))}]*" if leaf.get("dependencies") else ""
                                st.markdown(f"- {m_status} **{m_title}** [{m_time}]{m_hours}{m_dep}")

                        resources = g.get("resources", [])
                        if resources:
                            st.markdown("**📚 Tài nguyên & Báo giá:**")
                            for r in resources:
                                url_target = r.get("url", "#")
                                res_type = r.get("type", "Resource")
                                cost_str = f" | 💵 `{r.get('estimated_cost')}`" if r.get("estimated_cost") else ""
                                st.markdown(f"- 🔗 [{r.get('title')}]({url_target}) *({res_type})*{cost_str}")

    st.markdown("---")
    if st.button("🔄 Làm mới phiên trò chuyện (Reset)", use_container_width=True):
        st.session_state[thread_ver_key] = st.session_state.get(thread_ver_key, 1) + 1
        st.session_state[msg_key] = [
            {
                "role": "assistant",
                "content": OPENING_GREETING,
            }
        ]
        st.session_state[energy_key] = "high"
        st.session_state[emotion_key] = "neutral"
        st.session_state[intent_key] = "chat"
        st.session_state[plan_key] = []
        st.session_state[pending_goal_key] = None
        st.session_state[awaiting_confirmation_key] = False
        st.session_state[goal_profile_key] = {}
        st.session_state[goals_key] = []
        st.session_state[resources_key] = []
        st.session_state[roadmap_key] = {}
        st.session_state[profile_key] = {
            "current_situation": "",
            "financial_status": "",
            "time_constraints": "",
            "is_onboarded": False,
        }
        st.rerun()


# ==========================================
# 5. MAIN PANEL: BẢNG CHỈ HUY & GIAO DIỆN HỘI THOẠI
# ==========================================
st.title("🤖 Mavis AI Executive & Life Coach")
st.markdown(
    f"**Không gian làm việc:** `{current_name}` (`@{current_username}`) | Tối ưu hóa nhịp sinh học • Phản biện chi phí cơ hội • Đa người dùng SaaS"
)

# 4 Tab Trực quan hiển thị dữ liệu real-time từ State
tab_chat, tab_profile, tab_resources, tab_roadmap = st.tabs([
    "💬 Trò Chuyện & Coaching",
    "🎯 Hồ Sơ Mục Tiêu",
    "📚 Kho Tài Liệu Thẩm Định",
    "🗺️ Lộ Trình Backcasting",
])

with tab_chat:
    # Hiển thị các tin nhắn trong phiên trò chuyện
    for msg in st.session_state[msg_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

with tab_profile:
    st.markdown("### 🎯 Hồ Sơ Đa Mục Tiêu Song Song (Multi-Goal Portfolio)")
    goals_list = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))
    if not goals_list:
        p_dict = safe_dict(st.session_state.get(goal_profile_key))
        if p_dict.get("goal_name"):
            goals_list = [p_dict]

    if goals_list:
        # Hàng thống kê tổng quan
        total_g = len(goals_list)
        comp_g = sum(1 for g in goals_list if safe_dict(g).get("is_complete"))
        total_hrs = sum(float(safe_dict(g).get("daily_hours") or 0) for g in goals_list)
        cats = list(set(safe_dict(g).get("category", "Học tập") for g in goals_list))

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Tổng Số Mục Tiêu", f"{total_g} mục tiêu")
        with m2:
            st.metric("Mục Tiêu Đã Chốt", f"{comp_g}/{total_g}")
        with m3:
            st.metric("Tổng Quỹ Thời Gian", f"{total_hrs:.1f} h/ngày")
        with m4:
            st.metric("Lĩnh Vực", ", ".join(cats) if cats else "Đa lĩnh vực")

        st.markdown("---")
        st.markdown("#### 📋 Danh Sách Mục Tiêu Chi Tiết:")

        for idx, g in enumerate(goals_list, 1):
            g_dict = safe_dict(g)
            g_name = g_dict.get("goal_name", f"Mục tiêu {idx}")
            cat = g_dict.get("category", "Học tập")
            prio = g_dict.get("priority", "medium")
            level = g_dict.get("current_level") or "Chưa rõ"
            days = g_dict.get("duration_days") or "N/A"
            hrs = g_dict.get("daily_hours") or "N/A"
            slots = g_dict.get("preferred_slots") or "Tối ưu theo nhịp sinh học"
            is_comp = g_dict.get("is_complete", False)

            prio_badge = "🔥 High Priority" if prio == "high" else ("⚡ Medium" if prio == "medium" else "🌱 Low Priority")
            status_badge = "✅ ĐÃ CHỐT CHIẾN LƯỢC" if is_comp else "⚠️ CHƯA HOÀN THIỆN"

            with st.container(border=True):
                col_title, col_status = st.columns([3, 2])
                with col_title:
                    st.markdown(f"### 🎯 #{idx}: {g_name} `({cat})`")
                    st.caption(f"Mức ưu tiên: `{prio_badge}`")
                with col_status:
                    if is_comp:
                        st.success(f"{status_badge}")
                    else:
                        st.warning(f"{status_badge}")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Vạch Xuất Phát", level)
                with c2:
                    st.metric("Thời Hạn", f"{days} ngày" if days != "N/A" else "Chưa rõ")
                with c3:
                    st.metric("Cam Kết", f"{hrs} h/ngày" if hrs != "N/A" else "Chưa rõ")
                with c4:
                    st.metric("Khung Giờ", slots[:18] + "..." if len(str(slots)) > 18 else str(slots))

                if not is_comp:
                    missing = []
                    if not g_dict.get("goal_name"): missing.append("Tên mục tiêu cụ thể")
                    if not g_dict.get("current_level"): missing.append("Trình độ / vạch xuất phát")
                    if not g_dict.get("duration_days"): missing.append("Thời gian hoàn thành (ngày)")
                    if not g_dict.get("daily_hours"): missing.append("Số giờ cam kết mỗi ngày")
                    st.info(f"💡 Đang thiếu thông số: **{', '.join(missing)}**. Bạn hãy trao đổi thêm trong tab **Trò Chuyện & Coaching** để Coach chốt mục tiêu này!")
    else:
        st.info("💡 Bạn chưa thiết lập mục tiêu nào. Hãy vào tab **Trò Chuyện & Coaching** và chia sẻ các mục tiêu của bạn (ví dụ: *'Tôi vừa muốn học IELTS 7.0 trong 3 tháng, vừa muốn học HSK 4 trong 6 tháng, vừa build dự án AI'*).")

with tab_resources:
    st.markdown("### 📚 Kho Tài Liệu & Công Cụ Thực Tế Đã Thẩm Định")
    res_list = safe_list(st.session_state.get(resources_key))
    if res_list:
        for idx, r in enumerate(res_list, 1):
            r_dict = safe_dict(r)
            title = r_dict.get("title", f"Tài liệu {idx}")
            url = r_dict.get("url", "#")
            rtype = r_dict.get("type", "Tài liệu học tập")
            hours = r_dict.get("estimated_hours", "N/A")
            how_to = r_dict.get("how_to_use", "Học tập và giải bài tập theo lộ trình đề ra.")
            g_tag = f"🎯 `[{r_dict.get('goal_name')}]` " if r_dict.get("goal_name") else ""

            with st.container(border=True):
                st.markdown(f"#### 🔗 {g_tag}[{title}]({url})")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.caption(f"🏷️ Phân loại: **{rtype}** | ⏳ Thời lượng: **{hours}h**")
                with c2:
                    st.caption(f"💡 Hướng dẫn: {how_to}")
    else:
        st.info("💡 Chưa có tài liệu nào được trích xuất. Khi các mục tiêu được chốt đầy đủ 4 thông số cốt lõi, Agent Research sẽ tự động tìm kiếm các bộ đề, giáo trình uy tín kèm link trực tiếp tại đây!")

with tab_roadmap:
    st.markdown("### 🗺️ Lộ Trình Backcasting & Kế Hoạch Đa Mục Tiêu")
    roadmap_dict = safe_dict(st.session_state.get(roadmap_key))
    goals_list = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))
    if not goals_list:
        p_dict = safe_dict(st.session_state.get(goal_profile_key))
        if p_dict.get("goal_name"):
            goals_list = [p_dict]

    if roadmap_dict and (roadmap_dict.get("target_vision") or roadmap_dict.get("weekly_milestones")):
        st.info(f"🎯 **Tầm nhìn Chiến lược:** {roadmap_dict.get('target_vision', 'Chinh phục toàn diện các mục tiêu')}")
        if roadmap_dict.get("total_phases"):
            st.markdown(f"**Phân kỳ Quý / Tháng:** {roadmap_dict.get('total_phases')}")

        if roadmap_dict.get("balance_strategy"):
            st.success(f"⚖️ **Chiến lược cân bằng nhịp sinh học & Quỹ thời gian ({roadmap_dict.get('total_daily_hours', 'N/A')}h/ngày):** {roadmap_dict.get('balance_strategy')}")

        st.markdown("---")

        # Bộ lọc mục tiêu cho Lộ trình Backcasting
        goal_names = [safe_dict(g).get("goal_name") for g in goals_list if safe_dict(g).get("goal_name")]
        filter_options = ["🎯 Tất cả mục tiêu"] + goal_names
        selected_goal_filter = st.selectbox(
            "🔍 Lọc Lộ Trình & Nhiệm Vụ Theo Mục Tiêu:",
            options=filter_options,
            index=0,
            help="Chọn mục tiêu cụ thể để theo dõi chi tiết các task hành động của mục tiêu đó mà không bị phân tán."
        )

        st.markdown("---")

        # Nút Đồng bộ Google Calendar
        st.subheader("📅 Đồng Bộ Lịch Trình (Google Calendar & iCal)")
        w_ms = safe_list(roadmap_dict.get("weekly_milestones", []))
        w1_tasks = safe_list(safe_dict(w_ms[0]).get("daily_tasks", [])) if w_ms else []
        d1 = safe_dict(w1_tasks[0]) if w1_tasks else {}
        d1_title = d1.get("task_title", "Bắt đầu kế hoạch hành động")
        d1_dur = d1.get("duration_minutes", 90)
        d1_res = d1.get("attached_resource", "")
        d1_slot = d1.get("time_slot", "08:00 - 10:00")

        col_gcal, col_ics = st.columns(2)
        with col_gcal:
            gcal_url = generate_gcal_link(d1_title, d1_slot, d1_dur, d1_res)
            st.link_button("🌐 Mở Google Calendar (Thêm Ngày 1)", url=gcal_url, use_container_width=True)

        with col_ics:
            goal_label = selected_goal_filter if selected_goal_filter != "🎯 Tất cả mục tiêu" else "Đa Mục Tiêu"
            ics_data = generate_ics_calendar(roadmap_dict, goal_label, d1_slot)
            st.download_button(
                label="📥 Tải File Lịch (.ics) Cho Google / Apple / Outlook",
                data=ics_data,
                file_name=f"mavis_schedule_{current_username}.ics",
                mime="text/calendar",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown(f"#### 🚩 Chi Tiết Cột Mốc Từng Tuần & Nhiệm Vụ Hàng Ngày ({selected_goal_filter}):")

        for w in w_ms:
            w_dict = safe_dict(w)
            w_num = w_dict.get("week_number", 1)
            w_title = w_dict.get("milestone_title", f"Tuần {w_num}")
            all_daily_tasks = safe_list(w_dict.get("daily_tasks", []))

            # Áp dụng bộ lọc mục tiêu
            if selected_goal_filter != "🎯 Tất cả mục tiêu":
                target_norm = selected_goal_filter.lower().strip()
                filtered_daily_tasks = [
                    t for t in all_daily_tasks
                    if target_norm in safe_dict(t).get("goal_name", "").lower()
                    or target_norm in safe_dict(t).get("task_title", "").lower()
                ]
            else:
                filtered_daily_tasks = all_daily_tasks

            with st.expander(f"📌 Tuần {w_num}: {w_title} ({len(filtered_daily_tasks)} nhiệm vụ)", expanded=(w_num == 1)):
                if filtered_daily_tasks:
                    for t in filtered_daily_tasks:
                        t_dict = safe_dict(t)
                        day_num = t_dict.get("day_number", 1)
                        t_goal = t_dict.get("goal_name", "")
                        t_title = t_dict.get("task_title", "")
                        t_dur = t_dict.get("duration_minutes", 60)
                        t_slot = t_dict.get("time_slot", "08:00 - 10:00")
                        t_res = t_dict.get("attached_resource", "Tài liệu chuẩn")
                        cog = t_dict.get("cognitive_load", "medium")

                        cog_badge = "🔥 High Load" if cog == "high" else ("⚡ Medium" if cog == "medium" else "🌱 Low Load")
                        goal_tag = f"`[🎯 {t_goal}]` " if t_goal else ""
                        st.markdown(
                            f"- **Ngày {day_num}:** {goal_tag}**{t_title}**\n"
                            f"  *Khung giờ:* `{t_slot}` ({t_dur} phút) | `{cog_badge}` | 📖 *Tài liệu:* {t_res}"
                        )
                else:
                    st.caption(f"Không có nhiệm vụ nào thuộc mục tiêu '{selected_goal_filter}' trong tuần này.")
    else:
        st.info("💡 Lộ trình Backcasting chưa được khởi tạo. Sau khi bạn cung cấp đủ thông số các mục tiêu, Agent Strategic Planner sẽ tự động phân rã lộ trình cân bằng tại đây!")

# Khung nhập tin nhắn (nằm bên dưới các tab để điều hướng mượt mà)
if user_input := st.chat_input("Nhập mục tiêu hoặc trao đổi cùng Coach (VD: 'Tôi muốn học Data Science trong 3 tháng', 'Thiết lập mục tiêu chạy bộ')..."):
    # 1. Thêm tin nhắn của User vào giao diện
    st.session_state[msg_key].append({"role": "user", "content": user_input})

    # 2. Chuẩn bị input cho LangGraph Agent với định danh username
    active_username = (st.session_state.get("username") or current_username or "mavis").strip().lower()

    # Chuyển đổi toàn bộ lịch sử trao đổi trong phiên thành HumanMessage / AIMessage để bảo toàn ngữ cảnh trọn vẹn
    full_messages = []
    for m in st.session_state.get(msg_key, []):
        m_role = m.get("role")
        m_content = m.get("content", "")
        if m_role == "user":
            full_messages.append(HumanMessage(content=m_content))
        elif m_role == "assistant":
            full_messages.append(AIMessage(content=m_content))
    if not full_messages:
        full_messages = [HumanMessage(content=user_input)]

    input_state = {
        "messages": full_messages,
        "goals": safe_list(st.session_state.get(goals_key) or load_user_goals(active_username)),
        "profile": safe_dict(st.session_state.get(goal_profile_key) or load_user_goal_profile(active_username)),
        "resources": safe_list(st.session_state.get(resources_key) or load_user_resources(active_username)),
        "roadmap": safe_dict(st.session_state.get(roadmap_key) or load_user_roadmap(active_username)),
        "current_energy_level": st.session_state.get(energy_key, "high"),
        "detected_emotion": st.session_state.get(emotion_key, "neutral"),
        "intent": st.session_state.get(intent_key, "chat"),
        "plan": st.session_state.get(plan_key, []),
        "user_profile": st.session_state.get(profile_key, {}),
        "coaching_stage": st.session_state.get(stage_key, "interviewing"),
        "user_obstacles": st.session_state.get(obstacles_key, []),
        "status": st.session_state.get(f"status_{active_username}", "interviewing"),
        "is_info_sufficient": False,
        "uploaded_context": st.session_state.get(rag_key),
        "username": active_username,
        "user_id": active_username,
        "pending_goal": st.session_state.get(pending_goal_key),
        "awaiting_confirmation": st.session_state.get(awaiting_confirmation_key, False),
    }

    # 3. Kích hoạt Agent xử lý
    with st.chat_message("assistant"):
        with st.spinner(f"Executive Coach đang phân tích dữ liệu cho {current_name}..."):
            try:
                # Cấu hình thread_id cố định theo phiên người dùng (st.session_state.username)
                thread_user = getattr(st.session_state, "username", None) or active_username
                config = {"configurable": {"thread_id": thread_user}}
                output_state = mavis_agent.invoke(input_state, config=config)

                # Dọn dẹp hiển thị UI: Gom tất cả các phản hồi AI mới được sinh ra trong lượt này (sau tin nhắn của user)
                new_ai_texts = []
                all_msgs = output_state.get("messages", [])

                last_user_idx = -1
                for idx, m in enumerate(all_msgs):
                    if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human" or (isinstance(m, dict) and m.get("role") == "user"):
                        last_user_idx = idx

                if last_user_idx >= 0:
                    for m in all_msgs[last_user_idx + 1:]:
                        if isinstance(m, AIMessage) or getattr(m, "type", "") == "ai":
                            c = extract_text_from_content(getattr(m, "content", m))
                            if c and c.strip() and c.strip() != user_input.strip() and c.strip() not in new_ai_texts:
                                new_ai_texts.append(c.strip())
                        elif isinstance(m, dict) and m.get("role") == "assistant":
                            c = extract_text_from_content(m.get("content", ""))
                            if c and c.strip() and c.strip() != user_input.strip() and c.strip() not in new_ai_texts:
                                new_ai_texts.append(c.strip())

                if new_ai_texts:
                    combined_reply = "\n\n---\n\n".join(new_ai_texts)
                else:
                    last_reply = None
                    for msg in reversed(all_msgs):
                        if isinstance(msg, AIMessage) or getattr(msg, "type", "") == "ai":
                            c = extract_text_from_content(getattr(msg, "content", msg))
                            if c and c.strip() and c.strip() != user_input.strip():
                                last_reply = c
                                break
                    if not last_reply:
                        if chat_node is not None:
                            input_state["username"] = active_username
                            chat_fallback = chat_node(input_state)
                            last_reply = extract_text_from_content(chat_fallback["messages"][-1].content)
                        else:
                            last_reply = "Chào bạn! Tôi đã ghi nhận mục tiêu của bạn và đang thiết lập lộ trình."
                    combined_reply = last_reply

                st.markdown(combined_reply)

                # Lưu vào lịch sử hiển thị của user
                st.session_state[msg_key].append(
                    {"role": "assistant", "content": combined_reply}
                )

                # Cập nhật các trạng thái của Agent vào session_state của user và MongoDB Atlas (collection 'user_states')
                if "goals" in output_state and output_state["goals"]:
                    st.session_state[goals_key] = output_state["goals"]
                    save_user_goals(output_state["goals"], username=active_username)
                    if output_state["goals"]:
                        st.session_state[goal_profile_key] = output_state["goals"][0]

                if "profile" in output_state and output_state["profile"]:
                    st.session_state[goal_profile_key] = output_state["profile"]
                    save_user_goal_profile(output_state["profile"], username=active_username)

                if "resources" in output_state and output_state["resources"]:
                    st.session_state[resources_key] = output_state["resources"]
                    save_user_resources(output_state["resources"], username=active_username)

                if "roadmap" in output_state and output_state["roadmap"]:
                    st.session_state[roadmap_key] = output_state["roadmap"]
                    save_user_roadmap(output_state["roadmap"], username=active_username)

                if "schedule" in output_state and output_state["schedule"]:
                    st.session_state[f"schedule_{active_username}"] = output_state["schedule"]

                if "user_profile" in output_state and output_state["user_profile"]:
                    st.session_state[profile_key] = output_state["user_profile"]
                    save_user_profile(output_state["user_profile"], username=active_username)

                if "coaching_stage" in output_state and output_state["coaching_stage"]:
                    st.session_state[stage_key] = output_state["coaching_stage"]

                if "user_obstacles" in output_state and output_state["user_obstacles"]:
                    st.session_state[obstacles_key] = output_state["user_obstacles"]

                if "status" in output_state and output_state["status"]:
                    st.session_state[f"status_{active_username}"] = output_state["status"]

                if "current_energy_level" in output_state:
                    st.session_state[energy_key] = output_state["current_energy_level"]

                if "detected_emotion" in output_state and output_state["detected_emotion"]:
                    st.session_state[emotion_key] = output_state["detected_emotion"]

                if "intent" in output_state and output_state["intent"]:
                    st.session_state[intent_key] = output_state["intent"]

                if "plan" in output_state and output_state["plan"]:
                    st.session_state[plan_key] = output_state["plan"]

                if "uploaded_context" in output_state:
                    st.session_state[rag_key] = output_state["uploaded_context"]

                if "pending_goal" in output_state:
                    st.session_state[pending_goal_key] = output_state["pending_goal"]

                if "awaiting_confirmation" in output_state:
                    st.session_state[awaiting_confirmation_key] = output_state["awaiting_confirmation"]

                # Rerun để Sidebar đồng bộ ngay lập tức các chỉ số mới
                st.rerun()

            except Exception as e:
                error_msg = f"Đã xảy ra lỗi trong quá trình điều phối Agent: {str(e)}"
                st.error(error_msg)
                st.session_state[msg_key].append(
                    {"role": "assistant", "content": error_msg}
                )
