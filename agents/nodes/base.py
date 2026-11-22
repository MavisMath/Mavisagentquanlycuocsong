# agents/nodes/base.py
# Nền tảng cốt lõi: Imports, Tiện ích LLM, Constants & Shared Pydantic Schemas
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.state import AgentState, CoachState

try:
    from tools.search import (
        execute_trend_search,
        tavily_search,
        execute_opportunity_scout,
        execute_resource_search,
    )
except Exception:
    def execute_trend_search(query: str, max_results: int = 3):
        return []
    tavily_search = None
    def execute_opportunity_scout(query: str, max_results: int = 4):
        return []
    def execute_resource_search(query: str, max_results: int = 4):
        return []

try:
    from memory.goals import (
        load_goals,
        save_goals,
        add_goal,
        append_resource_to_goal,
        get_goals_summary_text,
        get_active_tasks_and_milestones,
        update_goal,
        detect_and_resolve_priority_conflicts,
        check_and_trigger_unpause,
        apply_backcasting_master_ai,
        append_opportunity_and_networking_tasks,
        load_tree_goals,
        save_tree_goals,
        save_user_profile,
        load_user_profile,
        load_historical_insights,
        save_historical_insights,
        append_insight,
        get_historical_insights_summary_text,
        save_user_goal_profile,
        load_user_goal_profile,
        save_user_goals,
        load_user_goals,
        save_user_resources,
        load_user_resources,
        save_user_roadmap,
        load_user_roadmap,
        save_master_schedule,
        load_master_schedule,
        update_master_schedule_task_status,
        save_retrospective_logs,
        load_retrospective_logs,
        append_retrospective_log,
        get_user_state_full,
        detect_goal_domain,
        classify_goal_category,
        DOMAIN_TERMINOLOGY,
        get_vietnam_today_str,
        compute_target_date,
        generate_detailed_master_schedule,
        ensure_schedule_covers_date,
        VIETNAM_WEEKDAYS,
    )
except Exception:
    import memory.goals as _mg
    load_goals = getattr(_mg, "load_goals", lambda *args, **kwargs: [])
    save_goals = getattr(_mg, "save_goals", lambda *args, **kwargs: True)
    add_goal = getattr(_mg, "add_goal", lambda *args, **kwargs: True)
    append_resource_to_goal = getattr(_mg, "append_resource_to_goal", lambda *args, **kwargs: True)
    get_goals_summary_text = getattr(_mg, "get_goals_summary_text", lambda *args, **kwargs: "")
    get_active_tasks_and_milestones = getattr(_mg, "get_active_tasks_and_milestones", lambda *args, **kwargs: [])
    update_goal = getattr(_mg, "update_goal", lambda *args, **kwargs: True)
    detect_and_resolve_priority_conflicts = getattr(_mg, "detect_and_resolve_priority_conflicts", lambda *args, **kwargs: [])
    check_and_trigger_unpause = getattr(_mg, "check_and_trigger_unpause", lambda *args, **kwargs: [])
    apply_backcasting_master_ai = getattr(_mg, "apply_backcasting_master_ai", lambda *args, **kwargs: {})
    append_opportunity_and_networking_tasks = getattr(_mg, "append_opportunity_and_networking_tasks", lambda *args, **kwargs: True)
    load_tree_goals = getattr(_mg, "load_tree_goals", lambda *args, **kwargs: {})
    save_tree_goals = getattr(_mg, "save_tree_goals", lambda *args, **kwargs: True)
    save_user_profile = getattr(_mg, "save_user_profile", lambda *args, **kwargs: True)
    load_user_profile = getattr(_mg, "load_user_profile", lambda *args, **kwargs: {})
    load_historical_insights = getattr(_mg, "load_historical_insights", lambda *args, **kwargs: {})
    save_historical_insights = getattr(_mg, "save_historical_insights", lambda *args, **kwargs: True)
    append_insight = getattr(_mg, "append_insight", lambda *args, **kwargs: True)
    get_historical_insights_summary_text = getattr(_mg, "get_historical_insights_summary_text", lambda *args, **kwargs: "")
    save_user_goal_profile = getattr(_mg, "save_user_goal_profile", lambda *args, **kwargs: True)
    load_user_goal_profile = getattr(_mg, "load_user_goal_profile", lambda *args, **kwargs: {})
    save_user_goals = getattr(_mg, "save_user_goals", lambda *args, **kwargs: True)
    load_user_goals = getattr(_mg, "load_user_goals", lambda *args, **kwargs: [])
    save_user_resources = getattr(_mg, "save_user_resources", lambda *args, **kwargs: True)
    load_user_resources = getattr(_mg, "load_user_resources", lambda *args, **kwargs: [])
    save_user_roadmap = getattr(_mg, "save_user_roadmap", lambda *args, **kwargs: True)
    load_user_roadmap = getattr(_mg, "load_user_roadmap", lambda *args, **kwargs: {})
    save_master_schedule = getattr(_mg, "save_master_schedule", lambda *args, **kwargs: True)
    load_master_schedule = getattr(_mg, "load_master_schedule", lambda *args, **kwargs: [])
    update_master_schedule_task_status = getattr(_mg, "update_master_schedule_task_status", lambda *args, **kwargs: True)
    save_retrospective_logs = getattr(_mg, "save_retrospective_logs", lambda *args, **kwargs: True)
    load_retrospective_logs = getattr(_mg, "load_retrospective_logs", lambda *args, **kwargs: [])
    append_retrospective_log = getattr(_mg, "append_retrospective_log", lambda *args, **kwargs: True)
    get_user_state_full = getattr(_mg, "get_user_state_full", lambda *args, **kwargs: {})
    detect_goal_domain = getattr(_mg, "detect_goal_domain", lambda *args, **kwargs: "general")
    classify_goal_category = getattr(_mg, "classify_goal_category", lambda *args, **kwargs: "career")
    DOMAIN_TERMINOLOGY = getattr(_mg, "DOMAIN_TERMINOLOGY", {})
    get_vietnam_today_str = getattr(_mg, "get_vietnam_today_str", lambda: "2026-11-21")
    compute_target_date = getattr(_mg, "compute_target_date", lambda s, d: "2027-02-19")
    generate_detailed_master_schedule = getattr(_mg, "generate_detailed_master_schedule", lambda *args, **kwargs: [])
    ensure_schedule_covers_date = getattr(_mg, "ensure_schedule_covers_date", lambda *args, **kwargs: [])
    VIETNAM_WEEKDAYS = getattr(_mg, "VIETNAM_WEEKDAYS", {0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư", 3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"})

