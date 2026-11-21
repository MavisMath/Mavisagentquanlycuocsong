# tools/google_calendar.py
# Google Calendar API Real-time 2-Way Sync Engine for Mavis AI Executive Coach

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import Flow
    import googleapiclient.discovery
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_SDK_AVAILABLE = True
except Exception as _e:
    Credentials = None  # type: ignore
    Request = None  # type: ignore
    Flow = None  # type: ignore
    googleapiclient = None  # type: ignore
    HttpError = Exception  # type: ignore
    GOOGLE_CALENDAR_SDK_AVAILABLE = False

from memory.mongodb import get_mongo_db, db_update_user_state
from memory.goals import get_user_state_full

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]

VN_TIMEZONE = timezone(timedelta(hours=7))

VIETNAM_WEEKDAY_MAP = {
    "thứ hai": 0,
    "thứ 2": 0,
    "monday": 0,
    "thứ ba": 1,
    "thứ 3": 1,
    "tuesday": 1,
    "thứ tư": 2,
    "thứ 4": 2,
    "wednesday": 2,
    "thứ năm": 3,
    "thứ 5": 3,
    "thursday": 3,
    "thứ sáu": 4,
    "thứ 6": 4,
    "friday": 4,
    "thứ bảy": 5,
    "thứ 7": 5,
    "saturday": 5,
    "chủ nhật": 6,
    "cn": 6,
    "sunday": 6,
}


def get_google_client_config() -> Optional[Dict[str, Any]]:
    """
    Lấy Google OAuth Client ID & Secret từ st.secrets, biến môi trường hoặc credentials.json.
    """
    client_id = None
    client_secret = None

    # 1. Thử lấy từ streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            client_id = st.secrets.get("GOOGLE_CLIENT_ID")
            client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
            if not client_id and "google_calendar" in st.secrets:
                gcal_sec = st.secrets["google_calendar"]
                if isinstance(gcal_sec, dict):
                    client_id = gcal_sec.get("client_id") or gcal_sec.get("GOOGLE_CLIENT_ID")
                    client_secret = gcal_sec.get("client_secret") or gcal_sec.get("GOOGLE_CLIENT_SECRET")
    except Exception:
        pass

    # 2. Thử lấy từ biến môi trường (.env)
    if not client_id:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_secret:
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    # 3. Thử đọc file credentials.json nếu có
    if (not client_id or not client_secret) and os.path.exists("credentials.json"):
        try:
            with open("credentials.json", "r", encoding="utf-8") as f:
                cdata = json.load(f)
                web_or_installed = cdata.get("web") or cdata.get("installed") or {}
                client_id = web_or_installed.get("client_id", client_id)
                client_secret = web_or_installed.get("client_secret", client_secret)
        except Exception:
            pass

    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip(),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }
    return None


def get_default_redirect_uri() -> str:
    """
    Lấy URI chuyển hướng mặc định từ st.secrets, .env, credentials.json hoặc request context.
    """
    # 1. Thử lấy từ streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GOOGLE_REDIRECT_URI" in st.secrets:
                return str(st.secrets["GOOGLE_REDIRECT_URI"]).strip()
            if "google_calendar" in st.secrets and isinstance(st.secrets["google_calendar"], dict):
                g_uri = st.secrets["google_calendar"].get("redirect_uri") or st.secrets["google_calendar"].get("GOOGLE_REDIRECT_URI")
                if g_uri:
                    return str(g_uri).strip()
    except Exception:
        pass

    # 2. Thử lấy từ biến môi trường (.env)
    env_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if env_uri and env_uri.strip():
        return env_uri.strip()

    # 3. Thử đọc từ credentials.json nếu có
    if os.path.exists("credentials.json"):
        try:
            with open("credentials.json", "r", encoding="utf-8") as f:
                cdata = json.load(f)
                web_or_installed = cdata.get("web") or cdata.get("installed") or {}
                r_uris = web_or_installed.get("redirect_uris")
                if r_uris and isinstance(r_uris, list) and len(r_uris) > 0:
                    return str(r_uris[0]).strip()
        except Exception:
            pass

    # 4. Thử lấy từ Streamlit context headers (nếu đang chạy trên server/cloud)
    try:
        import streamlit as st
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            host = headers.get("host")
            if host:
                proto = headers.get("x-forwarded-proto", "http")
                if "streamlit.app" in host or "herokuapp.com" in host or "render.com" in host or "ngrok" in host:
                    proto = "https"
                return f"{proto}://{host}"
    except Exception:
        pass

    return "http://localhost:8501"


