"""
ui/components/tab_adaptive_memory.py - Dedicated Tab / Component for Adaptive Memory & Behavioral Insights.
Dịch toàn bộ thông số kỹ thuật nội bộ sang tiếng Việt tự nhiên:
- failed_methods -> Phương pháp chưa phù hợp / Cần tránh lặp lại
- effective_methods -> Phương pháp hiệu quả cao / Đã kiểm chứng
- productivity_patterns -> Quy luật năng suất & Nhịp sinh học cá nhân
"""

import streamlit as st
from ui.components.helpers import (
    load_historical_insights,
    save_historical_insights,
    append_insight,
)


def render_tab_adaptive_memory(current_username: str, current_name: str, key_suffix: str = ""):
    """
    Hiển thị giao diện Bộ Nhớ Thích Nghi (Adaptive Memory) chuyên nghiệp,
    100% tiếng Việt tự nhiên, trực quan theo phong cách Duolingo.
    """
    st.markdown("### 🧠 Bộ Nhớ Thích Nghi & Hồ Sơ Hành Vi Trọn Đời")
    st.caption(
        "Mavis AI Executive Coach tự động quan sát, đúc kết kinh nghiệm qua các chu kỳ làm việc thực tế và các phiên hồi cứu "
        "để liên tục tối ưu hóa chiến lược, bảo vệ nhịp sinh học và cá nhân hóa lộ trình riêng biệt cho bạn."
    )

    insights = load_historical_insights(username=current_username)
    failed = list(insights.get("failed_methods", []))
    effective = list(insights.get("effective_methods", []))
    patterns = list(insights.get("productivity_patterns", []))

    # Metric tóm tắt 3D
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("🛑 Cần tránh lặp lại", f"{len(failed)} bài học")
    with m_col2:
        st.metric("⭐ Hiệu quả cao", f"{len(effective)} phương pháp")
    with m_col3:
        st.metric("⏰ Quy luật năng suất", f"{len(patterns)} quy luật")

    st.markdown("---")

    col1, col2, col3 = st.columns(3, gap="medium")

    # 1. Phương pháp chưa phù hợp / Cần tránh lặp lại (thay thế failed_methods)
    with col1:
        st.markdown("#### 🛑 Phương Pháp Cần Tránh")
        st.caption(
            "Các chiến lược, giáo trình hoặc cách làm việc trước đây không mang lại hiệu quả hoặc gây quá tải/bỏ cuộc. "
            "AI sẽ **tuyệt đối không đề xuất lại** các phương pháp này."
        )
        with st.container(border=True):
            if failed:
                for idx, item in enumerate(failed):
                    c_txt, c_del = st.columns([0.84, 0.16])
                    with c_txt:
                        st.markdown(f"• <span style='color:#e11d48; font-weight:500;'>{item}</span>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️", key=f"del_failed_{idx}_{current_username}{key_suffix}", help="Xóa bài học này"):
                            failed.pop(idx)
                            insights["failed_methods"] = failed
                            save_historical_insights(insights, username=current_username)
                            st.toast("Đã xóa bài học cần tránh!", icon="🗑️")
                            st.rerun()
            else:
                st.info("Chưa có ghi nhận phương pháp cần tránh nào. Hệ thống đang đồng hành và quan sát tích cực.")

    # 2. Phương pháp hiệu quả cao / Đã kiểm chứng (thay thế effective_methods)
    with col2:
        st.markdown("#### ⭐ Phương Pháp Hiệu Quả Cao")
        st.caption(
            "Các kỹ thuật, thói quen và công cụ giúp bạn tập trung sâu (Deep Work), duy trì kỷ luật thép và hoàn thành xuất sắc mục tiêu."
        )
        with st.container(border=True):
            if effective:
                for idx, item in enumerate(effective):
                    c_txt, c_del = st.columns([0.84, 0.16])
                    with c_txt:
                        st.markdown(f"• <span style='color:#16a34a; font-weight:500;'>{item}</span>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️", key=f"del_eff_{idx}_{current_username}{key_suffix}", help="Xóa phương pháp này"):
                            effective.pop(idx)
                            insights["effective_methods"] = effective
                            save_historical_insights(insights, username=current_username)
                            st.toast("Đã xóa phương pháp hiệu quả!", icon="🗑️")
                            st.rerun()
            else:
                st.info("Chưa có ghi nhận phương pháp hiệu quả. Hệ thống sẽ tự động đúc kết sau các chu kỳ hoàn thành.")

    # 3. Quy luật năng suất & Nhịp sinh học cá nhân (thay thế productivity_patterns)
    with col3:
        st.markdown("#### ⏰ Quy Luật Năng Suất")
        st.caption(
            "Những khung giờ vàng, thói quen sinh hoạt và chu kỳ năng lượng tự nhiên tối ưu được nhận diện từ dữ liệu thực tế của bạn."
        )
        with st.container(border=True):
            if patterns:
                for idx, item in enumerate(patterns):
                    c_txt, c_del = st.columns([0.84, 0.16])
                    with c_txt:
                        st.markdown(f"• <span style='color:#0284c7; font-weight:500;'>{item}</span>", unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️", key=f"del_patt_{idx}_{current_username}{key_suffix}", help="Xóa quy luật này"):
                            patterns.pop(idx)
                            insights["productivity_patterns"] = patterns
                            save_historical_insights(insights, username=current_username)
                            st.toast("Đã xóa quy luật năng suất!", icon="🗑️")
                            st.rerun()
            else:
                st.info("Đang phân tích nhịp sinh học và các khung giờ năng suất hàng ngày của bạn.")

    st.markdown("---")

    # Mục thêm ghi nhận kinh nghiệm chủ động
    with st.expander("➕ Đóng Góp Thêm Kinh Nghiệm / Quy Luật Cá Nhân", expanded=False):
        st.caption("Bạn có thể chủ động huấn luyện thêm cho AI về những kinh nghiệm, sở thích hoặc thói quen cá nhân:")
        with st.form(key=f"form_add_insight_{current_username}{key_suffix}"):
            cat_choice = st.selectbox(
                "Chọn nhóm kinh nghiệm:",
                [
                    "⭐ Phương pháp hiệu quả cao / Đã kiểm chứng",
                    "🛑 Phương pháp chưa phù hợp / Cần tránh lặp lại",
                    "⏰ Quy luật năng suất & Nhịp sinh học cá nhân",
                ],
                key=f"sel_insight_cat_{current_username}{key_suffix}",
            )
            content_input = st.text_input(
                "Nội dung bài học hoặc quy luật:",
                placeholder="VD: Không học bài khó sau 21:00; Ôn từ vựng lúc 06:30 sáng nhớ lâu nhất; Chạy bộ chiều giúp giải tỏa stress...",
                key=f"txt_insight_content_{current_username}{key_suffix}",
            )
            submit_btn = st.form_submit_button("💾 Lưu Vào Bộ Nhớ Thích Nghi", type="primary")

            if submit_btn:
                if not content_input or not content_input.strip():
                    st.warning("Vui lòng nhập nội dung bài học trước khi lưu.")
                else:
                    if "tránh" in cat_choice:
                        itype = "failed_methods"
                    elif "hiệu quả" in cat_choice:
                        itype = "effective_methods"
                    else:
                        itype = "productivity_patterns"

                    fn_append = append_insight
                    if fn_append:
                        success = fn_append(itype, content_input.strip(), username=current_username)
                    else:
                        current_list = list(insights.get(itype, []))
                        if content_input.strip() not in current_list:
                            current_list.append(content_input.strip())
                            insights[itype] = current_list
                            success = save_historical_insights(insights, username=current_username)
                        else:
                            success = False

                    if success:
                        st.toast("✅ Đã lưu kinh nghiệm vào Bộ Nhớ Thích Nghi thành công!", icon="🧠")
                        st.rerun()
                    else:
                        st.info("Kinh nghiệm này đã có trong hệ thống hoặc không thể lưu.")
