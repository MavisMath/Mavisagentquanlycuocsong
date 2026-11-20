import os
import yaml
from typing import Dict, Any, Optional
import streamlit_authenticator as stauth

from memory.mongodb import (
    is_mongodb_available,
    db_load_all_users,
    db_save_user,
    db_get_user,
    db_update_user_state,
)

AUTH_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_config.yaml")

DEFAULT_COOKIE = {
    "expiry_days": 30.0,
    "key": "mavis_secret_signature_key_2026",
    "name": "mavis_auth_cookie",
}


def load_auth_config() -> Dict[str, Any]:
    """
    Tải cấu hình người dùng từ MongoDB Atlas (collection 'users').
    Tự động fallback về file cục bộ auth_config.yaml khi chưa cấu hình MONGO_URI.
    """
    local_config = {}
    if os.path.exists(AUTH_CONFIG_PATH):
        try:
            with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
                local_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Cảnh báo đọc auth_config.yaml: {e}")

    if "credentials" not in local_config or not isinstance(local_config.get("credentials"), dict):
        local_config["credentials"] = {"usernames": {}}
    if "usernames" not in local_config["credentials"] or not isinstance(local_config["credentials"].get("usernames"), dict):
        local_config["credentials"]["usernames"] = {}
    if "cookie" not in local_config:
        local_config["cookie"] = DEFAULT_COOKIE

    # 1. Nếu MongoDB Atlas khả dụng: Ưu tiên tải tài khoản từ MongoDB Atlas
    if is_mongodb_available():
        try:
            db_users = db_load_all_users()
            if db_users:
                local_config["credentials"]["usernames"] = db_users
            else:
                # MongoDB đang hoàn toàn trống, sẵn sàng cho người dùng mới đăng ký tài khoản sạch
                local_config["credentials"]["usernames"] = {}
        except Exception as e:
            print(f"Lỗi khi đồng bộ users từ MongoDB: {e}")

    return local_config


def save_auth_config(config: Dict[str, Any]) -> bool:
    """Lưu cấu hình người dùng dự phòng vào auth_config.yaml."""
    try:
        with open(AUTH_CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu auth_config.yaml: {e}")
        return False


def get_authenticator() -> stauth.Authenticate:
    """Khởi tạo và trả về instance Authenticate đã liên kết với MongoDB Atlas / auth_config."""
    config = load_auth_config()
    credentials = config.get("credentials", {})
    cookie = config.get("cookie", DEFAULT_COOKIE)

    return stauth.Authenticate(
        credentials=credentials,
        cookie_name=cookie.get("name", "mavis_auth_cookie"),
        cookie_key=cookie.get("key", "mavis_secret_signature_key_2026"),
        cookie_expiry_days=float(cookie.get("expiry_days", 30.0)),
        auto_hash=False,
    )


def register_user(username: str, name: str, email: str, password: str) -> bool:
    """
    Đăng ký tài khoản người dùng mới:
    - Băm mật khẩu (hashed_password).
    - Lưu vào collection 'users' trên MongoDB Atlas (nếu có MONGO_URI).
    - Khởi tạo document trạng thái rỗng trong 'user_states'.
    - Đồng bộ dự phòng vào auth_config.yaml & goals_ledger.json.
    """
    username = username.strip().lower()
    if not username or not password:
        return False

    # 1. Kiểm tra trên MongoDB Atlas nếu có kết nối
    if is_mongodb_available():
        existing_db_user = db_get_user(username)
        if existing_db_user:
            return False  # Username đã tồn tại trên MongoDB

    # 2. Kiểm tra trên local config
    local_config = load_auth_config()
    usernames = local_config["credentials"].get("usernames", {})
    if username in usernames:
        return False  # Username đã tồn tại

    # Hash mật khẩu an toàn
    hashed_pw = stauth.Hasher.hash(password)
    user_data = {
        "email": email or "",
        "name": name or username.capitalize(),
        "password": hashed_pw,
    }

    # 3. Lưu vào collection 'users' trên MongoDB Atlas
    if is_mongodb_available():
        db_saved = db_save_user(
            username=username,
            name=user_data["name"],
            email=user_data["email"],
            hashed_password=hashed_pw,
        )
        if db_saved:
            # Khởi tạo bản ghi ban đầu trong collection 'user_states'
            db_update_user_state(
                username=username,
                state_update={
                    "profile": {},
                    "resources": [],
                    "roadmap": {},
                    "user_profile": {"is_onboarded": False, "coaching_stage": "interviewing"},
                },
            )

    # 4. Lưu đồng bộ vào auth_config.yaml cục bộ
    usernames[username] = user_data
    local_config["credentials"]["usernames"] = usernames
    save_auth_config(local_config)

    # Khởi tạo không gian dữ liệu sạch trong goals_ledger.json
    try:
        from memory.goals import init_user_tree
        init_user_tree(username)
    except Exception as e:
        print(f"Lỗi khi khởi tạo tree cho {username}: {e}")

    return True