def get_oauth_authorization_url(redirect_uri: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Tạo đường dẫn đăng nhập Google OAuth 2.0.
    Trả về (authorization_url, state).
    """
    if not redirect_uri:
        redirect_uri = get_default_redirect_uri()

    client_config = get_google_client_config()
    if not client_config or not GOOGLE_CALENDAR_SDK_AVAILABLE:
        return None, None

    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url, state
    except Exception as e:
        print(f"Lỗi khởi tạo Google OAuth Flow: {e}")
        return None, None


def exchange_code_and_save_token(code: str, redirect_uri: Optional[str] = None, username: str = "mavis") -> bool:
    """
    Đổi authorization code lấy Access Token / Refresh Token và lưu bền vững vào MongoDB Atlas.
    """
    if not redirect_uri:
        redirect_uri = get_default_redirect_uri()

    client_config = get_google_client_config()
    if not client_config or not GOOGLE_CALENDAR_SDK_AVAILABLE:
        return False

    try:
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        token_data = json.loads(creds.to_json())
        return save_user_calendar_token(username, token_data)
    except Exception as e:
        print(f"Lỗi khi đổi authorization code Google: {e}")
        return False


def save_user_calendar_token(username: str, token_data: Dict[str, Any]) -> bool:
    """
    Lưu token Google Calendar vào collection user_states trong MongoDB Atlas và local ledger fallback.
    """
    username = (username or "mavis").strip().lower()
    try:
        from memory.mongodb import is_mongodb_available, db_update_user_state
        if is_mongodb_available():
            db_update_user_state(username, {"google_calendar_token": token_data})
    except Exception:
        pass

    try:
        from memory.goals import load_all_users_data, save_all_users_data, get_blank_tree
        all_data = load_all_users_data()
        if username not in all_data or not isinstance(all_data[username], dict):
            all_data[username] = get_blank_tree()
        all_data[username]["google_calendar_token"] = token_data
        return save_all_users_data(all_data)
    except Exception as e:
        print(f"Lỗi lưu token Google Calendar: {e}")
        return False


def load_user_calendar_token(username: str) -> Optional[Dict[str, Any]]:
    """
    Nạp token Google Calendar của user từ MongoDB Atlas hoặc local ledger fallback.
    """
    username = (username or "mavis").strip().lower()
    try:
        from memory.mongodb import is_mongodb_available, db_get_user_state
        if is_mongodb_available():
            st = db_get_user_state(username)
            if st and st.get("google_calendar_token"):
                tok = st.get("google_calendar_token")
                if isinstance(tok, dict) and (tok.get("token") or tok.get("refresh_token")):
                    return tok
    except Exception:
        pass

    try:
        from memory.goals import load_all_users_data
        all_data = load_all_users_data()
        tok = all_data.get(username, {}).get("google_calendar_token")
        if tok and isinstance(tok, dict) and (tok.get("token") or tok.get("refresh_token")):
            return tok
    except Exception:
        pass
    return None


def is_calendar_connected(username: str) -> bool:
    """
    Kiểm tra xem user đã liên kết Google Calendar hay chưa.
    """
    tok = load_user_calendar_token(username)
    return bool(tok and (tok.get("token") or tok.get("refresh_token")))


def disconnect_calendar(username: str) -> bool:
    """
    Hủy kết nối Google Calendar, dọn sạch token trong MongoDB và local ledger.
    """
    username = (username or "mavis").strip().lower()
    try:
        from memory.mongodb import is_mongodb_available, db_update_user_state
        if is_mongodb_available():
            db_update_user_state(username, {"google_calendar_token": None})
    except Exception:
        pass

    try:
        from memory.goals import load_all_users_data, save_all_users_data
        all_data = load_all_users_data()
        if username in all_data and isinstance(all_data[username], dict):
            all_data[username]["google_calendar_token"] = None
            save_all_users_data(all_data)
    except Exception:
        pass
    return True


def get_calendar_service(username: str) -> Optional[Any]:
    """
    Khởi tạo Google Calendar API Client từ token đã lưu (tự động làm mới khi hết hạn).
    """
    if not GOOGLE_CALENDAR_SDK_AVAILABLE:
        return None

    tok_data = load_user_calendar_token(username)
    if not tok_data:
        return None

    try:
        creds = Credentials.from_authorized_user_info(tok_data, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Lưu lại token mới sau khi refresh
            save_user_calendar_token(username, json.loads(creds.to_json()))

        service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Lỗi kết nối Google Calendar Service cho '{username}': {e}")
        return None


def fetch_busy_events(username: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Đọc danh sách sự kiện bận trong 7 ngày tới từ Google Calendar của user.
    Hỗ trợ nhận diện các khung giờ bận thực tế để né trùng lịch khi phân bổ.
    """
    service = get_calendar_service(username)
    if not service:
        return []

    try:
        now_utc = datetime.now(timezone.utc)
        time_min = now_utc.isoformat()
        time_max = (now_utc + timedelta(days=days)).isoformat()

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        ).execute()

        items = events_result.get("items", [])
        busy_slots = []
        for ev in items:
            start_raw = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
            end_raw = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
            summary = ev.get("summary", "Sự kiện bận")
            ev_id = ev.get("id", "")

            busy_slots.append({
                "id": ev_id,
                "summary": summary,
                "start": start_raw,
                "end": end_raw,
            })
        return busy_slots
    except Exception as e:
        print(f"Lỗi khi đọc sự kiện Google Calendar cho '{username}': {e}")
        return []


