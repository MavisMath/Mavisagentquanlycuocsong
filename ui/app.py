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

# Đảm bảo đường dẫn import tương thích khi chạy streamlit từ mọi thư mục (Local, Docker, Streamlit Cloud)
CURRENT_FILE = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CWD = os.path.abspath(os.getcwd())

for p in [PROJECT_ROOT, CWD, CURRENT_DIR]:
    if p and os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st

# Tự động đồng bộ hóa secrets từ Streamlit Cloud vào biến môi trường hệ thống
try:
    if hasattr(st, "secrets"):
        for _k, _v in st.secrets.items():
            if isinstance(_v, str):
                os.environ[_k] = _v
                if _k == "GEMINI_API_KEY" and "GOOGLE_API_KEY" not in os.environ:
                    os.environ["GOOGLE_API_KEY"] = _v
                if _k in ["MONGO_URI", "MONGODB_URI"]:
                    os.environ["MONGO_URI"] = _v
                    os.environ["MONGODB_URI"] = _v
except Exception:
    pass

# Dọn dẹp cache module cũ trong sys.modules khi Streamlit Cloud reload mã nguồn
import importlib
for _mod in ["memory.goals", "memory.auth", "memory.mongodb", "agents.brain", "agents.graph", "memory", "agents"]:
    if _mod in sys.modules:
        try:
            del sys.modules[_mod]
        except Exception:
            pass
importlib.invalidate_caches()

from langchain_core.messages import HumanMessage, AIMessage

# Khởi tạo an toàn Agent Graph với cơ chế báo lỗi trực quan trên Cloud
try:
    import agents.graph as ag
    importlib.reload(ag)
    build_graph = getattr(ag, "build_graph")
    mavis_agent = getattr(ag, "mavis_agent", None) or build_graph()
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

# Nạp an toàn module memory.goals với importlib.reload dọn sạch cache
try:
    import memory.goals as mg
    importlib.reload(mg)

    load_goals = getattr(mg, "load_goals")
    save_goals = getattr(mg, "save_goals")
    add_goal = getattr(mg, "add_goal")
    update_goal = getattr(mg, "update_goal")
    CATEGORY_LABELS = getattr(mg, "CATEGORY_LABELS", {})
    load_historical_insights = getattr(mg, "load_historical_insights")
    save_historical_insights = getattr(mg, "save_historical_insights")
    load_user_profile = getattr(mg, "load_user_profile")
    save_user_profile = getattr(mg, "save_user_profile")
    load_user_goal_profile = getattr(mg, "load_user_goal_profile")
    save_user_goal_profile = getattr(mg, "save_user_goal_profile")
    load_user_goals = getattr(mg, "load_user_goals")
    save_user_goals = getattr(mg, "save_user_goals")
    load_user_resources = getattr(mg, "load_user_resources")
    save_user_resources = getattr(mg, "save_user_resources")
    load_user_roadmap = getattr(mg, "load_user_roadmap")
    save_user_roadmap = getattr(mg, "save_user_roadmap")
    load_categorized_goals = getattr(mg, "load_categorized_goals")
    save_categorized_goals = getattr(mg, "save_categorized_goals")
    load_master_schedule = getattr(mg, "load_master_schedule")
    save_master_schedule = getattr(mg, "save_master_schedule")
    update_master_schedule_task_status = getattr(mg, "update_master_schedule_task_status")
    load_retrospective_logs = getattr(mg, "load_retrospective_logs")
    save_retrospective_logs = getattr(mg, "save_retrospective_logs")
    append_retrospective_log = getattr(mg, "append_retrospective_log")
    get_user_state_full = getattr(mg, "get_user_state_full")
    update_user_goal_status = getattr(mg, "update_user_goal_status")
    update_user_goal_details = getattr(mg, "update_user_goal_details")
    delete_user_goal = getattr(mg, "delete_user_goal")
except Exception as _goals_import_err:
    import traceback
    st.error(f"⚠️ Cảnh báo nạp module `memory.goals`: {_goals_import_err}")
    with st.expander("Chi tiết kỹ thuật lỗi nạp memory.goals"):
        st.code(traceback.format_exc())

    def load_goals(*args, **kwargs): return []
    def save_goals(*args, **kwargs): return True
    def add_goal(*args, **kwargs): return True
    def update_goal(*args, **kwargs): return True
    CATEGORY_LABELS = {}
    def load_historical_insights(*args, **kwargs): return {}
    def save_historical_insights(*args, **kwargs): return True
    def load_user_profile(*args, **kwargs): return {}
    def save_user_profile(*args, **kwargs): return True
    def load_user_goal_profile(*args, **kwargs): return {}
    def save_user_goal_profile(*args, **kwargs): return True
    def load_user_goals(*args, **kwargs): return []
    def save_user_goals(*args, **kwargs): return True
    def load_user_resources(*args, **kwargs): return []
    def save_user_resources(*args, **kwargs): return True
    def load_user_roadmap(*args, **kwargs): return {}
    def save_user_roadmap(*args, **kwargs): return True
    def load_categorized_goals(*args, **kwargs): return {}
    def save_categorized_goals(*args, **kwargs): return True
    def load_master_schedule(*args, **kwargs): return []
    def save_master_schedule(*args, **kwargs): return True
    def update_master_schedule_task_status(*args, **kwargs): return True
    def load_retrospective_logs(*args, **kwargs): return []
    def save_retrospective_logs(*args, **kwargs): return True
    def append_retrospective_log(*args, **kwargs): return True
    def get_user_state_full(*args, **kwargs): return {}
    def update_user_goal_status(*args, **kwargs): return True
    def update_user_goal_details(*args, **kwargs): return True
    def delete_user_goal(*args, **kwargs): return True

# Nạp an toàn module memory.auth với importlib.reload
try:
    import memory.auth as ma
    importlib.reload(ma)
    get_authenticator = getattr(ma, "get_authenticator", None)
    register_user = getattr(ma, "register_user", None)
except Exception as _auth_import_err:
    import traceback
    st.error(f"⚠️ Cảnh báo nạp module `memory.auth`: {_auth_import_err}")
    with st.expander("Chi tiết kỹ thuật lỗi nạp memory.auth"):
        st.code(traceback.format_exc())
    get_authenticator = None
    register_user = None

