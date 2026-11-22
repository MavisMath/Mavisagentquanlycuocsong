"""
ui/components/tab_ceo.py - Tab 1: Tổng Hành Dinh Chiến Lược (CEO Coach).
"""

import streamlit as st
from ui.components.mascot_banner import render_mascot_banner
from ui.components.helpers import (
    safe_dict,
    safe_list,
    load_user_goals,
    save_user_goals,
    classify_goal_category,
    ceo_coach_chat,
    push_undo_state,
    load_master_schedule,
    save_master_schedule,
    generate_detailed_master_schedule,
    get_vietnam_today_str,
)


def render_tab_ceo(current_username: str, current_name: str):
    """Hiển thị Giao diện Tab 1: Tổng Hành Dinh Chiến Lược (CEO Coach)."""
    goals_key = f"goals_{current_username}"
    chat_ceo_key = f"chat_ceo_{current_username}"

    # Linh vật Mavis & Thanh tiến trình ngày phong cách Duolingo ở đầu màn hình chính
    render_mascot_banner(current_username, current_name)

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
                cat = eg_dict.get("category")
                if not cat or str(cat).strip().lower() in ["học tập", "sự nghiệp", "career"]:
                    c_grp = classify_goal_category(eg_dict) if classify_goal_category else "career"
                    if c_grp == "health_beauty":
                        cat = "Sức khỏe & Sắc vóc"
                    elif c_grp == "relationships":
                        cat = "Mối quan hệ"
                    else:
                        cat = cat or "Học tập"
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
                gid = ag_dict.get("id") or ag_dict.get("goal_id", f"act_{idx}")
                a_title = ag_dict.get("title") or ag_dict.get("goal_name", f"Mục tiêu {idx}")
                a_cat = ag_dict.get("category")
                if not a_cat or str(a_cat).strip().lower() in ["học tập", "sự nghiệp", "career"]:
                    c_grp = classify_goal_category(ag_dict) if classify_goal_category else "career"
                    if c_grp == "health_beauty":
                        a_cat = "Sức khỏe & Sắc vóc"
                    elif c_grp == "relationships":
                        a_cat = "Mối quan hệ"
                    else:
                        a_cat = a_cat or "Sự nghiệp"
                a_h = ag_dict.get("daily_hours", 1.5)
                a_prio = ag_dict.get("priority", "P2 - High")

                with st.container(border=True):
                    col_info, col_btn = st.columns([0.62, 0.38], vertical_alignment="center")
                    with col_info:
                        st.markdown(f"🚀 **{a_title}** `({a_cat})` — 🟢 *Active*")
                        st.caption(f"⏱️ `{a_h}h/ngày` | Mức ưu tiên: `{a_prio}`")
                    with col_btn:
                        if st.button("📅 Phân rã & Xếp lịch ngay", key=f"btn_sched_goal_{gid}_{idx}", use_container_width=True, help="Tự động gọi Scheduler phân rã mục tiêu này vào Master Schedule"):
                            push_undo_state(current_username)
                            cur_sched = load_master_schedule(current_username)
                            new_tasks = generate_detailed_master_schedule(
                                active_goals=[ag_dict],
                                start_date_str=get_vietnam_today_str(),
                                num_days=14,
                                username=current_username,
                            )
                            existing_sigs = set(
                                (t.get("date"), t.get("time_slot"), str(t.get("title") or t.get("task_name")).strip().lower())
                                for t in cur_sched if isinstance(t, dict)
                            )
                            added_tasks = [
                                nt for nt in new_tasks
                                if (nt.get("date"), nt.get("time_slot"), str(nt.get("title") or nt.get("task_name")).strip().lower()) not in existing_sigs
                            ]
                            updated_sched = cur_sched + added_tasks
                            save_master_schedule(updated_sched, username=current_username)
                            st.session_state[f"master_schedule_{current_username}"] = updated_sched

                            # Ghi nhận thông báo vào chat scheduler
                            sched_chat_key = f"chat_sched_{current_username}"
                            if sched_chat_key not in st.session_state:
                                st.session_state[sched_chat_key] = []
                            st.session_state[sched_chat_key].append({
                                "role": "assistant",
                                "content": f"📅 **Đã xếp lịch tự động:** Mục tiêu '**{a_title}**' đã được phân rã thành **{len(added_tasks)} nhiệm vụ** cụ thể trong 14 ngày tới trên Master Schedule! Mời bạn sang Tab **Giai đoạn 2** để xem thời khóa biểu!"
                            })

                            st.toast(f"✅ Đã phân rã và xếp lịch cho '{a_title}'!")
                            st.rerun()
        else:
            st.caption("Chưa có mục tiêu Active nào. Khi mục tiêu được thẩm định khả thi, hãy bấm '✅ Đồng ý' ở trên.")

    with col_chat:
        st.markdown("#### 💬 Trò Chuyện Cùng CEO Coach")
        st.caption("Đánh giá mục tiêu mới • Kiểm tra quỹ giờ • Quản trị nhịp sinh học")

        chat_container_ceo = st.container(height=520)
        with chat_container_ceo:
            for msg in st.session_state.get(chat_ceo_key, []):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if ceo_input := st.chat_input(
            "Nhập mục tiêu mới hoặc thảo luận cùng CEO Coach...",
            key=f"input_ceo_{current_username}",
        ):
            if chat_ceo_key not in st.session_state:
                st.session_state[chat_ceo_key] = []
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
