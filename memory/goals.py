# Mavis Executive Memory System - Build 2026.11.21-v2
import os
import json
import uuid
import re
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from memory.mongodb import (
    is_mongodb_available,
    db_update_user_state,
    db_get_user_state,
)

__all__ = [
    "load_goals",
    "save_goals",
    "add_goal",
    "update_goal",
    "CATEGORY_LABELS",
    "load_historical_insights",
    "save_historical_insights",
    "load_user_profile",
    "save_user_profile",
    "load_user_goal_profile",
    "save_user_goal_profile",
    "load_user_goals",
    "save_user_goals",
    "load_user_resources",
    "save_user_resources",
    "load_user_roadmap",
    "save_user_roadmap",
    "load_categorized_goals",
    "save_categorized_goals",
    "load_master_schedule",
    "save_master_schedule",
    "update_master_schedule_task_status",
    "defer_master_schedule_task_to_tomorrow",
    "load_retrospective_logs",
    "save_retrospective_logs",
    "append_retrospective_log",
    "get_user_state_full",
    "update_user_goal_status",
    "update_user_goal_details",
    "delete_user_goal",
    "calculate_user_streak",
    "append_resource_to_goal",
    "get_goals_summary_text",
    "get_active_tasks_and_milestones",
    "detect_and_resolve_priority_conflicts",
    "check_and_trigger_unpause",
    "apply_backcasting_master_ai",
    "append_opportunity_and_networking_tasks",
    "load_tree_goals",
    "save_tree_goals",
    "append_insight",
    "get_historical_insights_summary_text",
    "init_user_tree",
    "detect_goal_domain",
    "DOMAIN_TERMINOLOGY",
    "VIETNAM_WEEKDAYS",
    "get_vietnam_now",
    "get_vietnam_today",
    "get_vietnam_today_str",
    "compute_target_date",
    "generate_detailed_master_schedule",
    "ensure_schedule_covers_date",
]

LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goals_ledger.json")

# 4 Root Nodes chuẩn hóa theo yêu cầu Phase 7.1
ROOT_NODES = [
    "career",
    "relationships",
    "health",
    "beauty",
]

ROOT_LABELS = {
    "career": "💼 Sự nghiệp & Học tập (Career)",
    "relationships": "🤝 Mối quan hệ (Relationships)",
    "health": "🧘 Sức khỏe & Thể chất (Health)",
    "beauty": "✨ Sắc vóc & Làm đẹp (Beauty)",
}

ROOT_DESCRIPTIONS = {
    "career": "Học tập, Công việc, Quan hệ đối tác & Sự nghiệp",
    "relationships": "Gia đình, Bạn bè, Tình yêu & Mạng lưới kết nối",
    "health": "Thể chất, Tinh thần, Dinh dưỡng & Nhịp sinh học",
    "beauty": "Vóc dáng, Làm đẹp, Skincare & Phong thái Executive",
}

# Ánh xạ tương thích ngược từ các phân loại cũ sang 4 Root Nodes
CATEGORY_TO_ROOT = {
    "career": "career",
    "study_work": "career",
    "finance": "career",
    "relationships": "relationships",
    "family": "relationships",
    "health": "health",
    "daily_routine": "health",
    "health_beauty": "health",
    "beauty": "beauty",
}

DEFAULT_CATEGORIES = ROOT_NODES
CATEGORY_LABELS = ROOT_LABELS
DEFAULT_USER = "mavis"

# ==============================================================================
# HỆ THỐNG PHÂN LOẠI LĨNH VỰC & TỪ ĐIỂN THUẬT NGỮ CHUYÊN BIỆT (DOMAIN-AWARE PERSONA)
# ==============================================================================

DOMAIN_TERMINOLOGY = {
    "health": {
        "domain_name": "Sức khỏe & Thể chất",
        "role_title": "Chuyên Gia Thể Lực & Dinh Dưỡng Cấp Cao (Senior Fitness & Nutrition Architect)",
        "chat_title": "💬 Trò Chuyện Cùng Chuyên Gia Thể Lực & Dinh Dưỡng",
        "chat_caption": "Tư vấn chế độ dinh dưỡng • Giáo án tập luyện khoa học • Chốt lộ trình thể chất 4 tầng",
        "input_placeholder": "Thảo luận thực đơn, lịch tập luyện, thâm hụt calo hoặc gõ 'chốt phương pháp'...",
        "finalize_btn": "🚀 Chốt phương pháp & Xuất bản lộ trình rèn luyện 4 tầng",
        "strategy_label": "🥗 Nguyên tắc Dinh dưỡng & Tập luyện cốt lõi (Kim chỉ nam):",
        "q_label": "🏆 Giai đoạn rèn luyện (Quý)",
        "m_resources_label": "Chế độ dinh dưỡng & giáo án",
        "curated_title": "🥗 Thực Đơn Dinh Dưỡng & Giáo Án Rèn Luyện Thẩm Định (Curated Resources):",
        "curated_empty_caption": "*(Chưa có tài liệu. Hãy chat với Chuyên Gia Thể Lực & Dinh Dưỡng để lên thực đơn calo và giáo án bài tập chuẩn)*",
        "how_to_use_label": "Chỉ dẫn áp dụng",
        "energy_deep": "🔴 Bài tập trọng tâm / Kháng lực (High Intensity)",
        "energy_shallow": "🟡 Vận động nhẹ / Cardio Zone 2 / Chuẩn bị bữa ăn (Low Impact / Meal Prep)",
        "energy_recharge": "🟢 Giãn cơ / Phục hồi / Giấc ngủ (Recovery / Sleep)",
        "opening_greeting": (
            "Chào **{name}**! Tôi là **Chuyên Gia Thể Lực & Dinh Dưỡng Cấp Cao** phụ trách mục tiêu **{goal_title}**.\n\n"
            "Tôi sẽ đồng hành cùng bạn thiết kế chế độ dinh dưỡng chuẩn khoa học (tính toán thâm hụt calo, macro cân bằng) "
            "kết hợp giáo án tập luyện tối ưu (kháng lực duy trì cơ bắp & cardio Zone 2 đốt mỡ thừa).\n\n"
            "👉 Hãy cho tôi biết cân nặng, thể trạng hiện tại hoặc gõ *'Bạn đề xuất phương pháp cho tôi'* để tôi lên chiến lược dinh dưỡng & tập luyện 3 giai đoạn chi tiết nhất!"
        ),
        "prohibited_terms": [
            "giờ học", "giáo trình", "quá tải nhận thức", "deep work", "ôn thi",
            "bài tập về nhà", "giải đề", "học viên", "sách giáo khoa", "ôn tập"
        ],
        "preferred_terms": [
            "lịch tập luyện", "buổi tập", "chế độ dinh dưỡng", "thực đơn ăn uống",
            "thâm hụt calo", "bài tập kháng lực", "cardio zone 2", "phục hồi cơ bắp",
            "calo in / calo out", "intermittent fasting", "protein", "vóc dáng"
        ],
    },
    "language": {
        "domain_name": "Ngoại ngữ & Ngôn ngữ",
        "role_title": "Kiến Trúc Sư Chiến Lược Ngoại Ngữ (Senior Language Roadmap Architect)",
        "chat_title": "💬 Trò Chuyện Cùng Kiến Trúc Sư Ngoại Ngữ",
        "chat_caption": "Tư vấn phương pháp học • Chọn lọc giáo trình & đề thi chuẩn • Chốt lộ trình 4 tầng",
        "input_placeholder": "Thảo luận giáo trình, phương pháp học, luyện đề hoặc gõ 'chốt phương pháp'...",
        "finalize_btn": "🚀 Chốt phương pháp & Tự động phân rã 4 tầng",
        "strategy_label": "💡 Phương pháp & Chiến lược học tập (Kim chỉ nam):",
        "q_label": "🏆 Phân kỳ chiến lược (Quý)",
        "m_resources_label": "Giáo trình & bộ đề",
        "curated_title": "📚 Kho Giáo Trình & Bộ Đề Thẩm Định (Curated Resources):",
        "curated_empty_caption": "*(Chưa có giáo trình. Hãy chat với Architect Bot để tự động trích xuất bộ đề thi thử và tài liệu chính thống)*",
        "how_to_use_label": "Hướng dẫn học & luyện tập",
        "energy_deep": "🔴 Deep Work (Tập trung nhận thức cao độ / Luyện đề chuẩn)",
        "energy_shallow": "🟡 Shallow Work (Ôn từ vựng / Flashcard / Shadowing nhẹ)",
        "energy_recharge": "🟢 Recharge (Nghe Podcast thụ động / Thư giãn phục hồi)",
        "opening_greeting": (
            "Chào **{name}**! Tôi là **Kiến Trúc Sư Chiến Lược Ngoại Ngữ** phụ trách mục tiêu **{goal_title}**.\n\n"
            "Tôi sẽ giúp bạn thiết kế lộ trình ôn luyện 4 tầng, chọn lọc giáo trình chuẩn quốc tế và phương pháp học ngắt quãng (Spaced Repetition & Active Recall) hiệu quả nhất.\n\n"
            "👉 Hãy cho tôi biết trình độ xuất phát điểm của bạn hoặc gõ *'Bạn đề xuất phương pháp cho tôi'* để tôi lên kế hoạch chi tiết!"
        ),
        "prohibited_terms": [],
        "preferred_terms": ["giờ học", "giáo trình", "lộ trình ôn luyện", "bài tập thực hành", "tài liệu chuẩn", "đề thi chuẩn"],
    },
    "tech_study": {
        "domain_name": "Kỹ thuật & Công nghệ",
        "role_title": "Kiến Trúc Sư Lộ Trình Kỹ Thuật (Senior Tech & Engineering Architect)",
        "chat_title": "💬 Trò Chuyện Cùng Kiến Trúc Sư Kỹ Thuật",
        "chat_caption": "Định hướng kiến trúc công nghệ • Dự án thực chiến • Chốt lộ trình 4 tầng",
        "input_placeholder": "Thảo luận tech stack, đồ án thực chiến, giải thuật hoặc gõ 'chốt phương pháp'...",
        "finalize_btn": "🚀 Chốt phương pháp & Tự động phân rã 4 tầng",
        "strategy_label": "💡 Kiến trúc công nghệ & Phương pháp thực chiến (Kim chỉ nam):",
        "q_label": "🏆 Cột mốc kiến trúc & Sản phẩm (Quý)",
        "m_resources_label": "Tài liệu kỹ thuật & Kho mã nguồn",
        "curated_title": "💻 Tài Liệu Kỹ Thuật, Repo Mẫu & Công Cụ (Curated Resources):",
        "curated_empty_caption": "*(Chưa có tài nguyên. Chat với Architect Bot để tự động đề xuất tài liệu chuẩn và repo mẫu)*",
        "how_to_use_label": "Hướng dẫn thực hành dự án",
        "energy_deep": "🔴 Deep Work (Lập trình kiến trúc / Debug / Thuật toán chuyên sâu)",
        "energy_shallow": "🟡 Shallow Work (Đọc doc / Xem demo / Refactor code nhỏ)",
        "energy_recharge": "🟢 Recharge (Đi bộ thư giãn mắt / Giãn cơ / Nghe podcast tech)",
        "opening_greeting": (
            "Chào **{name}**! Tôi là **Kiến Trúc Sư Lộ Trình Kỹ Thuật** phụ trách mục tiêu **{goal_title}**.\n\n"
            "Tôi sẽ giúp bạn cấu trúc lộ trình từ nền tảng đến dự án thực chiến (Project-based Learning), tối ưu tech stack và nhịp Deep Work hiệu quả.\n\n"
            "👉 Bạn muốn tôi đề xuất lộ trình kỹ thuật hay bạn đã có sẵn đồ án thực hành?"
        ),
        "prohibited_terms": [],
        "preferred_terms": ["khung giờ code tập trung", "dự án thực chiến", "kiến trúc hệ thống", "tài liệu kỹ thuật", "giải thuật & tối ưu"],
    },
    "career_finance": {
        "domain_name": "Sự nghiệp & Tài chính",
        "role_title": "Cố Vấn Chiến Lược Sự Nghiệp & Thực Thi (Executive Strategy Advisor)",
        "chat_title": "💬 Trò Chuyện Cùng Cố Vấn Chiến Lược Sự Nghiệp",
        "chat_caption": "Chiến lược hành động • Quản trị KPI & nguồn lực • Chốt lộ trình thực thi 4 tầng",
        "input_placeholder": "Thảo luận KPI, nguồn lực, tối ưu doanh thu hoặc gõ 'chốt phương pháp'...",
        "finalize_btn": "🚀 Chốt phương pháp & Xuất bản lộ trình thực thi 4 tầng",
        "strategy_label": "💼 Chiến lược thực thi & Quản trị nguồn lực (Kim chỉ nam):",
        "q_label": "🏆 Cột mốc KPI & Doanh số (Quý)",
        "m_resources_label": "Công cụ & mẫu biểu điều hành",
        "curated_title": "💼 Bộ Công Cụ, Mẫu Biểu & Tài Nguyên Thực Thi (Curated Resources):",
        "curated_empty_caption": "*(Chưa có tài nguyên. Chat với Cố Vấn Chiến Lược để thiết lập bộ công cụ quản trị KPI)*",
        "how_to_use_label": "Quy trình ứng dụng",
        "energy_deep": "🔴 Deep Work (Chiến lược cấp cao / Đàm phán / Xây dựng hệ thống)",
        "energy_shallow": "🟡 Shallow Work (Gửi email / Họp nhanh / Cập nhật báo cáo KPI)",
        "energy_recharge": "🟢 Recharge (Đi bộ tái tạo năng lượng / Thiền / Giấc ngủ chất lượng)",
        "opening_greeting": (
            "Chào **{name}**! Tôi là **Cố Vấn Chiến Lược Sự Nghiệp & Thực Thi** phụ trách mục tiêu **{goal_title}**.\n\n"
            "Tôi sẽ cùng bạn phân rã mục tiêu thành các cột mốc KPI bàn giao đo lường được, tối ưu hóa khung giờ làm việc và nguồn lực thực thi.\n\n"
            "👉 Bạn muốn tôi đề xuất chiến lược thực thi hay bạn đã có sẵn kế hoạch cần tối ưu?"
        ),
        "prohibited_terms": [],
        "preferred_terms": ["khung giờ làm việc", "hạng mục công việc", "tài nguyên/công cụ", "KPI/cột mốc"],
    },
    "general": {
        "domain_name": "Phát triển cá nhân",
        "role_title": "Trưởng Kiến Trúc Sư Chiến Lược (Senior Strategy Architect)",
        "chat_title": "💬 Trò Chuyện Cùng Strategy Architect",
        "chat_caption": "Thảo luận phương pháp • Tinh chỉnh chiến lược • Chốt lộ trình 4 tầng khép kín",
        "input_placeholder": "Thảo luận phương pháp, tinh chỉnh chiến lược hoặc gõ 'chốt phương pháp'...",
        "finalize_btn": "🚀 Chốt phương pháp & Tự động phân rã 4 tầng",
        "strategy_label": "💡 Phương pháp chiến lược (Kim chỉ nam):",
        "q_label": "🏆 Phân kỳ chiến lược (Quý)",
        "m_resources_label": "Tài liệu & nguồn lực",
        "curated_title": "📚 Kho Tài Liệu & Công Cụ Thẩm Định (Curated Resources):",
        "curated_empty_caption": "*(Chưa có tài liệu. Chat với Architect Bot để tự động tìm kiếm công cụ và tài liệu uy tín)*",
        "how_to_use_label": "Hướng dẫn khai thác",
        "energy_deep": "🔴 Deep Work (Tập trung nhận thức cao độ)",
        "energy_shallow": "🟡 Shallow Work (Nhiệm vụ bổ trợ nhẹ nhàng)",
        "energy_recharge": "🟢 Recharge (Phục hồi nhận thức & thể chất)",
        "opening_greeting": (
            "Chào **{name}**! Tôi là **Strategy & Resource Architect** phụ trách mục tiêu **{goal_title}**.\n\n"
            "Tôi chịu trách nhiệm phân rã mục tiêu thành lộ trình 4 tầng (**Năm ➔ Quý ➔ Tháng ➔ Tuần**) và thẩm định tài nguyên thực thi chuẩn mực.\n\n"
            "👉 Bạn có muốn tôi đề xuất phương pháp tiếp cận tối ưu nhất cho mục tiêu này không?"
        ),
        "prohibited_terms": [],
        "preferred_terms": ["khung giờ tập trung", "lộ trình thực thi", "tài nguyên chuẩn", "tiêu chí hoàn thành"],
    },
}


