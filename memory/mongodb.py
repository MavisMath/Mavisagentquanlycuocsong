import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    from pymongo.database import Database
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None  # type: ignore
    Collection = None   # type: ignore
    Database = None     # type: ignore
    PYMONGO_AVAILABLE = False

DB_NAME = "mavis_coach_db"

_mongo_client: Optional[Any] = None
_mongo_db: Optional[Any] = None


def get_mongo_uri() -> Optional[str]:
    """
    Trích xuất MONGO_URI từ st.secrets['MONGO_URI'] hoặc biến môi trường os.getenv('MONGO_URI').
    Hỗ trợ cả trường hợp secrets dạng nested hoặc string.
    """
    # 1. Thử lấy từ streamlit.secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "MONGO_URI" in st.secrets and isinstance(st.secrets["MONGO_URI"], str):
                return st.secrets["MONGO_URI"].strip()
            # Kiểm tra trường hợp đặt trong mục [mongo] uri = "..."
            if "mongo" in st.secrets and isinstance(st.secrets["mongo"], dict):
                uri = st.secrets["mongo"].get("uri") or st.secrets["mongo"].get("MONGO_URI")
                if uri and isinstance(uri, str):
                    return uri.strip()
    except Exception:
        pass

    # 2. Thử lấy từ biến môi trường hệ thống
    env_uri = os.getenv("MONGO_URI")
    if env_uri and env_uri.strip():
        return env_uri.strip()

    return None


def get_mongo_db() -> Optional[Any]:
    """
    Khởi tạo hoặc trả về instance Database mavis_coach_db kết nối đến MongoDB Atlas.
    Sử dụng connection pooling và timeout kiểm soát để tránh treo luồng ứng dụng.
    """
    global _mongo_client, _mongo_db

    if not PYMONGO_AVAILABLE:
        return None

    if _mongo_db is not None:
        return _mongo_db

    uri = get_mongo_uri()
    if not uri:
        return None

    try:
        _mongo_client = MongoClient(
            uri,
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000,
            retryWrites=True,
        )
        # Kiểm tra nhanh kết nối bằng lệnh ping
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[DB_NAME]
        return _mongo_db
    except Exception as e:
        print(f"⚠️ Cảnh báo kết nối MongoDB Atlas ({DB_NAME}): {e}")
        _mongo_client = None
        _mongo_db = None
        return None


def is_mongodb_available() -> bool:
    """Kiểm tra xem MongoDB Atlas đã sẵn sàng hoạt động hay chưa."""
    db = get_mongo_db()
    return db is not None


# ==============================================================================
# COLLECTION: users (QUẢN LÝ TÀI KHOẢN SAAS & HASH MẬT KHẨU)
# ==============================================================================

def db_save_user(username: str, name: str, email: str, hashed_password: str) -> bool:
    """
    Lưu hoặc cập nhật tài khoản người dùng vào collection 'users' (MongoDB Atlas).
    Bảo đảm mật khẩu đã được hash an toàn trước khi lưu.
    """
    db = get_mongo_db()
    if db is None:
        return False

    username = username.strip().lower()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        db.users.update_one(
            {"username": username},
            {
                "$set": {
                    "username": username,
                    "name": name or username.capitalize(),
                    "email": email or "",
                    "password": hashed_password,
                    "updated_at": now_iso,
                },
                "$setOnInsert": {
                    "created_at": now_iso,
                },
            },
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"Lỗi khi lưu user '{username}' vào MongoDB: {e}")
        return False


def db_get_user(username: str) -> Optional[Dict[str, Any]]:
    """Truy vấn thông tin tài khoản người dùng từ collection 'users'."""
    db = get_mongo_db()
    if db is None:
        return None

    username = username.strip().lower()
    try:
        doc = db.users.find_one({"username": username}, {"_id": 0})
        return doc
    except Exception as e:
        print(f"Lỗi khi tìm user '{username}' trong MongoDB: {e}")
        return None


def db_load_all_users() -> Dict[str, Dict[str, Any]]:
    """
    Tải toàn bộ danh sách người dùng từ collection 'users' để cung cấp cho streamlit-authenticator.
    Cấu trúc trả về khớp với stauth:
    {
        username: {
            "name": "...",
            "email": "...",
            "password": "<hash>"
        }
    }
    """
    db = get_mongo_db()
    if db is None:
        return {}

    users_dict = {}
    try:
        cursor = db.users.find({}, {"_id": 0, "username": 1, "name": 1, "email": 1, "password": 1})
        for doc in cursor:
            uname = doc.get("username")
            if uname:
                users_dict[uname] = {
                    "name": doc.get("name", uname.capitalize()),
                    "email": doc.get("email", ""),
                    "password": doc.get("password", ""),
                }
    except Exception as e:
        print(f"Lỗi khi tải toàn bộ users từ MongoDB: {e}")

    return users_dict


def seed_default_users_if_needed(default_credentials: Dict[str, Any]) -> None:
    """Khởi tạo tài khoản mẫu (mavis, user_b) lên MongoDB nếu collection users đang trống."""
    db = get_mongo_db()
    if db is None:
        return

    try:
        count = db.users.count_documents({})
        if count == 0 and default_credentials:
            for uname, info in default_credentials.items():
                db_save_user(
                    username=uname,
                    name=info.get("name", uname.capitalize()),
                    email=info.get("email", f"{uname}@executive.ai"),
                    hashed_password=info.get("password", ""),
                )
    except Exception as e:
        print(f"Lỗi khi seed tài khoản mặc định vào MongoDB: {e}")


# ==============================================================================
# COLLECTION: user_states (LƯU TRỮ BỀN VỮNG profile, resources, roadmap)
# ==============================================================================

def db_update_user_state(username: str, state_update: Dict[str, Any]) -> bool:
    """
    Tự động update_one(..., upsert=True) vào collection 'user_states' theo username.
    Đảm bảo khi user chốt profile hoặc sinh roadmap, dữ liệu được ghi bền vững lên Cloud ngay lập tức.
    """
    db = get_mongo_db()
    if db is None:
        return False

    username = username.strip().lower()
    if not username:
        return False

    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_update = {k: v for k, v in state_update.items() if k != "_id"}
        clean_update["username"] = username
        clean_update["updated_at"] = now_iso

        db.user_states.update_one(
            {"username": username},
            {"$set": clean_update},
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"Lỗi khi cập nhật user_state cho '{username}' vào MongoDB: {e}")
        return False


def db_get_user_state(username: str) -> Dict[str, Any]:
    """Tải toàn bộ trạng thái của user (profile, resources, roadmap) từ collection 'user_states'."""
    db = get_mongo_db()
    if db is None:
        return {}

    username = username.strip().lower()
    try:
        doc = db.user_states.find_one({"username": username}, {"_id": 0})
        return doc if isinstance(doc, dict) else {}
    except Exception as e:
        print(f"Lỗi khi tải user_state của '{username}' từ MongoDB: {e}")
        return {}
