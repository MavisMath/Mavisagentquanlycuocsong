"""
ui/components/auth.py - Authentication wall (Login & Registration forms).
"""

from typing import Any
import streamlit as st
from ui.components.helpers import (
    get_mongo_uri,
    is_mongodb_available,
    get_mongo_connection_error,
    register_user,
)


def render_auth_screen(authenticator: Any = None):
    """Hiển thị giao diện Đăng Nhập / Đăng Ký khi người dùng chưa xác thực và dừng luồng ứng dụng."""
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

        if get_mongo_uri() and not is_mongodb_available():
            mongo_err = get_mongo_connection_error()
            if mongo_err and "Chưa cấu hình" not in mongo_err:
                st.error(f"Lỗi kết nối MongoDB: {mongo_err}")

        tab_login, tab_register = st.tabs(["🔑 Đăng Nhập", "📝 Đăng Ký Tài Khoản"])

        with tab_login:
            if authenticator is not None:
                try:
                    authenticator.login(location="main", key="login_widget")
                except Exception as e:
                    st.error(f"Lỗi xác thực: {e}")
            else:
                st.error("Không tìm thấy cấu hình xác thực Authenticator.")

            if st.session_state.get("authentication_status") is False:
                st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng thử lại!")
            elif st.session_state.get("authentication_status") is None:
                st.info("💡 Vui lòng nhập thông tin để đăng nhập vào không gian làm việc của bạn.")

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
                        if register_user is not None:
                            success = register_user(
                                username=new_user,
                                name=new_name,
                                email=new_email,
                                password=new_pass,
                            )
                            if success:
                                st.success(
                                    f"🎉 Chúc mừng! Tài khoản **{new_user}** đã được khởi tạo thành công. "
                                    "Bạn có thể chuyển sang tab **Đăng Nhập** ngay bây giờ!"
                                )
                            else:
                                st.error(f"❌ Tên đăng nhập '{new_user}' đã tồn tại trong hệ thống. Vui lòng chọn tên khác!")
                        else:
                            st.error("Chức năng đăng ký tạm thời không khả dụng.")

    # Chặn hoàn toàn không hiển thị Sidebar hay Main App khi chưa đăng nhập thành công
    st.stop()