def detect_goal_domain(
    goal_data: Any = None,
    goal_title: str = "",
    category: str = "",
) -> str:
    """
    Tự động nhận diện lĩnh vực chuyên biệt của mục tiêu dựa trên title, goal_name và category.
    Hỗ trợ linh hoạt cả truyền dict hoặc truyền trực tiếp goal_title vào vị trí đầu tiên.
    """
    if isinstance(goal_data, str):
        if not goal_title:
            goal_title = goal_data
        goal_data = {}
    elif not isinstance(goal_data, dict):
        goal_data = {}

    g = goal_data
    t_str = str(goal_title or g.get("title") or g.get("goal_name", "")).strip().lower()
    c_str = str(category or g.get("category", "")).strip().lower()
    combined = f"{t_str} {c_str}"

    # 1. Nhóm Sức khỏe / Thể chất / Giảm cân / Dinh dưỡng
    health_keywords = [
        "giảm cân", "giam can", "tăng cân", "tang can", "calo", "calorie", "calories",
        "thể chất", "the chat", "sức khỏe", "suc khoe", "chạy bộ", "chay bo", "marathon",
        "gym", "fitness", "dinh dưỡng", "dinh duong", "thực đơn", "thuc don", "eat clean",
        "cân nặng", "can nang", "tập luyện", "tap luyen", "cardio", "kháng lực", "khang luc",
        "giãn cơ", "gian co", "yoga", "body fat", "siết cơ", "siet co", "tăng cơ", "tang co",
        "vận động", "van dong", "thể thao", "the thao", "bơi lội", "đạp xe", "nhịn ăn",
        "fasting", "weight loss", "workout", "giảm mỡ", "giam mo", "bụng", "eo"
    ]
    if re.search(r"\b\d+\s*kg\b", combined) or any(k in combined for k in health_keywords):
        return "health"
    if c_str in ["health", "sức khỏe", "thể chất", "sức khỏe & thể chất", "beauty", "sắc vóc & làm đẹp", "thể hình"]:
        return "health"

    # 2. Nhóm Ngoại ngữ / Ngôn ngữ
    language_keywords = [
        "tiếng", "tieng", "ielts", "toeic", "toefl", "hsk", "jlpt", "topik", "ngoại ngữ",
        "ngoai ngu", "ngôn ngữ", "ngon ngu", "ngữ pháp", "ngu phap", "từ vựng", "tu vung",
        "phát âm", "phat am", "nghe nói", "giao tiếp tiếng", "speaking", "listening",
        "reading", "writing", "english", "chinese", "japanese", "korean", "vocab"
    ]
    if any(k in combined for k in language_keywords):
        return "language"
    if c_str in ["ngoại ngữ", "ngôn ngữ", "language"]:
        return "language"

    # 3. Nhóm Kỹ thuật / Lập trình / Công nghệ
    tech_keywords = [
        "lập trình", "lap trinh", "developer", "coding", "code", "python", "java", "javascript",
        "typescript", "react", "backend", "frontend", "fullstack", "data science", "ai",
        "machine learning", "deep learning", "thuật toán", "thuat toan", "cấu trúc dữ liệu",
        "leetcode", "devops", "cloud", "aws", "docker", "kubernetes", "khoa học máy tính",
        "công nghệ thông tin", "software", "api", "database", "sql"
    ]
    if any(k in combined for k in tech_keywords):
        return "tech_study"

    # 4. Nhóm Sự nghiệp / Tài chính / Dự án
    career_keywords = [
        "tài chính", "tai chinh", "sự nghiệp", "su nghiep", "kinh doanh", "doanh thu", "doanh so",
        "tiết kiệm", "tiet kiem", "đầu tư", "dau tu", "dự án", "du an", "startup", "khởi nghiệp",
        "khoi nghiep", "kpi", "sales", "marketing", "khách hàng", "thăng tiến", "tăng lương",
        "tài sản", "thu nhập", "lợi nhuận"
    ]
    if any(k in combined for k in career_keywords):
        return "career_finance"
    if c_str in ["career", "sự nghiệp", "tài chính", "finance", "business"]:
        return "career_finance"

    return "general"



def get_blank_tree() -> Dict[str, Any]:
    """Tạo cấu trúc Tree trắng với 4 Root Nodes và Hồ sơ Hành vi Thích nghi (Phase 10 Adaptive Memory) hoàn toàn trống rỗng cho user mới."""
    tree = {
        root: {
            "label": ROOT_LABELS[root],
            "description": ROOT_DESCRIPTIONS[root],
            "children": [],
        }
        for root in ROOT_NODES
    }
    tree["historical_insights"] = {
        "failed_methods": [],
        "effective_methods": [],
        "productivity_patterns": [],
    }
    tree["goals"] = []
    tree["profile"] = {}
    tree["goal_profile"] = {}
    tree["resources"] = []
    tree["roadmap"] = {}
    tree["master_schedule"] = []
    tree["retrospective_logs"] = []
    tree["user_profile"] = {
        "is_onboarded": False,
        "coaching_stage": "interviewing",
        "current_situation": "Chưa có mục tiêu",
        "time_constraints": "0h/ngày",
    }
    return tree


def load_all_users_data() -> Dict[str, Any]:
    """Tải toàn bộ cơ sở dữ liệu đa người dùng từ goals_ledger.json (Phase 8 SaaS Multi-user)."""
    if not os.path.exists(LEDGER_PATH):
        default_data = {
            "mavis": get_blank_tree(),
            "user_b": get_blank_tree(),
        }
        save_all_users_data(default_data)
        return default_data

    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            data = {"mavis": get_blank_tree()}

        # Kiểm tra xem file có phải dạng single-user cũ không (top level chứa 4 Root Nodes)
        is_single_user = any(
            k in data and isinstance(data[k], dict) and "children" in data[k]
            for k in ROOT_NODES
        )
        if is_single_user:
            data = {
                "mavis": data,
                "user_b": get_blank_tree(),
            }
            save_all_users_data(data)
            return data

        return data
    except Exception as e:
        print(f"Lỗi khi đọc file {LEDGER_PATH}: {e}")
        return {"mavis": get_blank_tree()}


