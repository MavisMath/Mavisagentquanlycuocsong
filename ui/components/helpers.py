"""
ui/components/helpers.py - Shared data loaders, calendar tools, undo/redo mechanisms,
and AI agent invokers for the Mavis Executive Life Coach UI.
"""

import os
import sys
import json
import uuid
import copy
import urllib.parse
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

import streamlit as st

# ==========================================
# 1. NẠP AN TOÀN MODULE MEMORY.MONGODB
# ==========================================
try:
    import memory.mongodb as mm
    is_mongodb_available = getattr(mm, "is_mongodb_available", lambda: False)
    db_update_user_state = getattr(mm, "db_update_user_state", lambda *args, **kwargs: False)
    get_mongo_connection_error = getattr(mm, "get_mongo_connection_error", lambda: None)
    get_mongo_uri = getattr(mm, "get_mongo_uri", lambda: None)
except Exception as _mongo_import_err:
    is_mongodb_available = lambda: False
    db_update_user_state = lambda *args, **kwargs: False
    get_mongo_connection_error = lambda: str(_mongo_import_err)
    get_mongo_uri = lambda: None

# ==========================================
# 2. NẠP AN TOÀN MODULE MEMORY.GOALS
# ==========================================
try:
    import memory.goals as mg

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
    defer_master_schedule_task_to_tomorrow = getattr(mg, "defer_master_schedule_task_to_tomorrow")
    load_retrospective_logs = getattr(mg, "load_retrospective_logs")
    save_retrospective_logs = getattr(mg, "save_retrospective_logs")
    append_retrospective_log = getattr(mg, "append_retrospective_log")
    get_user_state_full = getattr(mg, "get_user_state_full")
    update_user_goal_status = getattr(mg, "update_user_goal_status")
    update_user_goal_details = getattr(mg, "update_user_goal_details")
    delete_user_goal = getattr(mg, "delete_user_goal")
    calculate_user_streak = getattr(mg, "calculate_user_streak")
    detect_goal_domain = getattr(mg, "detect_goal_domain")
    DOMAIN_TERMINOLOGY = getattr(mg, "DOMAIN_TERMINOLOGY", {})
    get_vietnam_today = getattr(mg, "get_vietnam_today")
    get_vietnam_today_str = getattr(mg, "get_vietnam_today_str")
    compute_target_date = getattr(mg, "compute_target_date")
    generate_detailed_master_schedule = getattr(mg, "generate_detailed_master_schedule")
    ensure_schedule_covers_date = getattr(mg, "ensure_schedule_covers_date")
    VIETNAM_WEEKDAYS = getattr(
        mg,
        "VIETNAM_WEEKDAYS",
        {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"},
    )
except Exception as _goals_import_err:
    raise RuntimeError(f"Không thể nạp memory.goals: {_goals_import_err}")

# ==========================================
# 3. NẠP AN TOÀN MODULE MEMORY.AUTH
# ==========================================
try:
    import memory.auth as ma
    get_authenticator = getattr(ma, "get_authenticator", None)
    register_user = getattr(ma, "register_user", None)
except Exception:
    get_authenticator = None
    register_user = None

# ==========================================
# 4. LAZY-LOAD CÁC CHATBOT VÀ GRAPH QUA CACHE RESOURCE
# ==========================================
@st.cache_resource
def get_brain_modules():
    """Lazy-load các chatbot functions từ agents.brain chỉ khi cần tương tác chat để tiết kiệm RAM khi khởi động."""
    try:
        import agents.brain as ab
        return {
            "chat_node": getattr(ab, "chat_node", None),
            "ceo_coach_chat": getattr(ab, "ceo_coach_chat", None),
            "architect_chat": getattr(ab, "architect_chat", None),
            "scheduler_chat": getattr(ab, "scheduler_chat", None),
            "retrospective_chat": getattr(ab, "retrospective_chat", None),
        }
    except Exception as _brain_err:
        return {
            "chat_node": None,
            "ceo_coach_chat": None,
            "architect_chat": None,
            "scheduler_chat": None,
            "retrospective_chat": None,
        }

@st.cache_resource
def get_mavis_agent():
    """Lazy-load và khởi tạo MavisAgentWrapper từ agents.graph duy nhất 1 lần qua @st.cache_resource."""
    try:
        from agents.graph import build_graph
        return build_graph()
    except Exception:
        class FallbackAgent:
            def invoke(self, state, config=None):
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "⚠️ Hệ thống đang đồng bộ cấu hình trên Cloud. Vui lòng kiểm tra lại API Key hoặc liên hệ Quản trị viên."
                        }
                    ]
                }
        return FallbackAgent()