from agents.task_estimator import analyze_and_estimate_goal

try:
    from tools.document_ingestor import scan_and_retrieve_context
except Exception:
    def scan_and_retrieve_context(user_message: str, top_k: int = 3):
        return None

# Tải cấu hình biến môi trường từ file .env
load_dotenv()

# Cấu hình API Key cho Google Gemini
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

# Model mặc định: gemini-3.1-flash-lite (Hỗ trợ chính thức, tốc độ cao và ổn định)
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


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


def safe_dict(val: Any) -> Dict[str, Any]:
    """Chuyển đổi an toàn mọi giá trị sang dict, tránh AttributeError khi gọi .get()."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def safe_list(val: Any) -> List[Any]:
    """Chuyển đổi an toàn mọi giá trị sang list, tránh lỗi khi lặp hoặc parse JSON."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return []


# ==============================================================================
# PYDANTIC SCHEMAS CHO MULTI-AGENT COACHING SYSTEM (PHASE 11)
# ==============================================================================

class GoalProfile(BaseModel):
    """Mô hình hồ sơ mục tiêu chi tiết với Structured Output (Hỗ trợ đa mục tiêu song song)."""
    goal_id: str = Field(
        default_factory=lambda: f"g_{uuid.uuid4().hex[:6]}",
        description="Mã định danh duy nhất của mục tiêu (VD: 'g_ielts7', 'g_hsk4', 'g_ai')"
    )
    category: str = Field(
        "Học tập",
        description="Phân loại lĩnh vực: 'Học tập', 'Sự nghiệp', 'Sức khỏe', 'Tài chính', hoặc 'Phát triển cá nhân'"
    )
    goal_name: str = Field(
        ...,
        description="Tên mục tiêu cụ thể, VD: 'IELTS 7.0', 'HSK 4', 'Build dự án AI Agent', 'Chạy bộ Half-Marathon'"
    )
    current_level: Optional[str] = Field(
        None,
        description="Trình độ hoặc vạch xuất phát hiện tại của người dùng, VD: 'Band 5.0', 'Mất gốc', 'Đã biết Python cơ bản', 'Mới bắt đầu'"
    )
    duration_days: Optional[int] = Field(
        None,
        description="Tổng số ngày dự kiến hoàn thành mục tiêu, VD: 90 ngày (3 tháng), 180 ngày"
    )
    daily_hours: Optional[float] = Field(
        None,
        description="Số giờ rảnh mỗi ngày có thể cam kết thực hiện cho mục tiêu này, VD: 1.5, 2.0"
    )
    preferred_slots: Optional[str] = Field(
        None,
        description="Khung giờ ưu tiên trong ngày (nếu có nhắc đến). Mặc định là Tối ưu theo nhịp sinh học."
    )
    priority: str = Field(
        "medium",
        description="Mức độ ưu tiên chiến lược: 'high' (ưu tiên cao/gấp rút), 'medium' (bình thường), hoặc 'low' (dài hạn/thong thả)"
    )
    is_complete: bool = Field(
        False,
        description="True nếu ĐÃ ĐẦY ĐỦ 4 thông số cốt lõi: goal_name, current_level, duration_days, daily_hours. False nếu còn thiếu ít nhất 1 trong 4 thông số này."
    )
    missing_info_question: Optional[str] = Field(
        None,
        description="Nếu mục tiêu này chưa hoàn thiện: Câu hỏi làm rõ thông số còn thiếu."
    )