def save_all_users_data(all_data: Dict[str, Any]) -> bool:
    """Lưu toàn bộ cơ sở dữ liệu đa người dùng vào goals_ledger.json."""
    try:
        with open(LEDGER_PATH, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Lỗi khi ghi file {LEDGER_PATH}: {e}")
        return False


def init_user_tree(username: str = "mavis") -> Dict[str, Any]:
    """Khởi tạo không gian dữ liệu Tree mới cho một người dùng nếu chưa có."""
    username = (username or DEFAULT_USER).strip().lower()
    all_data = load_all_users_data()
    if username not in all_data:
        all_data[username] = get_blank_tree()
        save_all_users_data(all_data)
    return all_data[username]


def load_tree_goals(username: str = "mavis") -> Dict[str, Any]:
    """Tải cấu trúc Tree 4 Root Nodes của một người dùng cụ thể từ goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()
    all_data = load_all_users_data()

    if username not in all_data:
        all_data[username] = get_blank_tree()
        save_all_users_data(all_data)

    user_tree = all_data[username]
    if not isinstance(user_tree, dict):
        user_tree = get_blank_tree()
        all_data[username] = user_tree
        save_all_users_data(all_data)

    # Đảm bảo đủ 4 Root Nodes
    for root in ROOT_NODES:
        if root not in user_tree:
            user_tree[root] = {
                "label": ROOT_LABELS[root],
                "description": ROOT_DESCRIPTIONS[root],
                "children": [],
            }

    # Đảm bảo có nhánh historical_insights (Phase 10 Adaptive Memory)
    if "historical_insights" not in user_tree or not isinstance(user_tree["historical_insights"], dict):
        user_tree["historical_insights"] = {
            "failed_methods": [],
            "effective_methods": [],
            "productivity_patterns": [],
        }
    else:
        for k in ["failed_methods", "effective_methods", "productivity_patterns"]:
            if k not in user_tree["historical_insights"]:
                user_tree["historical_insights"][k] = []

    return user_tree


def load_historical_insights(username: str = "mavis") -> Dict[str, List[str]]:
    """Tải hồ sơ hành vi và bài học thích nghi (Adaptive Memory) của username (Phase 10)."""
    user_tree = load_tree_goals(username=username)
    insights = user_tree.get("historical_insights", {})
    if not isinstance(insights, dict):
        insights = {}
    return {
        "failed_methods": list(insights.get("failed_methods", [])),
        "effective_methods": list(insights.get("effective_methods", [])),
        "productivity_patterns": list(insights.get("productivity_patterns", [])),
    }


def save_historical_insights(insights: Dict[str, List[str]], username: str = "mavis") -> bool:
    """Lưu hồ sơ hành vi và bài học thích nghi của username vào goals_ledger.json (Phase 10)."""
    username = (username or DEFAULT_USER).strip().lower()
    user_tree = load_tree_goals(username=username)
    user_tree["historical_insights"] = {
        "failed_methods": list(insights.get("failed_methods", [])),
        "effective_methods": list(insights.get("effective_methods", [])),
        "productivity_patterns": list(insights.get("productivity_patterns", [])),
    }
    return save_tree_goals(user_tree, username=username)


def append_insight(insight_type: str, content: str, username: str = "mavis") -> bool:
    """Thêm một bài học/phương pháp vào historical_insights của username mà không bị trùng lặp (Phase 10)."""
    if not content or not content.strip():
        return False
    content = content.strip()
    valid_types = ["failed_methods", "effective_methods", "productivity_patterns"]
    if insight_type not in valid_types:
        return False

    insights = load_historical_insights(username=username)
    existing_items = insights.get(insight_type, [])
    for item in existing_items:
        if content.lower() == item.lower() or (len(content) > 10 and content.lower() in item.lower()):
            return False

    existing_items.append(content)
    insights[insight_type] = existing_items
    return save_historical_insights(insights, username=username)


def get_historical_insights_summary_text(username: str = "mavis") -> str:
    """Tạo văn bản tóm tắt Bộ Nhớ Thích Nghi (Adaptive Memory Summary) để truyền vào Prompt (Phase 10)."""
    insights = load_historical_insights(username=username)
    failed = insights.get("failed_methods", [])
    effective = insights.get("effective_methods", [])
    patterns = insights.get("productivity_patterns", [])

    lines = [f"[BỘ NHỚ THÍCH NGHI - HISTORICAL INSIGHTS & BEHAVIORAL PROFILE (User: {username})]"]
    if not failed and not effective and not patterns:
        lines.append("  (Chưa có ghi nhận thất bại hay thói quen đặc thù - Đang ở chế độ quan sát ban đầu)")
        return "\n".join(lines)

    if failed:
        lines.append("  ❌ CÁC PHƯƠNG PHÁP ĐÃ THẤT BẠI / BỎ CUỘC (failed_methods - BẮT BUỘC TRÁNH ĐỀ XUẤT LẠI):")
        for f in failed:
            lines.append(f"     - 🛑 {f}")
    else:
        lines.append("  ❌ CÁC PHƯƠNG PHÁP ĐÃ THẤT BẠI (failed_methods): (Chưa ghi nhận)")

    if effective:
        lines.append("  ✅ CÁC PHƯƠNG PHÁP ĐẠT HIỆU QUẢ CAO (effective_methods - ƯU TIÊN ÁP DỤNG):")
        for e in effective:
            lines.append(f"     - ⭐ {e}")
    else:
        lines.append("  ✅ CÁC PHƯƠNG PHÁP HIỆU QUẢ (effective_methods): (Chưa ghi nhận)")

    if patterns:
        lines.append("  ⚡ QUY LUẬT NĂNG SUẤT & NHỊP SINH HỌC (productivity_patterns):")
        for p in patterns:
            lines.append(f"     - ⏰ {p}")
    else:
        lines.append("  ⚡ QUY LUẬT NĂNG SUẤT (productivity_patterns): (Chưa ghi nhận)")

    return "\n".join(lines)


def save_tree_goals(data: Dict[str, Any], username: str = "mavis") -> bool:
    """Lưu cấu trúc Tree của một người dùng cụ thể vào goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()
    all_data = load_all_users_data()
    all_data[username] = data
    return save_all_users_data(all_data)


def save_user_profile(profile: Dict[str, Any], username: str = "mavis") -> bool:
    """Lưu hồ sơ người dùng vào MongoDB Atlas (collection 'user_states') và goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Lưu vào MongoDB Atlas nếu khả dụng
    if is_mongodb_available():
        db_update_user_state(username, {"user_profile": profile})

    # 2. Lưu dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    existing_profile = all_data[username].get("user_profile", {})
    if isinstance(existing_profile, dict):
        existing_profile.update(profile)
        all_data[username]["user_profile"] = existing_profile
    else:
        all_data[username]["user_profile"] = profile
    return save_all_users_data(all_data)


def load_user_profile(username: str = "mavis") -> Dict[str, Any]:
    """Tải hồ sơ người dùng từ MongoDB Atlas hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    if is_mongodb_available():
        state = db_get_user_state(username)
        if state and "user_profile" in state and isinstance(state["user_profile"], dict):
            return state["user_profile"]

    all_data = load_all_users_data()
    return all_data.get(username, {}).get("user_profile", {})


# ==============================================================================
# TIMEZONE & DATE AXIS UTILITIES (ASIA/HO_CHI_MINH)
# ==============================================================================

VIETNAM_WEEKDAYS = {
    0: "Thứ Hai",
    1: "Thứ Ba",
    2: "Thứ Tư",
    3: "Thứ Năm",
    4: "Thứ Sáu",
    5: "Thứ Bảy",
    6: "Chủ Nhật",
}


def get_vietnam_now() -> datetime:
    """Lấy thời điểm hiện tại theo múi giờ Việt Nam (Asia/Ho_Chi_Minh - UTC+7)."""
    from datetime import timezone
    vn_tz = timezone(timedelta(hours=7))
    return datetime.now(vn_tz)


def get_vietnam_today() -> Any:
    """Lấy ngày hôm nay (date object) theo giờ Việt Nam."""
    return get_vietnam_now().date()


def get_vietnam_today_str() -> str:
    """Lấy chuỗi ngày hôm nay YYYY-MM-DD theo giờ Việt Nam."""
    return get_vietnam_today().strftime("%Y-%m-%d")


def compute_target_date(start_date_str: str, duration_days: int) -> str:
    """Tự động tính ngày đích (target_date = start_date + duration_days)."""
    try:
        s_dt = datetime.strptime(str(start_date_str).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        s_dt = get_vietnam_today()
    try:
        d_days = int(duration_days)
    except Exception:
        d_days = 90
    t_dt = s_dt + timedelta(days=d_days)
    return t_dt.strftime("%Y-%m-%d")


def standardize_goal_schema(g: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chuẩn hóa cấu trúc Goal theo Schema CEO 3 Giai đoạn:
    - id, title, category, priority, preferred_time
    - status: 'evaluating' | 'active' | 'completed'
    - breakdown: yearly -> quarterly -> monthly -> weekly kèm resources
    - start_date (YYYY-MM-DD) và target_date (start_date + duration_days)
    Đồng thời bảo toàn các trường tương thích ngược (goal_id, goal_name, preferred_slots, is_complete).
    """
    if not isinstance(g, dict):
        return {}
    clean = dict(g)

    # 1. ID & Tiêu đề
    gid = clean.get("id") or clean.get("goal_id") or f"goal_{uuid.uuid4().hex[:6]}"
    title = clean.get("title") or clean.get("goal_name") or "Mục tiêu phát triển"
    clean["id"] = gid
    clean["goal_id"] = gid
    clean["title"] = title
    clean["goal_name"] = title

    # 2. Phân loại & Mức ưu tiên
    clean["category"] = clean.get("category") or "Học tập"
    clean["priority"] = clean.get("priority") or "P2 - High"

    # 3. Khung giờ, Quỹ thời gian & Trục ngày thực tế (start_date -> target_date)
    clean["preferred_time"] = clean.get("preferred_time") or clean.get("preferred_slots") or "08:00 - 10:00 Sáng"
    clean["preferred_slots"] = clean["preferred_time"]
    try:
        clean["daily_hours"] = float(clean.get("daily_hours", 1.5))
    except (ValueError, TypeError):
        clean["daily_hours"] = 1.5
    try:
        clean["duration_days"] = int(clean.get("duration_days", 90))
    except (ValueError, TypeError):
        clean["duration_days"] = 90

    # Trục thời gian thực tế: start_date (mặc định hôm nay giờ VN) & target_date (start_date + duration_days)
    raw_start = clean.get("start_date")
    if raw_start:
        try:
            datetime.strptime(str(raw_start).strip()[:10], "%Y-%m-%d")
            clean["start_date"] = str(raw_start).strip()[:10]
        except Exception:
            clean["start_date"] = get_vietnam_today_str()
    else:
        clean["start_date"] = get_vietnam_today_str()

    raw_target = clean.get("target_date")
    if raw_target:
        try:
            datetime.strptime(str(raw_target).strip()[:10], "%Y-%m-%d")
            clean["target_date"] = str(raw_target).strip()[:10]
        except Exception:
            clean["target_date"] = compute_target_date(clean["start_date"], clean["duration_days"])
    else:
        clean["target_date"] = compute_target_date(clean["start_date"], clean["duration_days"])

    # 4. Trạng thái: 'evaluating' | 'active' | 'completed' | 'paused'
    st = clean.get("status")
    if not st or st not in ["evaluating", "active", "completed", "paused"]:
        clean["status"] = "active" if clean.get("is_complete") else "evaluating"
    clean["is_complete"] = True if clean["status"] == "completed" else clean.get("is_complete", False)

    # 5. Phân cấp chi tiết (breakdown: yearly -> quarterly -> monthly -> weekly kèm resources)
    bd = clean.get("breakdown")
    if not isinstance(bd, dict):
        bd = {}
    if "yearly" not in bd:
        bd["yearly"] = clean.get("target_vision") or f"Chinh phục thành công mục tiêu {title}"
    if "quarterly" not in bd or not isinstance(bd["quarterly"], list):
        bd["quarterly"] = []
    if "monthly" not in bd or not isinstance(bd["monthly"], list):
        bd["monthly"] = []
    if "weekly" not in bd or not isinstance(bd["weekly"], list):
        bd["weekly"] = []
    if "resources" not in bd or not isinstance(bd["resources"], list):
        bd["resources"] = clean.get("resources", [])
    clean["breakdown"] = bd

    # 6. Phương pháp chiến lược tổng (Strategy Summary - Quy trình 2 Nhịp)
    if "strategy_summary" in clean and clean["strategy_summary"]:
        clean["strategy_summary"] = str(clean["strategy_summary"]).strip()
    else:
        clean["strategy_summary"] = clean.get("strategy_summary", "")

    return clean


# ==============================================================================
# MASTER SCHEDULE PERSISTENCE (LỊCH TỔNG HỢP GỘP TẤT CẢ ACTIVE GOALS)
# ==============================================================================

def save_master_schedule(schedule: List[Dict[str, Any]], username: str = "mavis") -> bool:
    """
    Lưu lịch trình tổng hợp Master Schedule gộp tất cả active goals vào collection 'user_states'
    trên MongoDB Atlas và đồng bộ dự phòng vào goals_ledger.json.
    Mỗi slot: date, session (Sáng/Chiều/Tối), time_slot, goal_id, goal_title, task_detail, resource_link, is_done.
    """
    username = (username or DEFAULT_USER).strip().lower()
    clean_schedule = [s for s in schedule if isinstance(s, dict)]

    # 1. Lưu vào MongoDB Atlas
    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={"master_schedule": clean_schedule},
        )

    # 2. Lưu dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    all_data[username]["master_schedule"] = clean_schedule
    return save_all_users_data(all_data)


def load_master_schedule(username: str = "mavis") -> List[Dict[str, Any]]:
    """Tải lịch trình tổng hợp Master Schedule từ MongoDB Atlas hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    if is_mongodb_available():
        state = db_get_user_state(username)
        if state:
            sched = state.get("master_schedule")
            if isinstance(sched, list):
                return sched
            return []

    all_data = load_all_users_data()
    user_entry = all_data.get(username, {})
    if isinstance(user_entry, dict) and "master_schedule" in user_entry:
        sched = user_entry.get("master_schedule")
        if isinstance(sched, list):
            return sched

    return []


def update_master_schedule_task_status(
    task_identifier: str,
    is_done: bool = True,
    date: Optional[str] = None,
    username: str = "mavis",
) -> bool:
    """Cập nhật trạng thái is_done cho task trong master_schedule trên MongoDB Atlas."""
    username = (username or DEFAULT_USER).strip().lower()
    schedule = load_master_schedule(username)
    if not schedule:
        return False

    matched = False
    task_clean = task_identifier.strip().lower()

    for item in schedule:
        if not isinstance(item, dict):
            continue
        # Cấu trúc phẳng từng task
        t_title = str(item.get("task_detail", "")).lower()
        if t_title and (task_clean in t_title or t_title in task_clean):
            item_date = str(item.get("date", ""))
            item_day = str(item.get("day_name", ""))
            date_match = (
                date is None
                or item_date == date
                or item_day == date
                or (len(str(date)) >= 10 and str(date) in item_date)
                or (len(item_date) >= 10 and item_date in str(date))
            )
            if date_match:
                item["is_done"] = is_done
                matched = True

        # Cấu trúc theo ngày / sessions
        if "sessions" in item and isinstance(item["sessions"], dict):
            for sess_name, task_list in item["sessions"].items():
                if isinstance(task_list, list):
                    for t in task_list:
                        if isinstance(t, dict):
                            st_title = str(t.get("task_detail", "")).lower()
                            if st_title and (task_clean in st_title or st_title in task_clean):
                                t["is_done"] = is_done
                                matched = True

    if matched:
        save_master_schedule(schedule, username=username)
    return matched


def defer_master_schedule_task_to_tomorrow(
    task_identifier: str,
    current_date: Optional[str] = None,
    username: str = "mavis",
) -> Tuple[bool, Optional[str]]:
    """Dời một task sang ngày mai trong master_schedule trên MongoDB Atlas."""
    username = (username or DEFAULT_USER).strip().lower()
    schedule = load_master_schedule(username)
    if not schedule:
        return False, None

    try:
        cur_dt = datetime.strptime(str(current_date)[:10], "%Y-%m-%d").date()
    except Exception:
        cur_dt = get_vietnam_today()
    next_dt = cur_dt + timedelta(days=1)
    next_date_str = next_dt.strftime("%Y-%m-%d")
    next_day_name = VIETNAM_WEEKDAYS.get(next_dt.weekday(), "Thứ Hai")

    matched = False
    task_clean = task_identifier.strip().lower()
    for item in schedule:
        if not isinstance(item, dict):
            continue
        t_title = str(item.get("task_detail", "")).lower()
        if t_title and (task_clean in t_title or t_title in task_clean):
            item_date = str(item.get("date", ""))
            date_match = (
                current_date is None
                or item_date == current_date
                or (len(str(current_date)) >= 10 and str(current_date) in item_date)
            )
            if date_match:
                item["date"] = next_date_str
                item["day_name"] = next_day_name
                matched = True
                break

    if matched:
        save_master_schedule(schedule, username=username)
        return True, next_date_str
    return False, None


def generate_detailed_master_schedule(
    active_goals: List[Dict[str, Any]],
    start_date_str: Optional[str] = None,
    num_days: int = 14,
    username: str = "mavis",
) -> List[Dict[str, Any]]:
    """
    Sinh lịch trình chi tiết theo ngày thực tế (YYYY-MM-DD), bóc tách rõ từng khung giờ sinh hoạt trong ngày:
    - Khung tập luyện / học tập chuyên sâu: tên bài tập cụ thể, số hiệp/reps/thời lượng (VD: Chạy bộ Zone 2 40p + 3 hiệp Plank 1p)
    - Khung dinh dưỡng IF 16:8: Tách riêng Bữa 1 (12:00 - 12:30) và Bữa 2 (19:00 - 19:30) ghi rõ tên món + định lượng gram/calo
    - Khung uống nước sớm & chiều, khung ngủ sâu phục hồi 22:30.
    - Tuyệt đối không gộp chung 1 dòng!
    """
    if not start_date_str:
        start_date_str = get_vietnam_today_str()

    try:
        start_dt = datetime.strptime(str(start_date_str).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        start_dt = get_vietnam_today()

    clean_goals = [g for g in active_goals if isinstance(g, dict)]
    if not clean_goals:
        return []

    # Thực đơn Bữa 1 theo thứ (12:00 - 12:30)
    meal1_plans = {
        0: "Bữa 1 (12:00 - 12:30): 150g ức gà áp chảo dầu olive, 100g khoai lang luộc, 200g bông cải xanh hấp (~450 kcal, 38g Protein)",
        1: "Bữa 1 (12:00 - 12:30): 150g nạc thăn bò xào cần tỏi, 1 bát nhỏ cơm gạo lứt (120g), 1 đĩa dưa chuột cà chua bi (~480 kcal, 35g Protein)",
        2: "Bữa 1 (12:00 - 12:30): 150g ức gà hấp nấm đông cô, 1 bắp ngô ngọt nhỏ (120g), 200g đậu que luộc (~440 kcal, 37g Protein)",
        3: "Bữa 1 (12:00 - 12:30): 150g tôm xào ớt chuông nấm đùi gà, 100g khoai lang tím nướng, 1 bát canh cải ngọt (~430 kcal, 34g Protein)",
        4: "Bữa 1 (12:00 - 12:30): 150g phi lê cá basa/cá hồi áp chảo, 1 bát nhỏ cơm gạo lứt, 200g măng tây xào tỏi (~490 kcal, 33g Protein)",
        5: "Bữa 1 (12:00 - 12:30): 150g ức gà cuộn măng tây đút lò, 1 củ khoai lang luộc 100g, salad xà lách sốt mè rang (~460 kcal, 36g Protein)",
        6: "Bữa 1 (12:00 - 12:30): 150g nạc lưng heo hấp cuốn bánh tráng rau rừng chấm nước mắm nhạt (~480 kcal, 32g Protein)",
    }

    # Thực đơn Bữa 2 theo thứ (19:00 - 19:30)
    meal2_plans = {
        0: "Bữa 2 (19:00 - 19:30): 150g cá phi lê hấp gừng xì dầu, 200g rau cải luộc chấm trứng dầm, 1 quả táo nhỏ (~420 kcal, 32g Protein)",
        1: "Bữa 2 (19:00 - 19:30): 150g tôm rim nhạt, canh rong biển thịt nạc đậu hũ non (100g đậu), 1 bát rau củ luộc (~400 kcal, 36g Protein)",
        2: "Bữa 2 (19:00 - 19:30): 150g ức gà xé phay trộn rau răm dưa chuột hành tây, 1 bắp ngô luộc nhỏ (~390 kcal, 35g Protein)",
        3: "Bữa 2 (19:00 - 19:30): 150g bò áp chảo măng tây sốt tiêu đen, 200g súp lơ trắng luộc, 1 quả ổi giòn (~410 kcal, 34g Protein)",
        4: "Bữa 2 (19:00 - 19:30): 150g mực hấp lá ổi, canh mùng tơi nấu cua đồng/thịt băm, 1 đĩa bầu luộc chấm muối vừng (~380 kcal, 31g Protein)",
        5: "Bữa 2 (19:00 - 19:30): 150g cá chép/cá rô phi giòn sốt cà chua ít dầu, 200g rau muống luộc dầm sấu (~400 kcal, 33g Protein)",
        6: "Bữa 2 (19:00 - 19:30): 150g ức gà nướng hương thảo, đĩa salad rau mầm dưa chuột cà chua bi dầu olive (~390 kcal, 35g Protein)",
    }

    # Kế hoạch tập luyện theo thứ
    workout_plans = {
        0: ("Kháng lực Upper Body: Push-up 4x12, Dumbbell Shoulder Press 4x10, Bent-over Row 4x12, Plank 3x1p", "🔴 Deep Work", "Hoàn thành 4 bài tập đúng form, ghi chép mức tạ và nghỉ 90s giữa hiệp."),
        1: ("Chạy bộ Zone 2 40 phút + 3 hiệp Plank 1 phút (duy trì nhịp tim 120-135 bpm)", "🟡 Shallow Work", "Duy trì nhịp tim vùng Zone 2 đốt mỡ tối đa, nhịp thở đều nói chuyện được không hụt hơi."),
        2: ("Kháng lực Lower Body: Goblet Squat 4x12, Romanian Deadlift 4x10, Walking Lunges 3x12/chân, Glute Bridge 3x15", "🔴 Deep Work", "Đúng kỹ thuật chuẩn, siết chặt cơ mông và đùi sau, không đau lưng dưới."),
        3: ("Đi bộ máy dốc 12% tốc độ 5.5 km/h Zone 2 trong 45 phút + Cooldown giãn cơ", "🟡 Shallow Work", "Đốt cháy ~350-400 kcal, giữ nhịp tim ổn định và hạ nhiệt bằng 10 phút kéo giãn cơ tĩnh."),
        4: ("Kháng lực Full Body & Core: Dumbbell Swing 4x15, Push-up 4x12, Lat Pulldown/Row 4x10, Russian Twist 3x20", "🔴 Deep Work", "Nhịp thở liên tục, siết cơ core xuyên suốt bài tập, mồ hôi toát đều."),
        5: ("Chạy bộ ngoài trời Zone 2 40 phút + 3 hiệp Plank 1 phút (hoặc bơi lội 1.000m)", "🟡 Shallow Work", "Chạy ngoài không gian xanh, kiểm soát tốc độ và hoàn thành đủ cự ly đề ra."),
        6: ("Phục hồi tích cực: Đi bộ thong thả ngoài trời 5.000 bước & Lăn bọt Foam Roller giãn cơ 25 phút", "🟢 Recharge", "Thả lỏng toàn bộ các nhóm cơ căng mỏi sau tuần tập luyện, ngâm chân nước ấm."),
    }

    schedule_items = []
    for day_offset in range(num_days):
        curr_d = start_dt + timedelta(days=day_offset)
        d_str = curr_d.strftime("%Y-%m-%d")
        d_weekday = curr_d.weekday()
        d_name = VIETNAM_WEEKDAYS[d_weekday]

        # 1. Khung uống nước ấm & đón nắng sớm
        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Sáng",
            "time_slot": "06:30 - 07:00",
            "goal_id": "life_hydration_morning",
            "goal_title": "Nhịp Sinh Học & Đón Nắng",
            "task_detail": "Uống 500ml nước ấm chanh muối khoáng & đón ánh sáng mặt trời 15 phút (Đánh thức hormone cortisol)",
            "energy_level": "🟢 Recharge",
            "definition_of_done": "Bù nước cho não bộ, đón nắng sớm kích hoạt nhịp sinh học, giữ trạng thái nhịn IF 16:8.",
            "resource_link": "https://hubermanlab.com",
            "resource_url": "https://hubermanlab.com",
            "resource_title": "Huberman Protocol: Đánh thức đồng hồ sinh học",
            "is_done": False,
        })

        # 2. Khung Tập Luyện Thể Chất
        w_detail, w_energy, w_dod = workout_plans.get(d_weekday, workout_plans[0])
        health_goal = next((g for g in clean_goals if detect_goal_domain(g.get("title") or g.get("goal_name", ""), g.get("category", "")) == "health"), None)
        h_title = health_goal.get("title") or health_goal.get("goal_name") if health_goal else "Rèn Luyện Thể Lực & Đốt Mỡ"
        h_id = health_goal.get("id") if health_goal else "life_fitness"

        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Sáng",
            "time_slot": "07:00 - 08:00",
            "goal_id": h_id,
            "goal_title": h_title,
            "task_detail": f"{w_detail} cho {h_title}",
            "energy_level": w_energy,
            "definition_of_done": w_dod,
            "resource_link": "https://muscleandstrength.com",
            "resource_url": "https://muscleandstrength.com",
            "resource_title": "Giáo án vận động thể chất chuẩn",
            "is_done": False,
        })

        # 3. Khung Học tập / Công việc Chuyên Sâu (Deep Work P1) nếu có mục tiêu khác
        other_goals = [g for g in clean_goals if g != health_goal]
        for og_idx, og in enumerate(other_goals):
            og_title = og.get("title") or og.get("goal_name", "Mục tiêu phát triển")
            og_id = og.get("id", f"goal_{og_idx}")
            og_bd = og.get("breakdown", {})
            w_tasks = []
            for wk in og_bd.get("weekly", []):
                for tk in wk.get("tasks", []):
                    w_tasks.append(tk)

            if w_tasks:
                chosen_tk = w_tasks[(day_offset + og_idx) % len(w_tasks)]
                og_detail = chosen_tk.get("task", chosen_tk.get("detail", f"Deep Work chuyên sâu cho {og_title}"))
                og_dod = chosen_tk.get("definition_of_done", f"Hoàn thành trọn vẹn nội dung bài học/công việc cho {og_title}.")
                og_link = chosen_tk.get("link", og.get("resources", [{}])[0].get("url", "https://developer.mozilla.org"))
            else:
                og_detail = f"Deep Work tập trung: Nghiên cứu module cốt lõi & làm bài tập thực hành cho {og_title}"
                og_dod = f"Tập trung 100% không xao nhãng, giải quyết trọn vẹn 1 chủ đề trọng tâm cho {og_title}."
                og_link = "https://developer.mozilla.org"

            slot_time = "08:30 - 11:00" if og_idx == 0 else "14:30 - 16:30"
            sess_name = "Sáng" if og_idx == 0 else "Chiều"
            schedule_items.append({
                "date": d_str,
                "day_name": d_name,
                "session": sess_name,
                "time_slot": slot_time,
                "goal_id": og_id,
                "goal_title": og_title,
                "task_detail": og_detail,
                "energy_level": "🔴 Deep Work",
                "definition_of_done": og_dod,
                "resource_link": og_link,
                "resource_url": og_link,
                "resource_title": f"Tài nguyên chính thức: {og_title}",
                "is_done": False,
            })

        # 4. Khung Dinh Dưỡng Bữa 1 (12:00 - 12:30, IF 16:8)
        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Chiều",
            "time_slot": "12:00 - 12:30",
            "goal_id": "life_nutrition_meal1",
            "goal_title": "Dinh Dưỡng IF 16:8 — Bữa 1",
            "task_detail": meal1_plans.get(d_weekday, meal1_plans[0]),
            "energy_level": "🟢 Recharge",
            "definition_of_done": "Ăn chậm nhai kỹ trong 25-30 phút, mở đầu cửa sổ ăn IF 16:8 đúng 12:00 trưa.",
            "resource_link": "https://eatthismuch.com",
            "resource_url": "https://eatthismuch.com",
            "resource_title": "Thực đơn dinh dưỡng Eat Clean & Calo",
            "is_done": False,
        })

        # 5. Khung Bù nước & Hạt ăn nhẹ chiều (15:30 - 16:00)
        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Chiều",
            "time_slot": "15:30 - 16:00",
            "goal_id": "life_hydration_afternoon",
            "goal_title": "Bù Nước & Tỉnh Táo Chiều",
            "task_detail": "Uống 500ml nước lọc / trà xanh ấm không đường & bổ sung 15g hạt hạnh nhân/óc chó",
            "energy_level": "🟢 Recharge",
            "definition_of_done": "Bù nước cho cơ thể, chống hạ đường huyết, giữ tỉnh táo sảng khoái.",
            "resource_link": "https://healthline.com",
            "resource_url": "https://healthline.com",
            "resource_title": "Cơ chế trao đổi chất & Nhịn ăn gián đoạn",
            "is_done": False,
        })

        # 6. Khung Dinh Dưỡng Bữa 2 (19:00 - 19:30, IF 16:8)
        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Tối",
            "time_slot": "19:00 - 19:30",
            "goal_id": "life_nutrition_meal2",
            "goal_title": "Dinh Dưỡng IF 16:8 — Bữa 2",
            "task_detail": meal2_plans.get(d_weekday, meal2_plans[0]),
            "energy_level": "🟢 Recharge",
            "definition_of_done": "Kết thúc bữa ăn trước 19:30 để đóng cửa sổ ăn IF 16:8 (bắt đầu nhịn 16 tiếng đến 12:00 hôm sau).",
            "resource_link": "https://eatthismuch.com",
            "resource_url": "https://eatthismuch.com",
            "resource_title": "Thực đơn thâm hụt calo bữa tối",
            "is_done": False,
        })

        # 7. Khung Giấc Ngủ Tái Tạo (22:15 - 22:30)
        schedule_items.append({
            "date": d_str,
            "day_name": d_name,
            "session": "Tối",
            "time_slot": "22:15 - 22:30",
            "goal_id": "life_sleep",
            "goal_title": "Giấc Ngủ Tái Tạo Phục Hồi",
            "task_detail": "Tắt toàn bộ thiết bị điện tử, uống 1 ly trà hoa cúc ấm & Đi ngủ đúng 22:30 để ngủ sâu 8 tiếng",
            "energy_level": "🟢 Recharge",
            "definition_of_done": "Tắt màn hình xanh lúc 22:15, lên giường ngủ lúc 22:30 trong phòng tối hoàn toàn, thoáng mát 22-24°C.",
            "resource_link": "https://sleepfoundation.org",
            "resource_url": "https://sleepfoundation.org",
            "resource_title": "Khoa học giấc ngủ sâu & Phục hồi cơ thể",
            "is_done": False,
        })

    return schedule_items