def get_busy_events_text_summary(username: str, days: int = 7) -> str:
    """
    Xuất bản tóm tắt danh sách sự kiện bận dạng văn bản dễ đọc để tiêm vào prompt của Architect & Scheduler.
    """
    events = fetch_busy_events(username, days=days)
    if not events:
        return "Hiện chưa có sự kiện bận nào trên Google Calendar (Toàn bộ khung giờ đều rảnh)."

    lines = ["DANH SÁCH KHUNG GIỜ BẬN THỰC TẾ TRÊN GOOGLE CALENDAR (BẮT BUỘC TRÁNH TRÙNG LỊCH):"]
    for ev in events:
        lines.append(f"- ⏰ {ev.get('start')} -> {ev.get('end')}: {ev.get('summary')}")
    return "\n".join(lines)


def _convert_task_to_datetime_range(date_str: str, time_slot_str: str) -> Tuple[datetime, datetime]:
    """
    Chuyển đổi chuỗi ngày ('Thứ Hai'..) và time_slot ('08:00 - 10:00') sang cặp datetime chuẩn (Asia/Ho_Chi_Minh).
    """
    now_vn = datetime.now(VN_TIMEZONE)
    target_weekday = VIETNAM_WEEKDAY_MAP.get(str(date_str).strip().lower(), 0)
    current_weekday = now_vn.weekday()

    # Tính toán ngày rơi vào tuần hiện tại (bắt đầu từ Thứ Hai)
    monday_current_week = now_vn - timedelta(days=current_weekday)
    target_date = monday_current_week + timedelta(days=target_weekday)

    # Phân tích chuỗi time_slot
    start_hour, start_min = 8, 0
    end_hour, end_min = 9, 30

    if "-" in str(time_slot_str):
        parts = time_slot_str.split("-")
        try:
            s_parts = parts[0].strip().split(":")
            start_hour, start_min = int(s_parts[0]), int(s_parts[1])
            e_parts = parts[1].strip().split(":")
            end_hour, end_min = int(e_parts[0]), int(e_parts[1])
        except Exception:
            pass

    start_dt = target_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
    end_dt = target_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=1, minutes=30)

    return start_dt, end_dt