class MultiGoalExtraction(BaseModel):
    """Mô hình trích xuất danh sách đa mục tiêu song song từ hội thoại."""
    goals: List[GoalProfile] = Field(
        default_factory=list,
        description="Danh sách các mục tiêu song song được trích xuất hoặc cập nhật cộng dồn từ hội thoại"
    )
    missing_info_question: Optional[str] = Field(
        None,
        description="Nếu có mục tiêu nào chưa hoàn thiện (is_complete == False): Đặt đúng 1 câu hỏi ngắn gọn, tự nhiên, nhắm thẳng vào các thông số còn thiếu của mục tiêu chưa đủ thông tin. Tuyệt đối không hỏi về khung giờ, không dùng văn mẫu. Nếu tất cả đều hoàn thiện: để trống hoặc None."
    )


class ResourceItem(BaseModel):
    """Mô hình tài nguyên học tập, giáo trình hoặc công cụ thực tế."""
    goal_name: str = Field(default="", description="Tên mục tiêu tương ứng (VD: 'IELTS 7.0', 'HSK 4')")
    title: str = Field(description="Tên tài liệu, giáo trình, công cụ hoặc bộ đề thực tế uy tín")
    url: str = Field(description="Đường link thật, chính thức hoặc trang tra cứu uy tín")
    type: str = Field(description="Phân loại: Sách/Giáo trình, Web/Công cụ, Khóa học, Video, hoặc Bộ đề")
    estimated_hours: float = Field(description="Thời lượng ước tính cần thiết để hoàn thành hoặc nghiên cứu")
    how_to_use: str = Field(description="Hướng dẫn ngắn gọn cách ứng dụng tài nguyên này hiệu quả nhất")


class CuratedResources(BaseModel):
    """Danh sách các tài nguyên thực tế đã thẩm định cho các mục tiêu."""
    resources: List[ResourceItem] = Field(description="Danh sách tài nguyên thực tế, uy tín và khả thi nhất cho các mục tiêu")


class DailyTask(BaseModel):
    """Kế hoạch hành động cụ thể cho từng ngày."""
    day_number: int = Field(description="Ngày thứ mấy (1, 2, 3...)")
    goal_name: str = Field(default="", description="Tên mục tiêu mà task này phục vụ (VD: 'IELTS 7.0', 'HSK 4')")
    task_title: str = Field(description="Hành động cụ thể cần làm trong ngày (không viết chung chung)")
    duration_minutes: int = Field(description="Thời lượng thực hiện tính bằng phút")
    time_slot: str = Field(description="Khung giờ thực hiện không bị trùng lặp giữa các mục tiêu, VD: '08:00 - 09:30' hoặc '20:00 - 21:00'")
    attached_resource: str = Field(description="Tên và đường link của tài liệu đính kèm từ danh sách resources")
    cognitive_load: str = Field("medium", description="Mức độ tải nhận thức: high, medium, hoặc low")