def ensure_schedule_covers_date(
    target_date: Any,
    active_goals: Optional[List[Dict[str, Any]]] = None,
    username: str = "mavis",
) -> List[Dict[str, Any]]:
    """
    Đảm bảo master_schedule luôn có dữ liệu cho ngày target_date.
    Nếu ngày đó chưa có lịch, tự động sinh 7 ngày cho tuần đó và nối vào master_schedule trên MongoDB Atlas.
    """
    username = (username or "mavis").strip().lower()
    current_schedule = load_master_schedule(username)
    if not isinstance(target_date, datetime) and not hasattr(target_date, "strftime"):
        try:
            target_date = datetime.strptime(str(target_date)[:10], "%Y-%m-%d").date()
        except Exception:
            target_date = get_vietnam_today()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()

    target_d_str = target_date.strftime("%Y-%m-%d")

    # Kiểm tra xem ngày này đã có task nào chưa
    has_date = any(t.get("date") == target_d_str for t in current_schedule if isinstance(t, dict))
    if has_date:
        return current_schedule

    # Nếu chưa có, lấy active goals
    if active_goals is None:
        all_goals = load_user_goals(username)
        active_goals = [g for g in all_goals if g.get("status") == "active"]
        if not active_goals:
            active_goals = [g for g in all_goals if g.get("status") not in ("paused", "completed")]

    if not active_goals:
        return current_schedule or []

    # Bắt đầu sinh từ thứ Hai của tuần chứa target_date
    monday_of_week = target_date - timedelta(days=target_date.weekday())
    new_items = generate_detailed_master_schedule(
        active_goals=active_goals,
        start_date_str=monday_of_week.strftime("%Y-%m-%d"),
        num_days=7,
        username=username,
    )

    # Lọc bỏ trùng lặp nếu bất kỳ ngày nào trong 7 ngày đó đã tồn tại
    existing_dates = set(t.get("date") for t in current_schedule if isinstance(t, dict) and t.get("date"))
    items_to_append = [it for it in new_items if it.get("date") not in existing_dates]

    if items_to_append:
        merged_schedule = current_schedule + items_to_append
        save_master_schedule(merged_schedule, username=username)
        return merged_schedule

    return current_schedule


