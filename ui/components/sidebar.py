"""
ui/components/sidebar.py - Sidebar Control Center for Mavis AI Executive & Life Coach.

Sidebar tinh gọn, chỉ giữ lại:
1. Thông tin user & Đăng xuất (User Info & Logout).
2. Khung giờ năng lượng hiện tại (Current Bio-Energy Slot).
3. Tóm tắt task hôm nay (Today's Tasks Summary).
4. Nút Reset All với xác nhận 2 lần an toàn (Popover + Checkbox).
"""

from typing import Any
from datetime import datetime
import streamlit as st

from ui.components.helpers import (
    safe_list,
    load_user_goals,
    load_master_schedule,
    load_retrospective_logs,
    is_mongodb_available,
    get_mongo_connection_error,
    get_mongo_uri,
    OPENING_GREETING,
    VIETNAM_WEEKDAYS,
)


def render_sidebar(current_username: str, current_name: str, authenticator: Any = None):
    """
    Hiển thị Bảng Điều Khiển Tinh Gọn bên trái (Sidebar Control Center).
    Chỉ giữ lại: Thông tin user, Khung giờ năng lượng hiện tại, Tóm tắt task hôm nay,
    và nút Reset All có xác nhận 2 lần an toàn.
    """
    goals_key = f"goals_{current_username}"
    resources_key = f"resources_{current_username}"
    energy_key = f"energy_{current_username}"
    emotion_key = f"emotion_{current_username}"
    intent_key = f"intent_{current_username}"
    plan_key = f"plan_{current_username}"
    thread_ver_key = f"thread_ver_{current_username}"
    msg_key = f"messages_{current_username}"
    chat_ceo_key = f"chat_ceo_{current_username}"
    chat_arch_key = f"chat_arch_{current_username}"
    chat_sched_key = f"chat_sched_{current_username}"
    chat_retro_key = f"chat_retro_{current_username}"
    master_schedule_key = f"master_schedule_{current_username}"
    retro_logs_key = f"retro_logs_{current_username}"
    pending_goal_key = f"pending_goal_{current_username}"
    awaiting_confirmation_key = f"awaiting_confirmation_{current_username}"
    goal_profile_key = f"goal_profile_{current_username}"
    roadmap_key = f"roadmap_{current_username}"
    profile_key = f"profile_{current_username}"

    with st.sidebar:
        # ==========================================
        # 1. THÔNG TIN USER & ĐĂNG XUẤT
        # ==========================================
        st.markdown("## ⚡ Executive Center")
        st.caption("Bảng chỉ huy nhịp sinh học & kế hoạch điều hành")

        st.markdown(
            f"""
            <div class="user-badge">
                <div style="font-size:0.8em; text-transform:uppercase; letter-spacing:1px; opacity:0.8;">Tài khoản điều hành</div>
                <div style="font-size:1.15em; font-weight:bold; margin-top:2px;">{current_name}</div>
                <div style="font-size:0.85em; opacity:0.9;"><code>@{current_username}</code> | SaaS Pro Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if authenticator is not None:
            try:
                authenticator.logout(button_name="🚪 Đăng Xuất (Logout)", location="sidebar", key="sidebar_logout_btn")
            except Exception:
                if st.sidebar.button("🚪 Đăng Xuất", key="fallback_logout"):
                    st.session_state["authentication_status"] = None
                    st.session_state["username"] = None
                    st.session_state["name"] = None
                    st.rerun()
        else:
            if st.sidebar.button("🚪 Đăng Xuất", key="fallback_logout_noauth"):
                st.session_state["authentication_status"] = None
                st.session_state["username"] = None
                st.session_state["name"] = None
                st.rerun()

        st.markdown("---")

        # ==========================================
        # 2. KHUNG GIỜ NĂNG LƯỢNG HIỆN TẠI
        # ==========================================
        st.subheader("🔋 Khung Giờ Năng Lượng")
        energy = st.session_state.get(energy_key, "high")

        # Đọc danh sách mục tiêu Active để đề xuất ưu tiên động
        user_goals_sidebar = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))
        active_goals_sidebar = [g for g in user_goals_sidebar if g.get("status") in ["active", "in_progress"]]

        if energy == "high":
            st.success("🟢 **NĂNG LƯỢNG ĐỈNH CAO (HIGH)**")
            if active_goals_sidebar:
                focus_titles = [f"**{g.get('title') or g.get('goal_name')}**" for g in active_goals_sidebar[:2] if (g.get('title') or g.get('goal_name'))]
                priority_text = f"Tập trung Deep Work bứt phá: {', '.join(focus_titles)}"
            else:
                priority_text = "Tối ưu hóa các tác vụ nhận thức cao, tư duy chiến lược và quyết định quan trọng"
            st.markdown(
                f"""
                * **Khung giờ vàng:** `08:00 - 10:00 (Sáng)`
                * **Trạng thái:** Tối ưu tải nhận thức cao & năng lượng đỉnh
                * **Ưu tiên:** {priority_text}
                """
            )
        else:
            st.warning("🟠 **NĂNG LƯỢNG HẠ TẢI (LOW)**")
            st.markdown(
                """
                * **Khung giờ:** `Buổi chiều (sau 14:00)` hoặc khi mệt mỏi
                * **Trạng thái:** Hạ tải nhận thức, tái tạo năng lượng
                * **Hành động:** Pomodoro 15 phút, rà soát tài liệu hoặc nghỉ ngơi phục hồi
                """
            )

        st.markdown("---")

        # ==========================================
        # 3. TÓM TẮT TASK HÔM NAY (TODAY'S TASKS)
        # ==========================================
        st.subheader("📋 Tóm Tắt Task Hôm Nay")

        today_date = datetime.now().date()
        today_iso = today_date.strftime("%Y-%m-%d")
        today_vi = VIETNAM_WEEKDAYS.get(today_date.weekday(), "")

        ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))
        today_tasks = [
            t for t in ms
            if isinstance(t, dict) and (
                str(t.get("date", "")).strip() == today_iso
                or (not str(t.get("date", "")).startswith("202") and str(t.get("date", "")).strip() == today_vi)
            )
        ]

        total_today = len(today_tasks)
        done_today = sum(1 for t in today_tasks if t.get("is_done") is True)

        if total_today > 0:
            percent_today = int(round(done_today / total_today * 100))
            st.caption(f"Tiến độ: **{done_today}/{total_today} việc** ({percent_today}%)")
            for idx, task in enumerate(today_tasks, 1):
                slot = str(task.get("time_slot") or task.get("session") or "N/A").strip()
                name = str(task.get("title") or task.get("task_name") or task.get("task_detail") or "Nhiệm vụ").strip()
                is_done = bool(task.get("is_done"))
                energy_lvl = str(task.get("energy_level") or "").strip()

                status_icon = "✅" if is_done else "⏳"

                # Tag năng lượng trực quan
                if "deep" in energy_lvl.lower() or "🔴" in energy_lvl:
                    tag = "🔴 Deep Work"
                elif "recharge" in energy_lvl.lower() or "ngủ" in name.lower() or "🟢" in energy_lvl:
                    tag = "🟢 Phục hồi"
                elif "ăn" in name.lower() or "uống" in name.lower() or "tập" in name.lower() or "🟡" in energy_lvl:
                    tag = "🟡 Thói quen"
                else:
                    tag = "⚡ Tiêu chuẩn"

                with st.container(border=True):
                    st.markdown(f"**{status_icon} {slot}** • `{tag}`")
                    st.markdown(f"{name[:70]}")
        else:
            if active_goals_sidebar:
                first_g_title = active_goals_sidebar[0].get("title") or active_goals_sidebar[0].get("goal_name") or "mục tiêu"
                st.info(f"Hôm nay chưa có lịch cho **{first_g_title}**. Hãy bấm nút **'📅 Phân rã & Xếp lịch ngay'** ở Tổng Hành Dinh để Coach tự động lên lịch!")
            else:
                st.info("Chưa có nhiệm vụ nào hôm nay. Hãy thiết lập mục tiêu ở Giai đoạn 1 để Coach phân bổ lịch trình!")

        st.markdown("---")

        # ==========================================
        # 4. NÚT RESET ALL VỚI XÁC NHẬN 2 LẦN (POPOVER + CHECKBOX)
        # ==========================================
        with st.popover("🔄 Làm mới phiên (Reset All)", use_container_width=True):
            st.markdown("#### ⚠️ Xác nhận làm mới phiên làm việc")
            st.markdown(
                "Thao tác này sẽ **đặt lại lịch sử hội thoại** của 4 Chatbot và xóa các trạng thái bộ nhớ tạm trong phiên hiện tại.\n\n"
                "🔒 **An toàn:** Toàn bộ mục tiêu và kế hoạch đã lưu trong **Cơ sở dữ liệu (MongoDB)** vẫn được bảo toàn an toàn."
            )
            confirm_reset = st.checkbox(
                "Tôi hiểu và xác nhận muốn làm mới phiên này",
                key=f"chk_confirm_reset_{current_username}",
            )
            if st.button(
                "🚨 Xác nhận Xóa & Làm Mới Toàn Bộ",
                type="primary",
                disabled=not confirm_reset,
                use_container_width=True,
                key=f"btn_execute_reset_{current_username}",
            ):
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
                st.toast("✅ Đã làm mới phiên làm việc thành công!", icon="🔄")
                st.rerun()

        st.markdown("---")

        # ==========================================
        # 5. TRẠNG THÁI KẾT NỐI DATABASE
        # ==========================================
        if is_mongodb_available():
            st.caption("🟢 **Đã kết nối Cloud DB (MongoDB)**")
        else:
            st.caption("🔴 **Chưa kết nối MongoDB**")
            mongo_err = get_mongo_connection_error()
            if get_mongo_uri() and mongo_err and "Chưa cấu hình" not in mongo_err:
                st.error(f"Lỗi kết nối MongoDB: {mongo_err}")