def sync_schedule_to_google_calendar(
    username: str,
    master_schedule: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Đẩy toàn bộ khung giờ thực thi từ master_schedule sang Google Calendar của user (2 chiều).
    Có tiêu chí hoàn thành (DoD), link tài liệu và thông báo nhắc nhở tự động 15 phút.
    """
    service = get_calendar_service(username)
    if not service:
        return {
            "success": False,
            "message": "Chưa kết nối tài khoản Google Calendar hoặc chưa cấp quyền OAuth.",
            "synced_count": 0,
        }

    synced_count = 0
    errors = []

    for item in master_schedule:
        try:
            date_str = item.get("date", "Thứ Hai")
            time_slot = item.get("time_slot", "08:00 - 10:00")
            detail = item.get("task_detail", "Thực thi mục tiêu Mavis")
            goal = item.get("goal_title", "")
            energy = item.get("energy_level", "🔴 Deep Work")
            dod = item.get("definition_of_done", "")
            link = item.get("resource_url") or item.get("resource_link", "")
            is_done = item.get("is_done", False)

            start_dt, end_dt = _convert_task_to_datetime_range(date_str, time_slot)

            summary = f"🎯 [{goal or 'Mavis'}] {detail}"
            desc_lines = [
                f"⚡ Nhãn năng lượng: {energy}",
                f"🏁 Tiêu chí hoàn thành (DoD): {dod or 'Hoàn thành trọn vẹn và ghi nhận tiến độ.'}",
                f"🎯 Mục tiêu liên kết: {goal}",
                f"📦 Tài liệu thực tế: {link or 'Mở trên Mavis Dashboard'}",
                f"Trạng thái: {'Đã hoàn thành ✅' if is_done else 'Đang thực thi ⏳'}",
                "---",
                "Được đồng bộ tự động từ Mavis AI Executive Life Coach.",
            ]
            description = "\n".join(desc_lines)

            event_body = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "Asia/Ho_Chi_Minh",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 15},
                    ],
                },
            }

            # Kiểm tra xem task này đã có google_event_id chưa
            ev_id = item.get("google_event_id")
            if ev_id:
                try:
                    updated_ev = service.events().update(
                        calendarId="primary",
                        eventId=ev_id,
                        body=event_body,
                    ).execute()
                    item["google_event_id"] = updated_ev.get("id")
                    synced_count += 1
                    continue
                except Exception:
                    pass

            # Nếu chưa có hoặc update lỗi thì chèn mới
            created_ev = service.events().insert(
                calendarId="primary",
                body=event_body,
            ).execute()
            item["google_event_id"] = created_ev.get("id")
            synced_count += 1
        except Exception as e:
            errors.append(str(e))

    return {
        "success": synced_count > 0 or len(master_schedule) == 0,
        "message": f"Đã đồng bộ thành công {synced_count}/{len(master_schedule)} sự kiện lên Google Calendar!",
        "synced_count": synced_count,
        "errors": errors,
    }


def update_rescheduled_calendar_event(
    username: str,
    task_identifier: str,
    new_date: str,
    new_time_slot: str,
) -> bool:
    """
    Khi user báo bận hoặc dời lịch trong chat Tab 2, cập nhật ngay sự kiện trên Google Calendar.
    """
    service = get_calendar_service(username)
    if not service:
        return False

    try:
        start_dt, end_dt = _convert_task_to_datetime_range(new_date, new_time_slot)
        # Tìm kiếm sự kiện theo tên
        events_result = service.events().list(
            calendarId="primary",
            q=task_identifier[:30],
            maxResults=5,
        ).execute()

        items = events_result.get("items", [])
        if items:
            target_ev = items[0]
            target_ev["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"}
            target_ev["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"}
            service.events().update(calendarId="primary", eventId=target_ev["id"], body=target_ev).execute()
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi cập nhật dời lịch trên Google Calendar: {e}")
        return False