def save_user_goals(goals: List[Dict[str, Any]], username: str = "mavis") -> bool:
    """
    Lưu danh sách đa mục tiêu song song (goals: List[GoalProfile]) vào collection 'user_states'
    trên MongoDB Atlas với update_one(..., upsert=True) và đồng bộ dự phòng vào goals_ledger.json.
    Tự động chuẩn hóa đầy đủ theo Schema CEO 3 Giai đoạn: id, title, category, priority, preferred_time, status, breakdown.
    """
    username = (username or DEFAULT_USER).strip().lower()
    clean_goals = [standardize_goal_schema(g) for g in goals if isinstance(g, dict) and (g.get("goal_name") or g.get("title"))]

    # 1. Tự động lưu bền vững lên MongoDB Atlas
    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={
                "goals": clean_goals,
                "profile": clean_goals[0] if clean_goals else {},
                "goal_profile": clean_goals[0] if clean_goals else {},
            },
        )

    # 2. Đồng bộ dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    all_data[username]["goals"] = clean_goals
    if clean_goals:
        all_data[username]["goal_profile"] = clean_goals[0]
    else:
        all_data[username]["goal_profile"] = {}
        all_data[username]["profile"] = {}

    # Đồng bộ sang user_profile để tương thích với các view khác
    if "user_profile" not in all_data[username] or not isinstance(all_data[username]["user_profile"], dict):
        all_data[username]["user_profile"] = {}
    if clean_goals:
        goal_names = [g.get("title") or g.get("goal_name") for g in clean_goals if (g.get("title") or g.get("goal_name"))]
        all_data[username]["user_profile"]["current_situation"] = f"Đa mục tiêu: {', '.join(goal_names)}"
        total_h = sum(float(g.get("daily_hours") or 0) for g in clean_goals)
        all_data[username]["user_profile"]["time_constraints"] = f"{total_h}h/ngày trên {len(clean_goals)} mục tiêu"
        if all(g.get("is_complete") for g in clean_goals):
            all_data[username]["user_profile"]["is_onboarded"] = True
            all_data[username]["user_profile"]["coaching_stage"] = "action"
    else:
        all_data[username]["user_profile"]["current_situation"] = "Chưa có mục tiêu"
        all_data[username]["user_profile"]["time_constraints"] = "0h/ngày"
    return save_all_users_data(all_data)


def load_user_goals(username: str = "mavis") -> List[Dict[str, Any]]:
    """Tải danh sách đa mục tiêu từ MongoDB Atlas hoặc goals_ledger.json và chuẩn hóa theo Schema."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Ưu tiên tải từ MongoDB Atlas
    if is_mongodb_available():
        state = db_get_user_state(username)
        if state:
            if "goals" in state and isinstance(state["goals"], list):
                return [standardize_goal_schema(g) for g in state["goals"]]
            p = state.get("profile") or state.get("goal_profile")
            if p and isinstance(p, dict) and (p.get("goal_name") or p.get("title")):
                return [standardize_goal_schema(p)]
            # User đã tồn tại trong user_states nhưng chưa có goals -> trả về rỗng, tuyệt đối không nạp mock data
            return []

    # 2. Fallback về goals_ledger.json
    all_data = load_all_users_data()
    user_entry = all_data.get(username, {})
    if isinstance(user_entry, dict):
        if "goals" in user_entry and isinstance(user_entry["goals"], list):
            return [standardize_goal_schema(g) for g in user_entry["goals"]]
        p = user_entry.get("goal_profile", {})
        if isinstance(p, dict) and (p.get("goal_name") or p.get("title")):
            return [standardize_goal_schema(p)]

    return []


def update_user_goal_status(goal_id: str, new_status: str, username: str = "mavis") -> bool:
    """
    Cập nhật trạng thái ('active', 'paused', 'completed', 'evaluating') của mục tiêu.
    Đồng bộ lưu vào MongoDB Atlas và goals_ledger.json.
    """
    username = (username or DEFAULT_USER).strip().lower()
    goals = load_user_goals(username)
    if not goals:
        return False

    updated = False
    gid_clean = str(goal_id).strip()
    for g in goals:
        if str(g.get("id", "")).strip() == gid_clean or str(g.get("title", "")).strip() == gid_clean or str(g.get("goal_name", "")).strip() == gid_clean:
            g["status"] = new_status
            if new_status == "completed":
                g["is_complete"] = True
            elif new_status in ["active", "paused", "evaluating"]:
                g["is_complete"] = False
            updated = True
            break

    if updated:
        save_user_goals(goals, username=username)
    return updated


def update_user_goal_details(goal_id: str, updates: Dict[str, Any], username: str = "mavis") -> bool:
    """
    Cập nhật thông tin chi tiết (title, duration_days, daily_hours, preferred_time, priority) của mục tiêu.
    Tự động cập nhật đồng bộ sang master_schedule nếu tiêu đề mục tiêu thay đổi.
    """
    username = (username or DEFAULT_USER).strip().lower()
    goals = load_user_goals(username)
    if not goals:
        return False

    updated = False
    old_title = ""
    new_title = ""
    gid_clean = str(goal_id).strip()

    for g in goals:
        if str(g.get("id", "")).strip() == gid_clean or str(g.get("title", "")).strip() == gid_clean or str(g.get("goal_name", "")).strip() == gid_clean:
            old_title = g.get("title") or g.get("goal_name") or ""
            for k, v in updates.items():
                if v is not None:
                    g[k] = v
                    if k == "title":
                        g["goal_name"] = v
                    elif k == "goal_name":
                        g["title"] = v
                    elif k == "preferred_time":
                        g["preferred_slots"] = v
                    elif k == "preferred_slots":
                        g["preferred_time"] = v
            new_title = g.get("title") or g.get("goal_name") or ""
            updated = True
            break

    if updated:
        save_user_goals(goals, username=username)
        if old_title and new_title and old_title != new_title:
            ms = load_master_schedule(username)
            if ms:
                ms_updated = False
                for item in ms:
                    if isinstance(item, dict):
                        if item.get("goal_id") == gid_clean or item.get("goal_title") == old_title:
                            item["goal_title"] = new_title
                            ms_updated = True
                if ms_updated:
                    save_master_schedule(ms, username=username)
    return updated


def delete_user_goal(goal_id: str, username: str = "mavis") -> bool:
    """
    Xóa vĩnh viễn mục tiêu khỏi danh sách goals và dọn sạch các task liên quan trong master_schedule.
    Nếu sau khi xóa không còn mục tiêu nào, dọn sạch triệt để các trường profile, goal_profile, roadmap, resources trong MongoDB và ledger.
    """
    username = (username or DEFAULT_USER).strip().lower()
    goals = load_user_goals(username)
    if not goals:
        return False

    gid_clean = str(goal_id).strip()
    target_goal = None
    remaining_goals = []

    for g in goals:
        if str(g.get("id", "")).strip() == gid_clean or str(g.get("title", "")).strip() == gid_clean or str(g.get("goal_name", "")).strip() == gid_clean:
            target_goal = g
        else:
            remaining_goals.append(g)

    if target_goal is None:
        return False

    # 1. Lưu lại danh sách mục tiêu mới
    save_user_goals(remaining_goals, username=username)

    # 2. Xóa các lịch trình liên quan trong master_schedule
    deleted_title = target_goal.get("title") or target_goal.get("goal_name") or ""
    deleted_id = target_goal.get("id") or gid_clean
    ms = load_master_schedule(username)
    if ms:
        clean_ms = [
            t for t in ms
            if isinstance(t, dict) and str(t.get("goal_id", "")) != str(deleted_id) and str(t.get("goal_id", "")) != gid_clean and t.get("goal_title") != deleted_title
        ]
        save_master_schedule(clean_ms, username=username)

    # 3. Dọn sạch triệt để schema profile cũ khi danh sách mục tiêu trống hoàn toàn
    if not remaining_goals:
        if is_mongodb_available():
            db_update_user_state(
                username=username,
                state_update={
                    "goals": [],
                    "profile": {},
                    "goal_profile": {},
                    "resources": [],
                    "curated_resources": [],
                    "roadmap": {},
                    "backcasting_roadmap": {},
                    "master_schedule": [],
                    "user_profile": {
                        "is_onboarded": False,
                        "coaching_stage": "interviewing",
                        "current_situation": "Chưa có mục tiêu",
                        "time_constraints": "0h/ngày",
                    },
                },
            )
        all_data = load_all_users_data()
        if username in all_data and isinstance(all_data[username], dict):
            all_data[username]["goals"] = []
            all_data[username]["profile"] = {}
            all_data[username]["goal_profile"] = {}
            all_data[username]["resources"] = []
            all_data[username]["curated_resources"] = []
            all_data[username]["roadmap"] = {}
            all_data[username]["backcasting_roadmap"] = {}
            all_data[username]["master_schedule"] = []
            all_data[username]["user_profile"] = {
                "is_onboarded": False,
                "coaching_stage": "interviewing",
                "current_situation": "Chưa có mục tiêu",
                "time_constraints": "0h/ngày",
            }
            save_all_users_data(all_data)

    return True


def save_user_goal_profile(profile: Dict[str, Any], username: str = "mavis") -> bool:
    """
    Lưu hồ sơ mục tiêu (GoalProfile) vào collection 'user_states' trên MongoDB Atlas
    với update_one(..., upsert=True) và đồng bộ dự phòng vào goals_ledger.json.
    """
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Tự động lưu bền vững lên MongoDB Atlas
    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={
                "profile": profile,
                "goal_profile": profile,
            },
        )

    # 2. Đồng bộ dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    existing_prof = all_data[username].get("goal_profile", {})
    if isinstance(existing_prof, dict):
        existing_prof.update(profile)
        all_data[username]["goal_profile"] = existing_prof
    else:
        all_data[username]["goal_profile"] = profile

    # Đồng bộ sang user_profile để tương thích với các view khác
    if "user_profile" not in all_data[username] or not isinstance(all_data[username]["user_profile"], dict):
        all_data[username]["user_profile"] = {}
    if profile.get("goal_name"):
        all_data[username]["user_profile"]["current_situation"] = f"Mục tiêu: {profile.get('goal_name')} (Trình độ: {profile.get('current_level', 'N/A')})"
    if profile.get("preferred_slots") or profile.get("daily_hours"):
        all_data[username]["user_profile"]["time_constraints"] = f"{profile.get('daily_hours', 2.0)}h/ngày ({profile.get('preferred_slots', 'Linh hoạt')})"
    if profile.get("is_complete"):
        all_data[username]["user_profile"]["is_onboarded"] = True
        all_data[username]["user_profile"]["coaching_stage"] = "action"
    return save_all_users_data(all_data)


def load_user_goal_profile(username: str = "mavis") -> Dict[str, Any]:
    """Tải hồ sơ mục tiêu GoalProfile từ MongoDB Atlas hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Ưu tiên tải từ MongoDB Atlas
    if is_mongodb_available():
        state = db_get_user_state(username)
        if state:
            goals = state.get("goals")
            if isinstance(goals, list) and len(goals) > 0 and (goals[0].get("goal_name") or goals[0].get("title")):
                return goals[0]
            p = state.get("profile") or state.get("goal_profile")
            if p and isinstance(p, dict) and (p.get("goal_name") or p.get("title")):
                return p
            return {}

    # 2. Fallback về goals_ledger.json
    all_data = load_all_users_data()
    user_entry = all_data.get(username, {})
    if isinstance(user_entry, dict):
        goals = user_entry.get("goals")
        if isinstance(goals, list) and len(goals) > 0 and (goals[0].get("goal_name") or goals[0].get("title")):
            return goals[0]
        p = user_entry.get("goal_profile", {})
        if isinstance(p, dict) and (p.get("goal_name") or p.get("title")):
            return p
    return {}


def save_user_resources(resources: List[Dict[str, Any]], username: str = "mavis") -> bool:
    """Lưu danh sách tài nguyên và công cụ thẩm định vào MongoDB Atlas và goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Lưu lên MongoDB Atlas
    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={
                "resources": resources,
                "curated_resources": resources,
            },
        )

    # 2. Lưu dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    all_data[username]["curated_resources"] = resources
    return save_all_users_data(all_data)


def load_user_resources(username: str = "mavis") -> List[Dict[str, Any]]:
    """Tải danh sách tài nguyên từ MongoDB Atlas hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Ưu tiên tải từ MongoDB Atlas
    if is_mongodb_available():
        state = db_get_user_state(username)
        if state:
            if "resources" in state and isinstance(state["resources"], list):
                return state["resources"]
            if "curated_resources" in state and isinstance(state["curated_resources"], list):
                return state["curated_resources"]
            return []

    # 2. Fallback về goals_ledger.json
    all_data = load_all_users_data()
    return all_data.get(username, {}).get("curated_resources", [])


def save_user_roadmap(roadmap: Dict[str, Any], username: str = "mavis") -> bool:
    """
    Lưu lộ trình Backcasting phân cấp vào collection 'user_states' trên MongoDB Atlas
    với update_one(..., upsert=True) và đồng bộ dự phòng vào goals_ledger.json.
    """
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Tự động lưu bền vững lên MongoDB Atlas
    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={
                "roadmap": roadmap,
                "backcasting_roadmap": roadmap,
            },
        )

    # 2. Lưu dự phòng vào goals_ledger.json
    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    all_data[username]["backcasting_roadmap"] = roadmap
    return save_all_users_data(all_data)


def load_user_roadmap(username: str = "mavis") -> Dict[str, Any]:
    """Tải lộ trình Backcasting từ MongoDB Atlas hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    # 1. Ưu tiên tải từ MongoDB Atlas
    if is_mongodb_available():
        state = db_get_user_state(username)
        if state:
            rm = state.get("roadmap") or state.get("backcasting_roadmap")
            if rm and isinstance(rm, dict) and rm.get("weekly_milestones"):
                return rm
            return {}

    # 2. Fallback về goals_ledger.json
    all_data = load_all_users_data()
    return all_data.get(username, {}).get("backcasting_roadmap", {})


# ==============================================================================
# RETROSPECTIVE LOGS PERSISTENCE (LỊCH SỬ CHECK-IN CẢM XÚC & TỶ LỆ HOÀN THÀNH)
# ==============================================================================

def save_retrospective_logs(logs: List[Dict[str, Any]], username: str = "mavis") -> bool:
    """Lưu lịch sử check-in cảm xúc, tỷ lệ hoàn thành vào MongoDB user_states và goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()
    clean_logs = [l for l in logs if isinstance(l, dict)]

    if is_mongodb_available():
        db_update_user_state(
            username=username,
            state_update={"retrospective_logs": clean_logs},
        )

    all_data = load_all_users_data()
    if username not in all_data or not isinstance(all_data[username], dict):
        all_data[username] = get_blank_tree()
    all_data[username]["retrospective_logs"] = clean_logs
    return save_all_users_data(all_data)


