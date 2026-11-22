"""
ui/components/mascot_banner.py - Dynamic Duolingo-style Mascot Banner for Mavis AI Executive & Life Coach.

Displays at the top of the main dashboard:
1. Mavis Mascot container (from assets/mascot/ with smart fallback to SVG/emoji).
2. Dynamic speech bubble with encouraging executive coach dialogue based on streak, completed tasks, and upcoming deadlines.
3. Daily progress bar (% tasks done today) + Duolingo-style 3D Flame Streak and Diamond XP badges.
"""

import os
import base64
from datetime import datetime, timedelta, date, time as dtime
import streamlit as st

from ui.components.helpers import (
    safe_dict,
    safe_list,
    load_master_schedule,
    calculate_user_streak,
    VIETNAM_WEEKDAYS,
)

# Inline SVG Fallback representing the friendly Duolingo-style Mavis Mascot
DEFAULT_MAVIS_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="bodyGrad_fb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2CD4FF"/>
      <stop offset="50%" stop-color="#1CB0F6"/>
      <stop offset="100%" stop-color="#0E8ED8"/>
    </linearGradient>
    <linearGradient id="bellyGrad_fb" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E8F7FF"/>
    </linearGradient>
    <linearGradient id="beakGrad_fb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFD43B"/>
      <stop offset="100%" stop-color="#FF9600"/>
    </linearGradient>
    <linearGradient id="phoneGrad_fb" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6EE721"/>
      <stop offset="100%" stop-color="#4CAF08"/>
    </linearGradient>
  </defs>
  <ellipse cx="60" cy="112" rx="36" ry="6" fill="#000000" opacity="0.08"/>
  <path d="M 22 56 C 12 62, 10 76, 18 84 C 26 90, 32 82, 30 70 Z" fill="#0E8ED8"/>
  <path d="M 98 56 C 112 50, 116 66, 106 78 C 98 84, 90 76, 92 64 Z" fill="#0E8ED8"/>
  <ellipse cx="60" cy="62" rx="42" ry="44" fill="url(#bodyGrad_fb)"/>
  <polygon points="30,28 42,16 46,32" fill="#0E8ED8"/>
  <polygon points="90,28 78,16 74,32" fill="#0E8ED8"/>
  <ellipse cx="60" cy="74" rx="28" ry="28" fill="url(#bellyGrad_fb)"/>
  <ellipse cx="32" cy="66" rx="8" ry="5" fill="#FF8CA3" opacity="0.6"/>
  <ellipse cx="88" cy="66" rx="8" ry="5" fill="#FF8CA3" opacity="0.6"/>
  <ellipse cx="44" cy="50" rx="14" ry="16" fill="#FFFFFF"/>
  <ellipse cx="46" cy="50" rx="8" ry="10" fill="#1C3854"/>
  <circle cx="48" cy="46" r="3.5" fill="#FFFFFF"/>
  <circle cx="44" cy="54" r="1.5" fill="#2CD4FF"/>
  <ellipse cx="76" cy="50" rx="14" ry="16" fill="#FFFFFF"/>
  <ellipse cx="74" cy="50" rx="8" ry="10" fill="#1C3854"/>
  <circle cx="72" cy="46" r="3.5" fill="#FFFFFF"/>
  <circle cx="76" cy="54" r="1.5" fill="#2CD4FF"/>
  <path d="M 54 58 Q 60 55 66 58 Q 60 72 54 58 Z" fill="url(#beakGrad_fb)"/>
  <path d="M 24 50 A 40 42 0 0 1 96 50" fill="none" stroke="#D1D5DB" stroke-width="5" stroke-linecap="round"/>
  <rect x="18" y="44" width="8" height="18" rx="4" fill="url(#phoneGrad_fb)"/>
  <rect x="94" y="44" width="8" height="18" rx="4" fill="url(#phoneGrad_fb)"/>
  <polygon points="56,76 64,76 62,82 58,82" fill="#FFC800"/>
  <polygon points="57,82 63,82 65,96 60,100 55,96" fill="#FF9600"/>
  <circle cx="60" cy="80" r="1.5" fill="#FFFFFF"/>
  <ellipse cx="48" cy="104" rx="7" ry="4" fill="#FF9600"/>
  <ellipse cx="72" cy="104" rx="7" ry="4" fill="#FF9600"/>
