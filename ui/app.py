import os
import sys
from typing import List, Dict, Any

# Đảm bảo đường dẫn import tương thích khi chạy streamlit từ mọi thư mục
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from agents.graph import mavis_agent
from memory.goals import load_goals, CATEGORY_LABELS, load_historical_insights
from memory.auth import get_authenticator, register_user


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
        from memory.goals import load_categorized_goals as _m_load
        return _m_load(username=username)
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

            st.markdown(
                """
                <div class="metric-card" style="margin-top: 20px;">
                    <div style="font-weight: bold; color: #38bdf8; margin-bottom: 6px;">🔐 TÀI KHOẢN MẪU KHẢO SÁT HỆ THỐNG:</div>
                    <div style="font-size: 0.9em; margin-bottom: 4px;">👑 <b>Executive Admin:</b> <code>mavis</code> | Mật khẩu: <code>mavis123</code></div>
                    <div style="font-size: 0.9em;">👤 <b>SaaS User B:</b> <code>user_b</code> | Mật khẩu: <code>user123</code></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
current_username = st.session_state.get("username", "mavis").strip().lower()
current_name = st.session_state.get("name", current_username.capitalize())

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
    st.session_state[profile_key] = {
        "current_situation": "",
        "financial_status": "",
        "time_constraints": "",
        "is_onboarded": False,
    }

thread_ver_key = f"thread_ver_{current_username}"
if thread_ver_key not in st.session_state:
    st.session_state[thread_ver_key] = 1


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

    # Hồ sơ cá nhân đa khía cạnh (User Profile)
    user_prof = st.session_state[profile_key]
    if user_prof.get("is_onboarded"):
        with st.expander("👤 Hồ Sơ Chiến Lược Cá Nhân", expanded=False):
            st.markdown(f"**Tình trạng:** {user_prof.get('current_situation', 'N/A')}")
            st.markdown(f"**Thời gian:** {user_prof.get('time_constraints', 'N/A')}")
            st.markdown(f"**Tài chính:** {user_prof.get('financial_status', 'N/A')}")
    else:
        st.warning("⚠️ Chưa hoàn thành Onboarding! Hãy chat để hoàn thiện hồ sơ.")

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
    if st.button("🔄 Làm mới phiên trò chuyện (Reset)", use_container_width=True):
        st.session_state[thread_ver_key] = st.session_state.get(thread_ver_key, 1) + 1
        st.session_state[msg_key] = [
            {
                "role": "assistant",
                "content": OPENING_GREETING,
            }
        ]
        st.session_state[energy_key] = "high"
        st.session_state[emotion_key] = "neutral"
        st.session_state[intent_key] = "chat"
        st.session_state[plan_key] = []
        st.session_state[pending_goal_key] = None
        st.session_state[awaiting_confirmation_key] = False
        st.session_state[profile_key] = {
            "current_situation": "",
            "financial_status": "",
            "time_constraints": "",
            "is_onboarded": False,
        }
        st.rerun()


# ==========================================
# 5. MAIN PANEL: GIAO DIỆN CHAT RIÊNG BIỆT
# ==========================================
st.title("🤖 Mavis AI Executive & Life Coach")
st.markdown(
    f"**Không gian làm việc:** `{current_name}` (`@{current_username}`) | Tối ưu hóa nhịp sinh học • Phản biện chi phí cơ hội • Đa người dùng SaaS"
)

# Hiển thị các tin nhắn cũ trong lịch sử của riêng user này
for msg in st.session_state[msg_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Khung nhập tin nhắn
if user_input := st.chat_input("Nhập mục tiêu hoặc trao đổi cùng Coach (VD: 'Tôi muốn học Data Science trong 3 tháng', 'Thiết lập mục tiêu chạy bộ')..."):
    # 1. Thêm tin nhắn của User vào giao diện
    st.session_state[msg_key].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Chuẩn bị input cho LangGraph Agent với định danh username
    # QUY TẮC PHÒNG NGỪA NHÂN BẢN:
    # LangGraph State Reducer (add_messages) tự động nối tin nhắn mới vào phiên trò chuyện.
    # Chỉ truyền duy nhất tin nhắn mới [HumanMessage(content=user_input)], tuyệt đối KHÔNG truyền lại mảng cũ!
    input_state = {
        "messages": [HumanMessage(content=user_input)],
        "current_energy_level": st.session_state[energy_key],
        "detected_emotion": st.session_state[emotion_key],
        "intent": st.session_state[intent_key],
        "plan": st.session_state[plan_key],
        "user_profile": st.session_state[profile_key],
        "uploaded_context": st.session_state.get(rag_key),
        "username": current_username,
        "pending_goal": st.session_state.get(pending_goal_key),
        "awaiting_confirmation": st.session_state.get(awaiting_confirmation_key, False),
    }

    # 3. Kích hoạt Agent xử lý
    with st.chat_message("assistant"):
        with st.spinner(f"Executive Coach đang phân tích dữ liệu cho {current_name}..."):
            try:
                # Cấu hình thread_id cho MemorySaver phân tách phiên trò chuyện theo user & phiên làm việc
                current_ver = st.session_state.get(thread_ver_key, 1)
                config = {"configurable": {"thread_id": f"thread_{current_username}_{current_ver}"}}
                output_state = mavis_agent.invoke(input_state, config=config)

                # Dọn dẹp hiển thị UI: Chỉ lấy duy nhất nội dung của tin nhắn AIMessage cuối cùng được sinh ra
                last_reply = None
                for msg in reversed(output_state.get("messages", [])):
                    if isinstance(msg, AIMessage) or getattr(msg, "type", "") == "ai":
                        c = extract_text_from_content(getattr(msg, "content", msg))
                        if c and c.strip():
                            last_reply = c
                            break
                    elif isinstance(msg, dict) and msg.get("role") == "assistant":
                        c = extract_text_from_content(msg.get("content", ""))
                        if c and c.strip():
                            last_reply = c
                            break

                # Phòng vệ: Tuyệt đối không lấy nhầm tin nhắn của user hoặc nhại lại lời user
                if not last_reply or last_reply.strip() == user_input.strip():
                    from agents.brain import chat_node
                    chat_fallback = chat_node(input_state)
                    last_reply = extract_text_from_content(chat_fallback["messages"][-1].content)

                st.markdown(last_reply)

                # Lưu vào lịch sử hiển thị của user (duy nhất 1 tin nhắn trợ lý cho lượt này)
                st.session_state[msg_key].append(
                    {"role": "assistant", "content": last_reply}
                )

                # Cập nhật các trạng thái của Agent vào session_state của user
                if "user_profile" in output_state and output_state["user_profile"]:
                    st.session_state[profile_key] = output_state["user_profile"]

                if "current_energy_level" in output_state:
                    st.session_state[energy_key] = output_state["current_energy_level"]

                if "detected_emotion" in output_state and output_state["detected_emotion"]:
                    st.session_state[emotion_key] = output_state["detected_emotion"]

                if "intent" in output_state and output_state["intent"]:
                    st.session_state[intent_key] = output_state["intent"]

                if "plan" in output_state and output_state["plan"]:
                    st.session_state[plan_key] = output_state["plan"]

                if "uploaded_context" in output_state:
                    st.session_state[rag_key] = output_state["uploaded_context"]

                if "pending_goal" in output_state:
                    st.session_state[pending_goal_key] = output_state["pending_goal"]

                if "awaiting_confirmation" in output_state:
                    st.session_state[awaiting_confirmation_key] = output_state["awaiting_confirmation"]

                # Rerun để Sidebar đồng bộ ngay lập tức các chỉ số mới
                st.rerun()

            except Exception as e:
                error_msg = f"Đã xảy ra lỗi trong quá trình điều phối Agent: {str(e)}"
                st.error(error_msg)
                st.session_state[msg_key].append(
                    {"role": "assistant", "content": error_msg}
                )