def load_retrospective_logs(username: str = "mavis") -> List[Dict[str, Any]]:
    """Tải lịch sử check-in cảm xúc và tỷ lệ hoàn thành từ MongoDB hoặc goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()

    if is_mongodb_available():
        state = db_get_user_state(username)
        if state and "retrospective_logs" in state:
            rlogs = state.get("retrospective_logs")
            if isinstance(rlogs, list):
                return rlogs

    all_data = load_all_users_data()
    user_entry = all_data.get(username, {})
    if isinstance(user_entry, dict) and "retrospective_logs" in user_entry:
        rlogs = user_entry.get("retrospective_logs")
        if isinstance(rlogs, list):
            return rlogs

    return []


def append_retrospective_log(log_entry: Dict[str, Any], username: str = "mavis") -> bool:
    """Thêm một bản ghi check-in mới vào retrospective_logs trên MongoDB."""
    username = (username or DEFAULT_USER).strip().lower()
    existing_logs = load_retrospective_logs(username)
    if not isinstance(log_entry, dict):
        return False

    clean_entry = dict(log_entry)
    if "log_id" not in clean_entry:
        clean_entry["log_id"] = f"retro_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if "timestamp" not in clean_entry:
        clean_entry["timestamp"] = datetime.now().isoformat()
    if "date" not in clean_entry:
        clean_entry["date"] = datetime.now().strftime("%Y-%m-%d")

    existing_logs.append(clean_entry)
    return save_retrospective_logs(existing_logs, username=username)


def get_user_state_full(username: str = "mavis") -> Dict[str, Any]:
    """Tải toàn bộ trạng thái người dùng (goals, master_schedule, retrospective_logs, user_profile) từ MongoDB."""
    username = (username or DEFAULT_USER).strip().lower()
    if is_mongodb_available():
        st = db_get_user_state(username)
        if st:
            return {
                "username": username,
                "goals": load_user_goals(username),
                "master_schedule": load_master_schedule(username),
                "retrospective_logs": load_retrospective_logs(username),
                "profile": st.get("profile", {}),
                "resources": st.get("resources", []),
                "roadmap": st.get("roadmap", {}),
                "user_profile": st.get("user_profile", {}),
            }

    return {
        "username": username,
        "goals": load_user_goals(username),
        "master_schedule": load_master_schedule(username),
        "retrospective_logs": load_retrospective_logs(username),
        "profile": {},
        "resources": [],
        "roadmap": {},
        "user_profile": {},
    }


def calculate_user_streak(username: str = "mavis") -> int:
    """Tính chuỗi ngày duy trì kỷ luật (Streak) liên tiếp từ MongoDB master_schedule và retrospective_logs."""
    username = (username or DEFAULT_USER).strip().lower()
    master_schedule = load_master_schedule(username)
    retrospective_logs = load_retrospective_logs(username)

    active_dates = set()
    for t in master_schedule:
        if isinstance(t, dict) and t.get("is_done") is True:
            d_str = str(t.get("date", "")).strip()
            if d_str:
                active_dates.add(d_str)

    for l in retrospective_logs:
        if isinstance(l, dict):
            d_str = str(l.get("date", "")).strip()
            if d_str:
                active_dates.add(d_str)

    if not active_dates:
        return 1

    parsed_dates = []
    for d in active_dates:
        try:
            parsed_dates.append(datetime.strptime(d[:10], "%Y-%m-%d").date())
        except Exception:
            pass

    if not parsed_dates:
        return max(1, len(active_dates))

    parsed_dates = sorted(list(set(parsed_dates)), reverse=True)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    if parsed_dates[0] not in [today, yesterday]:
        return 1

    streak = 1
    for i in range(len(parsed_dates) - 1):
        if (parsed_dates[i] - parsed_dates[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def load_categorized_goals(username: str = "mavis") -> Dict[str, Any]:
    """
    Truy xuất vào đúng nhánh dữ liệu của tài khoản đó từ memory/goals_ledger.json (Phase 8 Multi-Tenant).
    Ví dụ: data.get(username, {})
    """
    username = (username or DEFAULT_USER).strip().lower()

    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                # Truy xuất đúng nhánh dữ liệu của username (Phase 8)
                user_branch = data.get(username, {})
                if not user_branch and username == DEFAULT_USER and any(k in data for k in ROOT_NODES):
                    user_branch = data

                result = {}
                for root in ROOT_NODES:
                    node = user_branch.get(root, {})
                    children = node.get("children", []) if isinstance(node, dict) else (node if isinstance(node, list) else [])
                    for g in children:
                        if isinstance(g, dict):
                            if "leaf_nodes" in g and "milestones" not in g:
                                g["milestones"] = g["leaf_nodes"]
                            elif "milestones" in g and "leaf_nodes" not in g:
                                g["leaf_nodes"] = g["milestones"]
                    result[root] = children

                # Aliases tương thích ngược
                result["study_work"] = result.get("career", [])
                result["finance"] = result.get("career", [])
                result["family"] = result.get("relationships", [])
                result["daily_routine"] = result.get("health", [])
                result["health_beauty"] = result.get("health", []) + result.get("beauty", [])
                return result
        except Exception as e:
            print(f"Lỗi khi đọc file {LEDGER_PATH}: {e}")

    # Fallback qua load_tree_goals
    tree = load_tree_goals(username=username)
    result = {}
    for root in ROOT_NODES:
        node = tree.get(root, {})
        children = node.get("children", []) if isinstance(node, dict) else (node if isinstance(node, list) else [])
        result[root] = children

    result["study_work"] = result["career"]
    result["finance"] = result["career"]
    result["family"] = result["relationships"]
    result["daily_routine"] = result["health"]
    result["health_beauty"] = result["health"] + result["beauty"]

    return result


def save_categorized_goals(data: Dict[str, Any], username: str = "mavis") -> bool:
    """Lưu dữ liệu vào goals_ledger.json của username, tự động đóng gói theo cấu trúc Tree 4 Root Nodes."""
    username = (username or DEFAULT_USER).strip().lower()
    # Nếu data đã ở định dạng Tree (chứa dict có 'children')
    if any(k in data and isinstance(data[k], dict) and "children" in data[k] for k in ROOT_NODES):
        return save_tree_goals(data, username=username)

    current_tree = load_tree_goals(username=username)
    for root in ROOT_NODES:
        if root in data and isinstance(data[root], list):
            current_tree[root]["children"] = data[root]

    # Kiểm tra các key cũ
    if "study_work" in data and "career" not in data:
        current_tree["career"]["children"] = data["study_work"]
    if "family" in data and "relationships" not in data:
        current_tree["relationships"]["children"] = data["family"]

    return save_tree_goals(current_tree, username=username)


save_goals = save_categorized_goals


def load_goals(category: Optional[str] = None, username: str = "mavis") -> List[Dict[str, Any]]:
    """Trả về danh sách mục tiêu làm phẳng hoặc theo category của username."""
    cat_data = load_categorized_goals(username=username)
    if category:
        root_key = CATEGORY_TO_ROOT.get(category, category)
        return cat_data.get(root_key, cat_data.get(category, []))

    flat_list = []
    for root in ROOT_NODES:
        goals = cat_data.get(root, [])
        for g in goals:
            g_copy = dict(g)
            g_copy["category"] = root
            g_copy["category_label"] = ROOT_LABELS.get(root, root)
            flat_list.append(g_copy)
    return flat_list


def normalize_goal_title(title: str) -> str:
    """Chuẩn hóa tiêu đề mục tiêu để so sánh trùng lặp ngữ nghĩa/tên gọi (Phase 9)."""
    if not title:
        return ""
    t = title.lower().strip()
    prefixes = [
        "tôi muốn đặt mục tiêu mới:",
        "tôi muốn đặt mục tiêu:",
        "mục tiêu mới:",
        "đặt mục tiêu mới:",
        "đặt mục tiêu:",
        "tôi muốn học",
        "tôi muốn",
        "mục tiêu:",
        "chinh phục",
        "học tập",
        "ôn thi",
    ]
    for p in prefixes:
        if t.startswith(p):
            t = t[len(p):].strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_duplicate_goal(title1: str, title2: str) -> bool:
    """
    Kiểm tra xem hai mục tiêu có phải là trùng lặp ngữ nghĩa hoặc tên gọi không (Phase 9).
    1. So khớp chuỗi sau khi chuẩn hóa (Exact match sau normalize).
    2. Bao hàm chuỗi (Substring containment).
    3. Độ tương đồng tập từ khóa cốt lõi (Jaccard similarity).
    """
    n1 = normalize_goal_title(title1)
    n2 = normalize_goal_title(title2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True

    # Ràng buộc phân tách mục tiêu đặc thù: Không gộp nếu 1 bên là thạc sĩ và 1 bên không phải
    is_master_1 = any(w in n1 for w in ["thạc sĩ", "master"])
    is_master_2 = any(w in n2 for w in ["thạc sĩ", "master"])
    if is_master_1 != is_master_2:
        return False

    # Không gộp nếu 1 bên là IELTS và bên kia không phải
    if ("ielts" in n1) != ("ielts" in n2):
        return False

    # Không gộp nếu 1 bên là HSK/tiếng Trung và bên kia không phải
    is_chinese_1 = any(w in n1 for w in ["hsk", "tiếng trung"])
    is_chinese_2 = any(w in n2 for w in ["hsk", "tiếng trung"])
    if is_chinese_1 != is_chinese_2:
        return False

    if len(n1) > 8 and len(n2) > 8 and (n1 in n2 or n2 in n1):
        return True

    words1 = set([w for w in n1.split() if len(w) > 2])
    words2 = set([w for w in n2.split() if len(w) > 2])
    if not words1 or not words2:
        return False

    domain_keywords = [
        {"data", "science"},
        {"machine", "learning"},
        {"thạc", "sĩ"},
        {"master", "ai"},
        {"react", "next"},
    ]
    for dwords in domain_keywords:
        if dwords.issubset(words1) and dwords.issubset(words2):
            return True

    jaccard = len(words1.intersection(words2)) / len(words1.union(words2))
    return jaccard >= 0.6


def cleanup_duplicate_goals(username: str = "mavis") -> int:
    """
    Quét và xóa sạch các mục tiêu trùng lặp rác trong toàn bộ cây mục tiêu của username (Phase 9).
    Hợp nhất các tài nguyên và cột mốc của các mục tiêu trùng lặp vào mục tiêu gốc.
    Trả về số lượng mục tiêu rác đã được dọn sạch.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    total_removed = 0

    for root in ROOT_NODES:
        goals = tree.get(root, {}).get("children", [])
        if not goals:
            continue

        unique_goals = []
        for g in goals:
            matched = None
            for u in unique_goals:
                if is_duplicate_goal(g.get("title", ""), u.get("title", "")):
                    matched = u
                    break

            if matched:
                # Hợp nhất tài nguyên từ g sang matched
                matched_res_titles = set(r.get("title") for r in matched.get("resources", []))
                for r in g.get("resources", []):
                    if r.get("title") not in matched_res_titles:
                        matched.setdefault("resources", []).append(r)
                        matched_res_titles.add(r.get("title"))

                # Hợp nhất leaf_nodes từ g sang matched
                matched_leaf_titles = set(normalize_goal_title(l.get("title", "")) for l in matched.get("leaf_nodes", []))
                for l in g.get("leaf_nodes", []):
                    lt = normalize_goal_title(l.get("title", ""))
                    if lt and lt not in matched_leaf_titles:
                        matched.setdefault("leaf_nodes", []).append(l)
                        matched_leaf_titles.add(lt)
                matched["milestones"] = matched.get("leaf_nodes", [])

                # Giữ feasibility_analysis chi tiết hơn
                if len(g.get("feasibility_analysis", "")) > len(matched.get("feasibility_analysis", "")):
                    matched["feasibility_analysis"] = g["feasibility_analysis"]

                total_removed += 1
            else:
                unique_goals.append(g)

        tree[root]["children"] = unique_goals

    if total_removed > 0:
        save_tree_goals(tree, username=username)

    return total_removed