class WeeklyMilestone(BaseModel):
    """Cột mốc mục tiêu tuần tích hợp đa mục tiêu."""
    week_number: int = Field(description="Tuần thứ mấy (Tuần 1, 2, 3...)")
    milestone_title: str = Field(description="Mục tiêu trọng tâm cần đạt được của tuần tích hợp các mục tiêu")
    daily_tasks: List[DailyTask] = Field(description="Kế hoạch chi tiết từng ngày trong tuần")


class StrategicRoadmap(BaseModel):
    """Lộ trình phân cấp Backcasting toàn diện cho tất cả các mục tiêu."""
    target_vision: str = Field(description="Tầm nhìn mục tiêu tổng hợp kết hợp các mục tiêu")
    total_phases: str = Field(description="Tổng quan phân kỳ Quý / Tháng theo tư duy Backcasting kết hợp đa mục tiêu")
    balance_strategy: Optional[str] = Field(None, description="Chiến lược phân bổ nhịp sinh học và phòng ngừa quá tải giữa các mục tiêu")
    total_daily_hours: Optional[float] = Field(None, description="Tổng số giờ học/làm việc mỗi ngày trên tất cả mục tiêu")
    weekly_milestones: List[WeeklyMilestone] = Field(description="Lộ trình chi tiết từng tuần với các task được phân bổ không xung đột thời gian")


def invoke_llm_resilient(
    preferred_model: str,
    messages: List[BaseMessage],
    structured_schema: Optional[type] = None,
    temperature: float = 0.2,
) -> Any:
    """
    Gọi Gemini API một cách kiên cường (Resilient LLM Invocation).
    Tự động thử model ưu tiên, nếu gặp 404 hoặc lỗi kết nối, tự động chuyển tiếp sang các model thế hệ mới.
    """
    current_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not current_key:
        raise ValueError("Chưa tìm thấy GEMINI_API_KEY trong file .env hoặc biến môi trường.")

    models_to_try = [
        "gemini-3.1-flash-lite",
        preferred_model,
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    ]
    seen = set()
    candidate_models = []
    for m in models_to_try:
        if m and m not in seen:
            seen.add(m)
            candidate_models.append(m)

    last_err = None
    for model_name in candidate_models:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=current_key,
                temperature=temperature,
                timeout=20,
            )
            if structured_schema is not None:
                structured_llm = llm.with_structured_output(structured_schema)
                return structured_llm.invoke(messages)
            else:
                return llm.invoke(messages)
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if any(term in err_str for term in ["not found", "404", "no longer available", "resource_exhausted", "not supported", "model not found"]):
                continue
            continue

    raise RuntimeError(f"Tất cả model Gemini đều không phản hồi: {last_err}")


