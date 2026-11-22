"""
ui/components/sidebar.py - Sidebar Control Center (Profile, Goals, Bio-energy, Adaptive Memory).
"""

from typing import Any
import streamlit as st
from ui.components.helpers import (
    safe_dict,
    safe_list,
    load_user_goals,
    load_user_resources,
    load_historical_insights,
    load_categorized_goals,
    load_master_schedule,
    load_retrospective_logs,
    is_mongodb_available,
    get_mongo_connection_error,
    get_mongo_uri,
    OPENING_GREETING,
)


def render_sidebar(current_username: str, current_name: str, authenticator: Any = None):
    """Hiển thị toàn bộ bảng điều khiển bên trái (Sidebar Control Center)."""
    goals_key = f"goals_{current_username}"
    resources_key = f"resources_{current_username}"
    energy_key = f"energy_{current_username}"
    emotion_key = f"emotion_{current_username}"
    intent_key = f"intent_{current_username}"
    plan_key = f"plan_{current_username}"
    rag_key = f"rag_{current_username}"
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

        if authenticator is not None:
            try:
                authenticator.logout(button_name="🚪 Đăng Xuất (Logout)", location="sidebar", key="sidebar_logout_btn")
            except Exception:
                if st.sidebar.button("🚪 Đăng Xuất (Fallback)", key="fallback_logout"):
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
        energy = st.session_state.get(energy_key, "high")

        if energy == "high":
            st.success("🟢 **NĂNG LƯỢNG ĐỈNH CAO (HIGH)**")
            if active_goals_sidebar:
                focus_titles = [f"**{g.get('title') or g.get('goal_name')}**" for g in active_goals_sidebar[:2] if (g.get('title') or g.get('goal_name'))]
                priority_text = f"Tập trung Deep Work bứt phá: {', '.join(focus_titles)}"
            else:
                priority_text = "Tối ưu hóa các tác vụ nhận thức cao, tư duy chiến lược và quyết định quan trọng"
            st.markdown(
                f"""
                * **Khung giờ vàng:** 08:00 - 10:00 Sáng
                * **Trạng thái:** Tối ưu tải nhận thức cao & năng lượng đỉnh
                * **Ưu tiên:** {priority_text}
                """
            )
        else:
            st.warning("🟠 **NĂNG LƯỢNG GIẢM / HẠ TẢI (LOW)**")
            st.markdown(
                """
                * **Khung giờ:** Buổi chiều (sau 14:00) hoặc phát hiện quá tải
                * **Trạng thái:** Cần nghỉ ngơi hoặc tác vụ nhẹ
                * **Hành động:** Pomodoro 15 phút, rà soát tài liệu, tái tạo năng lượng
                """
            )

        # Hiển thị cảm xúc và ý định nhận diện
        detected_emo = st.session_state.get(emotion_key, "neutral")
        detected_intent = st.session_state.get(intent_key, "chat")
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:0.85em; color:#94a3b8;">CẢM XÚC NHẬN DIỆN</div>
                <div style="font-size:1.1em; font-weight:bold; margin-top:4px;">{str(detected_emo).upper()}</div>
                <div style="font-size:0.85em; color:#94a3b8; margin-top:8px;">Ý ĐỊNH XỬ LÝ (INTENT)</div>
                <div style="font-size:1.0em; font-weight:600; color:#38bdf8;">{str(detected_intent).upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Lịch trình dự kiến (Scheduled Plan)
        st.subheader("📅 Lịch trình dự kiến")
        current_plan = st.session_state.get(plan_key, [])
        if not current_plan:
            if active_goals_sidebar:
                first_g_title = active_goals_sidebar[0].get("title") or active_goals_sidebar[0].get("goal_name") or "mục tiêu"
                st.info(f"Chưa có task nào được lập cho **{first_g_title}**. Hãy bấm nút **'📅 Phân rã & Xếp lịch ngay'** ở Tổng Hành Dinh để Coach tự động lên lịch vào giờ vàng!")
            else:
                st.info("Chưa có task nào được lập. Hãy kích hoạt mục tiêu ở Giai đoạn 1 hoặc chat cùng CEO Coach để tự động phân rã lịch trình!")
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

        # Đồng bộ danh sách Active Goals với cây mục tiêu ở Sidebar
        active_goals_all = [g for g in user_goals_sidebar if g.get("status") in ["active", "in_progress"]]

        # Nhóm 1: Sự Nghiệp
        career_goals = categorized_goals.get("career", [])
        if isinstance(career_goals, dict):
            career_goals = career_goals.get("children", [])
        career_goals = list(career_goals)

        # Nhóm 2: Mối Quan Hệ
        rel_goals = categorized_goals.get("relationships", [])
        if isinstance(rel_goals, dict):
            rel_goals = rel_goals.get("children", [])
        rel_goals = list(rel_goals)

        # Nhóm 3: Sức Khỏe & Sắc Vóc (Gộp health + beauty)
        health_goals = categorized_goals.get("health", [])
        if isinstance(health_goals, dict):
            health_goals = health_goals.get("children", [])
        beauty_goals = categorized_goals.get("beauty", [])
        if isinstance(beauty_goals, dict):
            beauty_goals = beauty_goals.get("children", [])
        health_beauty_goals = list(health_goals) + list(beauty_goals)

        # Tự động đồng bộ các mục tiêu Active từ user_goals_sidebar nếu chưa có trong cây
        for ag in active_goals_all:
            ag_cat = str(ag.get("category", "")).lower()
            ag_title = str(ag.get("title") or ag.get("goal_name", "")).strip().lower()
            if any(str(g.get("title") or g.get("goal_name", "")).strip().lower() == ag_title for g in (career_goals + rel_goals + health_beauty_goals)):
                continue
            if any(k in ag_cat for k in ["sự nghiệp", "career", "học tập", "công việc"]):
                career_goals.append(ag)
            elif any(k in ag_cat for k in ["mối quan hệ", "relationship", "gia đình", "bạn bè"]):
                rel_goals.append(ag)
            else:
                health_beauty_goals.append(ag)

        tab_data = [
            ("💼 Sự Nghiệp", career_goals),
            ("🤝 Mối Quan Hệ", rel_goals),
            ("🧘 Sức Khỏe & Sắc Vóc", health_beauty_goals),
        ]

        tabs = st.tabs(["💼 Sự Nghiệp", "🤝 Mối Quan Hệ", "🧘 Sức Khỏe & Sắc Vóc"])

        for tab, (t_name, goals_in_cat) in zip(tabs, tab_data):
            with tab:
                if not goals_in_cat:
                    st.caption("Chưa có mục tiêu trong Nhóm mục tiêu này.")
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