def add_goal(
    title: str,
    deadline: str,
    category: str = "career",
    milestones: Optional[List[Dict[str, Any]]] = None,
    status: str = "in_progress",
    resources: Optional[List[Dict[str, Any]]] = None,
    feasibility_score: Optional[int] = None,
    priority: Optional[str] = None,
    feasibility_analysis: Optional[str] = None,
    total_estimated_hours: Optional[int] = None,
    recommended_hours_per_week: Optional[int] = None,
    dependencies: Optional[List[str]] = None,
    username: str = "mavis",
) -> Dict[str, Any]:
    """Thêm mục tiêu mới và các Leaf Node có status, deadline, dependencies vào Tree của username."""
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    target_root = CATEGORY_TO_ROOT.get(category, "career")
    if target_root not in ROOT_NODES:
        target_root = "career"

    prefix = target_root[:3]
    new_id = f"goal_{prefix}_{len(tree[target_root]['children']) + 1}_{uuid.uuid4().hex[:4]}"

    # Chuẩn hóa Leaf Nodes
    raw_milestones = milestones or [
        {"milestone": f"Khởi động kế hoạch {title}", "timeline": "Tuần 1 - Tuần 2", "status": "in_progress", "dependencies": []},
        {"milestone": "Tăng tốc và nghiệm thu giai đoạn 1", "timeline": "Tuần 3 - Tuần 4", "status": "pending", "dependencies": [f"leaf_{new_id}_1"]},
    ]

    leaf_nodes = []
    for idx, m in enumerate(raw_milestones, 1):
        leaf_id = m.get("id") or f"leaf_{new_id}_{idx}"
        leaf_nodes.append({
            "id": leaf_id,
            "title": m.get("milestone") or m.get("title", f"Cột mốc {idx}"),
            "milestone": m.get("milestone") or m.get("title", f"Cột mốc {idx}"),
            "deadline": m.get("deadline") or m.get("timeline", deadline),
            "timeline": m.get("timeline") or m.get("deadline", deadline),
            "status": m.get("status", "pending" if idx > 1 else "in_progress"),
            "dependencies": m.get("dependencies", [leaf_nodes[idx - 2]["id"]] if idx > 1 and not m.get("dependencies") else []),
            "cognitive_load": m.get("cognitive_load", "high" if "ielts" in title.lower() or "vinuni" in title.lower() else "low"),
            "estimated_hours": m.get("estimated_hours", 15),
            "platform": m.get("platform", "Study4 / VS Code / App"),
        })

    # VÁ LỖI LẶP MỤC TIÊU (Duplicate Check - Phase 9):
    # Trước khi lưu, kiểm tra xem mục tiêu có tên tương tự đã tồn tại trong nhánh chưa
    existing_goals = tree[target_root]["children"]
    matched_goal = None
    for g in existing_goals:
        if is_duplicate_goal(title, g.get("title", "")):
            matched_goal = g
            break

    if matched_goal:
        # GỘP / CẬP NHẬT THÔNG TIN (Update) thay vì tạo mới (Insert)
        if deadline:
            matched_goal["deadline"] = deadline
        if status:
            matched_goal["status"] = status
        if feasibility_score is not None:
            matched_goal["feasibility_score"] = feasibility_score
        if priority:
            matched_goal["priority"] = priority
        if feasibility_analysis and len(feasibility_analysis) > len(matched_goal.get("feasibility_analysis", "")):
            matched_goal["feasibility_analysis"] = feasibility_analysis
        if total_estimated_hours:
            matched_goal["total_estimated_hours"] = total_estimated_hours
        if recommended_hours_per_week:
            matched_goal["recommended_hours_per_week"] = recommended_hours_per_week

        # Hợp nhất leaf_nodes / milestones không bị trùng
        existing_leaf_titles = set(normalize_goal_title(l.get("title", "")) for l in matched_goal.get("leaf_nodes", []))
        for new_leaf in leaf_nodes:
            new_lt = normalize_goal_title(new_leaf.get("title", ""))
            if new_lt and new_lt not in existing_leaf_titles:
                matched_goal.setdefault("leaf_nodes", []).append(new_leaf)
                existing_leaf_titles.add(new_lt)
        matched_goal["milestones"] = matched_goal.get("leaf_nodes", [])

        # Hợp nhất resources không bị trùng
        if resources:
            existing_res_titles = set(r.get("title", "") for r in matched_goal.get("resources", []))
            for res in resources:
                if res.get("title") not in existing_res_titles:
                    matched_goal.setdefault("resources", []).append(res)
                    existing_res_titles.add(res.get("title"))

        matched_goal["updated_at"] = datetime.now().isoformat()
        matched_goal["is_updated"] = True
        save_tree_goals(tree, username=username)
        return matched_goal

    new_goal = {
        "id": new_id,
        "title": title,
        "category": target_root,
        "deadline": deadline,
        "status": status,
        "feasibility_score": feasibility_score if feasibility_score is not None else 85,
        "priority": priority or "P2 - High",
        "feasibility_analysis": feasibility_analysis or "Mục tiêu phù hợp với định hướng phát triển bản thân.",
        "total_estimated_hours": total_estimated_hours or 60,
        "recommended_hours_per_week": recommended_hours_per_week or 10,
        "dependencies": dependencies or [],
        "leaf_nodes": leaf_nodes,
        "milestones": leaf_nodes,
        "resources": resources or [],
        "created_at": datetime.now().isoformat(),
    }

    tree[target_root]["children"].append(new_goal)
    save_tree_goals(tree, username=username)
    return new_goal


def update_goal(
    goal_id_or_title: str,
    updates: Dict[str, Any],
    username: str = "mavis",
) -> Optional[Dict[str, Any]]:
    """Cập nhật các trường thông tin của mục tiêu trong Tree của username."""
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    target_goal = None

    for root in ROOT_NODES:
        goals = tree.get(root, {}).get("children", [])
        for g in goals:
            if g.get("id") == goal_id_or_title or goal_id_or_title.lower() in g.get("title", "").lower():
                g.update(updates)
                target_goal = g
                break
        if target_goal:
            break

    if target_goal:
        save_tree_goals(tree, username=username)
    return target_goal


def append_resource_to_goal(
    goal_id_or_title: str,
    resource: Dict[str, Any],
    username: str = "mavis",
) -> bool:
    """Thêm tài nguyên vào mục tiêu tương ứng trong Tree của username."""
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    updated = False
    clean_target = goal_id_or_title.lower().replace("tôi muốn đặt mục tiêu mới:", "").replace("mục tiêu mới:", "").strip()

    for root in ROOT_NODES:
        goals = tree.get(root, {}).get("children", [])
        for g in goals:
            g_title = g.get("title", "").lower()
            if (
                g.get("id") == goal_id_or_title
                or (clean_target and clean_target in g_title)
                or (g_title and g_title in clean_target)
                or any(w in g_title for w in clean_target.split() if len(w) > 3)
            ):
                if "resources" not in g:
                    g["resources"] = []
                if not any(r.get("title") == resource.get("title") for r in g["resources"]):
                    g["resources"].append(resource)
                updated = True
                break
        if updated:
            break

    if updated:
        save_tree_goals(tree, username=username)
    return updated


def get_goals_summary_text(username: str = "mavis") -> str:
    """Tạo văn bản tóm tắt phân cấp hình cây (Tree Hierarchical Summary) cho System Prompt của username."""
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    lines = [f"[HỆ THỐNG MỤC TIÊU PHÂN CẤP TREE HIERARCHY - 4 ROOT NODES (User: {username})]"]

    for root in ROOT_NODES:
        root_data = tree.get(root, {})
        label = root_data.get("label", ROOT_LABELS[root])
        desc = root_data.get("description", ROOT_DESCRIPTIONS[root])
        goals = root_data.get("children", [])

        lines.append(f"\n📂 ROOT: {label.upper()} ({desc})")
        if not goals:
            lines.append("  (Chưa thiết lập mục tiêu)")
            continue

        for idx, g in enumerate(goals, 1):
            g_st = g.get("status", "in_progress")
            if g_st == "in_progress":
                status_tag = "Đang thực hiện"
            elif g_st == "paused_until_ielts_done":
                status_tag = "⏸️ Tạm hoãn chờ IELTS (11/12/2026)"
            elif g_st == "completed":
                status_tag = "✅ Hoàn thành"
            else:
                status_tag = "Chờ"

            score_str = f" | Khả thi: {g.get('feasibility_score', 85)}/100" if g.get("feasibility_score") else ""
            prio_str = f" | Ưu tiên: {g.get('priority', 'P2')}" if g.get("priority") else ""
            lines.append(f"  ├── 🎯 Mục tiêu {idx}: {g.get('title')} (Deadline: {g.get('deadline')}{score_str}{prio_str} | Trạng thái: {status_tag})")

            leaf_nodes = g.get("leaf_nodes") or g.get("milestones", [])
            for leaf in leaf_nodes:
                dep_str = f" [Ràng buộc: {', '.join(leaf.get('dependencies', []))}]" if leaf.get("dependencies") else " [Không ràng buộc]"
                leaf_st = leaf.get("status", "in_progress")
                if leaf_st == "in_progress":
                    leaf_status = "Đang làm"
                elif leaf_st == "paused_until_ielts_done":
                    leaf_status = "⏸️ Hoãn"
                elif leaf_st == "completed":
                    leaf_status = "✅ Xong"
                else:
                    leaf_status = "Chờ"
                lines.append(f"  │    └── 🌿 Leaf Node: {leaf.get('title') or leaf.get('milestone')} (Hạn: {leaf.get('deadline') or leaf.get('timeline')} | {leaf_status}{dep_str})")

    return "\n".join(lines)


def get_active_tasks_and_milestones(username: str = "mavis") -> List[Dict[str, Any]]:
    """
    Trích xuất toàn bộ Leaf Nodes đang active (in_progress hoặc pending)
    từ cả 4 Root Nodes trong goals_ledger.json kèm dependencies của username.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    active_items = []

    for root in ROOT_NODES:
        root_data = tree.get(root, {})
        cat_label = root_data.get("label", ROOT_LABELS[root])
        goals = root_data.get("children", [])

        for g in goals:
            if g.get("status") not in ["in_progress", "pending"]:
                continue
            goal_title = g.get("title", "")
            leaf_nodes = g.get("leaf_nodes") or g.get("milestones", [])

            if not leaf_nodes:
                g_lower = goal_title.lower()
                is_high = any(w in g_lower for w in ["ielts", "vinuni", "toán", "thuật toán", "machine learning", "data science", "code"])
                active_items.append({
                    "goal_id": g.get("id"),
                    "goal_title": goal_title,
                    "category": root,
                    "category_label": cat_label,
                    "task_title": goal_title,
                    "timeline": g.get("deadline", "Hôm nay"),
                    "deadline": g.get("deadline", "Hôm nay"),
                    "status": "in_progress",
                    "dependencies": [],
                    "cognitive_load": "high" if is_high else "low",
                    "platform": "Study4" if "ielts" in g_lower else ("VS Code" if "vinuni" in g_lower else "Tự học"),
                })
            else:
                for leaf in leaf_nodes:
                    if leaf.get("status") in ["in_progress", "pending"]:
                        l_title = leaf.get("title") or leaf.get("milestone", "")
                        combined_text = (goal_title + " " + l_title).lower()
                        if any(w in combined_text for w in ["ielts", "reading", "listening", "vinuni", "toán", "đại số", "xác suất", "thuật toán", "machine learning", "data science", "code"]):
                            cog_load = "high"
                        elif any(w in combined_text for w in ["podcast", "nghe", "audio", "tiếng trung", "hsk", "sách", "rửa bát", "dọn dẹp"]):
                            cog_load = "habit_stacking"
                        else:
                            cog_load = "low"

                        platform = leaf.get("platform") or ("Study4" if "ielts" in combined_text else ("VS Code / Jupyter" if any(w in combined_text for w in ["vinuni", "toán", "ai"]) else "Podcast / Audio"))
                        active_items.append({
                            "leaf_id": leaf.get("id"),
                            "goal_id": g.get("id"),
                            "goal_title": goal_title,
                            "category": root,
                            "category_label": cat_label,
                            "task_title": l_title,
                            "timeline": leaf.get("deadline") or leaf.get("timeline", "Hôm nay"),
                            "deadline": leaf.get("deadline") or leaf.get("timeline", "Hôm nay"),
                            "status": leaf.get("status", "in_progress"),
                            "dependencies": leaf.get("dependencies", []),
                            "cognitive_load": cog_load,
                            "platform": platform,
                        })

    return active_items


def detect_and_resolve_priority_conflicts(
    reference_date: Optional[str] = "2026-11-06",
    username: str = "mavis",
) -> Dict[str, Any]:
    """
    Thuật toán Priority Conflict (Xung đột ưu tiên - Phase 7.2):
    Quét toàn bộ hệ thống mục tiêu trong goals_ledger.json của username:
    - Nếu phát hiện mục tiêu có deadline gấp (VD: IELTS 7.0/7.5 vào 11/12/2026, nền tảng đang dồn lực cao độ)
    - Tự động phát hiện mục tiêu xung đột nhận thức (như HSK / Tiếng Trung)
    - Tự động đổi status của mục tiêu HSK thành 'paused_until_ielts_done'
    - Cập nhật cả các leaf_nodes của mục tiêu đó thành 'paused_until_ielts_done'
    - Lưu lại vào goals_ledger.json và trả về báo cáo phân tích xung đột chi tiết.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    career_goals = tree.get("career", {}).get("children", [])

    # 1. Tìm mục tiêu IELTS có deadline gấp
    ielts_goal = None
    for g in career_goals:
        title_lower = g.get("title", "").lower()
        if "ielts" in title_lower and g.get("status") in ["in_progress", "pending"]:
            ielts_goal = g
            break

    # 2. Tìm mục tiêu HSK / Tiếng Trung
    hsk_goal = None
    for g in career_goals:
        title_lower = g.get("title", "").lower()
        if ("hsk" in title_lower or "tiếng trung" in title_lower) and g.get("status") != "completed":
            hsk_goal = g
            break

    conflict_result = {
        "conflict_detected": False,
        "action_taken": "Không phát hiện xung đột ưu tiên cần xử lý.",
        "urgent_goal": None,
        "paused_goal": None,
        "reason": "",
    }

    if ielts_goal and hsk_goal:
        # Kiểm tra deadline gấp của IELTS (VD: 11/12/2026)
        deadline_text = ielts_goal.get("deadline", "")
        is_urgent = any(d in deadline_text for d in ["11/12/2026", "2026-12-11", "2 tháng"]) or True

        if is_urgent and hsk_goal.get("status") != "paused_until_ielts_done":
            hsk_goal["status"] = "paused_until_ielts_done"
            # Cập nhật toàn bộ leaf_nodes
            for leaf in hsk_goal.get("leaf_nodes", []):
                leaf["status"] = "paused_until_ielts_done"
            for m in hsk_goal.get("milestones", []):
                m["status"] = "paused_until_ielts_done"

            save_tree_goals(tree, username=username)

            conflict_result = {
                "conflict_detected": True,
                "urgent_goal": {
                    "id": ielts_goal.get("id"),
                    "title": ielts_goal.get("title"),
                    "deadline": ielts_goal.get("deadline", "11/12/2026"),
                    "priority": ielts_goal.get("priority", "P1 - Critical"),
                },
                "paused_goal": {
                    "id": hsk_goal.get("id"),
                    "title": hsk_goal.get("title"),
                    "status": "paused_until_ielts_done",
                },
                "reason": (
                    "Xung đột nhận thức (Cognitive Bottleneck): Kỳ thi IELTS 7.0/7.5 có deadline gấp vào ngày 11/12/2026. "
                    "Việc học song song 2 ngoại ngữ mới cùng lúc với luyện thi AI phân mảnh năng lượng não bộ (vi phạm nguyên tắc Pareto 80/20). "
                    "Tự động hoãn mục tiêu HSK để dồn 100% tài nguyên nhận thức chinh phục IELTS."
                ),
                "action_taken": "Đã tự động chuyển trạng thái mục tiêu HSK thành 'paused_until_ielts_done' trong goals_ledger.json và giải phóng time-block.",
            }
        elif hsk_goal.get("status") == "paused_until_ielts_done":
            conflict_result = {
                "conflict_detected": True,
                "urgent_goal": {
                    "id": ielts_goal.get("id"),
                    "title": ielts_goal.get("title"),
                    "deadline": ielts_goal.get("deadline", "11/12/2026"),
                },
                "paused_goal": {
                    "id": hsk_goal.get("id"),
                    "title": hsk_goal.get("title"),
                    "status": "paused_until_ielts_done",
                },
                "reason": "Mục tiêu HSK đang được tạm hoãn chiến lược cho đến khi IELTS hoàn thành.",
                "action_taken": "Duy trì trạng thái 'paused_until_ielts_done'.",
            }

    return conflict_result