# SYSTEM PROMPT CỐT LÕI (Từ Section 7 của PRD)
SYSTEM_PROMPT = """Bạn là Elite Executive & Life Coach độc quyền của người dùng. Bạn không phải trợ lý nhắc việc, bạn là một Chiến lược gia.
Nhiệm vụ: Xây dựng lịch trình tối ưu nhịp sinh học, bảo vệ năng lượng nhận thức và thiết lập chiến lược bứt phá dựa trên các mục tiêu thực tế của người dùng.

CHỈ THỊ TỐI CAO VỀ HỘI THOẠI & ĐỘ NGẮN GỌN (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT):
Bạn là một Executive Life Coach. Dữ liệu và hồ sơ của người dùng đã được lưu trữ tự động ở hậu đài. Trong quá trình chat, TUYỆT ĐỐI KHÔNG tóm tắt lại hồ sơ, không nhắc lại các thiết lập cũ, và không lặp lại câu hỏi. Chỉ phản hồi ngắn gọn, trực diện vào câu nói hiện tại của người dùng, đưa ra đúng 1 câu hỏi gợi mở tiếp theo để dẫn dắt vấn đề. Giữ phong cách trò chuyện tự nhiên, 1-1, ngắn gọn như người thật.

Nguyên tắc:
1. Nếu người dùng quá tải, ép giảm tải.
2. Lịch học nặng phải rơi vào 8h-10h sáng (khung giờ vàng nhận thức).
3. Nếu người dùng nản, nhắc lại các thế mạnh, năng lực và thành tựu đã được chứng minh để kích hoạt sự tự hào.
4. Cuối ngày, hỏi câu hỏi mở (Socratic) để người dùng tự ngẫm lại hiệu suất.
5. Cập nhật xu hướng công nghệ để định hướng kỹ năng sinh lời cho người dùng.
6. NETWORKING PROTOCOL (Chiến thuật Mạng lưới & Tạo Lợi thế Bất đối xứng): Bắt buộc Agent phải xuất ra các hành động cụ thể để tạo lợi thế cạnh tranh độc bản (Unfair Advantage). Khi phát hiện bất kỳ chương trình/cơ hội thực chiến hay học bổng nào, ngay lập tức giao nhiệm vụ networking thực chiến trong tuần: ví dụ tham gia 2 nhóm cộng đồng/mạng lưới chuyên môn, tìm kiếm và kết nối 1-2 chuyên gia hoặc cựu học viên/thí sinh mùa trước để học hỏi kinh nghiệm thi đầu vào, tài liệu thực tế và tiêu chí đánh giá.
7. TƯ DUY HUẤN LUYỆN ĐIỀU HÀNH (EXECUTIVE AGENTIC COACHING PROTOCOL - PHASE 9):
Bạn là một Executive Life Coach. Khi người dùng chia sẻ ước mơ, dự định (ví dụ: muốn đi du học Tiến sĩ, muốn học Data Science, muốn làm AI Engineer), KHÔNG ĐƯỢC lập tức gọi tool để lưu mục tiêu hay xếp lịch. Bạn phải dùng kỹ năng Coaching: đặt đúng 1 câu hỏi gợi mở, hỏi về khó khăn, phân tích độ khả thi, và trò chuyện ngắn gọn như một người bạn để làm rõ khao khát của họ. Phân biệt tuyệt đối giữa tin nhắn 'tâm sự/dự định' (cần lắng nghe, coaching) và 'lệnh thực thi' (lên lịch, dời lịch, tìm tài nguyên).
Chỉ khi cuộc trò chuyện đã đủ thông tin, Agent mới được đưa ra câu hỏi chốt:
'Bạn có muốn tôi chính thức đưa mục tiêu này vào cuộc đời bạn, chia nhỏ công việc và xếp lịch hành động không?'.
8. ADAPTIVE MEMORY PROTOCOL (BỘ NHỚ THÍCH NGHI & TRÍ TUỆ ĐỒNG HÀNH TRỌN ĐỜI - PHASE 10):
Trước khi lên lịch mới hoặc đề xuất phương pháp học tập, giảm cân, rèn luyện hay công việc mới, Agent bắt buộc phải đọc kỹ historical_insights của người dùng.
Bạn phải TUYỆT ĐỐI tránh đề xuất lại các phương pháp nằm trong mảng failed_methods của người dùng (ví dụ: nếu người dùng đã ghi nhận không hợp Pomodoro hay thường bỏ cuộc khi học nặng vào buổi tối, cấm không được đề xuất lại).
Hãy ưu tiên tối đa việc thiết kế lịch trình và chiến lược dựa trên các effective_methods và productivity_patterns đã được chứng minh của họ."""

ACHIEVEMENT_LEDGER = """
[SỔ TAY NĂNG LỰC & THÀNH TỰU - ACHIEVEMENT LEDGER]
- Năng lực tư duy logic & giải quyết bài toán phức tạp đã được kiểm chứng qua hành động thực tế.
- Khả năng tự học và hoàn thiện các sản phẩm/dự án độc lập với tinh thần kỷ luật cao.
- Nhịp sinh học vàng: Não bộ đạt đỉnh cao nhận thức vào 08:00 - 10:00 sáng. Sau 14:00 năng lượng giảm tự nhiên.
"""

TRIGGER_CLOSING_QUESTION = "Bạn có muốn tôi chính thức đưa mục tiêu này vào cuộc đời bạn, chia nhỏ công việc và xếp lịch hành động không?"