</svg>
"""


def _load_mascot_media(mood: str = "default") -> str:
    """
    Tìm và đọc ảnh linh vật từ thư mục assets/mascot/.
    Hỗ trợ các định dạng .png, .jpg, .jpeg, .svg, .webp, .gif.
    Nếu không tìm thấy file phù hợp, trả về SVG linh vật Duolingo sắc nét.
    """
    possible_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "mascot"),
        os.path.join(os.getcwd(), "assets", "mascot"),
    ]

    target_dir = None
    for d in possible_dirs:
        norm_d = os.path.normpath(d)
        if os.path.exists(norm_d) and os.path.isdir(norm_d):
            target_dir = norm_d
            break

    if target_dir:
        try:
            files = os.listdir(target_dir)
            valid_exts = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")
            media_files = [f for f in files if f.lower().endswith(valid_exts)]

            if media_files:
                selected_file = None

                # Ưu tiên tìm file theo mood (celebrate, fire, focus, ready...)
                mood_patterns = {
                    "celebrate": ["celebrate", "happy", "win", "cheer"],
                    "fire": ["fire", "streak", "flame"],
                    "focus": ["focus", "work", "clock"],
                    "ready": ["ready", "run", "start"],
                }
                patterns = mood_patterns.get(mood, [])
                for pat in patterns:
                    for mf in media_files:
                        if pat in mf.lower():
                            selected_file = mf
                            break
                    if selected_file:
                        break

                # Nếu chưa tìm thấy, lấy file mavis.* hoặc mascot.* hoặc file đầu tiên
                if not selected_file:
                    for mf in media_files:
                        name_lower = mf.lower()
                        if "mavis" in name_lower or "mascot" in name_lower:
                            selected_file = mf
                            break

                if not selected_file and media_files:
                    selected_file = media_files[0]

                if selected_file:
                    file_path = os.path.join(target_dir, selected_file)
                    ext = os.path.splitext(selected_file)[1].lower()

                    if ext == ".svg":
                        with open(file_path, "r", encoding="utf-8") as fp:
                            svg_content = fp.read()
                            if "<svg" in svg_content:
                                return svg_content

                    mime_map = {
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".webp": "image/webp",
                        ".gif": "image/gif",
                        ".svg": "image/svg+xml",
                    }
                    mime_type = mime_map.get(ext, "image/png")
                    with open(file_path, "rb") as fp:
                        b64_data = base64.b64encode(fp.read()).decode("utf-8")
                    return f'<img src="data:{mime_type};base64,{b64_data}" alt="Mavis Mascot" style="width:100%; height:100%; object-fit:contain;" />'
        except Exception:
            pass

    return DEFAULT_MAVIS_SVG


def render_mascot_banner(current_username: str, current_name: str):
    """
    Render Mascot Banner phong cách Duolingo ở đầu màn hình chính (Tổng Hành Dinh).
    """
    # 1. Tính toán Streak người dùng
    try:
        streak = calculate_user_streak(current_username)
        streak = max(1, int(streak))
    except Exception:
        streak = 1

    # 2. Lấy Master Schedule cho ngày hôm nay
    sched_key = f"master_schedule_{current_username}"
    master_schedule = st.session_state.get(sched_key)
    if not master_schedule:
        try:
            master_schedule = load_master_schedule(current_username)
        except Exception:
            master_schedule = []

    today_date = datetime.now().date()
    today_iso = today_date.strftime("%Y-%m-%d")
    today_vi = VIETNAM_WEEKDAYS.get(today_date.weekday(), "")

    today_tasks = [
        t for t in (master_schedule or [])
        if isinstance(t, dict) and (
            str(t.get("date", "")).strip() == today_iso
            or (not str(t.get("date", "")).startswith("202") and str(t.get("date", "")).strip() == today_vi)
        )
    ]

    total_tasks = len(today_tasks)
    completed_tasks = len([t for t in today_tasks if t.get("is_done") is True])
    percent = int(round((completed_tasks / total_tasks * 100))) if total_tasks > 0 else 0

    # Điểm kinh nghiệm XP (Mỗi task xong +50 XP, thưởng streak +10 XP/ngày streak)
    xp = (completed_tasks * 50) + (streak * 10)

    # 3. Tìm task sắp đến hạn hoặc đang trong khung giờ
    now_time = datetime.now().time()
    upcoming_task = None
    for t in today_tasks:
        if not t.get("is_done"):
            slot_str = str(t.get("time_slot", "")).strip()
            if "-" in slot_str:
                try:
                    parts = slot_str.split("-")
                    end_str = parts[1].strip()
                    end_h, end_m = [int(x) for x in end_str.split(":")[:2]]
                    if now_time <= dtime(end_h, end_m):
                        upcoming_task = t
                        break
                except Exception:
                    if not upcoming_task:
                        upcoming_task = t
            elif not upcoming_task:
                upcoming_task = t

    # 4. Xác định thông điệp động viên & Trạng thái linh vật
    if total_tasks > 0 and completed_tasks == total_tasks:
        mood = "celebrate"
        bubble_title = "HUY HOÀNG HÔM NAY! 👑"
        bubble_msg = (
            f"Xuất sắc <b>{current_name}</b>! Bạn đã hoàn thành trọn vẹn 100% nhiệm vụ hôm nay. "
            "Hãy nghỉ ngơi, nạp năng lượng xứng đáng cho ngày mai nhé!"
        )
    elif upcoming_task:
        mood = "focus"
        t_name = str(upcoming_task.get("title") or upcoming_task.get("task_name") or "Nhiệm vụ tiếp theo").strip()
        t_slot = str(upcoming_task.get("time_slot") or "sắp tới").strip()
        bubble_title = "CHUẨN BỊ VÀO GUỒNG! ⏰"
        bubble_msg = (
            f"Sắp đến giờ thực hiện: <b>{t_name[:36]}</b> ({t_slot}). "
            f"Tập trung cao độ cùng Mavis để bảo vệ nhịp sinh học nhé!"
        )
    elif streak >= 3:
        mood = "fire"
        bubble_title = "NGỌN LỬA KỶ LUẬT! 🔥"
        bubble_msg = (
            f"Tuyệt đỉnh <b>{current_name}</b>! Chuỗi <b>{streak} ngày liên tiếp</b> đang rực sáng. "
            "Tiếp tục giữ vững kỷ luật của một Executive thực thụ nào!"
        )
    elif completed_tasks > 0:
        mood = "happy"
        bubble_title = "TIẾP TỤC BỨT PHÁ! ⚡"
        bubble_msg = (
            f"Đã giải quyết xong <b>{completed_tasks}/{total_tasks} việc</b> ({percent}%). "
            "Chỉ còn vài bước nữa là cán đích ngày hôm nay!"
        )
    elif total_tasks > 0:
        mood = "ready"
        bubble_title = "SẴN SÀNG CHINH PHỤC! 🚀"
        bubble_msg = (
            f"Chào <b>{current_name}</b>! Bạn có <b>{total_tasks} nhiệm vụ</b> hôm nay. "
            "Hãy hoàn thành task đầu tiên để bật ngọn lửa streak nhé!"
        )
    else:
        mood = "default"
        bubble_title = "CHÀO MỪNG TRỞ LẠI! ✨"
        bubble_msg = (
            f"Chào <b>{current_name}</b>! Bạn chưa có nhiệm vụ nào trong lịch hôm nay. "
            "Hãy sang <b>Giai đoạn 1</b> hoặc trò chuyện cùng <b>CEO Coach</b> để lên kế hoạch nhé!"
        )

    # 5. Lấy hình ảnh / SVG linh vật
    mascot_media_html = _load_mascot_media(mood)

    # 6. Render Giao diện HTML Duolingo
    banner_html = f"""
    <div class="mavis-mascot-banner">
        <div class="mascot-left-section">
            <div class="mascot-avatar-container">
                {mascot_media_html}
            </div>
            <div class="mascot-speech-bubble">
                <div class="bubble-arrow"></div>
                <div class="bubble-title">{bubble_title}</div>
                <div class="bubble-message">{bubble_msg}</div>
            </div>
        </div>
        <div class="mascot-right-section">
            <div class="mascot-badges-row">
                <div class="badge-streak" title="Chuỗi ngày duy trì kỷ luật liên tiếp">
                    <span class="badge-icon">🔥</span>
                    <span class="badge-value">{streak}</span>
                    <span class="badge-label">Ngày Streak</span>
                </div>
                <div class="badge-xp" title="Điểm kinh nghiệm tích lũy khi làm task và giữ streak">
                    <span class="badge-icon">💎</span>
                    <span class="badge-value">{xp}</span>
                    <span class="badge-label">XP Hôm Nay</span>
                </div>
            </div>
            <div class="mascot-progress-container">
                <div class="progress-labels">
                    <span class="progress-title">🎯 Tiến độ hôm nay:</span>
                    <span class="progress-count">{completed_tasks}/{total_tasks} việc</span>
                    <span class="progress-percent">({percent}%)</span>
                </div>
                <div class="progress-track" title="Tỷ lệ hoàn thành nhiệm vụ trong ngày">
                    <div class="progress-fill" style="width: {max(0, min(100, percent))}%;"></div>
                </div>
            </div>
        </div>
    </div>
    """

    st.markdown(banner_html, unsafe_allow_html=True)