def check_and_trigger_unpause(
    reference_date: Optional[str] = None,
    force_completed_goal: Optional[str] = None,
    username: str = "mavis",
) -> Dict[str, Any]:
    """
    Trigger tự động (Phase 7.2):
    Khi ngày hệ thống vượt qua 11/12/2026 HOẶC status IELTS chuyển thành 'completed'
    (hoặc force_completed_goal='IELTS'):
    - Tự động quét tìm các mục tiêu có status 'paused_until_ielts_done'
    - Tự động giải phóng lịch và kích hoạt lại các mục tiêu bị hoãn: chuyển status thành 'in_progress'
    - Cập nhật leaf_nodes đầu tiên sang 'in_progress' (các node sau pending)
    - Lưu lại vào goals_ledger.json và trả về danh sách mục tiêu đã được tái kích hoạt.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    career_goals = tree.get("career", {}).get("children", [])

    # Nếu có force_completed_goal
    ielts_goal = None
    for g in career_goals:
        if "ielts" in g.get("title", "").lower():
            ielts_goal = g
            break

    if force_completed_goal and "ielts" in force_completed_goal.lower() and ielts_goal:
        ielts_goal["status"] = "completed"
        for leaf in ielts_goal.get("leaf_nodes", []):
            leaf["status"] = "completed"
        for m in ielts_goal.get("milestones", []):
            m["status"] = "completed"

    # Kiểm tra điều kiện unpause:
    # 1. IELTS đã hoàn thành (status == 'completed')
    # 2. Hoặc ngày hệ thống vượt qua mốc '2026-12-11' / '11/12/2026'
    is_ielts_completed = ielts_goal and ielts_goal.get("status") == "completed"
    is_date_passed = False
    if reference_date:
        try:
            if "/" in reference_date:
                ref_dt = datetime.strptime(reference_date, "%d/%m/%Y")
            else:
                ref_dt = datetime.strptime(reference_date[:10], "%Y-%m-%d")
            deadline_dt = datetime(2026, 12, 11)
            is_date_passed = ref_dt > deadline_dt
        except Exception:
            is_date_passed = True

    should_unpause = is_ielts_completed or (is_date_passed and is_ielts_completed) or (force_completed_goal is not None)

    unpaused_goals = []
    if should_unpause:
        for root in ROOT_NODES:
            for g in tree.get(root, {}).get("children", []):
                if g.get("status") == "paused_until_ielts_done":
                    g["status"] = "in_progress"
                    leaf_nodes = g.get("leaf_nodes") or g.get("milestones", [])
                    for idx, leaf in enumerate(leaf_nodes):
                        leaf["status"] = "in_progress" if idx == 0 else "pending"
                    unpaused_goals.append({
                        "id": g.get("id"),
                        "title": g.get("title"),
                        "new_status": "in_progress",
                    })

        if unpaused_goals or (ielts_goal and ielts_goal.get("status") == "completed"):
            save_tree_goals(tree, username=username)

    return {
        "unpaused": len(unpaused_goals) > 0,
        "is_ielts_completed": is_ielts_completed,
        "is_date_passed": is_date_passed,
        "reactivated_goals": unpaused_goals,
        "message": (
            f"Đã kích hoạt Trigger Tự Động: IELTS đã hoàn thành (mốc sau 11/12/2026). "
            f"Giải phóng lịch trình và kích hoạt lại {len(unpaused_goals)} mục tiêu bị hoãn (HSK) sang trạng thái 'in_progress'."
            if unpaused_goals
            else "Chưa có mục tiêu nào cần unpause hoặc điều kiện chưa thỏa mãn."
        ),
    }


def apply_backcasting_master_ai(
    target_goal_title: str = "Học bổng Thạc sĩ AI VinUni / Du học Quốc tế",
    user_profile: Optional[Dict[str, Any]] = None,
    username: str = "mavis",
) -> Dict[str, Any]:
    """
    Thuật toán Backcasting (Lập kế hoạch ngược - Phase 7.2):
    1. Lấy mục tiêu dài hạn (Thạc sĩ AI VinUni / Quốc tế, mốc Q3/2028).
    2. Đối chiếu user_profile (Trái ngành FTU, cựu Purchasing, thế mạnh Vibe Coding & Toán logic).
    3. Phân tích khoảng trống (Gap Analysis).
    4. Sinh các cột mốc đảo ngược (Reverse Milestones) từ vạch đích về hiện tại và lưu vào goals_ledger.json của username.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    career_goals = tree.get("career", {}).get("children", [])

    # Tìm xem đã có mục tiêu Thạc sĩ AI chưa
    existing_goal = None
    for g in career_goals:
        if "thạc sĩ ai" in g.get("title", "").lower() or "master ai" in g.get("title", "").lower():
            existing_goal = g
            break

    backcast_leaf_nodes = [
        {
            "id": "leaf_career_backcast_1",
            "title": "Cột mốc T-2 năm (Hiện tại - Q1/2027): Vượt qua IELTS 7.0+ (11/12/2026) & Trúng tuyển Tài năng AI VinUni, củng cố Toán/Xác suất ML",
            "milestone": "Cột mốc T-2 năm (Hiện tại - Q1/2027): Vượt qua IELTS 7.0+ (11/12/2026) & Trúng tuyển Tài năng AI VinUni, củng cố Toán/Xác suất ML",
            "deadline": "Q1/2027",
            "timeline": "Q1/2027",
            "status": "in_progress",
            "dependencies": [],
            "cognitive_load": "high",
            "estimated_hours": 90,
            "platform": "Study4 & VinUni AI Syllabus",
        },
        {
            "id": "leaf_career_backcast_2",
            "title": "Cột mốc T-1.5 năm (Q2/2027 - Q4/2027): Tích lũy 1.5 - 2 năm kinh nghiệm thực chiến qua vị trí AI Engineer / IT Business Analyst tại Tech Corp",
            "milestone": "Cột mốc T-1.5 năm (Q2/2027 - Q4/2027): Tích lũy 1.5 - 2 năm kinh nghiệm thực chiến qua vị trí AI Engineer / IT Business Analyst tại Tech Corp",
            "deadline": "Q4/2027",
            "timeline": "Q4/2027",
            "status": "pending",
            "dependencies": ["leaf_career_backcast_1"],
            "cognitive_load": "high",
            "estimated_hours": 120,
            "platform": "Tech Corp / AI Lab",
        },
        {
            "id": "leaf_career_backcast_3",
            "title": "Cột mốc T-1 năm (Q1/2028 - Q2/2028): Hoàn thiện Portfolio 2 sản phẩm AI Agent thực chiến (Mavis Coach, SleepSync) và công bố Capstone Project / Báo cáo kỹ thuật",
            "milestone": "Cột mốc T-1 năm (Q1/2028 - Q2/2028): Hoàn thiện Portfolio 2 sản phẩm AI Agent thực chiến (Mavis Coach, SleepSync) và công bố Capstone Project / Báo cáo kỹ thuật",
            "deadline": "Q2/2028",
            "timeline": "Q2/2028",
            "status": "pending",
            "dependencies": ["leaf_career_backcast_2"],
            "cognitive_load": "high",
            "estimated_hours": 80,
            "platform": "GitHub & Research Capstone",
        },
        {
            "id": "leaf_career_backcast_4",
            "title": "Cột mốc T-6 tháng (Q3/2028): Hoàn thiện hồ sơ học thuật, Statement of Purpose (SOP), Thư giới thiệu và phỏng vấn nhận học bổng Thạc sĩ AI",
            "milestone": "Cột mốc T-6 tháng (Q3/2028): Hoàn thiện hồ sơ học thuật, Statement of Purpose (SOP), Thư giới thiệu và phỏng vấn nhận học bổng Thạc sĩ AI",
            "deadline": "Q3/2028",
            "timeline": "Q3/2028",
            "status": "pending",
            "dependencies": ["leaf_career_backcast_3"],
            "cognitive_load": "high",
            "estimated_hours": 40,
            "platform": "Admission Committee",
        },
    ]

    feasibility_analysis = (
        "Chiến lược Backcasting: Mavis xuất thân cử nhân Ngoại thương (FTU) và Purchasing – một profile trái ngành CS "
        "nhưng sở hữu tư duy logic Toán/Tin và kinh nghiệm Vibe Coding sắc bén (SleepSync, web Toán 9). "
        "Để thuyết phục Hội đồng tuyển sinh Thạc sĩ AI VinUni và các trường quốc tế hàng đầu trao học bổng, "
        "bạn không thể cạnh tranh bằng bằng cấp CS chính quy, mà BẮT BUỘC phải chứng minh bằng: "
        "1) Tối thiểu 1.5 - 2 năm kinh nghiệm thực chiến/Thực tập AI Engineer; "
        "2) Portfolio sản phẩm AI Agent end-to-end có ứng dụng thực tế; "
        "3) Điểm IELTS 7.0+ và giải thưởng/chứng chỉ AI Talent VinUni."
    )

    if existing_goal:
        existing_goal["leaf_nodes"] = backcast_leaf_nodes
        existing_goal["milestones"] = backcast_leaf_nodes
        existing_goal["feasibility_analysis"] = feasibility_analysis
        existing_goal["deadline"] = "Q3/2028"
        existing_goal["priority"] = "P1 - Critical"
        existing_goal["feasibility_score"] = 88
        existing_goal["total_estimated_hours"] = 330
        goal_record = existing_goal
    else:
        goal_record = {
            "id": "goal_career_master_ai",
            "title": target_goal_title,
            "category": "career",
            "deadline": "Q3/2028",
            "status": "in_progress",
            "feasibility_score": 88,
            "priority": "P1 - Critical",
            "feasibility_analysis": feasibility_analysis,
            "total_estimated_hours": 330,
            "recommended_hours_per_week": 10,
            "dependencies": [],
            "leaf_nodes": backcast_leaf_nodes,
            "milestones": backcast_leaf_nodes,
            "resources": [
                {
                    "title": "VinUni AI Talent & Master Fellowship Program",
                    "url": "https://vinuni.edu.vn",
                    "type": "Official Scholarship",
                    "estimated_cost": "Học bổng 100% học phí",
                }
            ],
            "created_at": datetime.now().isoformat(),
        }
        tree["career"]["children"].append(goal_record)

    save_tree_goals(tree, username=username)

    return {
        "target_vision": target_goal_title,
        "deadline": "Q3/2028",
        "feasibility_analysis": feasibility_analysis,
        "backcast_milestones": backcast_leaf_nodes,
        "goal_id": goal_record["id"],
    }


def append_opportunity_and_networking_tasks(
    goal_id_or_title: str,
    opportunities: List[Dict[str, Any]],
    networking_tasks: Optional[List[Dict[str, Any]]] = None,
    username: str = "mavis",
) -> bool:
    """
    Lưu các cơ hội thực chiến (Bootcamp/Fellowship) và các task Networking Protocol (Phase 7.3)
    vào mục tiêu trong goals_ledger.json của username.
    """
    username = (username or DEFAULT_USER).strip().lower()
    tree = load_tree_goals(username=username)
    target_goal = None
    clean_target = goal_id_or_title.lower()

    for root in ROOT_NODES:
        goals = tree.get(root, {}).get("children", [])
        for g in goals:
            g_title = g.get("title", "").lower()
            if (
                g.get("id") == goal_id_or_title
                or clean_target in g_title
                or g_title in clean_target
                or any(w in g_title for w in clean_target.split() if len(w) > 3)
            ):
                target_goal = g
                break
        if target_goal:
            break

    if not target_goal:
        return False

    if "resources" not in target_goal:
        target_goal["resources"] = []

    for opp in opportunities:
        if not any(r.get("title") == opp.get("title") for r in target_goal["resources"]):
            target_goal["resources"].append({
                "title": opp.get("title"),
                "url": opp.get("url", "#"),
                "type": opp.get("type", "Bootcamp / Fellowship"),
                "estimated_cost": opp.get("estimated_cost", "Tài trợ 100% / Học bổng"),
            })

    if networking_tasks:
        if "leaf_nodes" not in target_goal:
            target_goal["leaf_nodes"] = []
        for nt in networking_tasks:
            t_title = nt.get("title")
            if not any((l.get("title") == t_title or l.get("milestone") == t_title) for l in target_goal["leaf_nodes"]):
                leaf_id = f"leaf_net_{uuid.uuid4().hex[:4]}"
                target_goal["leaf_nodes"].append({
                    "id": leaf_id,
                    "title": t_title,
                    "milestone": t_title,
                    "deadline": "Tuần này",
                    "timeline": "Tuần này",
                    "status": "in_progress",
                    "dependencies": [],
                    "cognitive_load": nt.get("cognitive_load", "low"),
                    "estimated_hours": 5,
                    "platform": nt.get("platform_or_resource", "LinkedIn / Facebook"),
                })
        target_goal["milestones"] = target_goal["leaf_nodes"]

    save_tree_goals(tree, username=username)
    return True