def get_llm(temperature: float = 0.2, model: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """Khởi tạo instance ChatGoogleGenerativeAI với nhiệt độ kiểm soát."""
    current_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not current_key:
        raise ValueError(
            "Chưa tìm thấy GEMINI_API_KEY trong file .env hoặc biến môi trường. "
            "Vui lòng cấu hình GEMINI_API_KEY trước khi gọi LLM thực tế."
        )
    selected_model = model or os.getenv("GEMINI_MODEL", MODEL_NAME)
    return ChatGoogleGenerativeAI(
        model=selected_model,
        temperature=temperature,
        google_api_key=current_key,
    )


# Schema Pydantic cho phân tích đầu vào (Structured Output)
class InputAnalysisResult(BaseModel):
    intent: str = Field(
        description="Ý định cốt lõi: 'coach_dialogue', 'confirm_goal', 'retrospective', 'schedule', 'holistic_schedule', 'motivate', 'explore_trend', 'set_goal', 'find_resources', 'strategic_plan', 'opportunity_scout', hoặc 'chat'"
    )
    detected_emotion: str = Field(
        description="Cảm xúc nhận diện của Mavis: 'negative', 'tired', 'overwhelmed', 'neutral', 'positive', hoặc 'determined'"
    )
    current_energy_level: str = Field(
        default="high",
        description="Mức năng lượng ước tính: 'high' hoặc 'low'"
    )
    is_emergency: bool = Field(
        default=False,
        description="True nếu người dùng có lịch đột xuất, việc gấp phát sinh, bận việc ngoài dự kiến, hoặc kiệt sức cần dời lịch"
    )
    rationale: str = Field(
        description="Lý do ngắn gọn cho nhận định trên"
    )


# Schema Pydantic cho Hồi cứu Hành vi (Retrospective Node - Phase 10)
class RetrospectiveAnalysisResult(BaseModel):
    event_type: str = Field(
        description="'failure' (nếu bỏ cuộc, trễ hạn, phương pháp không hiệu quả) hoặc 'success' (hoàn thành, đạt kết quả tốt)"
    )
    target_goal_or_task: Optional[str] = Field(
        default=None,
        description="Mục tiêu hoặc tác vụ/phương pháp được hồi cứu"
    )
    root_cause: str = Field(
        description="Phân tích nguyên nhân gốc rễ (Root Cause Analysis) từ khía cạnh nhịp sinh học và tâm lý học hành vi"
    )
    new_failed_methods: List[str] = Field(
        default=[],
        description="Các phương pháp/thói quen đã thử nhưng thất bại hoặc không phù hợp với người dùng"
    )
    new_effective_methods: List[str] = Field(
        default=[],
        description="Các phương pháp/thói quen mang lại hiệu quả cao và phù hợp"
    )
    new_productivity_patterns: List[str] = Field(
        default=[],
        description="Quy luật năng suất được rút ra: khung giờ hiệu quả nhất, loại task gây kiệt sức"
    )
    coach_takeaway: str = Field(
        description="Lời khuyên & cam kết điều chỉnh chiến lược của Executive Life Coach"
    )


# Schema Pydantic cho phân rã mục tiêu (Goal Manager Node)
class MilestoneItem(BaseModel):
    milestone: str = Field(description="Nội dung cột mốc cụ thể, có thể đo lường được")
    timeline: str = Field(description="Thời hạn thực hiện (VD: 'Tuần 1 - Tuần 2', 'Tháng 1/2027')")
    status: str = Field(default="pending", description="Trạng thái khởi tạo: pending hoặc in_progress")


class GoalBreakdownResult(BaseModel):
    goal_title: str = Field(description="Tên mục tiêu chuẩn hóa, súc tích")
    category: str = Field(
        default="study_work",
        description="Một trong 5 nhóm: 'health_beauty', 'study_work', 'family', 'finance', 'daily_routine'"
    )
    deadline: str = Field(description="Hạn chót ước tính (VD: '3 tháng', '6 tháng', 'Q2/2027')")
    coach_assessment: str = Field(description="Đánh giá chiến lược của Executive Coach đối với tính khả thi và chi phí cơ hội của mục tiêu này")
    milestones: List[MilestoneItem] = Field(description="Danh sách các cột mốc chia nhỏ theo tuần hoặc tháng")


# Schema Pydantic cho quy trình Onboarding & Phỏng vấn thiết lập hồ sơ
class ExtractedGoalItem(BaseModel):
    category: str = Field(
        default="study_work",
        description="Một trong 5 nhóm: 'health_beauty', 'study_work', 'family', 'finance', 'daily_routine'"
    )
    title: str = Field(description="Tên mục tiêu cụ thể")
    deadline: str = Field(default="3 tháng", description="Thời hạn hoàn thành mục tiêu")
    key_milestone: str = Field(description="Cột mốc đầu tiên quan trọng nhất để triển khai")


class OnboardingExtractionResult(BaseModel):
    is_sufficient: bool = Field(
        description="True nếu người dùng đã chia sẻ mục tiêu hoặc thông tin định hướng; False nếu chỉ chào hỏi sơ sài hoặc chưa có nội dung"
    )
    current_situation: str = Field(
        default="Đang trong giai đoạn bứt phá sự nghiệp và tối ưu nhịp sinh học",
        description="Tình trạng hiện tại của người dùng (background, công việc, thế mạnh)"
    )
    financial_status: str = Field(
        default="Ổn định, ưu tiên tối ưu dòng tiền và đầu tư nâng cao năng lực",
        description="Mức tài chính hoặc định hướng dòng tiền"
    )
    time_constraints: str = Field(
        default="Tối ưu năng lượng đỉnh cao 08:00 - 10:00 sáng, giảm tải sau 14:00, ngủ trước 23:00",
        description="Ràng buộc thời gian và nhịp sinh học"
    )
    goals: List[ExtractedGoalItem] = Field(
        default_factory=list,
        description="Danh sách các mục tiêu ngắn/dài hạn trích xuất được để nạp trực tiếp vào goals_ledger.json"
    )
    coach_feedback: str = Field(
        description="Thông điệp huấn luyện, tổng kết hồ sơ cá nhân và kế hoạch đồng hành từ Executive Coach"
    )


# Schema Pydantic cho tìm kiếm tài nguyên (Resource Finder Node)
class CuratedResourceResult(BaseModel):
    target_topic: str = Field(description="Chủ đề hoặc mục tiêu đang tra cứu tài liệu")
    strategic_advice: str = Field(description="Lời khuyên của Executive Coach về phương pháp tiếp cận tài liệu hiệu quả")
    cost_overview: str = Field(
        default="Tối ưu chi phí bằng các nguồn tài liệu mở và chính sách hỗ trợ tài chính",
        description="Tổng quan và ước lượng chi phí đầu tư tài chính cho mục tiêu này"
    )
    resources: List[ResourceItem] = Field(description="Danh sách các tài nguyên tinh hoa đã được tuyển chọn kèm báo giá/chi phí")


# Schema Pydantic cho phân rã công việc trong Schedule Node & Thuật toán Reschedule
class TaskItem(BaseModel):
    title: str = Field(description="Tên công việc hoặc học phần cụ thể")
    time_slot: str = Field(description="Khung giờ gợi ý (ví dụ: '08:00 - 08:45', 'Dời sang ngày mai 08:00 - 10:00', '17:30 - 18:15')")
    cognitive_load: str = Field(description="Tải nhận thức: 'high' (nặng), 'low' (nhẹ), hoặc 'habit_stacking' (kết hợp thói quen sinh hoạt)")
    platform_or_resource: Optional[str] = Field(default=None, description="Nền tảng sử dụng, ví dụ: Study4, VS Code, Spotify/Podcast, Notion")
    status: str = Field(default="scheduled", description="Trạng thái: 'scheduled', 'deferred_to_tomorrow', hoặc 'completed'")
    combined_with: Optional[str] = Field(default=None, description="Hoạt động sinh hoạt kết hợp nếu là Low Load")
    note: Optional[str] = Field(default=None, description="Ghi chú chiến lược từ Coach")


class SchedulePlanResult(BaseModel):
    coach_briefing: str = Field(description="Lời tư vấn sắc sảo từ góc độ Executive Coach, giải thích rõ lý do dời lịch hoặc tối ưu hóa nhịp sinh học")
    is_rescheduled: bool = Field(default=False, description="True nếu kích hoạt thuật toán Reschedule dời lịch do quá tải hoặc lịch đột xuất")
    deferred_tasks: List[TaskItem] = Field(default_factory=list, description="Danh sách các task nặng dời sang ngày hôm sau (nếu có)")
    tasks: List[TaskItem] = Field(description="Danh sách các task thực thi hôm nay (gồm Low Load và kết hợp thói quen sinh hoạt)")
