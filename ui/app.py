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

import importlib

# 1. Nạp an toàn module memory.mongodb
try:
    import memory.mongodb as mm
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

# 2. Nạp an toàn module memory.goals
try:
    import memory.goals as mg

    load_goals = getattr(mg, "load_goals", lambda *args, **kwargs: [])
    save_goals = getattr(mg, "save_goals", lambda *args, **kwargs: True)
    add_goal = getattr(mg, "add_goal", lambda *args, **kwargs: True)
    update_goal = getattr(mg, "update_goal", lambda *args, **kwargs: True)
    CATEGORY_LABELS = getattr(mg, "CATEGORY_LABELS", {})
    load_historical_insights = getattr(mg, "load_historical_insights", lambda *args, **kwargs: {})
    save_historical_insights = getattr(mg, "save_historical_insights", lambda *args, **kwargs: True)
    load_user_profile = getattr(mg, "load_user_profile", lambda *args, **kwargs: {})
    save_user_profile = getattr(mg, "save_user_profile", lambda *args, **kwargs: True)
    load_user_goal_profile = getattr(mg, "load_user_goal_profile", lambda *args, **kwargs: {})
    save_user_goal_profile = getattr(mg, "save_user_goal_profile", lambda *args, **kwargs: True)
    load_user_goals = getattr(mg, "load_user_goals", lambda *args, **kwargs: [])
    save_user_goals = getattr(mg, "save_user_goals", lambda *args, **kwargs: True)
    load_user_resources = getattr(mg, "load_user_resources", lambda *args, **kwargs: [])
    save_user_resources = getattr(mg, "save_user_resources", lambda *args, **kwargs: True)
    load_user_roadmap = getattr(mg, "load_user_roadmap", lambda *args, **kwargs: {})
    save_user_roadmap = getattr(mg, "save_user_roadmap", lambda *args, **kwargs: True)
    load_categorized_goals = getattr(mg, "load_categorized_goals", lambda *args, **kwargs: {})
    save_categorized_goals = getattr(mg, "save_categorized_goals", lambda *args, **kwargs: True)
    load_master_schedule = getattr(mg, "load_master_schedule", lambda *args, **kwargs: [])
    save_master_schedule = getattr(mg, "save_master_schedule", lambda *args, **kwargs: True)
    update_master_schedule_task_status = getattr(mg, "update_master_schedule_task_status", lambda *args, **kwargs: True)
    load_retrospective_logs = getattr(mg, "load_retrospective_logs", lambda *args, **kwargs: [])
    save_retrospective_logs = getattr(mg, "save_retrospective_logs", lambda *args, **kwargs: True)
    append_retrospective_log = getattr(mg, "append_retrospective_log", lambda *args, **kwargs: True)
    get_user_state_full = getattr(mg, "get_user_state_full", lambda *args, **kwargs: {})
    update_user_goal_status = getattr(mg, "update_user_goal_status", lambda *args, **kwargs: True)
    update_user_goal_details = getattr(mg, "update_user_goal_details", lambda *args, **kwargs: True)
    delete_user_goal = getattr(mg, "delete_user_goal", lambda *args, **kwargs: True)
    calculate_user_streak = getattr(mg, "calculate_user_streak", lambda u="mavis": 1)
    detect_goal_domain = getattr(mg, "detect_goal_domain", lambda *args, **kwargs: "general")
    DOMAIN_TERMINOLOGY = getattr(mg, "DOMAIN_TERMINOLOGY", {})
    get_vietnam_today = getattr(mg, "get_vietnam_today", lambda: datetime.now().date())
    get_vietnam_today_str = getattr(mg, "get_vietnam_today_str", lambda: datetime.now().strftime("%Y-%m-%d"))
    compute_target_date = getattr(mg, "compute_target_date", lambda s, d: "2027-02-19")
    generate_detailed_master_schedule = getattr(mg, "generate_detailed_master_schedule", lambda *args, **kwargs: [])
    ensure_schedule_covers_date = getattr(mg, "ensure_schedule_covers_date", lambda *args, **kwargs: [])
    VIETNAM_WEEKDAYS = getattr(mg, "VIETNAM_WEEKDAYS", {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"})
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
    def calculate_user_streak(*args, **kwargs): return 1
    def detect_goal_domain(*args, **kwargs): return "general"
    DOMAIN_TERMINOLOGY = {}

# 3. Nạp an toàn module memory.auth
try:
    import memory.auth as ma
    get_authenticator = getattr(ma, "get_authenticator", None)
    register_user = getattr(ma, "register_user", None)
except Exception as _auth_import_err:
    import traceback
    st.error(f"⚠️ Cảnh báo nạp module `memory.auth`: {_auth_import_err}")
    with st.expander("Chi tiết kỹ thuật lỗi nạp memory.auth"):
        st.code(traceback.format_exc())
    get_authenticator = None
    register_user = None

# 4. Nạp an toàn các Chatbot functions từ agents.brain
try:
    import agents.brain as ab
    chat_node = getattr(ab, "chat_node", None)
    ceo_coach_chat = getattr(ab, "ceo_coach_chat", None)
    architect_chat = getattr(ab, "architect_chat", None)
    scheduler_chat = getattr(ab, "scheduler_chat", None)
    retrospective_chat = getattr(ab, "retrospective_chat", None)
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

from langchain_core.messages import HumanMessage, AIMessage

# 5. Khởi tạo an toàn Agent Graph
try:
    import agents.graph as ag
    build_graph = getattr(ag, "build_graph", None)
    mavis_agent = getattr(ag, "mavis_agent", None) or (build_graph() if callable(build_graph) else None)
    if mavis_agent is None:
        raise ImportError("Không thể khởi tạo mavis_agent từ agents.graph")
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

# 6. Nạp an toàn module tools.google_calendar (Tích hợp Google Calendar API 2 chiều)
try:
    import tools.google_calendar as tgc
    is_calendar_connected = getattr(tgc, "is_calendar_connected", lambda username: False)
    disconnect_calendar = getattr(tgc, "disconnect_calendar", lambda username: False)
    get_oauth_authorization_url = getattr(tgc, "get_oauth_authorization_url", lambda **kwargs: (None, None))
    exchange_code_and_save_token = getattr(tgc, "exchange_code_and_save_token", lambda *args, **kwargs: False)
    fetch_busy_events = getattr(tgc, "fetch_busy_events", lambda username, days=7: [])
    sync_schedule_to_google_calendar = getattr(tgc, "sync_schedule_to_google_calendar", lambda username, ms: {"success": False, "message": "Chưa sẵn sàng", "synced_count": 0})
    get_google_client_config = getattr(tgc, "get_google_client_config", lambda: None)
    get_default_redirect_uri = getattr(tgc, "get_default_redirect_uri", lambda: "https://mavisagentquanlycuocsong-252.streamlit.app")
    update_rescheduled_calendar_event = getattr(tgc, "update_rescheduled_calendar_event", lambda *args, **kwargs: False)
except Exception as _gcal_err:
    def is_calendar_connected(username): return False
    def disconnect_calendar(username): return False
    def get_oauth_authorization_url(**kwargs): return None, None
    def exchange_code_and_save_token(*args, **kwargs): return False
    def fetch_busy_events(username, days=7): return []
    def sync_schedule_to_google_calendar(username, ms): return {"success": False, "message": "Module Google Calendar chưa sẵn sàng", "synced_count": 0}
    def get_google_client_config(): return None
    def get_default_redirect_uri(): return "https://mavisagentquanlycuocsong-252.streamlit.app"
    def update_rescheduled_calendar_event(*args, **kwargs): return False


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

# Đồng bộ chặt chẽ với danh sách goals hiện tại trong MongoDB:
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

    # Hồ sơ mục tiêu có cấu trúc - Đọc trực tiếp từ danh sách goals mới trong MongoDB
    user_goals_sidebar = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))
    active_goals_sidebar = [g for g in user_goals_sidebar if g.get("status") in ["active", "in_progress"]]

    with st.expander("🎯 Hồ Sơ Mục Tiêu (Real-time)", expanded=True):
        if user_goals_sidebar:
            st.caption(f"Tổng số: **{len(user_goals_sidebar)} mục tiêu** ({len(active_goals_sidebar)} đang kích hoạt)")
            for g in user_goals_sidebar:
                g_title = g.get("title") or g.get("goal_name", "Mục tiêu")
                g_cat = g.get("category", "Học tập")
                g_hours = g.get("daily_hours", 1.5)
                g_time = g.get("preferred_time") or g.get("preferred_slots") or "Linh hoạt"
                g_status = g.get("status", "active")
                g_prio = g.get("priority", "Trung bình")

                status_label = "🟢 Đang chạy" if g_status in ["active", "in_progress"] else ("⏸️ Tạm dừng" if g_status == "paused" else "📋 Đang thẩm định")
                with st.container(border=True):
                    st.markdown(f"**{g_title}**")
                    st.caption(f"Trạng thái: `{status_label}` | Nhóm: `{g_cat}`")
                    st.markdown(f"⏱️ **Quỹ giờ:** `{g_hours}h/ngày` • `{g_time}`")
                    st.markdown(f"🎯 **Ưu tiên:** `{g_prio}`")
        else:
            st.caption("Chưa có mục tiêu nào đang kích hoạt. Hãy trò chuyện với CEO Coach ở Tab 1 để thiết lập mục tiêu cuộc đời!")

    # Kho tài liệu (resources) trên Sidebar - Gom từ user_goals và resources_key
    goal_resources = []
    for g in user_goals_sidebar:
        bd = g.get("breakdown", {})
        if isinstance(bd, dict):
            for r in bd.get("resources", []):
                if isinstance(r, dict) and (r.get("title") or r.get("resource_title")):
                    goal_resources.append({
                        "title": r.get("title") or r.get("resource_title"),
                        "url": r.get("url") or r.get("resource_url") or "#",
                        "type": r.get("type", "Giáo trình"),
                    })
    extra_res = safe_list(st.session_state.get(resources_key))
    for r in extra_res:
        if isinstance(r, dict) and r.get("title"):
            goal_resources.append(r)

    if goal_resources:
        with st.expander("📚 Kho Tài Liệu (Link nhanh)", expanded=False):
            seen_urls = set()
            for r_dict in goal_resources[:8]:
                title = r_dict.get("title", "Tài liệu")
                url = r_dict.get("url", "#")
                rtype = r_dict.get("type", "Tài liệu")
                if url not in seen_urls:
                    seen_urls.add(url)
                    st.markdown(f"- 🔗 [{title}]({url}) *({rtype})*")

    # Hồ sơ cá nhân đa khía cạnh (User Profile & Trạng thái Vận hành Lộ trình)
    if user_goals_sidebar:
        with st.expander("👤 Trạng Thái Vận Hành Lộ Trình", expanded=False):
            total_load = sum(float(g.get("daily_hours") or 1.5) for g in user_goals_sidebar)
            st.success(f"🚀 **Đang vận hành {len(user_goals_sidebar)} mục tiêu**")
            st.markdown(f"**Tổng tải thời gian:** `{total_load:.1f}h/ngày`")
            st.markdown(f"**Mục tiêu đang chạy:** `{len(active_goals_sidebar)}/{len(user_goals_sidebar)}`")
            st.markdown("**Giai đoạn:** `THỰC THI & LỊCH TRÌNH`")
    else:
        st.info("💡 **Khởi đầu mới:** Hãy trò chuyện cùng CEO Coach ở Tab 1 để thẩm định và kích hoạt mục tiêu đầu tiên!")

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
            st.metric("Quỹ Giờ Active / Ngưỡng An Toàn", f"{total_active_hours:.1f}h / 8.0h")

        if total_all_hours > 8.0:
            st.warning(
                f"⚠️ **Cơ chế Burnout Shield (Lá Chắn Quá Tải):** Tổng giờ cam kết ({total_all_hours:.1f}h/ngày) vượt ngưỡng an toàn 8.0h/ngày hoặc có nguy cơ dồn quá nhiều Deep Work. "
                "CEO Coach cảnh báo rủi ro kiệt sức và khuyến nghị tạm dừng (⏸️ Paused) bớt 1 mục tiêu cũ trong Giai đoạn 1 trước khi kích hoạt mục tiêu mới!"
            )
        elif total_active_hours > 8.0:
            st.error(
                f"🚨 **Nguy cơ kiệt sức (Burnout Risk):** Bạn đang cam kết `{total_active_hours:.1f}h/ngày` trên các mục tiêu Active (> 8h/ngày). "
                "Vui lòng tạm dừng ('paused') bớt mục tiêu cũ để bảo vệ năng lượng não bộ!"
            )
        else:
            st.success(
                f"🛡️ **Burnout Shield An Toàn:** Quỹ giờ cam kết `{total_active_hours:.1f}h/ngày` "
                "(nằm trong ngưỡng an toàn 8.0h/ngày) đảm bảo nhịp sinh học và năng lượng bền vững."
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
# TAB 2: 📐 GIAI ĐOẠN 1: BẢN THIẾT KẾ TỔNG THỂ (ARCHITECT & GOOGLE CALENDAR)
# ------------------------------------------------------------------------------
with tab_arch:
    st.markdown("### 📐 Giai đoạn 1: Bản Thiết Kế Tổng Thể (Năm ➔ Quý ➔ Tháng ➔ Tuần)")
    st.caption("Chiến lược vĩ mô • Thảo luận phương pháp • Phân cấp 4 tầng khép kín • Kết nối Google Calendar 2 chiều")

    # --------------------------------------------------------------------------
    # TÍCH HỢP GOOGLE CALENDAR OAUTH 2.0 (2 CHIỀU THỜI GIAN THỰC)
    # --------------------------------------------------------------------------
    default_redir = get_default_redirect_uri()
    redir_session_key = f"active_gcal_redir_{current_username}"
    if redir_session_key not in st.session_state:
        st.session_state[redir_session_key] = default_redir

    cal_connected = is_calendar_connected(current_username)
    with st.container(border=True):
        col_gc_status, col_gc_action = st.columns([0.65, 0.35])
        with col_gc_status:
            if cal_connected:
                st.markdown("##### 🟢 Google Calendar: Đã Kết Nối (2 Chiều Thời Gian Thực)")
                st.caption("Đã đồng bộ hóa với Google Calendar cá nhân. AI tự động đọc các khung giờ bận trong 7 ngày tới để né trùng lịch khi phân bổ.")
            else:
                st.markdown("##### ⚪ Google Calendar: Chưa Kết Nối")
                st.caption("Kết nối Google Calendar để AI nhận diện giờ bận trong 7 ngày tới và đồng bộ lịch trình 2 chiều.")
        with col_gc_action:
            if cal_connected:
                if st.button("🔌 Ngắt Kết Nối Lịch", key=f"btn_disc_gcal_{current_username}", use_container_width=True):
                    disconnect_calendar(current_username)
                    st.toast("Đã ngắt kết nối Google Calendar.")
                    st.rerun()
            else:
                client_cfg = get_google_client_config()
                current_redir = st.session_state.get(redir_session_key, default_redir)
                auth_url, _ = get_oauth_authorization_url(redirect_uri=current_redir)
                if auth_url:
                    st.link_button("🔗 Kết Nối Google Calendar", url=auth_url, use_container_width=True)
                else:
                    st.caption("*(Chưa cấu hình GOOGLE_CLIENT_ID trong st.secrets)*")

        if not cal_connected:
            with st.expander("🛠️ Khắc phục Lỗi 400: redirect_uri_mismatch (Chỉ mất 1 phút)", expanded=False):
                st.markdown(
                    "Google yêu cầu **URI chuyển hướng (Redirect URI)** gửi đi từ ứng dụng phải trùng khớp 100% với danh sách đã đăng ký trong **Google Cloud Console**.\n\n"
                    "👉 **Cách xử lý triệt để trong 3 bước:**\n"
                    "1. Truy cập [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials).\n"
                    "2. Nhấp vào tên **OAuth 2.0 Client ID** của bạn (loại Web Application).\n"
                    "3. Tại mục **Authorized redirect URIs (URI chuyển hướng được phép)**, nhấn **+ ADD URI** và thêm các dòng sau:\n"
                )
                st.code(
                    "https://mavisagentquanlycuocsong-252.streamlit.app\n"
                    "http://localhost:8501\n"
                    "http://127.0.0.1:8501",
                    language="text",
                )
                st.markdown("4. Nhấn nút **LƯU (SAVE)** ở cuối trang của Google và đợi 1-2 phút để Google cập nhật.")
                st.markdown("---")
                st.markdown("**Hoặc chuyển đổi Redirect URI ứng dụng đang gửi đi tại đây:**")
                preset_options = [
                    "https://mavisagentquanlycuocsong-252.streamlit.app",
                    "http://localhost:8501",
                    "http://127.0.0.1:8501",
                    "Tùy chỉnh URI khác...",
                ]
                cur_val = st.session_state.get(redir_session_key, default_redir)
                cur_idx = preset_options.index(cur_val) if cur_val in preset_options else 3
                chosen_opt = st.selectbox(
                    "Chọn Redirect URI gửi sang Google:",
                    options=preset_options,
                    index=cur_idx,
                    key=f"sel_redir_preset_{current_username}",
                )
                if chosen_opt == "Tùy chỉnh URI khác...":
                    custom_uri = st.text_input("Nhập Redirect URI đã đăng ký trên Google Console:", value=cur_val, key=f"txt_custom_uri_{current_username}")
                    if custom_uri and custom_uri.strip() != st.session_state.get(redir_session_key):
                        st.session_state[redir_session_key] = custom_uri.strip().rstrip("/")
                        st.rerun()
                else:
                    if chosen_opt != st.session_state.get(redir_session_key):
                        st.session_state[redir_session_key] = chosen_opt.strip().rstrip("/")
                        st.rerun()

            with st.expander("🔑 Nhập Mã Xác Thực Thủ Công (Không sợ lỗi Redirect)", expanded=False):
                st.markdown(
                    "Nếu Google chặn chuyển hướng tự động, sau khi bạn đăng nhập tài khoản Google thành công, "
                    "hãy nhìn lên thanh địa chỉ trình duyệt, copy toàn bộ đoạn mã nằm sau `code=` và dán vào đây:"
                )
                manual_code = st.text_input("Dán Authorization Code từ Google vào đây:", key=f"txt_manual_gcode_{current_username}")
                if st.button("Xác Nhận Kết Nối", key=f"btn_submit_gcode_{current_username}"):
                    if manual_code and manual_code.strip():
                        current_redir = st.session_state.get(redir_session_key, default_redir)
                        res = exchange_code_and_save_token(manual_code.strip(), redirect_uri=current_redir, username=current_username)
                        if bool(res):
                            st.success("✅ Kết nối Google Calendar thành công!")
                            st.rerun()
                        else:
                            err_msg = getattr(res, "error", None) or "Mã không hợp lệ hoặc không khớp với Redirect URI đang chọn."
                            st.error(f"❌ {err_msg}")

        if cal_connected:
            c_sync1, c_sync2 = st.columns([0.55, 0.45])
            with c_sync1:
                if st.button("🔄 Đồng Bộ Toàn Bộ Lịch Trình Lên Google Calendar", key=f"btn_sync_gcal_tab1_{current_username}", type="primary", use_container_width=True):
                    cur_ms = load_master_schedule(current_username)
                    with st.spinner("Đang đẩy các sự kiện sang Google Calendar..."):
                        sync_res = sync_schedule_to_google_calendar(current_username, cur_ms)
                        if sync_res.get("success"):
                            st.success(f"✅ {sync_res.get('message')}")
                            st.toast("🎉 Đã đồng bộ lịch lên Google Calendar thành công!")
                        else:
                            st.error(f"❌ {sync_res.get('message')}")
            with c_sync2:
                with st.expander("📅 Xem Các Khung Giờ Bận (7 Ngày Tới)"):
                    busy_evs = fetch_busy_events(current_username, days=7)
                    if busy_evs:
                        for bev in busy_evs[:10]:
                            st.markdown(f"- ⏰ **{bev.get('start', '')}**: {bev.get('summary', 'Bận')}")
                    else:
                        st.info("Không có lịch bận nào trong 7 ngày tới trên Google Calendar.")

    st.markdown("---")

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
                                    st.session_state[goal_profile_key] = updated_goals[0]
                                else:
                                    st.session_state[selected_goal_id_key] = None
                                    st.session_state[goal_profile_key] = {}
                                    st.session_state[resources_key] = []
                                    st.session_state[roadmap_key] = {}
                                    st.session_state[profile_key] = {
                                        "current_situation": "Chưa có mục tiêu",
                                        "financial_status": "",
                                        "time_constraints": "0h/ngày",
                                        "is_onboarded": False,
                                        "coaching_stage": "interviewing",
                                        "obstacles": [],
                                    }
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

            # Nhận diện lĩnh vực chuyên biệt (Domain-Aware Persona)
            target_domain = detect_goal_domain(selected_goal, selected_goal_name, selected_goal.get("category", ""))
            domain_terms = DOMAIN_TERMINOLOGY.get(target_domain, DOMAIN_TERMINOLOGY.get("general", {}))

            # Đồng bộ lời chào mở đầu thích ứng theo mục tiêu đang chọn
            arch_active_goal_key = f"arch_active_gid_{current_username}"
            prev_active_gid = st.session_state.get(arch_active_goal_key)
            if prev_active_gid != current_sel_id:
                st.session_state[arch_active_goal_key] = current_sel_id
                if len(st.session_state[chat_arch_key]) <= 1:
                    has_bd = bool(bd and bd.get("quarterly") and bd.get("weekly"))
                    if has_bd:
                        st.session_state[chat_arch_key] = [
                            {
                                "role": "assistant",
                                "content": (
                                    f"Chào **{current_name}**! Mục tiêu **'{selected_goal_name}'** đã có đầy đủ **Lộ trình 4 Tầng** được xuất bản ở cột bên trái.\n\n"
                                    "✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang **Tab Giai đoạn 2 (Lịch Trình Thực Thi)** để xem và tinh chỉnh lịch chi tiết từng ngày."
                                ),
                            }
                        ]
                    else:
                        st.session_state[chat_arch_key] = [
                            {
                                "role": "assistant",
                                "content": domain_terms.get("opening_greeting", "").format(
                                    name=current_name,
                                    goal_title=selected_goal_name,
                                ),
                            }
                        ]

            st.markdown("---")
            st.markdown(f"#### 🏛️ Phân Rã Lộ Trình 4 Tầng: **{selected_goal_name}**")

            # Tầng 1: Năm
            yearly_vision = bd.get("yearly") or f"Chinh phục toàn diện {selected_goal_name}"
            st.markdown("**🌟 TẦNG 1 — TẦM NHÌN DÀI HẠN (YEARLY):**")
            st.info(f"🎯 **{yearly_vision}**")

            # Tầng 2: Quý (Làm rõ giai đoạn 30-90 ngày, mục tiêu trọng tâm và kết quả bàn giao)
            quarterly_items = safe_list(bd.get("quarterly", []))
            q_header_label = domain_terms.get('q_label', '🏆 Giai đoạn chiến lược (Quý)').upper()
            st.markdown(f"**{q_header_label}:**")
            if quarterly_items:
                q_cols = st.columns(min(len(quarterly_items), 3) or 1)
                for q_idx, q in enumerate(quarterly_items[:3]):
                    q_dict = safe_dict(q)
                    raw_q = str(q_dict.get('quarter', f'Quý {q_idx+1}'))
                    if "giai đoạn" not in raw_q.lower() and "tháng" not in raw_q.lower():
                        q_display_title = f"🏆 Giai đoạn {q_idx+1} ({raw_q})"
                    else:
                        q_display_title = f"🏆 {raw_q}"

                    with q_cols[q_idx % len(q_cols)]:
                        with st.container(border=True):
                            st.markdown(f"##### {q_display_title}")
                            st.markdown(f"🎯 **Trọng tâm 30-90 ngày:**\n{q_dict.get('focus', 'Nền tảng & Kỹ năng cốt lõi')}")
                            st.markdown(f"🏁 **Cột mốc kết quả (Target Outcome):**\n{q_dict.get('target_outcome', 'Đạt chuẩn kỳ vọng')}")
            else:
                st.caption(f"*(Chưa có phân kỳ giai đoạn. Hãy chat với {domain_terms.get('role_title', 'Architect')} ở cột bên cạnh để tự động phân rã)*")

            # Tầng 3: Tháng
            monthly_items = safe_list(bd.get("monthly", []))
            st.markdown("**📅 TẦNG 3 — PHÂN RÃ THEO THÁNG (MONTHLY):**")
            if monthly_items:
                for m_idx, m in enumerate(monthly_items, 1):
                    m_dict = safe_dict(m)
                    m_res = m_dict.get('resources', '') or 'Định kỳ theo tuần'
                    m_res_label = domain_terms.get('m_resources_label', 'Tài liệu')
                    st.markdown(f"- **{m_dict.get('month', f'Tháng {m_idx}')}:** {m_dict.get('milestone', '')} *({m_res_label}: {m_res})*")
            else:
                st.caption("*(Chưa có phân rã Tháng)*")

            # Tầng 4: Tuần
            weekly_items = safe_list(bd.get("weekly", []))
            st.markdown("**⚡ TẦNG 4 — KẾ HOẠCH HÀNH ĐỘNG TỪNG TUẦN (WEEKLY):**")
            if weekly_items:
                for w_idx, w in enumerate(weekly_items, 1):
                    w_dict = safe_dict(w)
                    w_title = w_dict.get("milestone", f"Cột mốc Tuần {w_idx}")
                    w_tasks = safe_list(w_dict.get("tasks", []))
                    w_actions = safe_list(w_dict.get("action_items", []))
                    w_hrs = w_dict.get("estimated_hours", 7.0)
                    with st.expander(f"📌 {w_dict.get('week', f'Tuần {w_idx}')}: {w_title} ({w_hrs}h)", expanded=(w_idx == 1)):
                        if w_tasks:
                            for t in w_tasks:
                                t_dict = safe_dict(t)
                                t_name = t_dict.get("task_name", "Nhiệm vụ")
                                t_energy = t_dict.get("energy_level", "🔴 Deep Work")
                                t_dod = t_dict.get("definition_of_done", "")
                                t_res_title = t_dict.get("resource_title", "")
                                t_res_url = t_dict.get("resource_url", "")

                                with st.container(border=True):
                                    st.markdown(f"**{t_energy}** &nbsp; **{t_name}**")
                                    if t_dod:
                                        st.caption(f"🏁 *Tiêu chí hoàn thành (DoD):* {t_dod}")
                                    if t_res_title and t_res_url:
                                        st.caption(f"📦 *Gói tài liệu 1-Click:* [{t_res_title}]({t_res_url})")
                                    elif t_res_url:
                                        st.caption(f"📦 *Gói tài liệu 1-Click:* [Xem tài liệu thực tế]({t_res_url})")
                        elif w_actions:
                            for act in w_actions:
                                st.markdown(f"- ▫️ {act}")
            else:
                st.caption("*(Chưa có kế hoạch tuần)*")

            # Tài nguyên chuẩn
            resources_items = safe_list(bd.get("resources", []))
            st.markdown("---")
            curated_header = domain_terms.get('curated_title', '📚 Kho Tài Liệu & Công Cụ Thẩm Định (Curated Resources):')
            st.markdown(f"#### {curated_header}")
            if resources_items:
                for r_idx, r in enumerate(resources_items, 1):
                    r_dict = safe_dict(r)
                    r_title = r_dict.get("title", f"Tài nguyên {r_idx}")
                    r_url = r_dict.get("url", "#")
                    r_type = r_dict.get("type", "Tài liệu")
                    r_how = r_dict.get("how_to_use", "Áp dụng theo lịch trình đã định.")
                    how_label = domain_terms.get('how_to_use_label', 'Hướng dẫn khai thác')
                    with st.container(border=True):
                        st.markdown(f"🔗 **[{r_title}]({r_url})** `[{r_type}]`")
                        st.caption(f"💡 *{how_label}:* {r_how}")
            else:
                empty_cap = domain_terms.get('curated_empty_caption', '*(Chưa có tài liệu)*')
                st.caption(empty_cap)

    with col_chat_arch:
        chat_header = domain_terms.get('chat_title', '💬 Trò Chuyện Cùng Strategy Architect')
        arch_title = f"{chat_header}: {selected_goal_name}" if ('selected_goal_name' in locals() and selected_goal_name) else chat_header
        st.markdown(f"#### {arch_title}")
        st.caption(domain_terms.get('chat_caption', 'Thảo luận phương pháp • Tinh chỉnh chiến lược • Chốt lộ trình 4 tầng khép kín'))

        # Hiển thị phương pháp chiến lược đang định hình (nếu có)
        current_strat = (selected_goal.get("strategy_summary", "") if ('selected_goal' in locals() and selected_goal) else "").strip()
        if current_strat:
            strat_label = domain_terms.get('strategy_label', '💡 Phương pháp chiến lược (Kim chỉ nam):')
            with st.container(border=True):
                st.markdown(f"**{strat_label}**")
                st.info(current_strat)
                if bd and bd.get("quarterly") and bd.get("weekly"):
                    st.success("✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang **Tab Giai đoạn 2 (Lịch Trình Thực Thi)** để xem và tinh chỉnh lịch chi tiết từng ngày.")

        chat_container_arch = st.container(height=450)
        with chat_container_arch:
            for msg in st.session_state[chat_arch_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Nút Chốt phương pháp & Tự động phân rã 4 tầng (Quy trình 2 Nhịp)
        target_gid = selected_goal.get("id") if ('selected_goal' in locals() and selected_goal) else None
        btn_strat_key = f"btn_finalize_strat_{target_gid or current_username}"
        finalize_btn_text = domain_terms.get('finalize_btn', '🚀 Chốt phương pháp & Tự động phân rã 4 tầng')
        if st.button(finalize_btn_text, key=btn_strat_key, type="primary", use_container_width=True):
            with st.spinner(f"{domain_terms.get('role_title', 'AI Strategy Architect')} đang phân rã lộ trình 4 tầng theo phương pháp đã chốt..."):
                if architect_chat is not None:
                    res = architect_chat(
                        user_message=f"Hãy chốt phương pháp chiến lược trên và tự động xuất bản lộ trình 4 tầng cho mục tiêu {selected_goal_name}!",
                        username=current_username,
                        goal_id=target_gid,
                        chat_history=st.session_state[chat_arch_key],
                        force_breakdown=True,
                    )
                    arch_rep = res.get("response", "Đã chốt phương pháp và phân rã lộ trình 4 tầng thành công!")
                else:
                    arch_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                st.session_state[chat_arch_key].append({"role": "user", "content": finalize_btn_text})
                st.session_state[chat_arch_key].append({"role": "assistant", "content": arch_rep})
                st.session_state[goals_key] = load_user_goals(current_username)
                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                st.toast("🎉 Đã xuất bản Lộ trình 4 Tầng & Lịch trình 7 ngày thành công!")
                st.rerun()

        if arch_input := st.chat_input(
            domain_terms.get('input_placeholder', "Thảo luận phương pháp, tinh chỉnh chiến lược hoặc gõ 'chốt phương pháp'..."),
            key=f"input_arch_{current_username}",
        ):
            st.session_state[chat_arch_key].append({"role": "user", "content": arch_input})
            with chat_container_arch:
                with st.chat_message("user"):
                    st.markdown(arch_input)
                with st.chat_message("assistant"):
                    with st.spinner(f"{domain_terms.get('role_title', 'Strategy Architect')} đang phân tích chiến lược & tài nguyên..."):
                        if architect_chat is not None:
                            res = architect_chat(
                                user_message=arch_input,
                                username=current_username,
                                goal_id=target_gid,
                                chat_history=st.session_state[chat_arch_key],
                            )
                            arch_rep = res.get("response", "Tôi đã cập nhật chiến lược vào hệ thống.")
                        else:
                            arch_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(arch_rep)
                        st.session_state[chat_arch_key].append({"role": "assistant", "content": arch_rep})
                        st.session_state[goals_key] = load_user_goals(current_username)
                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                        st.rerun()


# ------------------------------------------------------------------------------
# TAB 3: 📅 GIAI ĐOẠN 2: TRỢ LÝ ĐỒNG HÀNH THỜI GIAN THỰC (SCHEDULER & LIVE HERO)
# ------------------------------------------------------------------------------
with tab_sched:
    st.markdown("### 📅 Giai đoạn 2: Trợ Lý Đồng Hành Thời Gian Thực (Hôm Nay ➔ Từng Giờ Cụ Thể)")
    st.caption("Đồng bộ thời gian thực Asia/Ho_Chi_Minh • Từng giờ cụ thể • Ăn gì / Uống gì / Tập gì / Ngủ mấy giờ • Đồng bộ Google Calendar 2 chiều")

    col_dash_sched, col_chat_sched = st.columns([1.15, 0.85], gap="large")

    with col_dash_sched:
        ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))
        user_goals_sched = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        # ----------------------------------------------------------------------
        # ĐỒNG HỒ THỜI GIAN THỰC & BANNER "⚡ HÀNH ĐỘNG NGAY BÂY GIỜ" (ASIA/HO_CHI_MINH)
        # ----------------------------------------------------------------------
        from datetime import time as dtime, timezone as d_timezone
        vn_tz = d_timezone(timedelta(hours=7))
        now_vn = datetime.now(vn_tz)
        day_names_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        today_vi_day = day_names_vi[now_vn.weekday()]
        today_date_str = now_vn.strftime("%Y-%m-%d")
        now_time = now_vn.time()
        now_str = now_vn.strftime(f"{today_vi_day}, ngày %d/%m/%Y — %H:%M (Giờ VN)")

        today_tasks = [
            t for t in ms
            if t.get("date") == today_date_str
            or (not str(t.get("date", "")).startswith("202") and t.get("date") == today_vi_day)
        ]
        active_hero_task = None
        upcoming_hero_task = None

        for tk in today_tasks:
            t_slot = tk.get("time_slot", "")
            if "-" in t_slot:
                try:
                    parts = t_slot.split("-")
                    s_h, s_m = map(int, parts[0].strip().split(":"))
                    e_h, e_m = map(int, parts[1].strip().split(":"))
                    s_t = dtime(s_h, s_m)
                    e_t = dtime(e_h, e_m)

                    if s_t <= now_time <= e_t:
                        active_hero_task = tk
                        break
                    elif s_t > now_time and upcoming_hero_task is None:
                        upcoming_hero_task = tk
                except Exception:
                    pass

        target_hero_task = active_hero_task or upcoming_hero_task
        is_live = (active_hero_task is not None)

        with st.container(border=True):
            col_hero_status, col_hero_clock = st.columns([0.65, 0.35])
            with col_hero_status:
                if is_live:
                    st.markdown("#### ⚡ HÀNH ĐỘNG NGAY BÂY GIỜ `[🟢 Đang diễn ra]`")
                elif target_hero_task:
                    st.markdown("#### ⚡ HÀNH ĐỘNG TIẾP THEO `[⏰ Sắp bắt đầu]`")
                else:
                    st.markdown("#### ⚡ TRẠNG THÁI HIỆN TẠI `[🌙 Phục hồi & Giấc ngủ]`")
            with col_hero_clock:
                st.markdown(f"🕒 **{now_str}**")

            if target_hero_task:
                h_detail = target_hero_task.get("task_detail", "Nhiệm vụ")
                h_slot = target_hero_task.get("time_slot", "")
                h_goal = target_hero_task.get("goal_title", "")
                h_energy = target_hero_task.get("energy_level", "🔴 Deep Work")
                h_dod = target_hero_task.get("definition_of_done", "")
                h_link = target_hero_task.get("resource_url") or target_hero_task.get("resource_link", "")
                h_is_done = bool(target_hero_task.get("is_done", False))

                col_h_chk, col_h_info = st.columns([0.08, 0.92])
                with col_h_chk:
                    hero_key = f"chk_hero_{current_username}_{today_vi_day}_{abs(hash(h_detail)) % 100000}"
                    new_h_done = st.checkbox("", value=h_is_done, key=hero_key, label_visibility="collapsed")
                    if new_h_done != h_is_done:
                        update_master_schedule_task_status(
                            task_identifier=h_detail,
                            is_done=new_h_done,
                            date=target_hero_task.get("date") or today_date_str,
                            username=current_username,
                        )
                        target_hero_task["is_done"] = new_h_done
                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                        st.toast(f"✅ Đã cập nhật: {h_detail[:35]}...")
                        st.rerun()
                with col_h_info:
                    st.markdown(f"**{h_energy}** &nbsp;|&nbsp; ⏰ **{h_slot}** — **{h_detail}** `[🎯 {h_goal}]`")
                    if h_is_done:
                        st.caption("✅ :green[**Đã hoàn thành xuất sắc!**]")
                    if h_dod:
                        st.caption(f"🏁 **Tiêu chí hoàn thành (DoD):** {h_dod}")
                    if h_link:
                        st.link_button("📦 Mở Tài Liệu Thực Tế (1-Click)", url=h_link)
            else:
                st.info("🌙 Hiện tại bạn đang ngoài khung giờ Deep Work. Hãy thư giãn, uống nước ấm hoặc chuẩn bị ngủ sớm 22:30 để tái tạo năng lượng cho ngày mai!")

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 1. THANH CHỌN CHẾ ĐỘ VẬN HÀNH HÔM NAY (TÁI CẤU TRÚC ĐỘNG THEO NĂNG LƯỢNG)
        # ----------------------------------------------------------------------
        energy_mode_key = f"energy_mode_{current_username}"
        if energy_mode_key not in st.session_state:
            st.session_state[energy_mode_key] = "🚀 Chiến Thần (100%)"

        st.markdown("#### 🔋 Chế Độ Vận Hành Hôm Nay:")
        col_em1, col_em2, col_em3 = st.columns(3)
        with col_em1:
            is_active_100 = (st.session_state[energy_mode_key] == "🚀 Chiến Thần (100%)")
            if st.button("🚀 Chiến Thần (100%)", key=f"btn_em_100_{current_username}", type="primary" if is_active_100 else "secondary", use_container_width=True):
                st.session_state[energy_mode_key] = "🚀 Chiến Thần (100%)"
                st.rerun()
        with col_em2:
            is_active_30 = (st.session_state[energy_mode_key] == "🛡️ Duy Trì Tối Thiểu (30% - Khi mệt/bận)")
            if st.button("🛡️ Duy Trì Tối Thiểu (30%)", key=f"btn_em_30_{current_username}", type="primary" if is_active_30 else "secondary", use_container_width=True):
                st.session_state[energy_mode_key] = "🛡️ Duy Trì Tối Thiểu (30% - Khi mệt/bận)"
                st.rerun()
        with col_em3:
            is_active_rec = (st.session_state[energy_mode_key] == "🔄 Xả Hơi (Recovery)")
            if st.button("🔄 Xả Hơi (Recovery)", key=f"btn_em_rec_{current_username}", type="primary" if is_active_rec else "secondary", use_container_width=True):
                st.session_state[energy_mode_key] = "🔄 Xả Hơi (Recovery)"
                st.rerun()

        cur_energy_mode = st.session_state[energy_mode_key]

        if cur_energy_mode == "🚀 Chiến Thần (100%)":
            st.success("⚡ **Chế độ Chiến Thần (100%):** Vận hành toàn bộ công suất theo đúng lịch trình chuẩn của nhịp sinh học.")
        elif cur_energy_mode == "🛡️ Duy Trì Tối Thiểu (30% - Khi mệt/bận)":
            st.warning("🛡️ **Chế độ Duy Trì Tối Thiểu (30%):** Đã tự động lọc chỉ giữ lại tối đa 3 task nhẹ nhàng nhất trong ngày để giữ streak kỷ luật. Các task 🔴 Deep Work đã tự động trượt sang ngày mai mà không ghi nhận trễ hạn.")
        else:
            st.info("🛌 **Chế độ Xả Hơi (Recovery):** Tạm gác toàn bộ task học tập & deep work để hệ thần kinh nghỉ ngơi, chỉ hiển thị checklist hồi phục năng lượng.")

        st.markdown("---")

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

        # Xử lý theo từng chế độ
        if cur_energy_mode == "🔄 Xả Hơi (Recovery)":
            st.markdown("#### 🌿 Checklist Phục Hồi & Tái Tạo Năng Lượng (Active Recovery Protocol):")
            recovery_items = [
                {
                    "slot": "07:30 - 08:30",
                    "title": "Uống 500ml nước ấm & đón ánh sáng mặt trời tự nhiên 15 phút",
                    "energy": "🟢 Recharge",
                    "dod": "Kích hoạt nhịp cortisol tự nhiên, bù nước sau đêm dài và đánh thức đồng hồ sinh học.",
                    "link": "https://hubermanlab.com",
                    "res_title": "Huberman Protocol: Tối ưu ánh sáng & nhịp sinh học",
                },
                {
                    "slot": "12:30 - 13:00",
                    "title": "Nghỉ trưa ngắn (Power Nap) 20 phút & thư giãn hoàn toàn không điện thoại",
                    "energy": "🟢 Recharge",
                    "dod": "Thả lỏng cơ thể, hạ nhịp tim, giải phóng adenosine tích tụ trong não bộ.",
                    "link": "",
                    "res_title": "",
                },
                {
                    "slot": "17:30 - 18:15",
                    "title": "Đi bộ ngoài trời 30 - 40 phút trong không gian xanh (Zone 2 Cardio nhẹ)",
                    "energy": "🟢 Recharge",
                    "dod": "Đạt 4.000 - 5.000 bước chân nhịp nhàng, hít thở sâu, không nghe nội dung áp lực.",
                    "link": "",
                    "res_title": "",
                },
                {
                    "slot": "21:30 - 22:30",
                    "title": "Tắt toàn bộ màn hình xanh, ngâm chân nước ấm và đi ngủ trước 22:30",
                    "energy": "🟢 Recharge",
                    "dod": "Ngủ đủ 7.5 - 8 tiếng trong phòng thoáng mát, tối hoàn toàn để não bộ dọn dẹp độc tố.",
                    "link": "https://sleepfoundation.org",
                    "res_title": "Sleep Foundation: Khoa học giấc ngủ sâu phục hồi nhận thức",
                },
            ]

            for r_idx, r_item in enumerate(recovery_items):
                r_key = f"chk_rec_{current_username}_{r_idx}"
                r_done = bool(st.session_state.get(r_key, False))
                with st.container(border=True):
                    col_r_chk, col_r_info = st.columns([0.08, 0.92])
                    with col_r_chk:
                        new_r_done = st.checkbox("", value=r_done, key=r_key, label_visibility="collapsed")
                        if new_r_done != r_done:
                            st.session_state[r_key] = new_r_done
                            st.toast(f"✅ Hoàn thành: {r_item['title'][:35]}...")
                            st.rerun()
                    with col_r_info:
                        st.markdown(f"**{r_item['energy']}** &nbsp;|&nbsp; ⏰ **{r_item['slot']}** — **{r_item['title']}**")
                        if new_r_done:
                            st.caption("✅ :green[**Đã hoàn thành xuất sắc!**]")
                        st.caption(f"🏁 **Tiêu chí hoàn thành (DoD):** {r_item['dod']}")
                        if r_item.get("link"):
                            st.link_button(f"📦 Mở Tài Liệu: {r_item['res_title']}", url=r_item["link"])

        else:
            STANDARD_DAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            DAY_SHORT = {
                "Thứ Hai": "Thứ 2",
                "Thứ Ba": "Thứ 3",
                "Thứ Tư": "Thứ 4",
                "Thứ Năm": "Thứ 5",
                "Thứ Sáu": "Thứ 6",
                "Thứ Bảy": "Thứ 7",
                "Chủ Nhật": "Chủ Nhật",
            }

            # ------------------------------------------------------------------
            # XÁC ĐỊNH TRỤC THỜI GIAN THỰC (start_date -> target_date)
            # ------------------------------------------------------------------
            today_date = get_vietnam_today()
            active_user_goals = [g for g in user_goals_sched if g.get("status") == "active"]
            if not active_user_goals:
                active_user_goals = [g for g in user_goals_sched if g.get("status") not in ("paused", "completed")]

            start_dates = []
            target_dates = []
            for g in (active_user_goals or user_goals_sched):
                sd_str = g.get("start_date")
                td_str = g.get("target_date")
                if sd_str:
                    try:
                        start_dates.append(datetime.strptime(str(sd_str)[:10], "%Y-%m-%d").date())
                    except Exception:
                        pass
                if td_str:
                    try:
                        target_dates.append(datetime.strptime(str(td_str)[:10], "%Y-%m-%d").date())
                    except Exception:
                        pass

            base_start_date = min(start_dates) if start_dates else today_date
            min_date_limit = min(base_start_date, today_date)
            base_target_date = max(target_dates) if target_dates else (base_start_date + timedelta(days=90))
            if base_target_date < min_date_limit:
                base_target_date = min_date_limit + timedelta(days=90)

            # Lưu vết ngày thực tế đang chọn
            sel_date_key = f"selected_sched_date_{current_username}"
            if sel_date_key not in st.session_state:
                st.session_state[sel_date_key] = today_date

            current_picked_date = st.session_state.get(sel_date_key, today_date)
            if not isinstance(current_picked_date, date):
                try:
                    current_picked_date = datetime.strptime(str(current_picked_date)[:10], "%Y-%m-%d").date()
                except Exception:
                    current_picked_date = today_date

            if current_picked_date < min_date_limit:
                current_picked_date = min_date_limit
            elif current_picked_date > base_target_date:
                current_picked_date = base_target_date

            # ------------------------------------------------------------------
            # 1. BỘ CHỌN GÓC NHÌN THỜI GIAN & PHẠM VI MỤC TIÊU
            # ------------------------------------------------------------------
            st.markdown("#### 🧭 Góc Nhìn Thời Gian & Lịch Trình Điều Hành:")
            view_options = ["📅 Theo Ngày", "🗓️ Theo Tuần", "📆 Theo Tháng", "📊 Theo Quý"]
            view_key = f"sched_view_mode_{current_username}"
            if hasattr(st, "segmented_control"):
                selected_view = st.segmented_control(
                    "Góc nhìn thời gian:",
                    options=view_options,
                    default=st.session_state.get(view_key, "📅 Theo Ngày"),
                    key=view_key,
                    label_visibility="collapsed",
                )
            else:
                default_idx = view_options.index(st.session_state.get(view_key, "📅 Theo Ngày")) if st.session_state.get(view_key) in view_options else 0
                selected_view = st.radio(
                    "Góc nhìn thời gian:",
                    options=view_options,
                    index=default_idx,
                    horizontal=True,
                    key=view_key,
                    label_visibility="collapsed",
                )
            if not selected_view:
                selected_view = "📅 Theo Ngày"

            col_mode, col_spec = st.columns([1.1, 0.9])
            with col_mode:
                mode = st.radio(
                    "Phạm vi hiển thị:",
                    options=["🌐 Lịch Tổng Hợp Tất Cả Mục Tiêu (Master Schedule)", "🎯 Xem Lịch Riêng Theo Từng Mục Tiêu"],
                    horizontal=True,
                    key=f"sched_mode_{current_username}",
                )

            # Tự động đảm bảo Master Schedule có dữ liệu cho ngày đang xem
            full_master_sched = ensure_schedule_covers_date(current_picked_date, active_goals=active_user_goals, username=current_username)
            filtered_schedule = full_master_sched
            chosen_g = None
            with col_spec:
                if mode == "🎯 Xem Lịch Riêng Theo Từng Mục Tiêu":
                    unique_goals = list(dict.fromkeys(t.get("goal_title", "Mục tiêu") for t in filtered_schedule if t.get("goal_title")))
                    if unique_goals:
                        chosen_g = st.selectbox("Chọn mục tiêu cụ thể:", options=unique_goals, key=f"sel_ms_goal_{current_username}")
                        filtered_schedule = [t for t in filtered_schedule if t.get("goal_title") == chosen_g]
                    else:
                        st.info("Chưa có mục tiêu nào trong lịch.")

            # Nút xuất lịch ICS & Google Calendar
            c_ics, c_gcal, c_gsync = st.columns(3)
            with c_ics:
                ics_text = generate_ics_from_master_schedule(filtered_schedule, current_username)
                st.download_button(
                    label="📥 Tải File Lịch (.ics)",
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
                    resource_info=first_task.get("resource_url") or first_task.get("resource_link", ""),
                )
                st.link_button("🌐 Mở Google Calendar (1-Chạm)", url=gcal_link, use_container_width=True)
            with c_gsync:
                if is_calendar_connected(current_username):
                    if st.button("🔄 Đồng Bộ Lên Google Calendar", key=f"btn_sync_gcal_tab2_{current_username}", type="primary", use_container_width=True):
                        with st.spinner("Đang đẩy các sự kiện sang Google Calendar..."):
                            sync_res = sync_schedule_to_google_calendar(current_username, filtered_schedule)
                            if sync_res.get("success"):
                                st.success(f"✅ {sync_res.get('message')}")
                                st.toast("🎉 Đã đồng bộ lịch lên Google Calendar thành công!")
                            else:
                                st.error(f"❌ {sync_res.get('message')}")
                else:
                    st.caption("*(Chưa kết nối Google Calendar)*")

            st.markdown("---")

            if not filtered_schedule:
                st.info(
                    "💡 Chưa có lịch trình. Bạn hãy trao đổi với **AI Master Scheduler** ở cột bên phải "
                    "(ví dụ: *'Hãy phân bổ lịch trình chi tiết cho mục tiêu của tôi'*) để tạo lịch ngay lập tức!"
                )
            else:
                # ==============================================================
                # GÓC NHÌN 1: 📅 THEO NGÀY (DAILY VIEW VỚI DATE_INPUT THỜI GIAN THỰC)
                # ==============================================================
                if selected_view == "📅 Theo Ngày":
                    col_dp1, col_dp2 = st.columns([0.70, 0.30])
                    with col_dp1:
                        new_picked_date = st.date_input(
                            "📅 Chọn ngày thực tế trên lộ trình:",
                            value=current_picked_date,
                            min_value=min_date_limit,
                            max_value=base_target_date,
                            format="DD/MM/YYYY",
                            key=f"picker_daily_date_{current_username}",
                        )
                        if new_picked_date != current_picked_date:
                            st.session_state[sel_date_key] = new_picked_date
                            st.rerun()
                    with col_dp2:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("📍 Về Hôm Nay", key=f"btn_back_today_{current_username}", use_container_width=True):
                            st.session_state[sel_date_key] = today_date
                            st.rerun()

                    # Tính toán thông số ngày
                    day_offset_num = (new_picked_date - base_start_date).days + 1
                    total_road_days = (base_target_date - base_start_date).days
                    if total_road_days <= 0:
                        total_road_days = 90
                    day_name_viet = VIETNAM_WEEKDAYS.get(new_picked_date.weekday(), "Thứ Bảy")
                    date_display_str = new_picked_date.strftime("%d/%m/%Y")
                    cur_d_iso = new_picked_date.strftime("%Y-%m-%d")

                    if day_offset_num < 1:
                        banner_title = f"🎯 Chuẩn Bị (Cách ngày bắt đầu {abs(day_offset_num - 1)} ngày) — {day_name_viet}, {date_display_str}"
                    elif day_offset_num > total_road_days:
                        banner_title = f"🎯 Đã Về Đích ({day_offset_num}/{total_road_days}) — {day_name_viet}, {date_display_str}"
                    else:
                        banner_title = f"🎯 Ngày {day_offset_num}/{total_road_days} — {day_name_viet}, {date_display_str}"

                    st.markdown(f"### {banner_title}")

                    # Lọc task theo ngày đang chọn
                    day_tasks = [
                        t for t in filtered_schedule
                        if t.get("date") == cur_d_iso
                        or (not str(t.get("date", "")).startswith("202") and t.get("date") == day_name_viet)
                    ]
                    deferred_tasks = []
                    displayed_tasks = day_tasks

                    if cur_energy_mode == "🛡️ Duy Trì Tối Thiểu (30% - Khi mệt/bận)":
                        light_tasks = []
                        heavy_tasks = []
                        for t in day_tasks:
                            e_str = str(t.get("energy_level", "")).lower()
                            if "shallow" in e_str or "recharge" in e_str or "🟡" in e_str or "🟢" in e_str:
                                light_tasks.append(t)
                            else:
                                heavy_tasks.append(t)

                        if len(light_tasks) >= 3:
                            displayed_tasks = light_tasks[:3]
                            deferred_tasks = heavy_tasks + light_tasks[3:]
                        else:
                            needed = 3 - len(light_tasks)
                            displayed_tasks = light_tasks + heavy_tasks[:needed]
                            deferred_tasks = heavy_tasks[needed:]

                    done_day = sum(1 for t in displayed_tasks if t.get("is_done") is True)
                    total_day = len(displayed_tasks)
                    pct_day = int((done_day / total_day * 100)) if total_day > 0 else 0

                    c_m1, c_m2, c_m3 = st.columns(3)
                    with c_m1:
                        st.metric("📌 Tổng nhiệm vụ ngày", f"{total_day} task")
                    with c_m2:
                        st.metric("✅ Đã hoàn thành", f"{done_day}/{total_day}")
                    with c_m3:
                        st.metric("⚡ Tỷ lệ thực thi", f"{pct_day}%")

                    st.progress(pct_day / 100)

                    if not displayed_tasks:
                        st.info(f"🌿 Ngày **{day_name_viet}, {date_display_str}** hiện chưa có lịch trình. Bạn có thể nhấn chat với Scheduler để xếp lịch bổ sung.")

                    for sess in ["Sáng", "Chiều", "Tối"]:
                        sess_tasks = [t for t in displayed_tasks if t.get("session") == sess]
                        if sess_tasks:
                            st.markdown(f"##### ⏰ Buổi {sess}:")
                            for idx, task in enumerate(sess_tasks):
                                t_detail = task.get("task_detail", "Nhiệm vụ")
                                t_slot = task.get("time_slot", "08:00 - 10:00")
                                t_goal = task.get("goal_title", "")
                                t_link = task.get("resource_url") or task.get("resource_link", "")
                                t_res_title = task.get("resource_title", "")
                                is_done_val = bool(task.get("is_done", False))

                                t_energy = task.get("energy_level")
                                if not t_energy:
                                    if sess == "Sáng":
                                        t_energy = "🔴 Deep Work"
                                    elif sess == "Chiều":
                                        t_energy = "🟡 Shallow Work"
                                    else:
                                        t_energy = "🟢 Recharge"

                                t_dod = task.get("definition_of_done")
                                if not t_dod:
                                    t_dod = f"Hoàn thành trọn vẹn nội dung '{t_detail}' và ghi chú tiến độ."

                                chk_key = f"chk_day_{current_username}_{cur_d_iso}_{sess}_{idx}_{abs(hash(t_detail)) % 100000}"

                                with st.container(border=True):
                                    col_chk, col_card = st.columns([0.08, 0.92])
                                    with col_chk:
                                        checked = st.checkbox("", value=is_done_val, key=chk_key, label_visibility="collapsed")
                                        if checked != is_done_val:
                                            update_master_schedule_task_status(
                                                task_identifier=t_detail,
                                                is_done=checked,
                                                date=cur_d_iso,
                                                username=current_username,
                                            )
                                            task["is_done"] = checked
                                            st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                            st.toast(f"✅ Đã cập nhật: {t_detail[:35]}...")
                                            st.rerun()
                                    with col_card:
                                        clean_detail = str(t_detail).replace('**', '').replace('__', '').strip()
                                        clean_dod = str(t_dod).replace('**', '').replace('__', '').strip()
                                        clean_slot = str(t_slot).replace('**', '').replace('__', '').strip()
                                        if t_goal:
                                            st.markdown(f"**{t_energy}** &nbsp;|&nbsp; ⏰ **{clean_slot}** — **{clean_detail}** `[🎯 {t_goal}]`")
                                        else:
                                            st.markdown(f"**{t_energy}** &nbsp;|&nbsp; ⏰ **{clean_slot}** — **{clean_detail}**")

                                        if is_done_val:
                                            st.caption("✅ :green[**Đã hoàn thành xuất sắc!**]")

                                        st.caption(f"🏁 **Tiêu chí hoàn thành (DoD):** {clean_dod}")

                                        if t_link:
                                            btn_lbl = f"📦 Mở Tài Liệu: {t_res_title}" if (t_res_title and len(t_res_title) < 35) else "📦 Mở Tài Liệu Thực Tế (1-Click)"
                                            st.link_button(label=btn_lbl, url=t_link, use_container_width=False)

                    if deferred_tasks:
                        st.markdown("---")
                        with st.expander(f"💤 {len(deferred_tasks)} task Deep Work đã tự động trượt sang ngày mai (Bảo toàn Streak, không tính trễ):", expanded=False):
                            for dt in deferred_tasks:
                                dt_title = dt.get("task_detail", "Nhiệm vụ")
                                dt_slot = dt.get("time_slot", "")
                                dt_goal = dt.get("goal_title", "")
                                st.markdown(f"- ▫️ ⏰ **{dt_slot}**: {dt_title} `[🎯 {dt_goal}]` &nbsp; `:orange[Đã trượt sang ngày mai]`")

                # ==============================================================
                # GÓC NHÌN 2: 🗓️ THEO TUẦN (WEEKLY MATRIX VIEW THEO NGÀY THỰC TẾ)
                # ==============================================================
                elif selected_view == "🗓️ Theo Tuần":
                    mon_of_week = current_picked_date - timedelta(days=current_picked_date.weekday())
                    week_dates = [mon_of_week + timedelta(days=i) for i in range(7)]

                    # Header điều hướng tuần
                    col_nav1, col_nav2, col_nav3 = st.columns([0.25, 0.50, 0.25])
                    with col_nav1:
                        if st.button("⬅️ Tuần Trước", key=f"btn_prev_wk_{current_username}", use_container_width=True):
                            st.session_state[sel_date_key] = max(min_date_limit, current_picked_date - timedelta(days=7))
                            st.rerun()
                    with col_nav2:
                        st.markdown(f"<p style='text-align:center; font-weight:bold; margin-top:5px;'>🗓️ Tuần: {week_dates[0].strftime('%d/%m')} ➔ {week_dates[6].strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
                    with col_nav3:
                        if st.button("Tuần Sau ➡️", key=f"btn_next_wk_{current_username}", use_container_width=True):
                            st.session_state[sel_date_key] = min(base_target_date, current_picked_date + timedelta(days=7))
                            st.rerun()

                    # Lọc toàn bộ task của tuần này
                    week_iso_dates = set(d.strftime("%Y-%m-%d") for d in week_dates)
                    week_tasks = [t for t in filtered_schedule if t.get("date") in week_iso_dates]

                    total_wk = len(week_tasks)
                    done_wk = sum(1 for t in week_tasks if t.get("is_done") is True)
                    pct_wk = int((done_wk / total_wk * 100)) if total_wk > 0 else 0

                    c_w1, c_w2, c_w3 = st.columns(3)
                    with c_w1:
                        st.metric("🗓️ Tổng nhiệm vụ tuần", f"{total_wk} task")
                    with c_w2:
                        st.metric("✅ Đã hoàn thành tuần", f"{done_wk}/{total_wk}")
                    with c_w3:
                        st.metric("⚡ Tiến độ thực thi tuần", f"{pct_wk}%")

                    st.progress(pct_wk / 100)
                    st.caption("💡 Bấm nút '🔍 Mở ngày' trên từng cột để mở ngay chi tiết lịch ngày hôm đó:")

                    # Header 7 cột cho 7 ngày thực tế
                    col_headers = st.columns(7)
                    for d_idx, d_obj in enumerate(week_dates):
                        d_str = d_obj.strftime("%Y-%m-%d")
                        d_short_date = d_obj.strftime("%d/%m")
                        d_name = VIETNAM_WEEKDAYS.get(d_obj.weekday(), "")
                        d_tasks = [
                            t for t in filtered_schedule
                            if t.get("date") == d_str
                            or (not str(t.get("date", "")).startswith("202") and t.get("date") == d_name)
                        ]
                        d_done = sum(1 for t in d_tasks if t.get("is_done") is True)
                        d_tot = len(d_tasks)
                        with col_headers[d_idx]:
                            is_today_col = (d_obj == today_date)
                            badge_style = "color:#ff4b4b;" if is_today_col else ""
                            st.markdown(f"<span style='{badge_style}'>**{DAY_SHORT.get(d_name, d_name)}**</span> `({d_short_date})`", unsafe_allow_html=True)
                            if d_tot > 0:
                                st.caption(f"{d_done}/{d_tot} xong")
                            else:
                                st.caption("Nghỉ")
                            if st.button("🔍 Mở ngày", key=f"btn_open_wkd_{current_username}_{d_str}", use_container_width=True):
                                st.session_state[sel_date_key] = d_obj
                                st.session_state[view_key] = "📅 Theo Ngày"
                                st.rerun()

                    # 3 Hàng: Sáng / Chiều / Tối
                    session_defs = [
                        ("🌅 Buổi Sáng", "Sáng", "06:30 - 11:30"),
                        ("☀️ Buổi Chiều", "Chiều", "12:00 - 18:30"),
                        ("🌙 Buổi Tối", "Tối", "19:00 - 22:30"),
                    ]

                    for sess_title, sess_name, sess_time in session_defs:
                        st.markdown(f"##### {sess_title} ({sess_time}):")
                        cols_sess = st.columns(7)
                        for d_idx, d_obj in enumerate(week_dates):
                            d_str = d_obj.strftime("%Y-%m-%d")
                            d_name = VIETNAM_WEEKDAYS.get(d_obj.weekday(), "")
                            with cols_sess[d_idx]:
                                cell_tasks = [
                                    t for t in filtered_schedule
                                    if (t.get("date") == d_str or (not str(t.get("date", "")).startswith("202") and t.get("date") == d_name))
                                    and t.get("session") == sess_name
                                ]
                                if not cell_tasks:
                                    st.caption("▫️ *Trống*")
                                else:
                                    for t_idx, tk in enumerate(cell_tasks):
                                        t_detail = tk.get("task_detail", "Nhiệm vụ")
                                        t_energy = tk.get("energy_level", "🔴 Deep Work")
                                        energy_badge = "🔴" if ("deep" in str(t_energy).lower() or "🔴" in str(t_energy)) else ("🟡" if ("shallow" in str(t_energy).lower() or "🟡" in str(t_energy)) else "🟢")
                                        t_is_done = bool(tk.get("is_done", False))
                                        t_dod = tk.get("definition_of_done", "")
                                        t_link = tk.get("resource_url") or tk.get("resource_link", "")

                                        wk_chk_key = f"chk_wk_{current_username}_{d_str}_{sess_name}_{t_idx}_{abs(hash(t_detail)) % 100000}"

                                        with st.container(border=True):
                                            c_w_chk, c_w_txt = st.columns([0.22, 0.78])
                                            with c_w_chk:
                                                new_done = st.checkbox("", value=t_is_done, key=wk_chk_key, label_visibility="collapsed")
                                                if new_done != t_is_done:
                                                    update_master_schedule_task_status(
                                                        task_identifier=t_detail,
                                                        is_done=new_done,
                                                        date=d_str,
                                                        username=current_username,
                                                    )
                                                    st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                                    st.toast(f"✅ Đã cập nhật: {t_detail[:30]}...")
                                                    st.rerun()
                                            with c_w_txt:
                                                clean_slot = str(tk.get('time_slot', '')).replace('**', '').replace('__', '').strip()
                                                clean_detail = str(t_detail).replace('**', '').replace('__', '').strip()
                                                clean_dod = str(t_dod).replace('**', '').replace('__', '').strip()

                                                st.markdown(f"{energy_badge} **{clean_slot}**")
                                                if t_is_done:
                                                    st.markdown(f"<div style='font-size:0.8rem; text-decoration:line-through; color:gray; line-height:1.25; word-break:break-word; margin-bottom:3px;'>{clean_detail}</div>", unsafe_allow_html=True)
                                                else:
                                                    st.markdown(f"<div style='font-size:0.82rem; font-weight:600; line-height:1.25; word-break:break-word; margin-bottom:3px;'>{clean_detail}</div>", unsafe_allow_html=True)
                                                if clean_dod:
                                                    st.markdown(f"<div style='font-size:0.75rem; color:#555; line-height:1.2; word-break:break-word; margin-bottom:4px;'>🏁 {clean_dod}</div>", unsafe_allow_html=True)
                                                if t_link:
                                                    st.link_button("📦 Tài liệu", url=t_link, use_container_width=True)

                # ==============================================================
                # GÓC NHÌN 3: 📆 THEO THÁNG (MONTHLY GRID THEO NGÀY THỰC TẾ)
                # ==============================================================
                elif selected_view == "📆 Theo Tháng":
                    tot_mth = len(filtered_schedule)
                    done_mth = sum(1 for t in filtered_schedule if t.get("is_done") is True)
                    pct_mth = int((done_mth / tot_mth * 100)) if tot_mth > 0 else 0

                    c_m1, c_m2, c_m3 = st.columns(3)
                    with c_m1:
                        st.metric("📆 Nhiệm vụ tháng", f"{tot_mth} task")
                    with c_m2:
                        st.metric("✅ Đã hoàn thành", f"{done_mth}/{tot_mth}")
                    with c_m3:
                        st.metric("⚡ Tỷ lệ tích lũy tháng", f"{pct_mth}%")

                    st.progress(pct_mth / 100)

                    # Hiển thị 4 tuần liên tiếp bắt đầu từ tuần của base_start_date
                    mth_mon = base_start_date - timedelta(days=base_start_date.weekday())
                    for w_idx in range(4):
                        w_start = mth_mon + timedelta(days=w_idx * 7)
                        w_end = w_start + timedelta(days=6)
                        st.markdown(f"#### 🗓️ Tuần {w_idx+1}: {w_start.strftime('%d/%m')} ➔ {w_end.strftime('%d/%m/%Y')}")
                        cols_m_days = st.columns(7)
                        for d_idx in range(7):
                            curr_m_date = w_start + timedelta(days=d_idx)
                            m_str = curr_m_date.strftime("%Y-%m-%d")
                            m_short = curr_m_date.strftime("%d/%m")
                            m_name = VIETNAM_WEEKDAYS.get(curr_m_date.weekday(), "")

                            day_tasks = [
                                t for t in filtered_schedule
                                if t.get("date") == m_str
                                or (not str(t.get("date", "")).startswith("202") and t.get("date") == m_name)
                            ]
                            d_done = sum(1 for t in day_tasks if t.get("is_done") is True)
                            d_tot = len(day_tasks)
                            with cols_m_days[d_idx]:
                                with st.container(border=True):
                                    is_curr_day = (curr_m_date == today_date)
                                    badge_lbl = f"<span style='color:#ff4b4b;'>**{DAY_SHORT.get(m_name, m_name)}**</span> `({m_short})`" if is_curr_day else f"**{DAY_SHORT.get(m_name, m_name)}** `({m_short})`"
                                    st.markdown(badge_lbl, unsafe_allow_html=True)
                                    badge_color = ":green" if (d_tot > 0 and d_done == d_tot) else (":orange" if d_done > 0 else ":gray")
                                    st.caption(f"{badge_color}[**{d_done}/{d_tot} xong**]")

                                    if st.button("🔍 Xem", key=f"btn_mth_open_{current_username}_{w_idx}_{d_idx}_{m_str}", use_container_width=True):
                                        st.session_state[sel_date_key] = curr_m_date
                                        st.session_state[view_key] = "📅 Theo Ngày"
                                        st.rerun()

                                    if day_tasks:
                                        for t_idx, tk in enumerate(day_tasks[:2]):
                                            t_detail = tk.get("task_detail", "Nhiệm vụ")
                                            t_energy = tk.get("energy_level", "🔴")
                                            e_icon = "🔴" if "deep" in str(t_energy).lower() or "🔴" in str(t_energy) else ("🟡" if "shallow" in str(t_energy).lower() or "🟡" in str(t_energy) else "🟢")
                                            t_done = bool(tk.get("is_done", False))
                                            m_chk_key = f"chk_mth_{current_username}_{w_idx}_{m_str}_{t_idx}_{abs(hash(t_detail)) % 100000}"

                                            new_m_done = st.checkbox(
                                                f"{e_icon} {t_detail[:22]}...",
                                                value=t_done,
                                                key=m_chk_key,
                                            )
                                            if new_m_done != t_done:
                                                update_master_schedule_task_status(
                                                    task_identifier=t_detail,
                                                    is_done=new_m_done,
                                                    date=m_str,
                                                    username=current_username,
                                                )
                                                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                                st.toast(f"✅ Đã cập nhật: {t_detail[:30]}...")
                                                st.rerun()
                                    else:
                                        st.caption("▫️ *Không có task*")

                # ==============================================================
                # GÓC NHÌN 4: 📊 THEO QUÝ (QUARTERLY 90-DAY ROADMAP VIEW)
                # ==============================================================
                elif selected_view == "📊 Theo Quý":
                    q_total = len(filtered_schedule)
                    q_done = sum(1 for t in filtered_schedule if t.get("is_done") is True)
                    q_pct = int((q_done / q_total * 100)) if q_total > 0 else 0

                    st.markdown("#### 🚀 Tổng Quan Lộ Trình 90 Ngày (Quý I - 3 Giai Đoạn):")
                    c_q1, c_q2, c_q3, c_q4 = st.columns(4)
                    with c_q1:
                        st.metric("🏁 Tiến độ Quý (90 ngày)", f"{q_pct}%")
                    with c_q2:
                        st.metric("📋 Tổng nhiệm vụ đã lập", f"{q_total} task")
                    with c_q3:
                        st.metric("✅ Đã hoàn thành thực tế", f"{q_done} task")
                    with c_q4:
                        st.metric("⏳ Nhiệm vụ đang chờ", f"{q_total - q_done} task")

                    st.progress(q_pct / 100)

                    # 3 Giai đoạn của Quý
                    quarter_phases = [
                        {
                            "phase_num": 1,
                            "title": "Giai Đoạn 1: Tháng 1 (Ngày 1 - 30) — Xây Dựng Nền Tảng & Thói Quen Cốt Lõi",
                            "focus": "Thiết lập nhịp sinh học cố định, nạp kiến thức/kỹ năng nền móng, xây dựng chuỗi kỷ luật 30 ngày không đứt đoạn.",
                            "target": "Đạt 100% thời lượng cam kết mỗi ngày, hoàn thành bộ giáo trình/bài tập cơ bản.",
                            "progress": min(100, int(q_pct * 1.5)) if q_pct > 0 else 0,
                            "resources": "Bộ tài liệu nhập môn, checklist theo dõi nhịp sinh học, Notion Tracker.",
                        },
                        {
                            "phase_num": 2,
                            "title": "Giai Đoạn 2: Tháng 2 (Ngày 31 - 60) — Tăng Tốc Khối Lượng & Chuyên Sâu Kỹ Năng",
                            "focus": "Gia tăng độ khó của bài tập Deep Work, chuyển dần sang giải quyết bài toán phức tạp và thực hành chuyên sâu.",
                            "target": "Vượt qua ngưỡng cản tâm lý (Plateau), tăng 40% khối lượng thực hành thực tế.",
                            "progress": min(100, int(q_pct * 1.0)) if q_pct > 0 else 0,
                            "resources": "Tài liệu chuyên sâu, đề thi thử / dự án thực chiến, công cụ đo lường KPI.",
                        },
                        {
                            "phase_num": 3,
                            "title": "Giai Đoạn 3: Tháng 3 (Ngày 61 - 90) — Thực Chiến Đỉnh Cao & Chạm Mốc KPI",
                            "focus": "Tổng ôn, mô phỏng áp lực thực tế, đóng gói kết quả đầu ra và kiểm thử tiêu chuẩn hoàn thành DoD.",
                            "target": "Chạm mốc mục tiêu đầu ra đã cam kết với CEO Coach (VD: IELTS 7.5, Giảm 15kg, Hoàn thành dự án).",
                            "progress": min(100, int(q_pct * 0.7)) if q_pct > 0 else 0,
                            "resources": "Bộ đề thi chuẩn quốc tế / Hệ thống đánh giá cuối kỳ / Báo cáo nghiệm thu.",
                        },
                    ]

                    # Bổ sung dữ liệu thực tế từ breakdown của Active Goals nếu có
                    for g in user_goals_sched:
                        g_title = g.get("title") or g.get("goal_name", "Mục tiêu")
                        bd = g.get("breakdown", {})
                        q_items = bd.get("quarterly", [])
                        if q_items and len(q_items) >= 1:
                            quarter_phases[0]["focus"] = f"[{g_title}] " + str(q_items[0].get("focus", q_items[0].get("objective", quarter_phases[0]["focus"])))
                            if len(q_items) >= 2:
                                quarter_phases[1]["focus"] = f"[{g_title}] " + str(q_items[1].get("focus", q_items[1].get("objective", quarter_phases[1]["focus"])))
                            if len(q_items) >= 3:
                                quarter_phases[2]["focus"] = f"[{g_title}] " + str(q_items[2].get("focus", q_items[2].get("objective", quarter_phases[2]["focus"])))

                    for phase in quarter_phases:
                        with st.container(border=True):
                            st.markdown(f"#### 🏆 {phase['title']}")
                            p_col1, p_col2 = st.columns([0.7, 0.3])
                            with p_col1:
                                st.markdown(f"🎯 **Trọng tâm thực thi:** {phase['focus']}")
                                st.markdown(f"🏁 **Cột mốc kết quả (Target):** {phase['target']}")
                                st.caption(f"📦 **Tài nguyên hỗ trợ:** {phase['resources']}")
                            with p_col2:
                                st.markdown(f"**Tiến độ giai đoạn:** `{phase['progress']}%`")
                                st.progress(phase['progress'] / 100)
                                if phase['progress'] >= 100:
                                    st.success("🎉 Giai đoạn hoàn tất!")
                                elif phase['progress'] > 0:
                                    st.info("⚡ Đang tăng tốc")
                                else:
                                    st.caption("⏳ Chưa bắt đầu")

                    # Checklist nhiệm vụ trọng tâm của Quý
                    st.markdown("---")
                    st.markdown("##### 📋 Checklist Nhiệm Vụ Trọng Tâm Toàn Quý (Tương Tác Real-time):")
                    for t_idx, tk in enumerate(filtered_schedule[:14]):  # Top 14 nhiệm vụ tiêu biểu
                        t_detail = tk.get("task_detail", "Nhiệm vụ")
                        t_date = tk.get("date", "Thứ Hai")
                        t_slot = tk.get("time_slot", "")
                        t_goal = tk.get("goal_title", "")
                        t_done = bool(tk.get("is_done", False))
                        t_energy = tk.get("energy_level", "🔴 Deep Work")
                        q_chk_key = f"chk_qtr_{current_username}_{t_date}_{t_idx}_{abs(hash(t_detail)) % 100000}"

                        col_q_c, col_q_t = st.columns([0.08, 0.92])
                        with col_q_c:
                            new_q_done = st.checkbox("", value=t_done, key=q_chk_key, label_visibility="collapsed")
                            if new_q_done != t_done:
                                update_master_schedule_task_status(
                                    task_identifier=t_detail,
                                    is_done=new_q_done,
                                    date=t_date,
                                    username=current_username,
                                )
                                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                st.toast(f"✅ Đã cập nhật: {t_detail[:35]}...")
                                st.rerun()
                        with col_q_t:
                            st.markdown(f"**{t_energy}** &nbsp;|&nbsp; 📅 **{t_date}** ({t_slot}) — **{t_detail}** `[🎯 {t_goal}]`")

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
                            if res.get("is_rescheduled") and is_calendar_connected(current_username):
                                updated_ms = load_master_schedule(current_username)
                                sync_schedule_to_google_calendar(current_username, updated_ms)
                                sched_rep += "\n\n*(Đã tự động cập nhật dời lịch trên Google Calendar cá nhân của bạn)*"
                        else:
                            sched_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                        st.markdown(sched_rep)
                        st.session_state[chat_sched_key].append({"role": "assistant", "content": sched_rep})
                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                        st.rerun()


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# TAB 4: 📊 GIAI ĐOẠN 3: TỔNG KẾT & CẢI THIỆN (RETROSPECTIVE)
# ------------------------------------------------------------------------------
with tab_retro:
    st.markdown("### 📊 Giai đoạn 3: Tổng Kết, Soi Điểm Mù & Tái Cấu Trúc Khép Kín")
    st.caption("Tự động soi điểm mù hành vi • Hội thoại thấu cảm & bảo vệ nhịp sinh học • 1-Click tự động tối ưu Giai đoạn 1 & 2")

    col_dash_retro, col_chat_retro = st.columns([1.15, 0.85], gap="large")

    with col_dash_retro:
        ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))
        r_logs = safe_list(st.session_state.get(retro_logs_key) or load_retrospective_logs(current_username))
        user_goals = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        total_tasks = len(ms)
        done_tasks = sum(1 for t in ms if t.get("is_done") is True)
        uncompleted_tasks_list = [t for t in ms if t.get("is_done") is False]
        uncompleted_tasks = len(uncompleted_tasks_list)
        rate = (done_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

        # Tính chuỗi ngày kỷ luật (Streak) thực tế từ MongoDB
        streak = calculate_user_streak(current_username)

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

        # Row 1: Thẻ chỉ số tổng quan (Metrics Card)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Tỷ Lệ Hoàn Thành", f"{rate:.1f}%")
        with m2:
            st.metric("Chuỗi Kỷ Luật", f"🔥 {streak} ngày")
        with m3:
            st.metric("Task Đã Xong", f"{done_tasks}/{total_tasks}")
        with m4:
            st.metric("Trạng Thái Năng Lượng", disp_emotion)

        st.progress(min(1.0, rate / 100.0))

        st.markdown("---")

        # Row 2: Biểu đồ % Kỷ luật theo từng mục tiêu
        st.markdown("#### 🎯 Biểu Đồ % Kỷ Luật Theo Từng Mục Tiêu:")
        goal_discipline = {}
        for g in user_goals:
            g_title = g.get("title") or g.get("goal_name", "Mục tiêu")
            g_id = g.get("id") or g.get("goal_id")
            g_tasks = [t for t in ms if (g_id and t.get("goal_id") == g_id) or t.get("goal_title") == g_title]
            g_done = sum(1 for t in g_tasks if t.get("is_done") is True)
            g_total = len(g_tasks)
            g_pct = (g_done / g_total * 100.0) if g_total > 0 else 0.0
            goal_discipline[g_title] = round(g_pct, 1)

        if goal_discipline:
            st.bar_chart(goal_discipline)
        else:
            st.caption("Chưa có dữ liệu mục tiêu để lập biểu đồ kỷ luật.")

        if user_goals:
            for g in user_goals:
                g_title = g.get("title") or g.get("goal_name", "Mục tiêu")
                g_id = g.get("id") or g.get("goal_id")
                g_tasks = [t for t in ms if (g_id and t.get("goal_id") == g_id) or t.get("goal_title") == g_title]
                g_done = sum(1 for t in g_tasks if t.get("is_done") is True)
                g_total = len(g_tasks)
                g_pct = (g_done / g_total * 100.0) if g_total > 0 else 0.0

                col_gt, col_gp = st.columns([0.7, 0.3])
                with col_gt:
                    st.markdown(f"**{g_title}** ({g_done}/{g_total} task • `{g.get('preferred_time', 'Linh hoạt')}`)")
                with col_gp:
                    st.caption(f"Kỷ luật: **{g_pct:.0f}%**")
                st.progress(min(1.0, g_pct / 100.0))
        else:
            st.caption("Chưa có mục tiêu nào trong hệ thống.")

        st.markdown("---")

        # Row 3: Tự động soi điểm mù hành vi (Behavioral Blindspots)
        st.markdown("#### 🚨 Soi Điểm Mù Hành Vi & Nhịp Sinh Học (7 Ngày Gần Nhất):")
        missed_slot_counts = {}
        missed_tasks_detail = {}
        for t in uncompleted_tasks_list:
            slot = t.get("time_slot") or t.get("session") or "Khung giờ khác"
            missed_slot_counts[slot] = missed_slot_counts.get(slot, 0) + 1
            td = t.get("task_detail") or "Nhiệm vụ chưa hoàn thành"
            gt = t.get("goal_title") or "Mục tiêu"
            task_key = f"{td} ({gt})"
            missed_tasks_detail[task_key] = missed_tasks_detail.get(task_key, 0) + 1

        sorted_missed_slots = sorted(missed_slot_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_missed_tasks = sorted(missed_tasks_detail.items(), key=lambda x: x[1], reverse=True)

        with st.container(border=True):
            if sorted_missed_slots:
                c_ms_1, c_ms_2 = st.columns(2)
                with c_ms_1:
                    st.markdown("**⏰ Khung Giờ Hay Bị Trượt Nhất:**")
                    for s_name, s_count in sorted_missed_slots[:3]:
                        st.error(f"• **`{s_name}`**: trượt {s_count} task")
                with c_ms_2:
                    st.markdown("**📌 Đầu Việc Hay Bị Bỏ Lỡ Nhất:**")
                    for t_name, t_count in sorted_missed_tasks[:3]:
                        st.warning(f"• **{t_name}**: lỡ {t_count} lần")

                # Chẩn đoán sinh học tự động
                has_morning_miss = any("sáng" in s.lower() or "06:" in s or "07:" in s for s, _ in sorted_missed_slots)
                has_night_miss = any("tối" in s.lower() or "19:" in s or "20:" in s or "21:" in s for s, _ in sorted_missed_slots)

                if has_morning_miss:
                    st.info("💡 **Chẩn đoán nhịp sinh học sáng:** Thường xuyên trượt lịch buổi sáng cho thấy thói quen thức khuya hoặc ngủ không đủ giấc. Khuyến nghị đi ngủ trước 22:15 hoặc dời khung giờ thực thi sang buổi chiều (17:30 - 18:30).")
                if has_night_miss:
                    st.info("💡 **Chẩn đoán nhịp sinh học tối:** Bỏ lỡ khung giờ tối muộn là dấu hiệu cạn kiệt năng lượng ý chí (ego depletion) sau cả ngày. Khuyến nghị dời task nặng sang sáng (08:30) hoặc giảm thời lượng xuống 45 phút.")
            else:
                st.success("🎉 **Tuyệt vời! Bạn không bỏ lỡ bất kỳ nhiệm vụ nào trong 7 ngày qua.** Kỷ luật thép được duy trì rất tốt!")

        st.markdown("---")

        # Row 4: Đề xuất Tái Cấu Trúc Khép Kín & Nút 1-Click Cập Nhật
        st.markdown("#### 🔄 Cơ Chế Tái Cấu Trúc Khép Kín (Closed-Loop Adaptation):")
        st.caption("Khi gặp tình trạng quá tải hoặc trượt lịch, hãy áp dụng đề xuất tái cấu trúc dưới đây để tự động cập nhật Giai đoạn 1 & 2 và đồng bộ Google Calendar:")

        prop_adj = latest_log.get("proposed_adjustment") or {}
        rec_target = prop_adj.get("target_goal_title") or (user_goals[0].get("title") if user_goals else "Mục tiêu")
        rec_time = prop_adj.get("recommended_preferred_time") or "17:30 - 18:30 (Chiều)"
        rec_sleep = prop_adj.get("recommended_sleep_time") or "22:15"
        rec_hours = prop_adj.get("recommended_daily_hours") or 1.5
        updated_strat = prop_adj.get("updated_strategy_summary") or f"Tái cấu trúc nhịp sinh học: chuyển giờ rèn luyện sang {rec_time}, ngủ sớm lúc {rec_sleep} và tối ưu {rec_hours}h Deep Work."
        adj_reason = prop_adj.get("adjustment_explanation") or latest_log.get("recommended_adjustments", "Tối ưu lại khung giờ và bảo vệ nhịp sinh học.")

        with st.container(border=True):
            st.markdown(f"**🎯 Mục tiêu điều chỉnh:** `{rec_target}`")
            st.markdown(f"**⏰ Khung giờ mới đề xuất:** `{rec_time}`")
            st.markdown(f"**💤 Giờ ngủ tối ưu đề xuất:** `{rec_sleep}`")
            st.markdown(f"**⏳ Thời lượng mới:** `{rec_hours} giờ/ngày`")
            st.markdown(f"**📝 Chiến lược mới (Giai đoạn 1):** {updated_strat}")
            st.markdown(f"**💡 Lý do điều chỉnh:** {adj_reason}")

        if st.button("✨ Áp dụng điều chỉnh này vào Kế hoạch (Giai đoạn 1 & 2)", type="primary", use_container_width=True, key=f"btn_apply_loop_{current_username}"):
            with st.spinner("Đang tự động cập nhật Giai đoạn 1, tái cấu trúc Giai đoạn 2 và đồng bộ Google Calendar..."):
                # 1. Cập nhật Giai đoạn 1 (user_goals)
                matched_goal = None
                for g in user_goals:
                    gid = g.get("id") or g.get("goal_id")
                    gt = (g.get("title") or g.get("goal_name") or "").lower().strip()
                    if (prop_adj.get("target_goal_id") and gid == prop_adj.get("target_goal_id")) or (rec_target and (rec_target.lower().strip() in gt or gt in rec_target.lower().strip())):
                        matched_goal = g
                        if rec_hours:
                            g["daily_hours"] = float(rec_hours)
                        if rec_time:
                            g["preferred_time"] = rec_time
                        if updated_strat:
                            g["strategy_summary"] = updated_strat
                        break

                if not matched_goal and user_goals:
                    matched_goal = user_goals[0]
                    if rec_hours:
                        matched_goal["daily_hours"] = float(rec_hours)
                    if rec_time:
                        matched_goal["preferred_time"] = rec_time
                    if updated_strat:
                        matched_goal["strategy_summary"] = updated_strat

                save_user_goals(user_goals, username=current_username)
                st.session_state[goals_key] = load_user_goals(current_username)

                # 2. Tái cấu trúc Giai đoạn 2 (master_schedule via scheduler_chat)
                target_goal_name = matched_goal.get("title") or matched_goal.get("goal_name", "Mục tiêu") if matched_goal else rec_target
                if scheduler_chat is not None:
                    sched_prompt = (
                        f"Tái cấu trúc lại Master Schedule 7 ngày cho mục tiêu '{target_goal_name}' "
                        f"theo khung giờ mới: {rec_time}, thời lượng: {rec_hours} giờ/ngày, "
                        f"giờ đi ngủ tối ưu: {rec_sleep}. "
                        f"Chiến lược mới: {updated_strat}. "
                        f"Hãy lập lịch cân bằng, chi tiết 7 ngày từ hôm nay!"
                    )
                    sched_res = scheduler_chat(sched_prompt, username=current_username)

                fresh_ms = load_master_schedule(current_username)
                st.session_state[master_schedule_key] = fresh_ms

                # 3. Đồng bộ lại lên Google Calendar nếu đã kết nối
                gcal_msg = ""
                if is_calendar_connected(current_username):
                    gcal_sync = sync_schedule_to_google_calendar(current_username, fresh_ms)
                    if gcal_sync.get("success"):
                        gcal_msg = f" • 📅 Đã đồng bộ {gcal_sync.get('synced_count', 0)} sự kiện lên Google Calendar!"
                    else:
                        gcal_msg = f" • ⚠️ Đồng bộ Google Calendar: {gcal_sync.get('message')}"

                st.success(f"🎉 Đã tái cấu trúc khép kín thành công! Giai đoạn 1 & 2 đã được cập nhật tối ưu.{gcal_msg}")
                st.rerun()

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
        st.caption("Check-in cuối ngày • Lắng nghe cảm xúc • Nhận diện quy luật 7 ngày • Đề xuất điều chỉnh")

        if st.button("🔍 Phân tích tuần qua cùng Coach", key=f"btn_coach_weekly_analyze_{current_username}", type="secondary", use_container_width=True):
            user_msg = "Chào Coach, hãy phân tích toàn bộ lịch trình 7 ngày qua của tôi từ Giai đoạn 2, chỉ ra các điểm mù hành vi và đề xuất giải pháp tái cấu trúc tối ưu."
            st.session_state[chat_retro_key].append({"role": "user", "content": user_msg})
            with st.spinner("Retrospective Coach đang soi điểm mù 7 ngày và sinh đề xuất tái cấu trúc..."):
                if retrospective_chat is not None:
                    res = retrospective_chat(
                        user_message=user_msg,
                        username=current_username,
                        chat_history=st.session_state[chat_retro_key],
                    )
                    retro_rep = res.get("response", "Cảm ơn bạn đã check-in.")
                else:
                    retro_rep = "Hệ thống đang chuẩn bị kết nối AI..."
                st.session_state[chat_retro_key].append({"role": "assistant", "content": retro_rep})
                st.session_state[retro_logs_key] = load_retrospective_logs(current_username)
                st.session_state[goals_key] = load_user_goals(current_username)
                st.rerun()

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
                    with st.spinner("Retrospective Coach đang phân tích dữ liệu 7 ngày và nhận diện quy luật..."):
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
