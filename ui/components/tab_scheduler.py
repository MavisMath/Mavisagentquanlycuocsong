"""
ui/components/tab_scheduler.py - Tab 3: Giai đoạn 2: Trợ Lý Đồng Hành Thời Gian Thực (Scheduler & Live Hero).
"""

from datetime import datetime, timedelta, date, time as dtime, timezone as d_timezone
import streamlit as st
from ui.components.helpers import (
    safe_dict,
    safe_list,
    shorten_task_name,
    push_undo_state,
    save_undo_snapshot,
    apply_undo,
    apply_redo,
    generate_gcal_link,
    generate_ics_from_master_schedule,
    load_user_goals,
    load_master_schedule,
    save_master_schedule,
    update_master_schedule_task_status,
    defer_master_schedule_task_to_tomorrow,
    ensure_schedule_covers_date,
    get_vietnam_today,
    VIETNAM_WEEKDAYS,
    is_calendar_connected,
    sync_schedule_to_google_calendar,
    scheduler_chat,
)


def render_tab_scheduler(current_username: str, current_name: str):
    """Hiển thị Giai đoạn 2: Trợ Lý Đồng Hành Thời Gian Thực (Hôm Nay ➔ Từng Giờ Cụ Thể)."""
    goals_key = f"goals_{current_username}"
    master_schedule_key = f"master_schedule_{current_username}"
    chat_sched_key = f"chat_sched_{current_username}"

    st.markdown("### 📅 Giai đoạn 2: Trợ Lý Đồng Hành Thời Gian Thực (Hôm Nay ➔ Từng Giờ Cụ Thể)")
    st.caption("Đồng bộ thời gian thực Asia/Ho_Chi_Minh • Từng giờ cụ thể • Ăn gì / Uống gì / Tập gì / Ngủ mấy giờ • Đồng bộ Google Calendar 2 chiều")

    col_dash_sched, col_chat_sched = st.columns([1.15, 0.85], gap="large")

    with col_dash_sched:
        user_goals_sched = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))
        active_user_goals = [g for g in user_goals_sched if safe_dict(g).get('status') == 'active']
        if not active_user_goals:
            active_user_goals = [g for g in user_goals_sched if safe_dict(g).get('status') not in ('paused', 'completed')]

        if not active_user_goals:
            st.info('💡 Chưa có mục tiêu nào đang kích hoạt. Hãy thiết lập mục tiêu ở Tổng Hành Dinh hoặc Giai đoạn 1 trước nhé!')
        else:
            ms = safe_list(st.session_state.get(master_schedule_key) or load_master_schedule(current_username))

            # ----------------------------------------------------------------------
            # ĐỒNG HỒ THỜI GIAN THỰC & BANNER "⚡ HÀNH ĐỘNG NGAY BÂY GIỜ" (ASIA/HO_CHI_MINH)
            # ----------------------------------------------------------------------
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
                            push_undo_state(current_username)
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

            active_schedule = [
                t for t in ms
                if not (
                    (t.get("goal_id") and str(t.get("goal_id")) in paused_goal_ids) or
                    (t.get("goal_title") and str(t.get("goal_title")) in paused_goal_titles)
                )
            ]

            if paused_goal_titles:
                st.info(f"⏸️ **{len(paused_goal_titles)} mục tiêu đang tạm dừng:** {', '.join(paused_goal_titles)}. Các khung giờ tương ứng tạm thời không chiếm lịch.")

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
                                push_undo_state(current_username)
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

                sel_date_key = f"selected_sched_date_{current_username}"
                if sel_date_key not in st.session_state:
                    st.session_state[sel_date_key] = today_date

                current_picked_date = st.session_state.get(sel_date_key, today_date)
                if not isinstance(current_picked_date, (date, datetime)):
                    try:
                        current_picked_date = datetime.strptime(str(current_picked_date)[:10], "%Y-%m-%d").date()
                    except Exception:
                        current_picked_date = today_date
                elif isinstance(current_picked_date, datetime):
                    current_picked_date = current_picked_date.date()

                if current_picked_date < min_date_limit:
                    current_picked_date = min_date_limit
                elif current_picked_date > base_target_date:
                    current_picked_date = base_target_date

                # ------------------------------------------------------------------
                # 1. BỘ CHỌN GÓC NHÌN THỜI GIAN & PHẠM VI MỤC TIÊU
                # ------------------------------------------------------------------
                col_view_title, col_t2_undo, col_t2_redo = st.columns([0.74, 0.13, 0.13])
                with col_view_title:
                    st.markdown("#### 🧭 Góc Nhìn Thời Gian & Lịch Trình Điều Hành:")
                with col_t2_undo:
                    undo_cnt = len(st.session_state.get(f"undo_stack_{current_username}", []))
                    if st.button(f"↩️ Undo ({undo_cnt})", key=f"btn_undo_tab2_{current_username}", disabled=(undo_cnt == 0), use_container_width=True, help="Hoàn tác thao tác trước đó (Ctrl+Z)"):
                        if apply_undo(current_username):
                            st.toast("↩️ Đã hoàn tác thao tác vừa rồi!")
                            st.rerun()
                with col_t2_redo:
                    redo_cnt = len(st.session_state.get(f"redo_stack_{current_username}", []))
                    if st.button(f"↪️ Redo ({redo_cnt})", key=f"btn_redo_tab2_{current_username}", disabled=(redo_cnt == 0), use_container_width=True, help="Làm lại thao tác vừa hoàn tác (Ctrl+Y)"):
                        if apply_redo(current_username):
                            st.toast("↪️ Đã làm lại thao tác!")
                            st.rerun()
                view_options = ["📅 Theo Ngày", "🗓️ Theo Tuần", "📆 Theo Tháng", "📊 Theo Quý"]
                view_key = f"sched_view_mode_{current_username}"
                pending_view_key = f"pending_sched_view_{current_username}"
                if pending_view_key in st.session_state:
                    st.session_state[view_key] = st.session_state.pop(pending_view_key)

                cur_selected_view = st.session_state.get(view_key, "📅 Theo Ngày")
                if cur_selected_view not in view_options:
                    cur_selected_view = "📅 Theo Ngày"

                if hasattr(st, "segmented_control"):
                    selected_view = st.segmented_control(
                        "Góc nhìn thời gian:",
                        options=view_options,
                        default=cur_selected_view,
                        key=view_key,
                        label_visibility="collapsed",
                    )
                else:
                    default_idx = view_options.index(cur_selected_view)
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

                # THANH ĐIỀU HƯỚNG THAO TÁC & TIỆN ÍCH THỰC CHIẾN
                undo_snapshot_key = f"ms_undo_snapshot_{current_username}"
                has_undo = bool(st.session_state.get(undo_snapshot_key))

                today_tasks_copy = [
                    t for t in filtered_schedule
                    if t.get("date") == today_date_str
                    or (not str(t.get("date", "")).startswith("202") and t.get("date") == today_vi_day)
                ]
                lines_summary = [f"📅 LỊCH TRÌNH HÔM NAY — {today_vi_day}, {today_date.strftime('%d/%m/%Y')}:"]
                if today_tasks_copy:
                    for t in today_tasks_copy:
                        status_icon = "✅" if t.get("is_done") else "▫️"
                        t_slot_disp = t.get("time_slot", "08:00")
                        t_name_disp = t.get("task_detail", "")
                        t_energy_disp = t.get("energy_level", "")
                        lines_summary.append(f"{status_icon} [{t_slot_disp}] {t_name_disp} ({t_energy_disp})")
                else:
                    lines_summary.append("(Chưa có task nào được lên lịch cho hôm nay)")
                copy_text_today = "\n".join(lines_summary)

                col_act_left, col_act_undo, col_act_today, col_act_right, col_act_copy = st.columns([0.18, 0.22, 0.20, 0.18, 0.22])
                with col_act_left:
                    if st.button("⬅️ Back", key=f"btn_global_back_{current_username}", use_container_width=True):
                        if selected_view == "📅 Theo Ngày":
                            st.session_state[sel_date_key] = max(min_date_limit, current_picked_date - timedelta(days=1))
                        elif selected_view == "🗓️ Theo Tuần":
                            st.session_state[sel_date_key] = max(min_date_limit, current_picked_date - timedelta(days=7))
                        else:
                            st.session_state[sel_date_key] = max(min_date_limit, current_picked_date - timedelta(days=30))
                        st.rerun()

                with col_act_undo:
                    if st.button("↩️ Undo Lịch", key=f"btn_global_undo_{current_username}", disabled=not has_undo, use_container_width=True):
                        prev_snapshot = st.session_state.pop(undo_snapshot_key, None)
                        if prev_snapshot:
                            save_master_schedule(prev_snapshot, username=current_username)
                            st.session_state[master_schedule_key] = prev_snapshot
                            st.toast("↩️ Đã hoàn tác thay đổi lịch gần nhất!")
                            st.rerun()

                with col_act_today:
                    if st.button("📍 Về Hôm Nay", key=f"btn_global_today_{current_username}", use_container_width=True):
                        st.session_state[sel_date_key] = today_date
                        st.session_state[pending_view_key] = "📅 Theo Ngày"
                        st.rerun()

                with col_act_right:
                    if st.button("➡️ Next", key=f"btn_global_next_{current_username}", use_container_width=True):
                        if selected_view == "📅 Theo Ngày":
                            st.session_state[sel_date_key] = min(base_target_date, current_picked_date + timedelta(days=1))
                        elif selected_view == "🗓️ Theo Tuần":
                            st.session_state[sel_date_key] = min(base_target_date, current_picked_date + timedelta(days=7))
                        else:
                            st.session_state[sel_date_key] = min(base_target_date, current_picked_date + timedelta(days=30))
                        st.rerun()

                with col_act_copy:
                    with st.popover("📋 Copy Lịch Hôm Nay", use_container_width=True):
                        st.markdown("**📋 Tóm Tắt Lịch Hôm Nay (1-Click Copy):**")
                        st.code(copy_text_today, language="text")
                        st.caption("💡 Bấm nút copy ở góc trên bên phải khung text để gửi Zalo / Telegram.")

                # BỘ CHỌN THÁNG & TUẦN TRONG THÁNG
                month_list = []
                cur_m_iter = min_date_limit.replace(day=1)
                end_m_limit = base_target_date.replace(day=1)
                while cur_m_iter <= end_m_limit:
                    month_list.append(cur_m_iter)
                    if cur_m_iter.month == 12:
                        cur_m_iter = cur_m_iter.replace(year=cur_m_iter.year + 1, month=1)
                    else:
                        cur_m_iter = cur_m_iter.replace(month=cur_m_iter.month + 1)

                if not month_list:
                    month_list = [today_date.replace(day=1)]

                current_month_first = current_picked_date.replace(day=1)
                m_options = [m.strftime("Tháng %m/%Y") for m in month_list]
                m_default_idx = month_list.index(current_month_first) if current_month_first in month_list else 0

                with st.expander("🗓️ Bộ Chọn Tháng & Tuần Trong Tháng (Mở nhanh)", expanded=(selected_view in ["🗓️ Theo Tuần", "📆 Theo Tháng"])):
                    col_m_sel, col_w_sel = st.columns([0.35, 0.65])
                    with col_m_sel:
                        chosen_m_label = st.selectbox(
                            "Chọn Tháng:",
                            options=m_options,
                            index=m_default_idx,
                            key=f"sel_quick_month_{current_username}",
                        )
                        chosen_month_date = month_list[m_options.index(chosen_m_label)]
                    with col_w_sel:
                        import calendar
                        _, last_day = calendar.monthrange(chosen_month_date.year, chosen_month_date.month)
                        weeks_in_month = []
                        for w_num, (s_day, e_day) in enumerate([(1, 7), (8, 14), (15, 21), (22, 28), (29, last_day)], 1):
                            if s_day <= last_day:
                                actual_e = min(e_day, last_day)
                                w_start = chosen_month_date.replace(day=s_day)
                                w_end = chosen_month_date.replace(day=actual_e)
                                weeks_in_month.append((f"Tuần {w_num} ({w_start.strftime('%d/%m')}-{w_end.strftime('%d/%m')})", w_start))

                        st.markdown("**Mở nhanh Tuần:**")
                        w_cols = st.columns(len(weeks_in_month))
                        for w_idx, (w_lbl, w_st_date) in enumerate(weeks_in_month):
                            with w_cols[w_idx]:
                                if st.button(w_lbl, key=f"btn_quick_wk_{current_username}_{chosen_month_date.strftime('%Y%m')}_{w_idx}", use_container_width=True):
                                    st.session_state[sel_date_key] = w_st_date
                                    st.session_state[pending_view_key] = "🗓️ Theo Tuần"
                                    st.rerun()

                st.markdown("---")

                if not filtered_schedule:
                    st.info(
                        "💡 Chưa có lịch trình. Bạn hãy trao đổi với **AI Master Scheduler** ở cột bên phải "
                        "(ví dụ: *'Hãy phân bổ lịch trình chi tiết cho mục tiêu của tôi'*) để tạo lịch ngay lập tức!"
                    )
                else:
                    # GÓC NHÌN 1: 📅 THEO NGÀY
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
                                                save_undo_snapshot(current_username, ms)
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

                                            col_btn_link, col_btn_defer = st.columns([0.65, 0.35])
                                            with col_btn_link:
                                                if t_link:
                                                    btn_lbl = f"📦 Mở Tài Liệu: {t_res_title[:28]}" if (t_res_title and len(t_res_title) < 28) else "📦 Mở Tài Liệu (1-Click)"
                                                    st.link_button(label=btn_lbl, url=t_link, use_container_width=False)
                                            with col_btn_defer:
                                                defer_k = f"btn_def_day_{current_username}_{cur_d_iso}_{sess}_{idx}_{abs(hash(t_detail)) % 100000}"
                                                if st.button("⏭️ Dời sang mai", key=defer_k, use_container_width=True):
                                                    save_undo_snapshot(current_username, ms)
                                                    ok_def, next_d = defer_master_schedule_task_to_tomorrow(t_detail, cur_d_iso, current_username)
                                                    if ok_def:
                                                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                                        st.toast(f"⏭️ Đã dời task sang ngày mai ({next_d})!")
                                                        st.rerun()

                        if deferred_tasks:
                            st.markdown("---")
                            with st.expander(f"💤 {len(deferred_tasks)} task Deep Work đã tự động trượt sang ngày mai (Bảo toàn Streak, không tính trễ):", expanded=False):
                                for dt in deferred_tasks:
                                    dt_title = dt.get("task_detail", "Nhiệm vụ")
                                    dt_slot = dt.get("time_slot", "")
                                    dt_goal = dt.get("goal_title", "")
                                    st.markdown(f"- ▫️ ⏰ **{dt_slot}**: {dt_title} `[🎯 {dt_goal}]` &nbsp; `:orange[Đã trượt sang ngày mai]`")

                    # GÓC NHÌN 2: 🗓️ THEO TUẦN (TIMETABLE GRID 8 CỘT)
                    elif selected_view == "🗓️ Theo Tuần":
                        mon_of_week = current_picked_date - timedelta(days=current_picked_date.weekday())
                        week_dates = [mon_of_week + timedelta(days=i) for i in range(7)]

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
                        st.caption("💡 Bấm '🔍 Mở' trên từng cột để xem chi tiết Ngày, hoặc bấm '📄 Chi tiết' để dời lịch / mở tài liệu:")

                        col_timetable_header = st.columns([0.16, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
                        with col_timetable_header[0]:
                            st.markdown("**⏰ Khung Giờ**")

                        for d_idx, d_obj in enumerate(week_dates):
                            d_str = d_obj.strftime("%Y-%m-%d")
                            d_short_date = d_obj.strftime("%d/%m")
                            d_name = VIETNAM_WEEKDAYS.get(d_obj.weekday(), "")
                            is_today_col = (d_obj == today_date)
                            badge_style = "color:#ff4b4b;" if is_today_col else ""
                            with col_timetable_header[d_idx + 1]:
                                st.markdown(f"<div style='text-align:center;'><span style='{badge_style}'>**{DAY_SHORT.get(d_name, d_name)}**</span><br/><code>{d_short_date}</code></div>", unsafe_allow_html=True)
                                if st.button("🔍 Mở", key=f"btn_open_wkd_{current_username}_{d_str}", use_container_width=True):
                                    st.session_state[sel_date_key] = d_obj
                                    st.session_state[pending_view_key] = "📅 Theo Ngày"
                                    st.rerun()

                        standard_slots = [
                            "06:30 - 07:30",
                            "08:00 - 10:00",
                            "10:30 - 11:30",
                            "12:00 - 12:30",
                            "14:00 - 16:00",
                            "16:30 - 17:30",
                            "18:00 - 18:30",
                            "19:30 - 21:00",
                            "21:30 - 22:30",
                        ]
                        all_slots_set = set(standard_slots)
                        for t in week_tasks:
                            ts = str(t.get("time_slot", "")).strip()
                            if ts and "-" in ts:
                                all_slots_set.add(ts)

                        def parse_slot_sort_key(slot_str: str) -> int:
                            try:
                                start_str = slot_str.split("-")[0].strip()
                                h, m = map(int, start_str.split(":"))
                                return h * 60 + m
                            except Exception:
                                return 9999

                        sorted_slots = sorted(list(all_slots_set), key=parse_slot_sort_key)

                        active_slots = [
                            slot for slot in sorted_slots
                            if any(
                                (t.get("date") == d.strftime("%Y-%m-%d") or (not str(t.get("date", "")).startswith("202") and t.get("date") == VIETNAM_WEEKDAYS.get(d.weekday(), "")))
                                and str(t.get("time_slot", "")).strip() == slot
                                for d in week_dates
                                for t in week_tasks
                            ) or slot in ["08:00 - 10:00", "12:00 - 12:30", "14:00 - 16:00", "16:30 - 17:30", "19:30 - 21:00"]
                        ]
                        if not active_slots:
                            active_slots = standard_slots

                        for slot_idx, slot in enumerate(active_slots):
                            st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px dashed #E5E5E5;'/>", unsafe_allow_html=True)
                            row_cols = st.columns([0.16, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
                            with row_cols[0]:
                                st.markdown(f"<div style='font-size:0.83rem; font-weight:bold; margin-top:6px;'>⏰ <code>{slot}</code></div>", unsafe_allow_html=True)

                            for d_idx, d_obj in enumerate(week_dates):
                                d_str = d_obj.strftime("%Y-%m-%d")
                                d_name = VIETNAM_WEEKDAYS.get(d_obj.weekday(), "")
                                with row_cols[d_idx + 1]:
                                    raw_matching = [
                                        t for t in filtered_schedule
                                        if (t.get("date") == d_str or (not str(t.get("date", "")).startswith("202") and t.get("date") == d_name))
                                        and str(t.get("time_slot", "")).strip() == slot
                                    ]
                                    seen_cell_details = set()
                                    cell_tasks = []
                                    for r_tk in raw_matching:
                                        detail_key = str(r_tk.get("task_detail", "")).strip().lower()
                                        if detail_key and detail_key not in seen_cell_details:
                                            seen_cell_details.add(detail_key)
                                            cell_tasks.append(r_tk)

                                    if not cell_tasks:
                                        st.markdown("<p style='color:#475569; text-align:center; margin-top:8px;'>—</p>", unsafe_allow_html=True)
                                    else:
                                        for t_idx, tk in enumerate(cell_tasks):
                                            t_detail = tk.get("task_detail", "Nhiệm vụ")
                                            t_energy = tk.get("energy_level", "🔴 Deep Work")
                                            energy_badge = "🔴" if ("deep" in str(t_energy).lower() or "🔴" in str(t_energy)) else ("🟡" if ("shallow" in str(t_energy).lower() or "🟡" in str(t_energy)) else "🟢")
                                            t_is_done = bool(tk.get("is_done", False))
                                            t_dod = tk.get("definition_of_done", "")
                                            t_link = tk.get("resource_url") or tk.get("resource_link", "")
                                            short_title = shorten_task_name(t_detail, max_words=5)

                                            grid_chk_key = f"chk_grd_{current_username}_{d_str}_{slot_idx}_{t_idx}_{abs(hash(t_detail)) % 100000}"

                                            new_done = st.checkbox(
                                                f"{energy_badge} {short_title}",
                                                value=t_is_done,
                                                key=grid_chk_key,
                                            )
                                            if new_done != t_is_done:
                                                save_undo_snapshot(current_username, ms)
                                                update_master_schedule_task_status(
                                                    task_identifier=t_detail,
                                                    is_done=new_done,
                                                    date=d_str,
                                                    username=current_username,
                                                )
                                                tk["is_done"] = new_done
                                                st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                                st.toast(f"✅ Đã cập nhật: {short_title}...")
                                                st.rerun()

                                            with st.popover("📄 Chi tiết", use_container_width=True):
                                                st.markdown(f"**{energy_badge}** | ⏰ **{slot}**")
                                                st.markdown(f"📌 **{t_detail}**")
                                                if tk.get("goal_title"):
                                                    st.caption(f"🎯 **Mục tiêu:** {tk.get('goal_title')}")
                                                if t_dod:
                                                    st.caption(f"🏁 **DoD:** {t_dod}")
                                                if t_link:
                                                    st.link_button("📦 Mở Tài Liệu", url=t_link, use_container_width=True)
                                                defer_grid_key = f"btn_def_pop_{grid_chk_key}"
                                                if st.button("⏭️ Dời sang mai", key=defer_grid_key, use_container_width=True):
                                                    save_undo_snapshot(current_username, ms)
                                                    ok_def, next_d = defer_master_schedule_task_to_tomorrow(t_detail, d_str, current_username)
                                                    if ok_def:
                                                        st.session_state[master_schedule_key] = load_master_schedule(current_username)
                                                        st.toast(f"⏭️ Đã dời task sang ngày mai ({next_d})!")
                                                        st.rerun()

                    # GÓC NHÌN 3: 📆 THEO THÁNG
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
                                            st.session_state[pending_view_key] = "📅 Theo Ngày"
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
                                                    push_undo_state(current_username)
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

                    # GÓC NHÌN 4: 📊 THEO QUÝ
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
                                Plague_col2 = p_col2
                                with Plague_col2:
                                    st.markdown(f"**Tiến độ giai đoạn:** `{phase['progress']}%`")
                                    st.progress(phase['progress'] / 100)
                                    if phase['progress'] >= 100:
                                        st.success("🎉 Giai đoạn hoàn tất!")
                                    elif phase['progress'] > 0:
                                        st.info("⚡ Đang tăng tốc")
                                    else:
                                        st.caption("⏳ Chưa bắt đầu")

                        st.markdown("---")
                        st.markdown("##### 📋 Checklist Nhiệm Vụ Trọng Tâm Toàn Quý (Tương Tác Real-time):")
                        for t_idx, tk in enumerate(filtered_schedule[:14]):
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
                                    push_undo_state(current_username)
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
            for msg in st.session_state.get(chat_sched_key, []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if sched_input := st.chat_input(
            "Báo bận (VD: 'chiều nay bận họp, dời task sang mai')...",
            key=f"input_sched_{current_username}",
        ):
            if chat_sched_key not in st.session_state:
                st.session_state[chat_sched_key] = []
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