def ceo_coach_chat(*args, **kwargs):
    fn = get_brain_modules().get("ceo_coach_chat")
    if fn:
        return fn(*args, **kwargs)
    return {"response": "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."}

def architect_chat(*args, **kwargs):
    fn = get_brain_modules().get("architect_chat")
    if fn:
        return fn(*args, **kwargs)
    return {"response": "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."}

def scheduler_chat(*args, **kwargs):
    fn = get_brain_modules().get("scheduler_chat")
    if fn:
        return fn(*args, **kwargs)
    return {"response": "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."}

def retrospective_chat(*args, **kwargs):
    fn = get_brain_modules().get("retrospective_chat")
    if fn:
        return fn(*args, **kwargs)
    return {"response": "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."}

def chat_node(*args, **kwargs):
    fn = get_brain_modules().get("chat_node")
    if fn:
        return fn(*args, **kwargs)
    return None

# ==========================================
# 5. GOOGLE CALENDAR API INTEGRATION
# ==========================================
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
except Exception:
    def is_calendar_connected(username): return False
    def disconnect_calendar(username): return False
    def get_oauth_authorization_url(**kwargs): return None, None
    def exchange_code_and_save_token(*args, **kwargs): return False
    def fetch_busy_events(username, days=7): return []
    def sync_schedule_to_google_calendar(username, ms): return {"success": False, "message": "Module Google Calendar chưa sẵn sàng", "synced_count": 0}
    def get_google_client_config(): return None
    def get_default_redirect_uri(): return "https://mavisagentquanlycuocsong-252.streamlit.app"
    def update_rescheduled_calendar_event(*args, **kwargs): return False


# ==========================================
# 6. SHARED UI HELPER FUNCTIONS
# ==========================================

def safe_dict(val: Any) -> Dict[str, Any]:
    """Chuyển đổi an toàn một object hoặc dict sang python dict thông thường."""
    if isinstance(val, dict):
        return val
    if hasattr(val, "model_dump") and callable(val.model_dump):
        try:
            return val.model_dump()
        except Exception:
            pass
    if hasattr(val, "dict") and callable(val.dict):
        try:
            return val.dict()
        except Exception:
            pass
    return {}


def safe_list(val: Any) -> List[Any]:
    """Chuyển đổi an toàn sang list."""
    if isinstance(val, list):
        return val
    if val is None:
        return []
    if isinstance(val, (tuple, set)):
        return list(val)
    return [val]


def shorten_task_name(name: str, max_words: int = 5) -> str:
    """Rút gọn tên nhiệm vụ hiển thị trong ô bảng lịch (tối đa max_words từ)."""
    words = str(name).strip().split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def get_state_snapshot(username: str) -> Dict[str, Any]:
    """Lấy snapshot sâu của goals và master_schedule để phục vụ Undo / Redo."""
    current_goals = load_user_goals(username)
    current_ms = load_master_schedule(username)
    return {
        "goals": copy.deepcopy(current_goals),
        "master_schedule": copy.deepcopy(current_ms),
    }


def push_undo_state(username: str):
    """Đẩy trạng thái hiện tại vào undo_stack trước khi có thao tác thay đổi dữ liệu."""
    undo_key = f"undo_stack_{username}"
    redo_key = f"redo_stack_{username}"
    if undo_key not in st.session_state:
        st.session_state[undo_key] = []
    if redo_key not in st.session_state:
        st.session_state[redo_key] = []

    snapshot = get_state_snapshot(username)
    st.session_state[undo_key].append(snapshot)
    if len(st.session_state[undo_key]) > 10:
        st.session_state[undo_key].pop(0)

    # Thao tác mới sẽ làm sạch redo stack
    st.session_state[redo_key].clear()