# Nạp an toàn module memory.mongodb với importlib.reload
try:
    import memory.mongodb as mm
    importlib.reload(mm)
    is_mongodb_available = getattr(mm, "is_mongodb_available", lambda: False)
    db_update_user_state = getattr(mm, "db_update_user_state", lambda *args, **kwargs: False)
    get_mongo_connection_error = getattr(mm, "get_mongo_connection_error", lambda: None)
    get_mongo_uri = getattr(mm, "get_mongo_uri", lambda: None)
except Exception as _mongo_import_err:
    import traceback
    st.error(f"⚠️ Cảnh báo nạp module `memory.mongodb`: {_mongo_import_err}")
    with st.expander("Chi tiết kỹ thuật lỗi nạp memory.mongodb"):
        st.code(traceback.format_exc())
    def is_mongodb_available(): return False
    def db_update_user_state(*args, **kwargs): return False
    def get_mongo_connection_error(): return str(_mongo_import_err)
    def get_mongo_uri(): return None

# Nạp an toàn 4 Chatbot functions từ agents.brain với importlib.reload
try:
    import agents.brain as ab
    importlib.reload(ab)
    chat_node = getattr(ab, "chat_node", None)
    ceo_coach_chat = getattr(ab, "ceo_coach_chat")
    architect_chat = getattr(ab, "architect_chat")
    scheduler_chat = getattr(ab, "scheduler_chat")
    retrospective_chat = getattr(ab, "retrospective_chat")
except Exception as _brain_err:
    import traceback
    st.error(f"⚠️ Cảnh báo nạp các Chatbot từ `agents.brain`: {_brain_err}")
    with st.expander("Chi tiết kỹ thuật lỗi nạp agents.brain"):
        st.code(traceback.format_exc())
    chat_node = None
    ceo_coach_chat = None
    architect_chat = None
    scheduler_chat = None
    retrospective_chat = None


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


