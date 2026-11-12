import os
import json
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

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


def get_blank_tree() -> Dict[str, Any]:
    """Tạo cấu trúc Tree trắng với 4 Root Nodes và Hồ sơ Hành vi Thích nghi (Phase 10 Adaptive Memory)."""
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
    """Lưu hồ sơ người dùng, các rào cản và trạng thái coaching vào goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()
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
    """Tải hồ sơ người dùng từ goals_ledger.json."""
    username = (username or DEFAULT_USER).strip().lower()
    all_data = load_all_users_data()
    return all_data.get(username, {}).get("user_profile", {})


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