def save_undo_snapshot(username: str, current_ms: Optional[List[Dict[str, Any]]] = None):
    """Wrapper tương thích ngược lưu snapshot undo."""
    push_undo_state(username)


def apply_undo(username: str) -> bool:
    """Khôi phục trạng thái từ undo_stack và đẩy trạng thái hiện tại vào redo_stack."""
    undo_key = f"undo_stack_{username}"
    redo_key = f"redo_stack_{username}"
    if not st.session_state.get(undo_key):
        return False

    current_snapshot = get_state_snapshot(username)
    if redo_key not in st.session_state:
        st.session_state[redo_key] = []
    st.session_state[redo_key].append(current_snapshot)

    prev_snapshot = st.session_state[undo_key].pop()
    save_user_goals(prev_snapshot["goals"], username=username)
    save_master_schedule(prev_snapshot["master_schedule"], username=username)

    st.session_state[f"goals_{username}"] = prev_snapshot["goals"]
    st.session_state[f"master_schedule_{username}"] = prev_snapshot["master_schedule"]
    return True


def apply_redo(username: str) -> bool:
    """Làm lại thao tác vừa hoàn tác từ redo_stack."""
    undo_key = f"undo_stack_{username}"
    redo_key = f"redo_stack_{username}"
    if not st.session_state.get(redo_key):
        return False

    current_snapshot = get_state_snapshot(username)
    if undo_key not in st.session_state:
        st.session_state[undo_key] = []
    st.session_state[undo_key].append(current_snapshot)

    next_snapshot = st.session_state[redo_key].pop()
    save_user_goals(next_snapshot["goals"], username=username)
    save_master_schedule(next_snapshot["master_schedule"], username=username)

    st.session_state[f"goals_{username}"] = next_snapshot["goals"]
    st.session_state[f"master_schedule_{username}"] = next_snapshot["master_schedule"]
    return True


def generate_gcal_link(task_title: str, time_slot: str, duration_minutes: int = 120, resource_info: str = "") -> str:
    """Tạo đường dẫn thêm sự kiện vào Google Calendar với thời gian thực."""
    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y%m%d")

    start_hour = 8
    start_min = 0
    if "-" in time_slot:
        try:
            start_part = time_slot.split("-")[0].strip()
            parts = start_part.split(":")
            start_hour = int(parts[0])
            start_min = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            start_hour = 8

    start_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, start_hour, start_min)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    dates_param = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    details = f"Lịch trình tự động thiết lập bởi Mavis AI Executive Life Coach.\nNhiệm vụ: {task_title}"
    if resource_info:
        details += f"\nTài liệu / Giáo trình: {resource_info}"

    params = {
        "text": f"🎯 Mavis AI: {task_title}",
        "dates": dates_param,
        "details": details,
    }
    return f"{base_url}&{urllib.parse.urlencode(params)}"