def generate_ics_from_master_schedule(schedule: List[Dict[str, Any]], username: str) -> str:
    """Tạo file lịch chuẩn .ics (iCalendar) từ Master Schedule để import vào Google Calendar, Outlook, Apple Calendar."""
    now = datetime.now()
    now_str = now.strftime("%Y%m%d")
    events = []

    day_map = {
        "thứ hai": 0, "thứ ba": 1, "thứ tư": 2, "thứ năm": 3,
        "thứ sáu": 4, "thứ bảy": 5, "chủ nhật": 6,
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    for idx, item in enumerate(schedule, 1):
        item_dict = safe_dict(item)
        task_title = item_dict.get("task_detail", f"Task {idx}")
        goal_title = item_dict.get("goal_title", "Mục tiêu")
        slot = str(item_dict.get("time_slot", "08:00 - 10:00"))
        date_str = str(item_dict.get("date", "Thứ Hai")).lower().strip()

        target_weekday = day_map.get(date_str, 0)
        curr_weekday = now.weekday()
        days_ahead = (target_weekday - curr_weekday) % 7
        if days_ahead == 0 and now.hour > 18:
            days_ahead = 7
        event_date = now + timedelta(days=days_ahead)
        dt_prefix = event_date.strftime("%Y%m%d")

        start_h, start_m = 8, 0
        end_h, end_m = 10, 0
        if "-" in slot:
            try:
                parts = slot.split("-")
                p1 = parts[0].strip().split(":")
                p2 = parts[1].strip().split(":")
                start_h, start_m = int(p1[0]), int(p1[1])
                end_h, end_m = int(p2[0]), int(p2[1])
            except Exception:
                pass

        dt_start = f"{dt_prefix}T{start_h:02d}{start_m:02d}00"
        dt_end = f"{dt_prefix}T{end_h:02d}{end_m:02d}00"
        res_link = item_dict.get("resource_link", "")

        events.extend([
            "BEGIN:VEVENT",
            f"UID:mavis_ms_{username}_{idx}_{dt_start}@maviscoach.ai",
            f"DTSTAMP:{now_str}T000000Z",
            f"DTSTART:{dt_start}",
            f"DTEND:{dt_end}",
            f"SUMMARY:🎯 [Mavis] {goal_title}: {task_title[:50]}",
            f"DESCRIPTION:Mục tiêu: {goal_title}\\nNhiệm vụ: {task_title}\\nTài liệu: {res_link}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    if not events:
        events.extend([
            "BEGIN:VEVENT",
            f"UID:mavis_ms_{username}_init@maviscoach.ai",
            f"DTSTAMP:{now_str}T000000Z",
            f"DTSTART:{now_str}T080000",
            f"DTEND:{now_str}T100000",
            "SUMMARY:🎯 [Mavis] Khởi động Master Schedule",
            "DESCRIPTION:Lịch trình thực thi cá nhân hóa từ Mavis Coach",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mavis Executive Life Coach//Master Schedule//VN",
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

        if get_mongo_uri() and not is_mongodb_available():
            mongo_err = get_mongo_connection_error()
            if mongo_err and "Chưa cấu hình" not in mongo_err:
                st.error(f"Lỗi kết nối MongoDB: {mongo_err}")

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

# Khởi tạo 4 luồng Chatbot chuyên biệt & Dữ liệu đồng bộ real-time từ MongoDB
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
                f"Chào **{current_name}**! Tôi là **Strategy & Resource Architect** (Chuyên trách Giai đoạn 1).\n\n"
                "Tôi chịu trách nhiệm phân rã mục tiêu thành lộ trình 4 tầng (**Năm ➔ Quý ➔ Tháng ➔ Tuần**) và thẩm định giáo trình/tài liệu chuẩn.\n\n"
                "👉 Bạn có thể yêu cầu tôi đổi giờ học, đổi mức ưu tiên hoặc thêm/bớt tài liệu bất kỳ lúc nào!"
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
    if st.button("🔄 Làm mới phiên làm việc (Reset All)", use_container_width=True):
        st.session_state[thread_ver_key] = st.session_state.get(thread_ver_key, 1) + 1
        st.session_state[msg_key] = [
            {
                "role": "assistant",
                "content": OPENING_GREETING,
            }
        ]
        st.session_state[chat_ceo_key] = [
            {
                "role": "assistant",
                "content": f"Xin chào **{current_name}**! Tôi là **Mavis CEO Coach**. Sẵn sàng thẩm định các mục tiêu mới cùng bạn!",
            }
        ]
        st.session_state[chat_arch_key] = [
            {
                "role": "assistant",
                "content": f"Chào **{current_name}**! Tôi là **Strategy & Resource Architect**. Sẵn sàng hỗ trợ bạn tinh chỉnh lộ trình & tài liệu!",
            }
        ]
        st.session_state[chat_sched_key] = [
            {
                "role": "assistant",
                "content": f"Chào **{current_name}**! Tôi là **AI Master Scheduler**. Sẵn sàng phân bổ và dời lịch trình cho bạn!",
            }
        ]
        st.session_state[chat_retro_key] = [
            {
                "role": "assistant",
                "content": f"Chào **{current_name}**! Tôi là **AI Retrospective Coach**. Sẵn sàng check-in và hồi cứu cùng bạn!",
            }
        ]
        st.session_state[goals_key] = load_user_goals(current_username)
        st.session_state[master_schedule_key] = load_master_schedule(current_username)
        st.session_state[retro_logs_key] = load_retrospective_logs(current_username)
        st.session_state[energy_key] = "high"
        st.session_state[emotion_key] = "neutral"
        st.session_state[intent_key] = "chat"
        st.session_state[plan_key] = []
        st.session_state[pending_goal_key] = None
        st.session_state[awaiting_confirmation_key] = False
        st.session_state[goal_profile_key] = {}
        st.session_state[resources_key] = []
        st.session_state[roadmap_key] = {}
        st.session_state[profile_key] = {
            "current_situation": "",
            "financial_status": "",
            "time_constraints": "",
            "is_onboarded": False,
        }
        st.rerun()

    st.markdown("---")
    # Trạng thái kết nối Cloud Database (MongoDB Atlas)
    if is_mongodb_available():
        st.caption("🟢 **Đã kết nối Cloud DB (MongoDB)**")
    else:
        st.caption("🔴 **Chưa kết nối MongoDB**")
        mongo_err = get_mongo_connection_error()
        if get_mongo_uri() and mongo_err and "Chưa cấu hình" not in mongo_err:
            st.error(f"Lỗi kết nối MongoDB: {mongo_err}")


# ==========================================
# 5. MAIN PANEL: BẢNG CHỈ HUY & GIAO DIỆN HỘI THOẠI
# ==========================================
st.title("🤖 Mavis AI Executive & Life Coach")
st.markdown(
    f"**Không gian làm việc:** `{current_name}` (`@{current_username}`) | Tối ưu hóa nhịp sinh học • Phản biện chi phí cơ hội • Đa người dùng SaaS"
)

# ==========================================
# 5. MAIN PANEL: BẢNG CHỈ HUY 4 GIAI ĐOẠN KHÉP KÍN & 4 CHATBOT CHUYÊN BIỆT
# ==========================================
st.title("🤖 Mavis AI Executive & Life Coach")
st.markdown(
    f"**Không gian làm việc:** `{current_name}` (`@{current_username}`) | Mô hình CEO điều phối 3 giai đoạn khép kín • Tối ưu nhịp sinh học • Đồng bộ Cloud MongoDB"
)

# 4 Tab Chuyên biệt theo Chu trình Điều hành Mavis CEO
tab_ceo, tab_arch, tab_sched, tab_retro = st.tabs([
    "🎙️ Tổng Hành Dinh (CEO Coach)",
    "📐 Giai đoạn 1: Thiết Lập Mục Tiêu",
    "📅 Giai đoạn 2: Thực Thi & Lịch Trình",
    "📊 Giai đoạn 3: Tổng Kết & Cải Thiện",
])

# ------------------------------------------------------------------------------
# TAB 1: 🎙️ TỔNG HÀNH DINH (CEO COACH)
# ------------------------------------------------------------------------------
with tab_ceo:
    st.markdown("### 🎙️ Tổng Hành Dinh Chiến Lược (CEO Coach)")
    st.caption("Thẩm định độ khả thi • Tính toán quỹ thời gian • Bảo vệ nhịp sinh học năng lượng đỉnh cao")

    col_dash, col_chat = st.columns([1.15, 0.85], gap="large")

    with col_dash:
        user_goals = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        evaluating_goals = [g for g in user_goals if safe_dict(g).get("status") == "evaluating"]
        active_goals = [g for g in user_goals if safe_dict(g).get("status") == "active"]

        total_active_hours = sum(float(safe_dict(g).get("daily_hours") or 0) for g in active_goals)
        total_eval_hours = sum(float(safe_dict(g).get("daily_hours") or 0) for g in evaluating_goals)
        total_all_hours = total_active_hours + total_eval_hours

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Đang Thẩm Định", f"{len(evaluating_goals)} mục tiêu")
        with m2:
            st.metric("Đã Kích Hoạt (Active)", f"{len(active_goals)} mục tiêu")
        with m3:
            st.metric("Quỹ Giờ Deep Work", f"{total_active_hours:.1f}h / 5.5h")

        if total_all_hours > 5.5:
            st.warning(
                f"⚠️ **Cảnh báo quá tải ({total_all_hours:.1f}h/ngày):** Vượt ngưỡng an toàn 5.5h/ngày. "
                "CEO Coach khuyến nghị hạ tải hoặc tạm hoãn mục tiêu ít ưu tiên để bảo vệ nhịp sinh học!"
            )
        else:
            st.success(
                f"🔋 **Nhịp sinh học tối ưu:** Quỹ giờ cam kết `{total_active_hours:.1f}h/ngày` "
                "nằm trong vùng năng lượng đỉnh cao an toàn."
            )

        st.markdown("---")
        st.markdown("#### 🔍 Mục Tiêu Đang Thẩm Định Độ Khả Thi:")

        if evaluating_goals:
            for idx, eg in enumerate(evaluating_goals, 1):
                eg_dict = safe_dict(eg)
                gid = eg_dict.get("id") or eg_dict.get("goal_id", f"eval_{idx}")
                g_title = eg_dict.get("title") or eg_dict.get("goal_name", f"Mục tiêu {idx}")
                cat = eg_dict.get("category", "Học tập")
                daily_h = eg_dict.get("daily_hours", 1.5)
                dur_days = eg_dict.get("duration_days", 90)
                pref_t = eg_dict.get("preferred_time") or eg_dict.get("preferred_slots", "08:00 - 10:00 Sáng")

                with st.container(border=True):
                    c_title, c_cat = st.columns([3, 1])
                    with c_title:
                        st.markdown(f"##### 🎯 #{idx}: **{g_title}**")
                    with c_cat:
                        st.caption(f"🏷️ `{cat}`")

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.caption(f"⏳ **Thời lượng:** {daily_h}h/ngày")
                    with c2:
                        st.caption(f"📅 **Thời hạn:** {dur_days} ngày")
                    with c3:
                        st.caption(f"⏰ **Khung giờ:** {str(pref_t)[:18]}")

                    if st.button(
                        "✅ Đồng ý thêm vào Mục tiêu cuộc đời",
                        key=f"btn_approve_{gid}_{idx}",
                        type="primary",
                        use_container_width=True,
                    ):
                        eg["status"] = "active"
                        eg["is_complete"] = True
                        save_user_goals(user_goals, username=current_username)
                        st.session_state[goals_key] = load_user_goals(current_username)
                        st.toast(f"🎉 Đã thêm '{g_title}' vào Mục tiêu cuộc đời!")
                        st.rerun()
        else:
            st.info(
                "💡 Hiện không có mục tiêu nào đang chờ thẩm định. Hãy chia sẻ với **CEO Coach** ở cột bên phải "
                "(ví dụ: *'Tôi muốn học IELTS 7.0 trong 3 tháng, mỗi ngày 2 tiếng'*) để bắt đầu thẩm định mục tiêu mới!"
            )

        st.markdown("---")
        st.markdown("#### 🌟 Mục Tiêu Cuộc Đời Đang Thực Hiện (Active Goals):")
        if active_goals:
            for idx, ag in enumerate(active_goals, 1):
                ag_dict = safe_dict(ag)
                a_title = ag_dict.get("title") or ag_dict.get("goal_name", f"Mục tiêu {idx}")
                a_cat = ag_dict.get("category", "Sự nghiệp")
                a_h = ag_dict.get("daily_hours", 1.5)
                a_prio = ag_dict.get("priority", "P2 - High")
                st.markdown(
                    f"- 🚀 **{a_title}** `({a_cat})` — `{a_h}h/ngày` | Ưu tiên: `{a_prio}` — 🟢 *Active*"
                )
        else:
            st.caption("Chưa có mục tiêu Active nào. Khi mục tiêu được thẩm định khả thi, hãy bấm '✅ Đồng ý' ở trên.")

    with col_chat:
        st.markdown("#### 💬 Trò Chuyện Cùng CEO Coach")
        st.caption("Đánh giá mục tiêu mới • Kiểm tra quỹ giờ • Quản trị nhịp sinh học")

        chat_container_ceo = st.container(height=520)
        with chat_container_ceo:
            for msg in st.session_state[chat_ceo_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if ceo_input := st.chat_input(
            "Nhập mục tiêu mới hoặc thảo luận cùng CEO Coach...",
            key=f"input_ceo_{current_username}",
        ):
            st.session_state[chat_ceo_key].append({"role": "user", "content": ceo_input})
            with chat_container_ceo:
                with st.chat_message("user"):
                    st.markdown(ceo_input)
                with st.chat_message("assistant"):
                    with st.spinner("CEO Coach đang phân tích quỹ thời gian và thẩm định khả thi..."):
                        if ceo_coach_chat is not None:
                            res = ceo_coach_chat(
                                user_message=ceo_input,
                                username=current_username,
                                chat_history=st.session_state[chat_ceo_key],
                            )
                            coach_rep = res.get("response", "Tôi đã ghi nhận mục tiêu của bạn.")
                        else:
                            coach_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(coach_rep)
                        st.session_state[chat_ceo_key].append({"role": "assistant", "content": coach_rep})
                        st.session_state[goals_key] = load_user_goals(current_username)
                        st.rerun()


# ------------------------------------------------------------------------------
# TAB 2: 📐 GIAI ĐOẠN 1: THIẾT LẬP MỤC TIÊU (ARCHITECT)
# ------------------------------------------------------------------------------
with tab_arch:
    st.markdown("### 📐 Giai đoạn 1: Thiết Lập Mục Tiêu & Phân Rã Lộ Trình")
    st.caption("Kiến trúc sư chiến lược phân cấp 4 tầng (Năm ➔ Quý ➔ Tháng ➔ Tuần) & Thẩm định tài liệu thực tế")

    col_dash_arch, col_chat_arch = st.columns([1.15, 0.85], gap="large")

    with col_dash_arch:
        user_goals = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        if not user_goals:
            st.info("💡 Chưa có mục tiêu nào trong hệ thống. Hãy trao đổi với CEO Coach tại Tab 1 để thẩm định và kích hoạt mục tiêu đầu tiên!")
            selected_goal = None
        else:
            selected_goal_id_key = f"selected_goal_id_{current_username}"
            all_gids = [str(g.get("id")) for g in user_goals if g.get("id")]
            if selected_goal_id_key not in st.session_state or st.session_state[selected_goal_id_key] not in all_gids:
                st.session_state[selected_goal_id_key] = all_gids[0] if all_gids else (user_goals[0].get("id") or "g0")

            current_sel_id = str(st.session_state[selected_goal_id_key])

            # ------------------------------------------------------------------
            # KHU VỰC: 🗂️ Quản Lý Danh Sách Mục Tiêu (Goal Manager)
            # ------------------------------------------------------------------
            st.markdown("#### 🗂️ Quản Lý Danh Sách Mục Tiêu (Goal Manager)")
            st.caption(f"Đang quản lý **{len(user_goals)}** mục tiêu • Bấm '🎯 Xem lộ trình' để đồng bộ bảng Phân rã 4 tầng & Architect Bot")

            for i, g in enumerate(user_goals):
                gid = str(g.get("id") or f"goal_{i}")
                g_title = str(g.get("title") or g.get("goal_name", f"Mục tiêu {i+1}"))
                g_status = str(g.get("status", "active")).lower()
                g_prio = str(g.get("priority", "Cao (P1)"))
                g_hours = g.get("daily_hours", 1.5)
                g_days = g.get("duration_days", 90)
                g_slot = str(g.get("preferred_time") or g.get("preferred_slots", "08:00 - 10:00 Sáng"))
                is_selected = (gid == current_sel_id)

                # Huy hiệu Trạng thái
                if g_status == "active":
                    status_badge = "🟢 :green[**Đang chạy**]"
                elif g_status == "paused":
                    status_badge = "⏸️ :orange[**Tạm dừng**]"
                elif g_status == "completed":
                    status_badge = "✅ :blue[**Hoàn thành**]"
                else:
                    status_badge = "🔍 :violet[**Đang thẩm định**]"

                # Huy hiệu Mức ưu tiên
                prio_lower = g_prio.lower()
                if "cao" in prio_lower or "p1" in prio_lower:
                    prio_badge = "🔥 :red[Cao (P1)]"
                elif "trung" in prio_lower or "p2" in prio_lower:
                    prio_badge = "⚡ :orange[Trung bình (P2)]"
                else:
                    prio_badge = "🌿 :gray[Thấp (P3)]"

                with st.container(border=True):
                    # Hàng 1: Tiêu đề + Huy hiệu + Nút chọn lộ trình
                    col_card_info, col_card_sel = st.columns([0.70, 0.30])
                    with col_card_info:
                        if is_selected:
                            st.markdown(f"**🎯 {g_title}** &nbsp; {status_badge} &nbsp;|&nbsp; {prio_badge}")
                        else:
                            st.markdown(f"**{g_title}** &nbsp; {status_badge} &nbsp;|&nbsp; {prio_badge}")
                        st.caption(f"⏱️ **{g_hours}h/ngày** • ⏰ **{g_slot}** • 📅 **{g_days} ngày**")
                    with col_card_sel:
                        if is_selected:
                            st.button("✅ Đang xem", key=f"is_sel_{gid}_{i}", disabled=True, use_container_width=True)
                        else:
                            if st.button("🎯 Xem lộ trình", key=f"sel_goal_{gid}_{i}", use_container_width=True):
                                st.session_state[selected_goal_id_key] = gid
                                st.rerun()

                    # Hàng 2: 3 nút thao tác trực tiếp (Tạm dừng/Tiếp tục, Sửa nhanh, Xóa)
                    col_b1, col_b2, col_b3 = st.columns([0.34, 0.36, 0.30])

                    # Nút 1: ⏸️ Tạm dừng / ▶️ Tiếp tục
                    with col_b1:
                        if g_status == "paused":
                            if st.button("▶️ Tiếp tục", key=f"resume_btn_{gid}_{i}", use_container_width=True):
                                update_user_goal_status(gid, "active", current_username)
                                st.session_state[goals_key] = load_user_goals(current_username)
                                st.toast(f"Đã tiếp tục mục tiêu '{g_title}'!")
                                st.rerun()
                        else:
                            if st.button("⏸️ Tạm dừng", key=f"pause_btn_{gid}_{i}", use_container_width=True):
                                update_user_goal_status(gid, "paused", current_username)
                                st.session_state[goals_key] = load_user_goals(current_username)
                                st.toast(f"Đã tạm dừng mục tiêu '{g_title}'. Lịch trình Giai đoạn 2 đã được giải phóng!")
                                st.rerun()

                    # Nút 2: ✏️ Sửa nhanh
                    with col_b2:
                        with st.popover("✏️ Sửa nhanh", use_container_width=True):
                            st.markdown(f"**Chỉnh sửa nhanh: {g_title}**")
                            new_t = st.text_input("Tên mục tiêu:", value=g_title, key=f"ed_t_{gid}_{i}")
                            c_e1, c_e2 = st.columns(2)
                            new_d = c_e1.number_input("Số ngày:", min_value=1, max_value=365, value=int(g_days), key=f"ed_d_{gid}_{i}")
                            new_h = c_e2.number_input("Giờ/ngày:", min_value=0.5, max_value=12.0, step=0.5, value=float(g_hours), key=f"ed_h_{gid}_{i}")
                            c_e3, c_e4 = st.columns(2)
                            prio_options = ["Cao (P1)", "Trung bình (P2)", "Thấp (P3)"]
                            prio_idx = 0
                            for p_i, p_opt in enumerate(prio_options):
                                if p_opt.split()[0].lower() in g_prio.lower():
                                    prio_idx = p_i
                                    break
                            new_p = c_e3.selectbox("Mức ưu tiên:", options=prio_options, index=prio_idx, key=f"ed_p_{gid}_{i}")
                            new_slot = c_e4.text_input("Khung giờ:", value=g_slot, key=f"ed_s_{gid}_{i}")

                            if st.button("💾 Lưu Cập Nhật", key=f"ed_save_{gid}_{i}", type="primary", use_container_width=True):
                                update_user_goal_details(
                                    goal_id=gid,
                                    updates={
                                        "title": new_t,
                                        "goal_name": new_t,
                                        "duration_days": new_d,
                                        "daily_hours": new_h,
                                        "priority": new_p,
                                        "preferred_time": new_slot,
                                        "preferred_slots": new_slot,
                                    },
                                    username=current_username,
                                )
                                st.session_state[goals_key] = load_user_goals(current_username)
                                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                st.toast("✅ Đã cập nhật mục tiêu thành công!")
                                st.rerun()

                    # Nút 3: 🗑️ Xóa có xác nhận
                    with col_b3:
                        with st.popover("🗑️ Xóa", use_container_width=True):
                            st.warning(f"⚠️ Xác nhận xóa vĩnh viễn mục tiêu **'{g_title}'** cùng toàn bộ lịch trình liên quan trong Master Schedule?")
                            if st.button("Xác nhận xóa vĩnh viễn", key=f"del_conf_{gid}_{i}", type="primary", use_container_width=True):
                                delete_user_goal(gid, current_username)
                                updated_goals = load_user_goals(current_username)
                                st.session_state[goals_key] = updated_goals
                                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                if updated_goals:
                                    st.session_state[selected_goal_id_key] = updated_goals[0].get("id")
                                else:
                                    st.session_state[selected_goal_id_key] = None
                                st.toast(f"Đã xóa vĩnh viễn mục tiêu '{g_title}'!")
                                st.rerun()

            # ------------------------------------------------------------------
            # PHÂN RÃ LỘ TRÌNH 4 TẦNG (ĐỒNG BỘ MỤC TIÊU ĐANG CHỌN)
            # ------------------------------------------------------------------
            selected_goal = next(
                (g for g in user_goals if str(g.get("id")) == current_sel_id),
                user_goals[0],
            )
            selected_goal_name = selected_goal.get("title") or selected_goal.get("goal_name", "Mục tiêu")
            bd = safe_dict(selected_goal.get("breakdown"))

            st.markdown("---")
            st.markdown(f"#### 🏛️ Phân Rã Lộ Trình 4 Tầng: **{selected_goal_name}**")

            # Tầng 1: Năm
            yearly_vision = bd.get("yearly") or f"Chinh phục toàn diện {selected_goal_name}"
            st.markdown("**🌟 TẦNG 1 — TẦM NHÌN DÀI HẠN (YEARLY):**")
            st.info(f"🎯 **{yearly_vision}**")

            # Tầng 2: Quý
            quarterly_items = safe_list(bd.get("quarterly", []))
            st.markdown("**🏆 TẦNG 2 — PHÂN KỲ CHIẾN LƯỢC (QUARTERLY):**")
            if quarterly_items:
                q_cols = st.columns(min(len(quarterly_items), 3) or 1)
                for q_idx, q in enumerate(quarterly_items[:3]):
                    q_dict = safe_dict(q)
                    with q_cols[q_idx % len(q_cols)]:
                        with st.container(border=True):
                            st.markdown(f"**{q_dict.get('quarter', f'Quý {q_idx+1}')}**")
                            st.caption(f"🎯 *Trọng tâm:* {q_dict.get('focus', 'Nền tảng')}")
                            st.caption(f"🏁 *Kết quả:* {q_dict.get('target_outcome', 'Đạt chuẩn')}")
            else:
                st.caption("*(Chưa có phân kỳ Quý. Hãy chat với Architect Bot ở cột phải để tự động phân rã)*")

            # Tầng 3: Tháng
            monthly_items = safe_list(bd.get("monthly", []))
            st.markdown("**📅 TẦNG 3 — PHÂN RÃ THEO THÁNG (MONTHLY):**")
            if monthly_items:
                for m_idx, m in enumerate(monthly_items, 1):
                    m_dict = safe_dict(m)
                    st.markdown(f"- **{m_dict.get('month', f'Tháng {m_idx}')}:** {m_dict.get('milestone', '')} *(Tài liệu: {m_dict.get('resources', 'Giáo trình chuẩn')})*")
            else:
                st.caption("*(Chưa có phân rã Tháng)*")

            # Tầng 4: Tuần
            weekly_items = safe_list(bd.get("weekly", []))
            st.markdown("**⚡ TẦNG 4 — KẾ HOẠCH HÀNH ĐỘNG TỪNG TUẦN (WEEKLY):**")
            if weekly_items:
                for w_idx, w in enumerate(weekly_items, 1):
                    w_dict = safe_dict(w)
                    w_title = w_dict.get("milestone", f"Cột mốc Tuần {w_idx}")
                    w_actions = safe_list(w_dict.get("action_items", []))
                    w_hrs = w_dict.get("estimated_hours", 7.0)
                    with st.expander(f"📌 {w_dict.get('week', f'Tuần {w_idx}')}: {w_title} ({w_hrs}h)", expanded=(w_idx == 1)):
                        for act in w_actions:
                            st.markdown(f"- ▫️ {act}")
            else:
                st.caption("*(Chưa có kế hoạch tuần)*")

            # Tài nguyên chuẩn
            resources_items = safe_list(bd.get("resources", []))
            st.markdown("---")
            st.markdown("#### 📚 Kho Tài Liệu & Công Cụ Thẩm Định (Curated Resources):")
            if resources_items:
                for r_idx, r in enumerate(resources_items, 1):
                    r_dict = safe_dict(r)
                    r_title = r_dict.get("title", f"Tài liệu {r_idx}")
                    r_url = r_dict.get("url", "#")
                    r_type = r_dict.get("type", "Giáo trình")
                    r_how = r_dict.get("how_to_use", "Học tập và làm bài tập theo khung giờ đã định.")
                    with st.container(border=True):
                        st.markdown(f"🔗 **[{r_title}]({r_url})** `[{r_type}]`")
                        st.caption(f"💡 *Hướng dẫn khai thác:* {r_how}")
            else:
                st.caption("*(Chưa có tài liệu. Chat với Architect Bot để tự động tìm kiếm bộ đề và giáo trình uy tín)*")

    with col_chat_arch:
        arch_title = f"💬 Trò Chuyện Cùng Strategy Architect: {selected_goal_name}" if ('selected_goal_name' in locals() and selected_goal_name) else "💬 Trò Chuyện Cùng Strategy Architect"
        st.markdown(f"#### {arch_title}")
        st.caption("Thêm/bớt tài liệu • Đổi giờ học • Phân rã lại tuần hoặc tinh chỉnh độ ưu tiên")

        chat_container_arch = st.container(height=520)
        with chat_container_arch:
            for msg in st.session_state[chat_arch_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if arch_input := st.chat_input(
            "Yêu cầu thêm tài liệu, đổi giờ học hoặc phân rã lại...",
            key=f"input_arch_{current_username}",
        ):
            st.session_state[chat_arch_key].append({"role": "user", "content": arch_input})
            with chat_container_arch:
                with st.chat_message("user"):
                    st.markdown(arch_input)
                with st.chat_message("assistant"):
                    with st.spinner("Strategy Architect đang tìm kiếm tài liệu chuẩn và tái cấu trúc lộ trình..."):
                        target_gid = selected_goal.get("id") if 'selected_goal' in locals() and selected_goal else None
                        if architect_chat is not None:
                            res = architect_chat(
                                user_message=arch_input,
                                username=current_username,
                                goal_id=target_gid,
                                chat_history=st.session_state[chat_arch_key],
                            )
                            arch_rep = res.get("response", "Tôi đã cập nhật lộ trình vào hệ thống.")
                        else:
                            arch_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(arch_rep)
                        st.session_state[chat_arch_key].append({"role": "assistant", "content": arch_rep})
                        st.session_state[goals_key] = load_user_goals(current_username)
                        st.rerun()


# ------------------------------------------------------------------------------
# TAB 3: 📅 GIAI ĐOẠN 2: THỰC THI & LỊCH TRÌNH (SCHEDULER)
# ------------------------------------------------------------------------------
with tab_sched:
    st.markdown("### 📅 Giai đoạn 2: Thực Thi & Lịch Trình Điều Hành")
    st.caption("Phân bổ nhịp sinh học không trùng lặp • Checklist tương tác real-time • Dời lịch linh hoạt khi bận")

    col_dash_sched, col_chat_sched = st.columns([1.15, 0.85], gap="large")

    with col_dash_sched:
        ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))
        user_goals_sched = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        paused_goal_ids = set(str(g.get("id")) for g in user_goals_sched if str(g.get("status", "")).lower() == "paused")
        paused_goal_titles = set(str(g.get("title") or g.get("goal_name")) for g in user_goals_sched if str(g.get("status", "")).lower() == "paused")

        # Khi mục tiêu ở trạng thái paused, tạm thời không chiếm lịch ở Tab Giai đoạn 2
        active_schedule = [
            t for t in ms
            if not (
                (t.get("goal_id") and str(t.get("goal_id")) in paused_goal_ids) or
                (t.get("goal_title") and str(t.get("goal_title")) in paused_goal_titles)
            )
        ]

        if paused_goal_titles:
            st.info(f"⏸️ **{len(paused_goal_titles)} mục tiêu đang tạm dừng:** {', '.join(paused_goal_titles)}. Các khung giờ tương ứng tạm thời không chiếm lịch.")

        mode = st.radio(
            "Chế độ hiển thị lịch:",
            options=["🌐 Lịch Tổng Hợp Tất Cả Mục Tiêu (Master Schedule)", "🎯 Xem Lịch Riêng Theo Từng Mục Tiêu"],
            horizontal=True,
            key=f"sched_mode_{current_username}",
        )

        filtered_schedule = active_schedule
        if mode == "🎯 Xem Lịch Riêng Theo Từng Mục Tiêu":
            unique_goals = list(set(t.get("goal_title", "Mục tiêu") for t in active_schedule if t.get("goal_title")))
            if unique_goals:
                chosen_g = st.selectbox("Chọn mục tiêu cụ thể:", options=unique_goals, key=f"sel_ms_goal_{current_username}")
                filtered_schedule = [t for t in active_schedule if t.get("goal_title") == chosen_g]
            else:
                st.info("Chưa có mục tiêu nào trong lịch.")

        st.markdown("---")
        # Nút xuất lịch
        c_ics, c_gcal = st.columns(2)
        with c_ics:
            ics_text = generate_ics_from_master_schedule(filtered_schedule, current_username)
            st.download_button(
                label="📥 Tải File Lịch (.ics) Cho Google / Apple / Outlook",
                data=ics_text,
                file_name=f"mavis_master_schedule_{current_username}.ics",
                mime="text/calendar",
                use_container_width=True,
            )
        with c_gcal:
            first_task = filtered_schedule[0] if filtered_schedule else {}
            gcal_link = generate_gcal_link(
                first_task.get("task_detail", "Học tập cùng Mavis"),
                first_task.get("time_slot", "08:00 - 10:00"),
                duration_minutes=90,
                resource_info=first_task.get("resource_link", ""),
            )
            st.link_button("🌐 Mở Google Calendar (Thêm Sự Kiện 1 Chạm)", url=gcal_link, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Checklist Thực Thi Tương Tác Hàng Ngày:")

        if not filtered_schedule:
            st.info(
                "💡 Chưa có lịch trình. Bạn hãy chat với **AI Master Scheduler** ở cột bên phải "
                "(ví dụ: *'Hãy gom tất cả active goals để xếp lịch tuần này cho tôi'*) để tạo lịch ngay lập tức!"
            )
        else:
            days_order = []
            for t in filtered_schedule:
                d = t.get("date", "Hôm nay")
                if d not in days_order:
                    days_order.append(d)

            for d in days_order:
                day_tasks = [t for t in filtered_schedule if t.get("date") == d]
                done_day = sum(1 for t in day_tasks if t.get("is_done") is True)
                total_day = len(day_tasks)

                with st.expander(f"📅 **{d}** — Tiến độ: {done_day}/{total_day} hoàn thành", expanded=(done_day < total_day)):
                    for sess in ["Sáng", "Chiều", "Tối"]:
                        sess_tasks = [t for t in day_tasks if t.get("session") == sess]
                        if sess_tasks:
                            st.markdown(f"##### ⏰ Buổi {sess}:")
                            for idx, task in enumerate(sess_tasks):
                                t_detail = task.get("task_detail", "Nhiệm vụ")
                                t_slot = task.get("time_slot", "08:00 - 10:00")
                                t_goal = task.get("goal_title", "")
                                t_link = task.get("resource_link", "")
                                is_done_val = bool(task.get("is_done", False))

                                chk_key = f"chk_{current_username}_{d}_{sess}_{idx}_{abs(hash(t_detail)) % 100000}"
                                label = f"**{t_slot}** — {t_detail} `[🎯 {t_goal}]`" if t_goal else f"**{t_slot}** — {t_detail}"
                                checked = st.checkbox(label, value=is_done_val, key=chk_key)

                                if checked != is_done_val:
                                    update_master_schedule_task_status(
                                        task_detail=t_detail,
                                        is_done=checked,
                                        date=d,
                                        username=current_username,
                                    )
                                    task["is_done"] = checked
                                    st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                    st.toast(f"✅ Đã cập nhật: {t_detail[:35]}...")
                                    st.rerun()

                                if t_link:
                                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📖 *Tài liệu:* [{t_link}]({t_link})")

    with col_chat_sched:
        st.markdown("#### 💬 Trò Chuyện Cùng Master Scheduler")
        st.caption("Báo bận • Dời lịch linh hoạt • Phân bổ nhịp sinh học không trùng lặp")

        chat_container_sched = st.container(height=520)
        with chat_container_sched:
            for msg in st.session_state[chat_sched_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if sched_input := st.chat_input(
            "Báo bận (VD: 'chiều nay bận họp, dời task sang mai')...",
            key=f"input_sched_{current_username}",
        ):
            st.session_state[chat_sched_key].append({"role": "user", "content": sched_input})
            with chat_container_sched:
                with st.chat_message("user"):
                    st.markdown(sched_input)
                with st.chat_message("assistant"):
                    with st.spinner("AI Master Scheduler đang tính toán tối ưu lại lịch trình..."):
                        if scheduler_chat is not None:
                            res = scheduler_chat(
                                user_message=sched_input,
                                username=current_username,
                                chat_history=st.session_state[chat_sched_key],
                            )
                            sched_rep = res.get("response", "Tôi đã điều chỉnh lịch trình phù hợp cho bạn.")
                        else:
                            sched_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(sched_rep)
                        st.session_state[chat_sched_key].append({"role": "assistant", "content": sched_rep})
                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                        st.rerun()


# ------------------------------------------------------------------------------
# TAB 4: 📊 GIAI ĐOẠN 3: TỔNG KẾT & CẢI THIỆN (RETROSPECTIVE)
# ------------------------------------------------------------------------------
with tab_retro:
    st.markdown("### 📊 Giai đoạn 3: Tổng Kết, Khai Vấn & Cải Thiện Khép Kín")
    st.caption("Phân tích điểm nghẽn • Khai vấn thấu cảm • Bảo vệ năng lượng • Tự động thích ứng lộ trình")

    col_dash_retro, col_chat_retro = st.columns([1.15, 0.85], gap="large")

    with col_dash_retro:
        ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))
        r_logs = safe_list(st.session_state.get(retro_logs_key) or load_retrospective_logs(current_username))
        user_goals = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        total_tasks = len(ms)
        done_tasks = sum(1 for t in ms if t.get("is_done") is True)
        uncompleted_tasks = total_tasks - done_tasks
        rate = (done_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

        latest_log = r_logs[-1] if r_logs else {}
        last_emotion = latest_log.get("emotion", "neutral")
        emotion_emojis = {
            "motivated": "🔥 Tràn đầy động lực",
            "overwhelmed": "⚠️ Quá tải / Cần hạ tải",
            "tired": "💤 Mệt mỏi / Cần nghỉ ngơi",
            "satisfied": "✨ Hài lòng / Thư thái",
            "discouraged": "🌱 Cần động viên",
            "neutral": "⚡ Cân bằng",
        }
        disp_emotion = emotion_emojis.get(last_emotion, f"⚡ {last_emotion}")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Tỷ Lệ Hoàn Thành", f"{rate:.1f}%")
        with m2:
            st.metric("Task Đã Xong", f"{done_tasks}/{total_tasks}")
        with m3:
            st.metric("Task Chưa Xong", f"{uncompleted_tasks}")
        with m4:
            st.metric("Trạng Thái Năng Lượng", disp_emotion)

        st.progress(rate / 100.0)

        st.markdown("---")
        st.markdown("#### 🔄 Cơ Chế Khép Kín Vòng Lặp (Closed-Loop Adaptation):")
        st.caption("Khi gặp tình trạng quá tải hoặc task quá khó, hãy bấm nút dưới đây để AI tự động điều chỉnh số giờ hoặc bổ sung tài liệu cho Giai đoạn 1:")

        if st.button("🔄 Cập nhật lại Thiết lập (Giai đoạn 1)", type="primary", use_container_width=True, key=f"btn_apply_loop_{current_username}"):
            if latest_log and latest_log.get("recommended_adjustments"):
                adj_desc = latest_log.get("recommended_adjustments")
                for g in user_goals:
                    if "Hạ tải" in adj_desc or "quá tải" in adj_desc or "giảm" in adj_desc.lower():
                        old_h = float(g.get("daily_hours", 1.5))
                        new_h = max(1.0, old_h - 0.5)
                        g["daily_hours"] = new_h
                save_user_goals(user_goals, username=current_username)
                st.session_state[goals_key] = load_user_goals(current_username)
                st.success(f"🎉 Đã cập nhật thành công thiết lập Giai đoạn 1: {adj_desc}")
                st.rerun()
            else:
                st.info("💡 Bạn hãy chia sẻ phản hồi với Retrospective Coach ở cột bên phải để Coach tạo đề xuất điều chỉnh cá nhân hóa trước!")

        st.markdown("---")
        st.markdown("#### 🎯 Tiến Độ Từng Mục Tiêu:")
        if user_goals:
            for g in user_goals:
                g_title = g.get("title") or g.get("goal_name", "Mục tiêu")
                g_tasks = [t for t in ms if t.get("goal_title") == g_title or t.get("goal_id") == g.get("id")]
                g_done = sum(1 for t in g_tasks if t.get("is_done") is True)
                g_total = len(g_tasks)
                g_rate = (g_done / g_total) if g_total > 0 else 0.0
                st.markdown(f"**{g_title}** ({g_done}/{g_total} task • {g_rate*100:.0f}%)")
                st.progress(g_rate)
        else:
            st.caption("Chưa có mục tiêu nào.")

        st.markdown("---")
        st.markdown("#### 📜 Lịch Sử Nhật Ký Khai Vấn Hồi Cứu (Retrospective Logs):")
        if r_logs:
            for l_idx, log in enumerate(reversed(r_logs[-5:]), 1):
                l_date = log.get("date", "N/A")
                l_emo = log.get("emotion", "neutral")
                l_rate = log.get("completion_rate", 0.0)
                l_notes = log.get("reflection_notes", "")
                l_adj = log.get("recommended_adjustments", "")
                with st.expander(f"📌 Check-in {l_date} — Cảm xúc: `{l_emo}` | Tỷ lệ: `{l_rate:.1f}%`", expanded=(l_idx == 1)):
                    st.markdown(f"**Lời khuyên của Coach:**\n> {l_notes}")
                    if l_adj:
                        st.info(f"💡 **Đề xuất điều chỉnh:** {l_adj}")
        else:
            st.caption("Chưa có lịch sử check-in. Bạn hãy trao đổi cùng Retrospective Coach ở cột bên phải để hoàn thiện buổi check-in đầu tiên!")

    with col_chat_retro:
        st.markdown("#### 💬 Trò Chuyện Cùng Retrospective Coach")
        st.caption("Check-in cuối ngày • Lắng nghe cảm xúc • Phân tích nguyên nhân (quá khó, quá tải...)")

        chat_container_retro = st.container(height=520)
        with chat_container_retro:
            for msg in st.session_state[chat_retro_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if retro_input := st.chat_input(
            "Chia sẻ cảm xúc hoặc nguyên nhân chưa xong task hôm nay...",
            key=f"input_retro_{current_username}",
        ):
            st.session_state[chat_retro_key].append({"role": "user", "content": retro_input})
            with chat_container_retro:
                with st.chat_message("user"):
                    st.markdown(retro_input)
                with st.chat_message("assistant"):
                    with st.spinner("Retrospective Coach đang lắng nghe và phân tích nguyên nhân..."):
                        if retrospective_chat is not None:
                            res = retrospective_chat(
                                user_message=retro_input,
                                username=current_username,
                                chat_history=st.session_state[chat_retro_key],
                            )
                            retro_rep = res.get("response", "Cảm ơn bạn đã chia sẻ cùng Coach.")
                        else:
                            retro_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(retro_rep)
                        st.session_state[chat_retro_key].append({"role": "assistant", "content": retro_rep})
                        st.session_state[retro_logs_key] = load_retrospective_logs(current_username)
                        st.session_state[goals_key] = load_user_goals(current_username)
                        st.rerun()
