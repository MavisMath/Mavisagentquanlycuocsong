"""
ui/components/tab_retrospective.py - Tab 4: Giai đoạn 3: Tổng Kết & Cải Thiện (Retrospective Coach).
"""

import streamlit as st
from ui.components.helpers import (
    safe_list,
    load_user_goals,
    save_user_goals,
    load_master_schedule,
    load_retrospective_logs,
    calculate_user_streak,
    is_calendar_connected,
    sync_schedule_to_google_calendar,
    scheduler_chat,
    retrospective_chat,
)


def render_tab_retrospective(current_username: str, current_name: str):
    """Hiển thị Giai đoạn 3: Tổng Kết, Soi Điểm Mù & Tái Cấu Trúc Khép Kín."""
    goals_key = f"goals_{current_username}"
    master_schedule_key = f"master_schedule_{current_username}"
    retro_logs_key = f"retro_logs_{current_username}"
    chat_retro_key = f"chat_retro_{current_username}"

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

                has_morning_miss = any("sáng" in s.lower() or "06:" in s or "07:" in s for s, _ in sorted_missed_slots)
                has_night_miss = any("tối" in s.lower() or "19:" in s or "20:" in s or "21:" in s for s, _ in sorted_missed_slots)

                if has_morning_miss:
                    st.info("💡 **Chẩn đoán nhịp sinh học sáng:** Thường xuyên trượt lịch buổi sáng cho thấy thói quen thức khuya hoặc ngủ không đủ giấc. Khuyến nghị đi ngủ trước 22:15 hoặc dời khung giờ thực thi sang buổi chiều (17:30 - 18:30).")
                if has_night_miss:
                    st.info("💡 **Chẩn đoán nhịp sinh học tối:** Bỏ lỡ khung giờ tối muộn là dấu hiệu cạn kiệt năng lượng ý chí (ego depletion) sau cả ngày. Khuyến nghị dời task nặng sang sáng (08:30) hoặc giảm thời lượng xuống 45 phút.")
            else:
                st.success("🎉 **Tuyệt vời! Bạn không bỏ lỡ bất kỳ nhiệm vụ nào trong 7 ngày qua.** Kỷ luật thép được duy trì rất tốt!")

        st.markdown("---")

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

                target_goal_name = matched_goal.get("title") or matched_goal.get("goal_name", "Mục tiêu") if matched_goal else rec_target
                if scheduler_chat is not None:
                    sched_prompt = (
                        f"Tái cấu trúc lại Master Schedule 7 ngày cho mục tiêu '{target_goal_name}' "
                        f"theo khung giờ mới: {rec_time}, thời lượng: {rec_hours} giờ/ngày, "
                        f"giờ đi ngủ tối ưu: {rec_sleep}. "
                        f"Chiến lược mới: {updated_strat}. "
                        f"Hãy lập lịch cân bằng, chi tiết 7 ngày từ hôm nay!"
                    )
                    scheduler_chat(sched_prompt, username=current_username)

                fresh_ms = load_master_schedule(current_username)
                st.session_state[master_schedule_key] = fresh_ms

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
            if chat_retro_key not in st.session_state:
                st.session_state[chat_retro_key] = []
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
            for msg in st.session_state.get(chat_retro_key, []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if retro_input := st.chat_input(
            "Chia sẻ cảm xúc hoặc nguyên nhân chưa xong task hôm nay...",
            key=f"input_retro_{current_username}",
        ):
            if chat_retro_key not in st.session_state:
                st.session_state[chat_retro_key] = []
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

    st.markdown("---")
    with st.expander("🧠 Bộ Nhớ Thích Nghi Trọn Đời (Adaptive Memory)", expanded=False):
        st.info(
            "💡 Toàn bộ các phương pháp hiệu quả cao, bài học cần tránh và quy luật năng suất được AI tự động đúc kết "
            "sau mỗi phiên hồi cứu. Bạn có thể xem chi tiết, quản lý và chủ động đóng góp thêm tại Tab **'🧠 Bộ Nhớ Thích Nghi'**."
        )
