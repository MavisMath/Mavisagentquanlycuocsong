"""
ui/components/tab_architect.py - Tab 2: Giai đoạn 1: Bản Thiết Kế Tổng Thể (Architect & Google Calendar).
"""

import streamlit as st
from ui.components.helpers import (
    safe_dict,
    safe_list,
    load_user_goals,
    save_user_goals,
    load_master_schedule,
    update_user_goal_status,
    update_user_goal_details,
    delete_user_goal,
    detect_goal_domain,
    DOMAIN_TERMINOLOGY,
    is_calendar_connected,
    disconnect_calendar,
    get_google_client_config,
    get_default_redirect_uri,
    get_oauth_authorization_url,
    sync_schedule_to_google_calendar,
    fetch_busy_events,
    architect_chat,
)


def render_tab_architect(current_username: str, current_name: str):
    """Hiển thị Giai đoạn 1: Bản Thiết Kế Tổng Thể (Năm ➔ Quý ➔ Tháng ➔ Tuần)."""
    goals_key = f"goals_{current_username}"
    master_schedule_key = f"master_schedule_{current_username}"
    chat_arch_key = f"chat_arch_{current_username}"
    resources_key = f"resources_{current_username}"
    roadmap_key = f"roadmap_{current_username}"
    profile_key = f"profile_{current_username}"
    goal_profile_key = f"goal_profile_{current_username}"

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

    default_general_terms = DOMAIN_TERMINOLOGY.get("general", {}) if isinstance(DOMAIN_TERMINOLOGY, dict) else {}
    domain_terms = {
        "domain_name": default_general_terms.get("domain_name", "Phát triển Tổng thể"),
        "role_title": default_general_terms.get("role_title", "AI Strategy Architect"),
        "chat_title": default_general_terms.get("chat_title", "💬 Trò Chuyện Cùng Strategy Architect"),
        "chat_caption": default_general_terms.get("chat_caption", "Thảo luận phương pháp • Tinh chỉnh chiến lược • Chốt lộ trình 4 tầng khép kín"),
        "input_placeholder": default_general_terms.get("input_placeholder", "Thảo luận phương pháp, tinh chỉnh chiến lược hoặc gõ 'chốt phương pháp'..."),
        "finalize_btn": default_general_terms.get("finalize_btn", "🚀 Chốt phương pháp & Tự động phân rã 4 tầng"),
        "strategy_label": default_general_terms.get("strategy_label", "💡 Phương pháp chiến lược (Kim chỉ nam):"),
        "q_label": default_general_terms.get("q_label", "🏆 Giai đoạn chiến lược (Quý)"),
        "m_resources_label": default_general_terms.get("m_resources_label", "Tài liệu & Công cụ"),
        "curated_title": default_general_terms.get("curated_title", "📚 Kho Tài Liệu & Công Cụ Thẩm Định (Curated Resources):"),
        "curated_empty_caption": default_general_terms.get("curated_empty_caption", "*(Chưa có tài liệu)*"),
        "how_to_use_label": default_general_terms.get("how_to_use_label", "Hướng dẫn khai thác"),
        "hours_label": "Số giờ/ngày",
        "resource_label": "Tài liệu & Giáo trình",
    }
    selected_goal = None
    selected_goal_name = "Chưa có mục tiêu"
    bd = {}

    with col_dash_arch:
        user_goals = safe_list(st.session_state.get(goals_key) or load_user_goals(current_username))

        if not user_goals:
            st.info("💡 Chưa có mục tiêu nào trong hệ thống. Hãy trao đổi với CEO Coach tại Tab 1 để thẩm định và kích hoạt mục tiêu đầu tiên!")
        else:
            selected_goal_id_key = f"selected_goal_id_{current_username}"
            all_gids = [str(g.get("id")) for g in user_goals if g.get("id")]
            if selected_goal_id_key not in st.session_state or st.session_state[selected_goal_id_key] not in all_gids:
                st.session_state[selected_goal_id_key] = all_gids[0] if all_gids else (user_goals[0].get("id") or "g0")

            current_sel_id = str(st.session_state[selected_goal_id_key])

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

                if g_status == "active":
                    status_badge = "🟢 :green[**Đang chạy**]"
                elif g_status == "paused":
                    status_badge = "⏸️ :orange[**Tạm dừng**]"
                elif g_status == "completed":
                    status_badge = "✅ :blue[**Hoàn thành**]"
                else:
                    status_badge = "🔍 :violet[**Đang thẩm định**]"

                prio_lower = g_prio.lower()
                if "cao" in prio_lower or "p1" in prio_lower:
                    prio_badge = "🔥 :red[Cao (P1)]"
                elif "trung" in prio_lower or "p2" in prio_lower:
                    prio_badge = "⚡ :orange[Trung bình (P2)]"
                else:
                    prio_badge = "🌿 :gray[Thấp (P3)]"

                with st.container(border=True):
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

                    col_b1, col_b2, col_b3 = st.columns([0.34, 0.36, 0.30])

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

            selected_goal = next(
                (g for g in user_goals if str(g.get("id")) == current_sel_id),
                user_goals[0],
            )
            selected_goal_name = selected_goal.get("title") or selected_goal.get("goal_name", "Mục tiêu")
            bd = safe_dict(selected_goal.get("breakdown"))

            target_domain = detect_goal_domain(selected_goal, selected_goal_name, selected_goal.get("category", ""))
            domain_terms = DOMAIN_TERMINOLOGY.get(target_domain, DOMAIN_TERMINOLOGY.get("general", {}))

            arch_active_goal_key = f"arch_active_gid_{current_username}"
            prev_active_gid = st.session_state.get(arch_active_goal_key)
            if prev_active_gid != current_sel_id:
                st.session_state[arch_active_goal_key] = current_sel_id
                if len(st.session_state.get(chat_arch_key, [])) <= 1:
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

            # Tầng 2: Quý
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
            for msg in st.session_state.get(chat_arch_key, []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

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
                        chat_history=st.session_state.get(chat_arch_key, []),
                        force_breakdown=True,
                    )
                    arch_rep = res.get("response", "Đã chốt phương pháp và phân rã lộ trình 4 tầng thành công!")
                else:
                    arch_rep = "Hệ thống đang đồng bộ kết nối AI. Vui lòng thử lại sau giây lát."
                if chat_arch_key not in st.session_state:
                    st.session_state[chat_arch_key] = []
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
            if chat_arch_key not in st.session_state:
                st.session_state[chat_arch_key] = []
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
