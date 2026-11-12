import os
import yaml
from typing import Dict, Any, Optional
import streamlit_authenticator as stauth

AUTH_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_config.yaml")

DEFAULT_COOKIE = {
    "expiry_days": 30.0,
    "key": "mavis_secret_signature_key_2026",
    "name": "mavis_auth_cookie",
}


def load_auth_config() -> Dict[str, Any]:
    """Tải cấu hình người dùng từ auth_config.yaml."""
    if not os.path.exists(AUTH_CONFIG_PATH):
        # Tạo cấu hình mặc định với mavis và user_b
        mavis_hash = stauth.Hasher.hash("mavis123")
        user_b_hash = stauth.Hasher.hash("user123")
        default_config = {
            "credentials": {
                "usernames": {
                    "mavis": {
                        "email": "mavis@executive.ai",
                        "name": "Mavis Executive",
                        "password": mavis_hash,
                    },
                    "user_b": {
                        "email": "user_b@saas.com",
                        "name": "User B",
                        "password": user_b_hash,
                    },
                }
            },
            "cookie": DEFAULT_COOKIE,
        }
        save_auth_config(default_config)
        return default_config

    with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if "credentials" not in config:
        config["credentials"] = {"usernames": {}}
    if "cookie" not in config:
        config["cookie"] = DEFAULT_COOKIE

    return config


def save_auth_config(config: Dict[str, Any]) -> bool:
    """Lưu cấu hình người dùng vào auth_config.yaml."""
    try:
        with open(AUTH_CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu auth_config.yaml: {e}")
        return False


def get_authenticator() -> stauth.Authenticate:
    """Khởi tạo và trả về instance Authenticate đã liên kết với auth_config.yaml."""
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
    """Đăng ký tài khoản người dùng mới và khởi tạo không gian dữ liệu độc lập."""
    username = username.strip().lower()
    if not username or not password:
        return False

    config = load_auth_config()
    usernames = config["credentials"].get("usernames", {})

    if username in usernames:
        return False  # Username đã tồn tại

    hashed_pw = stauth.Hasher.hash(password)
    usernames[username] = {
        "email": email,
        "name": name or username.capitalize(),
        "password": hashed_pw,
    }
    config["credentials"]["usernames"] = usernames
    save_auth_config(config)

    # Khởi tạo không gian dữ liệu sạch trong goals_ledger.json
    try:
        from memory.goals import init_user_tree
        init_user_tree(username)
    except Exception as e:
        print(f"Lỗi khi khởi tạo tree cho {username}: {e}")

    return True