def generate_ics_calendar(roadmap: Dict[str, Any], goal_name: str, preferred_slots: str) -> str:
    """Tạo file nội dung .ics theo chuẩn iCalendar RFC 5545 cho lộ trình."""
    now = datetime.now()
    now_str = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mavis Executive Life Coach//AI Calendar Sync//VI",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mavis AI - " + goal_name,
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
    ]

    start_hour = 8
    start_min = 0
    if "-" in preferred_slots:
        try:
            sp = preferred_slots.split("-")[0].strip().split(":")
            start_hour = int(sp[0])
            start_min = int(sp[1]) if len(sp) > 1 else 0
        except Exception:
            start_hour = 8

    weekly_plan = safe_dict(roadmap).get("weekly", [])
    day_offset = 1
    for week_idx, week_item in enumerate(weekly_plan):
        tasks = safe_list(safe_dict(week_item).get("tasks", []))
        for t_idx, task in enumerate(tasks):
            task_dict = safe_dict(task)
            t_name = task_dict.get("task_name") or f"Tuần {week_idx+1} - Task {t_idx+1}"
            energy = task_dict.get("energy_level", "🔴 Deep Work")
            event_date = now + timedelta(days=day_offset)
            dt_start = datetime(event_date.year, event_date.month, event_date.day, start_hour, start_min)
            dt_end = dt_start + timedelta(hours=2)

            lines.extend([
                "BEGIN:VEVENT",
                f"UID:mavis-{now.strftime('%Y%m%d%H%M%S')}-{week_idx}-{t_idx}@executive.ai",
                f"DTSTAMP:{now_str}",
                f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:🎯 [{energy}] {t_name}",
                f"DESCRIPTION:Mục tiêu: {goal_name}\\nNhiệm vụ: {t_name}\\nKhung giờ: {preferred_slots}",
                "STATUS:CONFIRMED",
                "END:VEVENT",
            ])
            day_offset += 1

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def generate_ics_from_master_schedule(schedule: List[Dict[str, Any]], username: str) -> str:
    """Tạo chuỗi .ics chuẩn iCalendar từ toàn bộ master_schedule của người dùng."""
    now = datetime.now()
    now_str = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mavis Executive Life Coach//Master Schedule Export//VI",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Mavis Master Schedule - {username}",
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
    ]

    day_map = {
        "Thứ Hai": 0, "Thứ Ba": 1, "Thứ Tư": 2, "Thứ Năm": 3,
        "Thứ Sáu": 4, "Thứ Bảy": 5, "Chủ Nhật": 6,
    }

    monday_of_week = now - timedelta(days=now.weekday())

    for idx, item in enumerate(schedule):
        task_dict = safe_dict(item)
        task_name = task_dict.get("task_detail", "Nhiệm vụ Mavis")
        goal_title = task_dict.get("goal_title", "Phát triển bản thân")
        time_slot = task_dict.get("time_slot", "08:00 - 10:00")
        energy = task_dict.get("energy_level", "🔴 Deep Work")
        res_link = task_dict.get("resource_url") or task_dict.get("resource_link", "")

        date_val = str(task_dict.get("date", "")).strip()
        event_date = None
        if date_val.startswith("202") and len(date_val) >= 10:
            try:
                event_date = datetime.strptime(date_val[:10], "%Y-%m-%d").date()
            except Exception:
                event_date = None

        if event_date is None:
            target_weekday = day_map.get(date_val, (idx % 7))
            event_date = (monday_of_week + timedelta(days=target_weekday)).date()

        start_h, start_m = 8, 0
        end_h, end_m = 10, 0
        if "-" in time_slot:
            try:
                parts = time_slot.split("-")
                sp = parts[0].strip().split(":")
                ep = parts[1].strip().split(":")
                start_h = int(sp[0])
                start_m = int(sp[1]) if len(sp) > 1 else 0
                end_h = int(ep[0])
                end_m = int(ep[1]) if len(ep) > 1 else 0
            except Exception:
                start_h, start_m = 8, 0
                end_h, end_m = 10, 0

        dt_start = datetime(event_date.year, event_date.month, event_date.day, start_h, start_m)
        dt_end = datetime(event_date.year, event_date.month, event_date.day, end_h, end_m)
        if dt_end <= dt_start:
            dt_end = dt_start + timedelta(hours=2)

        desc = f"Mục tiêu: {goal_title}\\nNhiệm vụ: {task_name}\\nKhung giờ: {time_slot}"
        if res_link:
            desc += f"\\nTài liệu: {res_link}"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:mavis-master-{username}-{idx}-{event_date.strftime('%Y%m%d')}@executive.ai",
            f"DTSTAMP:{now_str}",
            f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:🎯 [{energy}] {task_name}",
            f"DESCRIPTION:{desc}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def extract_text_from_content(content: Any) -> str:
    """Trích xuất chuỗi văn bản sạch từ nội dung LangChain AIMessage / dict."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and p.get("type") == "text":
                parts.append(p.get("text", ""))
            elif hasattr(p, "text"):
                parts.append(getattr(p, "text", ""))
        return "".join(parts)
    if isinstance(content, dict):
        return content.get("text") or content.get("content") or str(content)
    return str(content)


OPENING_GREETING = (
    "Chào bạn! Tôi là Elite Executive & Life Coach độc quyền của bạn. "
    "Hiện tại hồ sơ chiến lược của bạn đang hoàn toàn trống. "
    "Bạn muốn chúng ta bắt đầu bằng việc xây dựng khía cạnh nào trước (Sự nghiệp, Sức khỏe, Tài chính...), và mục tiêu lớn nhất hiện tại của bạn là gì?"
)
