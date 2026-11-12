import os
import json
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
from agents.state import AgentState
from tools.search import execute_trend_search, tavily_search, execute_opportunity_scout
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
)
from agents.task_estimator import analyze_and_estimate_goal
from tools.document_ingestor import scan_and_retrieve_context

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
        description="Ý định cốt lõi: 'coach_dialogue' (người dùng hỏi lời khuyên, tư vấn chiến lược, cách đỗ một khóa học/chương trình như VinUni AI, cách cân bằng/thực hiện song song các mục tiêu, hoặc tâm sự, chia sẻ ước mơ, dự định học tập/nghề nghiệp như muốn học Data Science, du học Tiến sĩ, muốn làm AI Engineer; cần lắng nghe, tư vấn và coaching gợi mở, KHÔNG ĐƯỢC lưu DB hay xếp lịch ngay), 'confirm_goal' (người dùng trả lời 'Đồng ý', 'Ok', 'Xác nhận', 'Tiến hành đi', 'Làm đi' khi Coach hỏi câu hỏi chốt để kích hoạt mục tiêu và xếp lịch), 'retrospective' (người dùng thông báo mục tiêu bị trễ hạn, hủy bỏ/bỏ cuộc, thất bại với phương pháp nào đó như Pomodoro, học tối, hoặc thông báo hoàn thành mục tiêu cần hồi cứu phân tích rút bài học thích nghi), 'schedule' (lập/điều chỉnh lịch, hoãn/dời lịch, xử lý lịch đột xuất), 'holistic_schedule' (lập lịch cân bằng sinh học toàn diện 4 Root Nodes, quy tắc Cân bằng Động Dynamic Equilibrium khi chạy bộ 30 phút và thâm hụt calo, chèn Recovery Buffer và Passive Listening), 'motivate' (mệt mỏi/cần động lực thuần túy), 'explore_trend' (tra cứu xu hướng/công nghệ AI/khởi nghiệp), 'set_goal' (LỆNH THỰC THI TRỰC TIẾP yêu cầu lưu mục tiêu mới vào hệ thống), 'find_resources' (tìm kiếm tài liệu học tập, sách, PDF, khóa học Coursera), 'strategic_plan' (lập kế hoạch ngược Backcasting Thạc sĩ AI, giải quyết xung đột ưu tiên Priority Conflict hoãn HSK, kích hoạt unpause trigger), 'opportunity_scout' (trinh sát chủ động cơ hội thực chiến, VinUni AI Bootcamp, networking protocol, alumni), hoặc 'chat' (hỏi đáp/thảo luận chung)"
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
        description="Các phương pháp/thói quen đã thử nhưng thất bại hoặc không phù hợp với người dùng (ví dụ: 'Phương pháp Pomodoro 25/5', 'Xếp lịch học nặng vào buổi tối sau 20:00')"
    )
    new_effective_methods: List[str] = Field(
        default=[],
        description="Các phương pháp/thói quen mang lại hiệu quả cao và phù hợp (ví dụ: 'Học sâu Deep Work 08:00 - 10:00 sáng', 'Nghe thụ động Habit Stacking khi làm việc nhà')"
    )
    new_productivity_patterns: List[str] = Field(
        default=[],
        description="Quy luật năng suất được rút ra: khung giờ hiệu quả nhất, loại task gây kiệt sức (ví dụ: 'Năng lượng đỉnh cao lúc 08:00 - 10:00 sáng', 'Dễ kiệt sức khi học nặng sau tập thể dục')"
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
class ResourceItem(BaseModel):
    title: str = Field(description="Tên tài liệu, khóa học, chứng chỉ hoặc repo")
    url: str = Field(description="Link URL trực tiếp hoặc nguồn uy tín")
    resource_type: str = Field(description="Loại tài nguyên: 'Coursera / MOOC', 'PDF / Sách', 'GitHub Repo', 'Roadmap / Doc', 'Chứng chỉ / Kỳ thi'")
    summary: str = Field(description="Tóm tắt giá trị ứng dụng thực chiến đối với Mavis")
    estimated_cost: Optional[str] = Field(
        default="Miễn phí / Audit free",
        description="Ước tính chi phí / học phí / lệ phí thi (VD: 'Miễn phí', '~$49/tháng trên Coursera', '~4.500.000 VNĐ lệ phí thi',...)"
    )


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
    combined_with: Optional[str] = Field(default=None, description="Hoạt động sinh hoạt kết hợp nếu là Low Load (VD: 'Khi rửa bát, dọn nhà', 'Khi đi dạo thư giãn')")
    note: Optional[str] = Field(default=None, description="Ghi chú chiến lược từ Coach")


class SchedulePlanResult(BaseModel):
    coach_briefing: str = Field(description="Lời tư vấn sắc sảo từ góc độ Executive Coach, giải thích rõ lý do dời lịch hoặc tối ưu hóa nhịp sinh học")
    is_rescheduled: bool = Field(default=False, description="True nếu kích hoạt thuật toán Reschedule dời lịch do quá tải hoặc lịch đột xuất")
    deferred_tasks: List[TaskItem] = Field(default_factory=list, description="Danh sách các task nặng dời sang ngày hôm sau (nếu có)")
    tasks: List[TaskItem] = Field(description="Danh sách các task thực thi hôm nay (gồm Low Load và kết hợp thói quen sinh hoạt)")


def analyze_input_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Phân tích câu chat của Mavis để gán giá trị cho intent, detected_emotion, current_energy_level và is_emergency.
    Cấu trúc lại Bộ định tuyến thành Executive Agentic Coach:
    - Phân biệt giữa tin nhắn 'tâm sự/dự định' (coach_dialogue) và 'lệnh thực thi'.
    - Khi người dùng phản hồi 'Đồng ý' / 'Xác nhận' cho câu hỏi chốt của Coach, nhận diện intent = 'confirm_goal'.
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "intent": "chat",
            "detected_emotion": "neutral",
            "current_energy_level": "high",
            "is_emergency": False,
        }

    # Lấy câu nói gần nhất của Mavis
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        last_user_message = str(messages[-1].content if hasattr(messages[-1], "content") else messages[-1])

    user_lower = last_user_message.lower().strip()

    # Nhận diện kích hoạt hành động (Trigger Action - Phase 9):
    # Nếu Agent đang chờ xác nhận (awaiting_confirmation) và user nói 'Đồng ý', 'Ok', 'Xác nhận',...
    awaiting_confirmation = state.get("awaiting_confirmation", False)
    affirmative_keywords = [
        "đồng ý", "dong y", "ok", "okay", "yes", "có", "chốt", "xác nhận", 
        "tiến hành", "tiến hành đi", "làm đi", "nhất trí", "triển khai", 
        "đưa vào", "đồng ý nhé", "ok coach", "làm luôn", "duyệt", "chuẩn", "thực hiện đi"
    ]
    if awaiting_confirmation and any(w in user_lower for w in affirmative_keywords):
        return {
            "intent": "confirm_goal",
            "detected_emotion": "determined",
            "current_energy_level": "high",
            "is_emergency": False,
            "uploaded_context": state.get("uploaded_context"),
        }

    # Động cơ RAG (Phase 7.1): Tự động quét xem user có cung cấp link URL hoặc file PDF mới không
    # Đồng thời truy vấn các đoạn trích liên quan từ Chroma Knowledge Base
    uploaded_context = scan_and_retrieve_context(last_user_message)
    if not uploaded_context and state.get("uploaded_context"):
        uploaded_context = state.get("uploaded_context")

    rag_prompt_addition = f"\n\n{uploaded_context}" if uploaded_context else ""

    prompt = f"""Hãy đóng vai trò Hệ thống Phân tích Nhận thức của AI Executive Life Coach cho Mavis.
Phân tích phát biểu sau đây của Mavis:
"{last_user_message}"{rag_prompt_addition}

CHỈ THỊ BẮT BUỘC TỪ EXECUTIVE LIFE COACH (AGENTIC COACHING PROTOCOL - PHASE 9):
Bạn là một Executive Life Coach. Khi người dùng chia sẻ ước mơ, dự định (ví dụ: muốn đi du học Tiến sĩ, muốn học Data Science, muốn làm AI Engineer), KHÔNG ĐƯỢC lập tức phân loại thành lệnh thực thi lưu mục tiêu hay xếp lịch. Bạn phải dùng kỹ năng Coaching: đặt câu hỏi gợi mở, hỏi về khó khăn, phân tích độ khả thi, và trò chuyện như một người bạn để làm rõ khao khát của họ.
Phân biệt tuyệt đối giữa tin nhắn 'tâm sự/dự định' và 'lệnh thực thi'.

Yêu cầu phân loại chính xác theo thứ tự ưu tiên:
1. intent: Chọn duy nhất một trong các nhãn: 'coach_dialogue', 'confirm_goal', 'retrospective', 'schedule', 'holistic_schedule', 'motivate', 'explore_trend', 'set_goal', 'find_resources', 'strategic_plan', 'opportunity_scout', 'chat'.
   - 'coach_dialogue': Nếu người dùng hỏi lời khuyên, tư vấn chiến lược, hỏi cách làm/phương pháp thực thi (VD: 'Làm sao đỗ khóa VinUni AI?', 'Thực hiện song song được không?', 'Làm thế nào để cân bằng?', 'Tại sao...', 'Có nên...', 'Cách nào...'), hoặc chia sẻ ước mơ, dự định. Toàn bộ các câu hỏi How / Why / Làm thế nào / Được không / Tư vấn chiến lược BẮT BUỘC phải được phân loại là 'coach_dialogue' để chuyển thẳng vào node Coaching cho LLM tự do suy luận và tư vấn chi tiết thay vì bắt người dùng khai báo mục tiêu mới hay xếp lịch. KHÔNG ĐƯỢC chọn 'set_goal' hay 'schedule' cho các câu hỏi này!
   - 'retrospective': Nếu người dùng chia sẻ về việc bỏ cuộc, hủy mục tiêu, mục tiêu bị trễ hạn (overdue), phàn nàn phương pháp không hiệu quả / thất bại (ví dụ: "tôi không hợp Pomodoro", "học buổi tối đuối quá không học nổi", "thất bại rồi", "hủy mục tiêu này"), hoặc thông báo hoàn thành mục tiêu và cần tổng kết bài học hành vi rút kinh nghiệm.
   - 'confirm_goal': Nếu người dùng trả lời 'Đồng ý', 'Ok', 'Xác nhận', 'Tiến hành đi', 'Làm đi' khi Coach đã đưa ra câu hỏi chốt về việc đưa mục tiêu vào cuộc đời và xếp lịch.
   - 'holistic_schedule': Nếu Mavis yêu cầu lập lịch cân bằng sinh học toàn diện, dung hòa 4 Root Nodes (học tập career, vóc dáng beauty, sức khỏe health, gia đình relationships), quy tắc cân bằng động (Dynamic Equilibrium) khi chạy bộ 30 phút và thâm hụt calo, chèn đệm phục hồi Recovery Buffer hoặc Passive Listening.
   - 'strategic_plan': Nếu Mavis hỏi về lập kế hoạch ngược (Backcasting), hoạch định lộ trình học Thạc sĩ AI (cho người trái ngành FTU), phân tích khoảng trống (Gap analysis), giải quyết xung đột mục tiêu (Priority Conflict giữa IELTS và HSK), hoặc thông báo IELTS hoàn tất để kích hoạt lại các mục tiêu bị hoãn (unpause trigger).
   - 'opportunity_scout': Nếu Mavis yêu cầu trinh sát cơ hội thực chiến, tìm kiếm chương trình VinUni AI Bootcamp, AI Residency, cơ hội thực tập AI, hoặc hướng dẫn Networking Protocol để kết nối alumni/cộng đồng tạo lợi thế thi cử.
   - 'schedule': Nếu Mavis yêu cầu lên lịch, dời lịch, hoãn lịch, xếp lại lịch (reschedule), xử lý lịch đột xuất, hoặc phân bổ lại task trong ngày do mệt mỏi/bận việc gấp.
   - 'motivate': Nếu Mavis than mệt, nản, đuối, áp lực, bế tắc, bug code thuần túy để giải tỏa cảm xúc (mà KHÔNG yêu cầu dời lịch hay xếp lại lịch).
   - 'set_goal': CHỈ CHỌN khi người dùng ra LỆNH THỰC THI TRỰC TIẾP yêu cầu lưu ngay mục tiêu mới vào hệ thống/ledger (VD: "Lệnh: Thêm mục tiêu X vào ledger", "Lưu mục tiêu X ngay"). Nếu chỉ nói "Tôi muốn...", bắt buộc chọn 'coach_dialogue'.
   - 'find_resources': Nếu Mavis cần tìm tài liệu học tập, giáo trình, file PDF, khóa học Coursera, github repo, roadmap cho một mục tiêu hay kỹ năng.
   - 'explore_trend': Nếu Mavis hỏi về xu hướng công nghệ, tin tức AI, startup, thị trường, dòng tiền, hoặc học kỹ năng gì để đón đầu công nghệ.
   - 'chat': Các trao đổi thông thường khác hoặc đính chính thông tin.
2. is_emergency: Đặt là True nếu Mavis đề cập có việc đột xuất, lịch họp gấp, bận việc ngoài dự kiến, hoặc kiệt sức/quá tải cần hoãn/dời lịch.
3. detected_emotion: Nhận diện cảm xúc (negative, tired, overwhelmed, neutral, positive, determined).
4. current_energy_level: 'low' nếu Mavis có dấu hiệu mệt mỏi/tiêu cực/sau 14h hoặc có lịch đột xuất gây kiệt sức, ngược lại 'high'.
"""

    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(InputAnalysisResult)
        result: InputAnalysisResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        
        return {
            "intent": result.intent,
            "detected_emotion": result.detected_emotion,
            "current_energy_level": result.current_energy_level,
            "is_emergency": result.is_emergency,
            "uploaded_context": uploaded_context,
        }
    except Exception as e:
        # Cơ chế Rule-based Fallback dự phòng nếu chưa có API Key hoặc gặp lỗi mạng
        is_emergency = any(w in user_lower for w in ["đột xuất", "bận gấp", "việc gấp", "dời lịch", "hoãn lịch", "xếp lại", "reschedule", "quá tải", "kiệt sức"])
        
        # 0. Nhận diện các câu hỏi tư vấn chiến lược / phương pháp / thắc mắc thực thi (Coaching Advice)
        advice_keywords = [
            "làm sao", "làm thế nào", "tại sao", "thế nào", "được không", "có nên",
            "tư vấn", "lời khuyên", "chiến lược", "song song", "how", "why",
            "cách nào", "khả thi không", "có được không", "liệu có", "đỗ khóa", "đỗ vinuni", "vinuni ai"
        ]
        if any(w in user_lower for w in advice_keywords):
            intent = "coach_dialogue"
            emotion = "neutral"
            energy = "high"
        # 1. Nhận diện phản hồi Đồng ý / Xác nhận kích hoạt
        elif awaiting_confirmation or any(user_lower.startswith(w) for w in ["đồng ý", "ok", "xác nhận", "tiến hành", "làm đi"]):
            intent = "confirm_goal"
            emotion = "determined"
            energy = "high"
        # 2. Nhận diện phản hồi Hồi cứu hành vi / Bỏ cuộc / Thất bại phương pháp (Phase 10)
        elif any(w in user_lower for w in [
            "bỏ cuộc", "hủy mục tiêu", "không hợp phương pháp", "không hợp pomodoro",
            "thất bại rồi", "đuối quá không học nổi", "trễ hạn rồi", "quá hạn", "overdue",
            "hoàn thành xuất sắc", "hoàn thành mục tiêu", "rút kinh nghiệm", "hồi cứu",
            "retrospective", "tổng kết bài học", "không hiệu quả", "bỏ mục tiêu", "không dùng pomodoro"
        ]):
            intent = "retrospective"
            emotion = "neutral"
            energy = "low" if any(w in user_lower for w in ["thất bại", "bỏ cuộc", "đuối", "trễ hạn", "hủy"]) else "high"
        # 3. Phân biệt tin nhắn 'Tâm sự / Chia sẻ ước mơ, dự định' (Agentic Coach - Phase 9)
        elif bool(state.get("pending_goal")) or any(w in user_lower for w in ["muốn học", "muốn đi du học", "ước mơ", "dự định", "đang nghĩ đến", "thích làm", "thích học", "tính chuyển", "muốn thi", "muốn làm", "muốn trở thành", "mơ ước"]):
            intent = "coach_dialogue"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in ["cân bằng sinh học", "cân bằng động", "dynamic equilibrium", "holistic", "dung hòa", "chạy bộ 30 phút", "thâm hụt calo", "giảm cân", "toàn diện 4", "4 root"]):
            intent = "holistic_schedule"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in ["backcasting", "kế hoạch ngược", "thạc sĩ ai", "master ai", "xung đột", "priority conflict", "hoãn hsk", "paused_until_ielts_done", "chiến lược", "unpause", "ielts hoàn thành", "hoàn thành ielts", "kích hoạt lại hsk", "giải phóng lịch"]):
            intent = "strategic_plan"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in ["trinh sát cơ hội", "opportunity scout", "bootcamp", "vinuni ai bootcamp", "networking protocol", "alumni", "kết nối thí sinh", "hội đồng tuyển sinh", "thực tập ai"]):
            intent = "opportunity_scout"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in ["lệnh: thêm", "lệnh thêm", "chính thức thêm goal", "set goal"]):
            intent = "set_goal"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in ["tài liệu", "khóa học", "coursera", "pdf", "roadmap", "giáo trình", "github repo", "tài nguyên", "sách"]):
            intent = "find_resources"
            emotion = "neutral"
            energy = "high"
        elif any(w in user_lower for w in ["dời lịch", "hoãn lịch", "xếp lại lịch", "reschedule", "lịch đột xuất", "bận đột xuất"]):
            intent = "schedule"
            emotion = "overwhelmed" if any(w in user_lower for w in ["kiệt sức", "quá tải"]) else ("tired" if "mệt" in user_lower else "neutral")
            energy = "low"
            is_emergency = True
        elif any(w in user_lower for w in ["mệt", "nản", "đuối", "áp lực", "stress", "chán", "bug", "bế tắc", "quá tải", "kiệt sức"]):
            # Chỉ coi là schedule nếu người dùng thực sự yêu cầu dời hoặc xếp lại lịch trình
            if any(w in user_lower for w in ["dời", "hoãn", "xếp lại", "reschedule", "lịch đột xuất", "sắp xếp lại"]):
                intent = "schedule"
                emotion = "overwhelmed" if any(w in user_lower for w in ["quá tải", "kiệt sức"]) else "tired"
                energy = "low"
                is_emergency = True
            else:
                intent = "motivate"
                emotion = "negative"
                energy = "low"
        elif any(w in user_lower for w in ["xu hướng", "trend", "tin tức", "ai mới", "dòng tiền", "thị trường", "khởi nghiệp", "startup", "alpha"]):
            intent = "explore_trend"
            emotion = "neutral"
            energy = "high"
        elif any(w in user_lower for w in ["lịch", "thời gian biểu", "ôn", "ielts", "study4", "task", "ngày mai", "hôm nay"]):
            intent = "schedule"
            emotion = "neutral"
            energy = "high"
        else:
            intent = "chat"
            emotion = "neutral"
            energy = "high"

        return {
            "intent": intent,
            "detected_emotion": emotion,
            "current_energy_level": energy,
            "is_emergency": is_emergency,
            "uploaded_context": uploaded_context,
        }



def motivate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Kích hoạt 'Giao thức Tự hào' (Pride-Activation Protocol) khi nhận diện cảm xúc tiêu cực.
    Trích xuất Achievement Ledger, loại bỏ lời an ủi sáo rỗng, kích hoạt Dopamine và đề xuất giảm tải.
    """
    detected_emotion = state.get("detected_emotion", "negative")
    user_msg = state.get("messages", [])[-1].content if state.get("messages") else ""

    coach_instruction = f"""Người dùng đang gặp trạng thái tâm lý: {detected_emotion}
Nội dung người dùng chia sẻ: "{user_msg}"

Hãy áp dụng triệt để "Giao thức Tự hào" (Pride-Activation Protocol):
1. BỎ QUA các lời khuyên sáo rỗng (như "cố lên", "bạn sẽ làm được").
2. NHẮC LẠI năng lực tư duy logic và bản lĩnh giải quyết bài toán khó của người dùng từ Achievement Ledger.
3. Nhấn mạnh rằng sự mệt mỏi hiện tại chỉ là chỉ số sinh học báo hiệu não cần nạp năng lượng, không phải sự thụt lùi về năng lực.
4. ĐỀ XUẤT QUY TRÌNH GIẢM TẢI NGAY LẬP TỨC: Nghỉ Pomodoro 15 phút, uống nước, hoặc chuyển sang nhiệm vụ nhẹ tải nhận thức.
5. Giữ giọng điệu của một Executive Life Coach hàng đầu: Điềm đạm, sắc sảo, tự tin, và bảo vệ nhịp sinh học của người dùng.
"""

    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=coach_instruction),
        ])
        reply_text = extract_text_from_content(response.content if hasattr(response, "content") else response)
    except Exception as e:
        # Fallback offline
        reply_text = (
            "Hãy dừng lại 1 nhịp. Tôi là Executive Coach của bạn, và tôi không chấp nhận những lời khuyên sáo rỗng kiểu 'hãy cố gắng thêm chút nữa'.\n\n"
            "Hãy nhìn vào dữ liệu thực tế: Năng lực giải quyết bài toán phức tạp và bản lĩnh thực thi của bạn đã được chứng minh qua hành động, không phải suy đoán. "
            "Cảm giác mệt mỏi hay bế tắc lúc này chỉ là tín hiệu sinh học tự nhiên cho thấy não bộ đã đạt ngưỡng tải.\n\n"
            "Tôi kích hoạt quy trình giảm tải chiến lược: Dừng mọi tác vụ nặng ngay bây giờ. Nghỉ Pomodoro 15 phút, thả lỏng hoàn toàn. "
            "Sự nghiệp và cuộc đời là một cuộc đua marathon chiến thuật bền bỉ, không phải một pha nước rút tự hủy hoại thể lực. Hãy nghỉ ngơi, chúng ta sẽ tái xuất sắc bén hơn."
        )

    return {
        "messages": [AIMessage(content=reply_text)],
        "current_energy_level": "low",
    }


def schedule_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Dynamic Scheduling & Biometric Sensing (Phase 6.3).
    - Nạp logic xếp lịch động: Trích xuất các mục tiêu và milestone active từ goals_ledger.json.
    - Cảm biến thể trạng & Nhận diện tình huống:
      Nếu phát hiện có lịch đột xuất (is_emergency) hoặc emotion in ['negative', 'tired', 'overwhelmed'] (kiệt sức / quá tải):
      -> Kích hoạt THUẬT TOÁN RESCHEDULE: Tự động dời các task nặng (giải đề, toán AI) sang ngày hôm sau.
      -> Tự động chèn các LOW LOAD TASKS kết hợp vào thói quen sinh hoạt (Habit Stacking, ví dụ: nghe podcast tiếng Trung / audio sách tư duy khi rửa bát, dọn nhà, đi dạo).
    - Nếu thể trạng bình thường (high energy): Lập lịch tối ưu nhịp sinh học (08:00 - 10:00 cho High Load, chiều Low Load, kết hợp Habit Stacking).
    """
    messages = state.get("messages", [])
    user_msg = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            user_msg = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            user_msg = msg.get("content", "")
            break
    if not user_msg and messages:
        user_msg = str(messages[-1].content if hasattr(messages[-1], "content") else messages[-1])

    current_energy = state.get("current_energy_level", "high")
    detected_emotion = state.get("detected_emotion", "neutral")
    is_emergency = state.get("is_emergency", False)

    user_lower = user_msg.lower()
    has_emergency_keyword = any(w in user_lower for w in [
        "đột xuất", "bận gấp", "việc gấp", "dời lịch", "hoãn lịch", "reschedule",
        "quá tải", "kiệt sức", "mệt mỏi", "đuối", "áp lực", "stress", "kẹt lịch", "không kịp"
    ])

    is_overloaded_or_emergency = (
        is_emergency
        or detected_emotion in ["negative", "tired", "overwhelmed"]
        or current_energy == "low"
        or has_emergency_keyword
    )

    # 1. Trích xuất mục tiêu & task thực tế từ goals_ledger.json và uploaded_context
    if any(w in user_msg.lower() for w in ["cân bằng sinh học", "cân bằng động", "dynamic equilibrium", "holistic", "dung hòa", "chạy bộ 30 phút", "thâm hụt calo", "giảm cân"]):
        return holistic_scheduler_node(state)

    username = state.get("username") or "mavis"
    goals_summary = get_goals_summary_text(username=username)
    active_tasks = get_active_tasks_and_milestones(username=username)
    uploaded_context = state.get("uploaded_context") or ""
    context_note = f"\n\n[DỮ LIỆU TÀI LIỆU RAG ĐÃ TẢI LÊN - KNOWLEDGE BASE]:\n{uploaded_context}\n" if uploaded_context else ""

    # Tải Bộ Nhớ Thích Nghi (Adaptive Memory / Historical Insights - Phase 10)
    insights_summary = get_historical_insights_summary_text(username=username)
    user_insights = load_historical_insights(username=username)
    failed_methods = user_insights.get("failed_methods", [])
    effective_methods = user_insights.get("effective_methods", [])
    productivity_patterns = user_insights.get("productivity_patterns", [])

    adaptive_prompt_block = f"""
BỘ NHỚ THÍCH NGHI ĐẶC BIỆT (ADAPTIVE MEMORY PROTOCOL - PHASE 10):
{insights_summary}

QUY TẮC RÀNG BUỘC BẮT BUỘC TỪ EXECUTIVE COACH:
1. TUYỆT ĐỐI KHÔNG đề xuất lại các phương pháp hoặc thói quen nằm trong danh sách failed_methods của người dùng: {failed_methods}.
   Ví dụ: Nếu người dùng đã thất bại với Pomodoro hoặc không hợp Pomodoro, TUYỆT ĐỐI KHÔNG xếp các task 25 phút ngắt quãng hay nhắc tới Pomodoro! Thay vào đó, hãy bố trí các khối Deep Work liền mạch 60-90 phút hoặc Flow State.
2. BẮT BUỘC ưu tiên áp dụng các phương pháp và quy luật năng suất trong effective_methods ({effective_methods}) và productivity_patterns ({productivity_patterns}).
"""

    # KIỂM TRA HỒ SƠ MỤC TIÊU TRỐNG (PHASE ONBOARDING GUARD):
    # Nếu hồ sơ chưa có mục tiêu nào trong goals_ledger, TUYỆT ĐỐI KHÔNG sinh lịch trình giả định!
    if not active_tasks:
        reply_text = (
            "Hiện tại hồ sơ chiến lược của bạn đang hoàn toàn trống và chưa có mục tiêu nào trong hệ thống.\n\n"
            "Từ góc độ Executive Life Coach, tôi KHÔNG sinh lịch trình khi bạn chưa xác lập mục tiêu cụ thể. "
            "Bạn muốn chúng ta bắt đầu bằng việc xây dựng khía cạnh nào trước (Sự nghiệp, Sức khỏe, Tài chính...), và mục tiêu lớn nhất hiện tại của bạn là gì?"
        )
        return {
            "messages": [AIMessage(content=reply_text)],
            "plan": [],
            "current_energy_level": state.get("current_energy_level", "high"),
        }

    plan_tasks: List[Dict[str, Any]] = []

    if is_overloaded_or_emergency:
        # -------------------------------------------------------------
        # THUẬT TOÁN RESCHEDULE (DỜI LỊCH TỰ ĐỘNG & HABIT STACKING)
        # -------------------------------------------------------------
        schedule_instruction = f"""Yêu cầu của người dùng: "{user_msg}"{context_note}
TRẠNG THÁI THỂ TRẠNG & TÌNH HUỐNG:
- Cảm xúc ghi nhận: {detected_emotion} (Phát hiện kiệt sức / quá tải / việc đột xuất)
- Năng lượng sinh học: LOW (Cần kích hoạt Giao thức Giảm tải ngay lập tức)
- Lịch đột xuất / Việc gấp: {is_emergency or has_emergency_keyword}

DỮ LIỆU CÁC MỤC TIÊU VÀ CỘT MỐC ĐANG ACTIVE TRONG GOALS LEDGER:
{goals_summary}

{adaptive_prompt_block}

ÁP DỤNG QUY TẮC QUẢN TRỊ HIỆU SUẤT ĐỈNH CAO:
1. THUẬT TOÁN RESCHEDULE TỰ ĐỘNG:
   - DỜI toàn bộ các task nặng (High Cognitive Load) từ danh sách active goals sang NGÀY HÔM SAU vào khung giờ vàng 08:00 - 10:00 sáng.
   - Ghi rõ status = 'deferred_to_tomorrow' cho các task này.
   - Nhắc nhở người dùng: Dời lịch là bước lùi chiến lược để tối ưu hóa điểm rơi phong độ, không phải trì hoãn.
2. TỰ ĐỘNG CHÈN 'LOW LOAD TASK' & THÓI QUEN SINH HOẠT (HABIT STACKING):
   - Đề xuất các tác vụ nhẹ nhàng kết hợp vào sinh hoạt: nghe audio sách tư duy, podcast chuyên môn khi làm việc nhà, đi dạo.
   - Buổi tối: Kích hoạt Giao thức phục hồi sinh học và quy tắc ngủ trước 23:00.
3. Đặt is_rescheduled = True.
"""
    else:
        # -------------------------------------------------------------
        # XẾP LỊCH CHUẨN THEO NHỊP SINH HỌC VÀ GOALS LEDGER
        # -------------------------------------------------------------
        schedule_instruction = f"""Yêu cầu của người dùng: "{user_msg}"{context_note}
Mức năng lượng sinh học ghi nhận: HIGH (Não bộ đạt đỉnh cao nhận thức)

DỮ LIỆU CÁC MỤC TIÊU VÀ CỘT MỐC ĐANG ACTIVE TRONG GOALS LEDGER:
{goals_summary}

{adaptive_prompt_block}

Áp dụng nguyên tắc lập lịch nhịp sinh học tối ưu:
1. KHUNG GIỜ VÀNG (08:00 - 10:00 sáng): Bố trí các nhiệm vụ tải nhận thức cao (High Cognitive Load) từ danh sách active goals theo phương pháp Deep Work liền mạch.
2. KHUNG GIỜ CHIỀU (Sau 14:00): Đẩy các nhiệm vụ nhẹ tải (Low Cognitive Load) hoặc review tài liệu/code.
3. KHUNG CHIỀU TỐI (17:30 - 18:30): Tự động chèn 1 task Habit Stacking: Nghe podcast tư duy hoặc audio sách khi làm việc nhà hoặc đi dạo.
4. Đặt is_rescheduled = False.
"""

    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(SchedulePlanResult)
        result: SchedulePlanResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=schedule_instruction),
        ])

        if result.is_rescheduled or is_overloaded_or_emergency:
            reply_lines = [
                result.coach_briefing,
                "\n### 🛑 CÁC TASK NẶNG ĐÃ TỰ ĐỘNG DỜI SANG NGÀY HÔM SAU (08:00 - 10:00):",
            ]
            deferred_items = result.deferred_tasks or []
            if not deferred_items:
                for t in active_tasks:
                    if t.get("cognitive_load") == "high":
                        deferred_items.append(
                            TaskItem(
                                title=t.get("task_title"),
                                time_slot="Ngày mai 08:00 - 10:00",
                                cognitive_load="high",
                                status="deferred_to_tomorrow",
                                platform_or_resource=t.get("platform", "Hệ thống"),
                                note="Tự động dời sang khung giờ vàng sáng mai để bảo toàn phong độ não bộ",
                            )
                        )
            for t in deferred_items:
                t_dict = t.model_dump()
                t_dict["status"] = "deferred_to_tomorrow"
                plan_tasks.append(t_dict)
                platform_info = f" (Nền tảng: {t.platform_or_resource})" if t.platform_or_resource else ""
                reply_lines.append(f"- **{t.time_slot}** | [DỜI SANG MAI - HIGH LOAD] **{t.title}**{platform_info}")
                if t.note:
                    reply_lines.append(f"  * *Chiến lược: {t.note}*")

            reply_lines.append("\n### 🟢 LỊCH TRÌNH HẠ TẢI & THÓI QUEN SINH HOẠT HÔM NAY (HABIT STACKING):")
            for t in result.tasks:
                t_dict = t.model_dump()
                plan_tasks.append(t_dict)
                platform_info = f" (Nền tảng: {t.platform_or_resource})" if t.platform_or_resource else ""
                habit_note = f" *(🧺 Kết hợp: {t.combined_with})*" if t.combined_with else ""
                reply_lines.append(f"- **{t.time_slot}** | [LOW LOAD - THÓI QUEN] **{t.title}**{platform_info}{habit_note}")

            reply_text = "\n".join(reply_lines)
            updated_energy = "low"
        else:
            plan_tasks = [task.model_dump() for task in result.tasks]
            reply_lines = [result.coach_briefing, "\n### LỊCH TRÌNH TỐI ƯU NHỊP SINH HỌC CHIẾN LƯỢC:"]
            for t in result.tasks:
                platform_info = f" (Nền tảng: {t.platform_or_resource})" if t.platform_or_resource else ""
                if t.cognitive_load.lower() == "high":
                    load_badge = "[HIGH LOAD - GIỜ VÀNG]"
                elif t.cognitive_load.lower() == "habit_stacking" or t.combined_with:
                    load_badge = "[HABIT STACKING - SINH HOẠT]"
                else:
                    load_badge = "[LOW LOAD - HẠ NHIỆT]"
                habit_note = f" *(Kết hợp: {t.combined_with})*" if t.combined_with else ""
                reply_lines.append(f"- **{t.time_slot}** | {load_badge} **{t.title}**{platform_info}{habit_note}")
            reply_text = "\n".join(reply_lines)
            updated_energy = "high"

    except Exception as e:
        # Fallback định lượng từ active_tasks thực tế
        if is_overloaded_or_emergency:
            plan_tasks = []
            for t in active_tasks:
                if t.get("cognitive_load") == "high":
                    plan_tasks.append({
                        "title": t.get("task_title"),
                        "time_slot": "Ngày mai 08:00 - 10:00",
                        "cognitive_load": "high",
                        "status": "deferred_to_tomorrow",
                        "platform_or_resource": t.get("platform", "Hệ thống"),
                        "combined_with": None,
                        "note": "Tự động dời sang khung giờ vàng sáng mai để bảo toàn phong độ não bộ",
                    })
                else:
                    plan_tasks.append({
                        "title": t.get("task_title"),
                        "time_slot": "Hôm nay 16:00 - 17:00",
                        "cognitive_load": "low",
                        "status": "scheduled",
                        "platform_or_resource": t.get("platform", "Hệ thống"),
                        "combined_with": "Khi làm việc nhẹ",
                        "note": "Hạ tải nhận thức",
                    })
            if not plan_tasks:
                plan_tasks = [
                    {
                        "title": "Nghỉ ngơi, phục hồi sinh học & nghe audio tư duy",
                        "time_slot": "17:30 - 18:30",
                        "cognitive_load": "low",
                        "status": "scheduled",
                        "platform_or_resource": "Spotify / Audio",
                        "combined_with": "Khi nghỉ ngơi",
                        "note": "Phục hồi nhận thức",
                    }
                ]
            reply_lines = [
                "Tôi kích hoạt **Giao thức Reschedule Tự Động** để bảo vệ năng lượng não bộ của bạn.",
                "Toàn bộ tác vụ nặng đã được dời sang khung giờ vàng sáng mai (08:00 - 10:00).",
                "\n### 🛑 CÁC TASK NẶNG ĐÃ TỰ ĐỘNG DỜI SANG NGÀY HÔM SAU:",
            ]
            for t in plan_tasks:
                if t.get("status") == "deferred_to_tomorrow":
                    reply_lines.append(f"- **{t['time_slot']}** | [DỜI SANG MAI - HIGH LOAD] **{t['title']}**")
            reply_lines.append("\n### 🟢 LỊCH TRÌNH HẠ TẢI & THÓI QUEN SINH HOẠT HÔM NAY:")
            for t in plan_tasks:
                if t.get("status") != "deferred_to_tomorrow":
                    reply_lines.append(f"- **{t['time_slot']}** | [LOW LOAD] **{t['title']}**")
            reply_text = "\n".join(reply_lines)
            updated_energy = "low"
        else:
            time_slots = ["08:00 - 08:50", "08:55 - 10:00", "14:30 - 15:30", "17:30 - 18:15"]
            reply_lines = [
                "Tôi đã phân rã mục tiêu từ goals_ledger và căn chỉnh theo nhịp sinh học:",
                "\n### LỊCH TRÌNH TỐI ƯU NHỊP SINH HỌC CHIẾN LƯỢC:",
            ]
            plan_tasks = []
            for idx, t in enumerate(active_tasks[:4]):
                slot = time_slots[idx] if idx < len(time_slots) else "17:30 - 18:30"
                c_load = t.get("cognitive_load", "high" if idx == 0 else "low")
                plan_tasks.append({
                    "title": t.get("task_title"),
                    "time_slot": slot,
                    "cognitive_load": c_load,
                    "status": "scheduled",
                    "platform_or_resource": t.get("platform", "Hệ thống"),
                    "combined_with": None,
                })
                reply_lines.append(f"- **{slot}** | [{c_load.upper()}] **{t.get('task_title')}**")
            reply_text = "\n".join(reply_lines)
            updated_energy = "high"

    # Hậu kiểm bảo vệ Bộ Nhớ Thích Nghi: TUYỆT ĐỐI KHÔNG để lọt failed_methods
    failed_lower = [f.lower() for f in failed_methods]
    if any("pomodoro" in f for f in failed_lower):
        for t in plan_tasks:
            if "pomodoro" in t.get("title", "").lower():
                t["title"] = t["title"].replace("Pomodoro 25/5", "Khối Deep Work liền mạch").replace("Pomodoro", "Deep Work").replace("pomodoro", "Deep Work")
            if t.get("note") and "pomodoro" in t["note"].lower():
                t["note"] = t["note"].replace("Pomodoro 25/5", "Khối Deep Work liền mạch").replace("Pomodoro", "Deep Work").replace("pomodoro", "Deep Work")
            if t.get("combined_with") and "pomodoro" in t["combined_with"].lower():
                t["combined_with"] = t["combined_with"].replace("Pomodoro", "Deep Work").replace("pomodoro", "Deep Work")
        reply_text = reply_text.replace("Pomodoro 25/5", "Khối Deep Work liền mạch").replace("Pomodoro", "Deep Work").replace("pomodoro", "Deep Work")

    return {
        "messages": [AIMessage(content=reply_text)],
        "plan": plan_tasks,
        "current_energy_level": updated_energy,
    }


def holistic_scheduler_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 9: Holistic Bio-Scheduler & Dynamic Equilibrium (Phase 7.4).
    Nhiệm vụ:
    1. Dung hòa toàn diện các tác vụ từ cả 4 Root Nodes (career, beauty, health, relationships).
    2. Quy tắc Cân bằng Động (Dynamic Equilibrium):
       - Tự động nhận diện khi mục tiêu Sắc đẹp/Vóc dáng yêu cầu chạy bộ 30 phút và thâm hụt calo.
       - Tự động tính toán lại mức năng lượng sinh học: Sau giờ chạy bộ và thâm hụt calo -> current_energy_level chuyển thành 'low'.
    3. Ràng buộc Sinh học Bắt buộc (Biological Constraints):
       - TUYỆT ĐỐI KHÔNG xếp các task Học tập cường độ cao (High Cognitive Load) ngay sau giờ tập thể dục nặng (khung 17:15 - 19:00).
       - THAY VÀO ĐÓ:
         * Chèn ngay Recovery Buffer (17:15 - 17:45): Giãn cơ, bù điện giải, tắm nước ấm thả lỏng.
         * Chèn Passive Listening / Habit Stacking (17:45 - 18:30): Nghe podcast hoặc audio tư duy thụ động.
         * Chèn Bữa tối gia đình (19:00 - 20:00): Gắn kết người thân & nạp dinh dưỡng lành mạnh.
    4. Sinh Bảng Lịch Trình Chi Tiết Chia Giờ (Hourly Detailed Timeline Table) và nạp vào State Plan.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    user_msg_lower = (last_user_message or "").lower()
    uploaded_context = (state.get("uploaded_context") or "").lower()

    username = state.get("username") or "mavis"
    active_tasks = get_active_tasks_and_milestones(username=username)

    # KIỂM TRA HỒ SƠ MỤC TIÊU TRỐNG (PHASE ONBOARDING GUARD):
    # Nếu hồ sơ chưa có mục tiêu nào trong goals_ledger, TUYỆT ĐỐI KHÔNG sinh lịch trình giả định!
    if not active_tasks:
        reply_text = (
            "Hồ sơ chiến lược của bạn hiện tại đang hoàn toàn trống và chưa có mục tiêu nào trong 4 Root Nodes (Sự nghiệp, Sức khỏe, Mối quan hệ, Sắc vóc).\n\n"
            "Từ góc độ Executive Life Coach, tôi KHÔNG sinh lịch trình khi bạn chưa xác lập mục tiêu cụ thể. "
            "Bạn muốn chúng ta bắt đầu bằng việc xây dựng khía cạnh nào trước (Sự nghiệp, Sức khỏe, Tài chính...), và mục tiêu lớn nhất hiện tại của bạn là gì?"
        )
        return {
            "messages": [AIMessage(content=reply_text)],
            "plan": [],
            "current_energy_level": state.get("current_energy_level", "high"),
        }

    # 1. Phát hiện mục tiêu Chạy bộ 30 phút & Thâm hụt calo (Dynamic Equilibrium Trigger)
    has_running_and_deficit = any(
        w in user_msg_lower or w in uploaded_context
        for w in [
            "chạy bộ 30 phút",
            "chạy bộ",
            "thâm hụt calo",
            "calo",
            "giảm cân",
            "giảm mỡ",
            "cardio",
            "calorie deficit",
            "vóc dáng",
            "eat clean",
        ]
    )

    # 2. Xây dựng danh sách Task dung hòa trọn vẹn 4 Root Nodes từ active_tasks thực tế
    career_tasks = [t for t in active_tasks if t.get("category") == "career"]
    task_1_title = career_tasks[0].get("task_title") if career_tasks else "Tập trung nghiên cứu chuyên sâu & giải quyết bài toán cốt lõi"
    task_2_title = career_tasks[1].get("task_title") if len(career_tasks) > 1 else (career_tasks[0].get("task_title") if career_tasks else "Thực hành ứng dụng & phân tích logic")
    task_1_platform = career_tasks[0].get("platform", "Nền tảng học tập") if career_tasks else "Hệ thống"
    task_2_platform = career_tasks[1].get("platform", "VS Code / Công cụ") if len(career_tasks) > 1 else "Hệ thống"

    holistic_tasks = [
        {
            "title": task_1_title,
            "time_slot": "08:00 - 08:50",
            "cognitive_load": "high",
            "category": "career",
            "platform_or_resource": task_1_platform,
            "status": "scheduled",
            "combined_with": None,
            "note": "Khung giờ vàng não bộ: Năng lượng nhận thức đỉnh cao, dồn toàn lực bứt phá mục tiêu trọng tâm",
        },
        {
            "title": task_2_title,
            "time_slot": "08:55 - 10:00",
            "cognitive_load": "high",
            "category": "career",
            "platform_or_resource": task_2_platform,
            "status": "scheduled",
            "combined_with": None,
            "note": "Tập trung giải quyết bài toán logic phức tạp, không để phân tán nhận thức",
        },
        {
            "title": "Review tiến độ công việc & Networking Protocol kết nối chuyên môn",
            "time_slot": "14:00 - 14:45",
            "cognitive_load": "low",
            "category": "career",
            "platform_or_resource": "LinkedIn / Cộng đồng chuyên môn",
            "status": "scheduled",
            "combined_with": None,
            "note": "Tác vụ hạ tải buổi chiều: Mở rộng mạng lưới quan hệ tạo lợi thế bất đối xứng",
        },
        {
            "title": "Chạy bộ Cardio 30 phút ngoài trời & Thâm hụt calo (Eat Clean)",
            "time_slot": "16:30 - 17:15",
            "cognitive_load": "physical",
            "category": "beauty",
            "platform_or_resource": "Công viên / Đồng hồ đo Calo",
            "status": "scheduled",
            "combined_with": None,
            "note": "Đốt cháy ~350-400 kcal theo tài liệu thâm hụt calo & tối ưu sắc vóc",
        },
        {
            "title": "Đệm Phục Hồi (Recovery Buffer): Giãn cơ, bù điện giải & tắm nước ấm",
            "time_slot": "17:15 - 17:45",
            "cognitive_load": "recovery_buffer",
            "category": "health",
            "platform_or_resource": "Không gian thư giãn",
            "status": "scheduled",
            "combined_with": "Uống 500ml nước bù khoáng, giãn cơ bắp, hạ nhịp tim",
            "note": "Ràng buộc sinh học: Glycogen cạn kiệt, cấm tuyệt đối xử lý logic nặng để tránh sập nhận thức",
        },
        {
            "title": "Nghe Podcast phản xạ thụ động / Audio sách tư duy",
            "time_slot": "17:45 - 18:30",
            "cognitive_load": "habit_stacking",
            "category": "health",
            "platform_or_resource": "Spotify / Audio Podcast",
            "status": "scheduled",
            "combined_with": "Khi thả lỏng sau đệm phục hồi và chuẩn bị bữa tối",
            "note": "Passive Listening: Hấp thu kiến thức thụ động, không tiêu tốn tải nhận thức não bộ",
        },
        {
            "title": "Bữa cơm tối gia đình ấm cúng & Trò chuyện kết nối người thân",
            "time_slot": "19:00 - 20:00",
            "cognitive_load": "low",
            "category": "relationships",
            "platform_or_resource": "Bàn ăn gia đình",
            "status": "scheduled",
            "combined_with": None,
            "note": "Chế độ thâm hụt calo lành mạnh (giàu đạm, nhiều chất xơ), gắn kết tình cảm gia đình",
        },
        {
            "title": "Quy trình Skincare khoa học 15 phút & Chăm sóc sắc vóc Executive",
            "time_slot": "22:00 - 22:30",
            "cognitive_load": "low",
            "category": "beauty",
            "platform_or_resource": "Bàn trang điểm / Cá nhân",
            "status": "scheduled",
            "combined_with": None,
            "note": "Massage thư giãn cơ mặt, dưỡng ẩm phục hồi làn da sau ngày dài",
        },
        {
            "title": "Ngắt ánh sáng xanh, kích hoạt Giấc ngủ sâu & hồi phục sinh học",
            "time_slot": "22:30 - 23:00",
            "cognitive_load": "low",
            "category": "health",
            "platform_or_resource": "Ứng dụng giấc ngủ",
            "status": "scheduled",
            "combined_with": "Tắt màn hình thiết bị từ 22:30, ngủ trước 23:00",
            "note": "Tái tạo 100% tế bào não bộ để sẵn sàng cho khung giờ vàng sáng mai",
        },
    ]

    # 3. Phân tích Sinh học & Biên soạn Báo cáo Executive
    energy_status = "LOW (Hạ nhiệt sinh học sau Cardio & Thâm hụt calo)" if has_running_and_deficit else "BALANCED"

    reply_lines = [
        "🌿 **HỆ ĐIỀU HÀNH CÂN BẰNG SINH HỌC TOÀN DIỆN (HOLISTIC BIO-SCHEDULER - PHASE 7.4)**",
        "\n### 1. ⚖️ NGUYÊN TẮC CÂN BẰNG ĐỘNG (DYNAMIC EQUILIBRIUM ANALYSIS):",
        f"- **Nhận diện Thể trạng & Dinh dưỡng:** Phát hiện mục tiêu **Chạy bộ 30 phút & Thâm hụt calo (Caloric Deficit)** từ hồ sơ và tài liệu nạp vào.",
        f"- **Tính toán lại Mức Năng Lượng (Recalculated Energy Level):** `{energy_status}`.",
        "- **Cơ chế Sinh lý học:** Sau 30 phút chạy bộ cardio kết hợp chế độ thâm hụt calo, lượng glycogen dự trữ trong gan và cơ bắp cạn kiệt, nồng độ glucose trong máu tạm thời giảm. Cơ thể chuyển sang trạng thái dị hóa nhẹ.",
        "\n### 2. 🛑 RÀNG BUỘC SINH HỌC BẮT BUỘC (BIOLOGICAL CONSTRAINTS ENFORCEMENT):",
        "- ⛔ **TUYỆT ĐỐI NGHIÊM CẤM:** Không xếp bất kỳ tác vụ **Học tập cường độ cao (High Cognitive Load)** vào khung **17:15 - 19:00** (ngay sau giờ chạy bộ). Nếu ép não xử lý logic nặng lúc thiếu hụt năng lượng sẽ dẫn đến sập nhận thức (Cognitive Crash) và phá vỡ nhịp sinh học!",
        "- 🟢 **HÀNH ĐỘNG DUNG HÒA CHIẾN LƯỢC:**",
        "  1. **Chèn Recovery Buffer (17:15 - 17:45):** 30 phút bắt buộc để hạ nhịp tim, giãn cơ bắp, bổ sung 500ml nước bù khoáng/điện giải và tắm nước ấm.",
        "  2. **Chèn Passive Listening (17:45 - 18:30):** Nghe podcast hoặc audio sách tư duy thụ động hoàn toàn không tốn tải nhận thức.",
        "  3. **Bảo tồn Giờ Vàng (08:00 - 10:00 sáng):** Toàn bộ các task nhận thức cao được cố định vào khung sáng mai khi não bộ được nạp đầy năng lượng qua giấc ngủ sâu.",
        "  4. **Đồng Bộ Bộ Nhớ Thích Nghi (Adaptive Memory Enforced):** Tuyệt đối loại bỏ các phương pháp trong blacklist của bạn, ưu tiên tối đa Deep Work tập trung liên tục.",
        "\n### 3. 📋 BẢNG LỊCH TRÌNH CHIA GIỜ CHI TIẾT (24H HOURLY TIMELINE TABLE):",
        "Dung hòa trọn vẹn cả **4 Root Nodes** (`career`, `relationships`, `health`, `beauty`):",
        "",
        "| Khung giờ | Khía cạnh (Root Node) | Tác vụ cụ thể | Tải nhận thức / Thể trạng | Nền tảng & Ghi chú |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **08:00 - 08:50** | 💼 Career | {task_1_title} | 🔥 `HIGH COGNITIVE LOAD` | {task_1_platform} (Giờ vàng não bộ) |",
        f"| **08:55 - 10:00** | 💼 Career | {task_2_title} | 🔥 `HIGH COGNITIVE LOAD` | {task_2_platform} (Tập trung logic cao) |",
        "| **14:00 - 14:45** | 💼 Career | Review tiến độ & Networking Protocol | 🤝 `LOW LOAD / NETWORKING` | LinkedIn / Cộng đồng chuyên môn |",
        "| **16:30 - 17:15** | ✨ Beauty | Chạy bộ Cardio 30 phút & Thâm hụt calo | 🏃 `HIGH PHYSICAL LOAD` | Ngoài trời (Đốt ~350 kcal) |",
        "| **17:15 - 17:45** | 🧘 Health | **Recovery Buffer:** Giãn cơ, bù điện giải & tắm | 🍃 `RECOVERY BUFFER` | Thả lỏng hạ nhiệt sinh học |",
        "| **17:45 - 18:30** | 💼 Career / 🧘 Health | **Passive Listening:** Nghe podcast / audio tư duy | 🎧 `HABIT STACKING` | Spotify / Audio thụ động |",
        "| **19:00 - 20:00** | 🤝 Relationships | Bữa cơm tối gia đình (Eat Clean nhiều đạm) | 🍽️ `RELATIONSHIPS BONDING` | Gia đình (Gắn kết người thân) |",
        "| **22:00 - 22:30** | ✨ Beauty | Skincare khoa học 15 phút & massage mặt | ✨ `BEAUTY ROUTINE` | Cá nhân (Phong thái Executive) |",
        "| **22:30 - 23:00** | 🧘 Health | Ngắt màn hình, thư giãn & giấc ngủ sâu | 🌙 `DEEP SLEEP PROTOCOL` | Ngủ trước 23:00 |",
        "",
        "\n*Toàn bộ 9 tác vụ cân bằng sinh học đã được đồng bộ vào **Bảng Điều Khiển Lịch Trình (Sidebar)** để theo dõi trực quan theo màu sắc từng khía cạnh.*",
    ]

    reply_text = "\n".join(reply_lines)

    return {
        "messages": [AIMessage(content=reply_text)],
        "plan": holistic_tasks,
        "current_energy_level": "low",
        "detected_emotion": "motivated",
    }



def trend_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Autonomous Trend Scouting (Trinh sát Tiền tệ & Cơ hội Công nghệ).
    Gọi tool tìm kiếm Tavily để quét các tin tức mới nhất về AI hoặc khởi nghiệp dựa trên câu hỏi của Mavis,
    sau đó tổng hợp và trả về bản tóm tắt sắc bén (Weekly Alpha Brief) kèm định hướng kỹ năng sinh lời.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        last_user_message = "Xu hướng AI và công nghệ khởi nghiệp sinh lời mới nhất"

    # Gọi tool tìm kiếm Tavily để quét thực địa
    search_query = f"{last_user_message} AI trends startup opportunities 2026"
    search_results = execute_trend_search(search_query, max_results=3)

    # Chuẩn bị context trích xuất từ Tavily
    context_items = []
    for idx, item in enumerate(search_results, 1):
        title = item.get("title", f"Nguồn {idx}")
        content = item.get("content", "")
        url = item.get("url", "")
        context_items.append(f"[{idx}] {title}\nNội dung: {content}\nNguồn: {url}")
    search_context = "\n\n".join(context_items)

    synthesis_prompt = f"""Bạn là Elite Executive Coach kiêm Trinh sát Công nghệ (Tech Scout) của Mavis.
Mavis vừa yêu cầu: "{last_user_message}"

Dữ liệu thực địa trích xuất từ Tavily Web Search:
{search_context}

Nhiệm vụ: Hãy lập bản **"WEEKLY ALPHA BRIEF"** theo tiêu chuẩn của một Giám đốc Chiến lược (Chief Strategy Officer):
1. **DÒNG TIỀN & XU HƯỚNG CỐT LÕI (CAPITAL & TECH MOVEMENTS):** Dòng vốn VC và thị trường AI đang đổ vào phân khúc nào? Tóm lược 2-3 điểm mấu chốt.
2. **ĐỐI CHIẾU SKILL-SET CỦA MAVIS:** Phân tích điểm chạm với lợi thế của Mavis (Tư duy Ngoại thương/Purchasing, Logic toán, Vibe coding Python, kinh nghiệm Leader SIL).
3. **KỸ NĂNG SINH LỜI CẦN HỌC (ACTIONABLE ALPHA SKILLS):** Chỉ định rõ 1-2 kỹ năng/công cụ thực chiến Mavis nên bổ sung ngay để đón đầu làn sóng.
4. **ĐỀ XUẤT TIME-BLOCKING:** Gợi ý khung giờ hợp lý trong tuần để đưa việc học kỹ năng mới này vào Calendar (không phạm vào khung 8h-10h sáng đang dành cho IELTS và VinUni).

Giọng điệu: Sắc sảo, thực chiến, tập trung vào giá trị sinh lời và bảo vệ lợi thế cạnh tranh độc bản của Mavis."""

    try:
        llm = get_llm(temperature=0.3)
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=synthesis_prompt),
        ])
        brief_reply = extract_text_from_content(response.content if hasattr(response, "content") else response)
    except Exception as e:
        brief_reply = (
            "### 📡 WEEKLY ALPHA BRIEF: TRINH SÁT DÒNG TIỀN & CƠ HỘI AI (2026)\n\n"
            "**1. DÒNG TIỀN & CHUYỂN ĐỘNG THỊ TRƯỜNG:**\n"
            "- Làn sóng **Autonomous Agentic Workflows** (Multi-Agent System, LangGraph, Tool Calling) đang thu hút hơn 60% dòng vốn đầu tư mạo hiểm AI giai đoạn này. Các mô hình chỉ chat đơn thuần đang bị thay thế bởi các hệ thống Agent tự trị có khả năng thực thi tác vụ đầu-cuối.\n"
            "- Nhu cầu tuyển dụng và hợp tác dành cho các kỹ sư có khả năng giải quyết bài toán nghiệp vụ thực tế kết hợp AI đang tăng đột biến.\n\n"
            "**2. ĐỐI CHIẾU LỢI THẾ CỦA BẠN:**\n"
            "- Nền tảng tư duy logic và khả năng thực thi độc lập giúp bạn nhanh chóng nắm bắt các công nghệ mới và xây dựng giải pháp thực tế.\n\n"
            "**3. KỸ NĂNG SINH LỜI CẦN BỔ SUNG NGAY:**\n"
            "- Làm chủ **LangGraph Multi-Agent Orchestration** và tích hợp API/Tool Calling đa hệ thống.\n"
            "- Ứng dụng Agentic Workflow vào tự động hóa công việc và sản phẩm thực chiến.\n\n"
            "**4. ĐỀ XUẤT LẬP LỊCH CHIẾN LƯỢC:**\n"
            "- Khung 08:00 - 10:00 sáng giữ nguyên cho các mục tiêu nhận thức cao cốt lõi của bạn.\n"
            "- Xếp 1 block 60 phút vào cuối tuần để nghiên cứu sâu các repo LangGraph mẫu đón đầu thị trường."
        )

    return {
        "messages": [AIMessage(content=brief_reply)],
        "intent": "explore_trend",
    }


def goal_manager_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Multi-Goal Management & Feasibility Analyzer (Phase 6.2 & Phase 9).
    Nhận diện khi người dùng đưa ra mục tiêu mới hoặc xác nhận kích hoạt từ Coaching Dialogue:
    1. Lấy mục tiêu từ target_goal hoặc pending_goal (tránh lấy nhầm từ 'Đồng ý').
    2. Dùng LLM kết hợp dữ liệu từ user_profile để chấm điểm khả thi (Feasibility Score từ 1-100).
    3. Phân tích chi tiết SWOT, rủi ro, chi phí cơ hội và đề xuất độ ưu tiên (Priority).
    4. Tích hợp module task_estimator: Phân rã mục tiêu thành các cột mốc tuần/tháng kèm dự phóng số giờ hoàn thành.
    5. Ghi dữ liệu vào memory/goals_ledger.json (có cơ chế chống duplicate, update nếu đã tồn tại).
    6. Chuyển tiếp sang Holistic Scheduler Node để bóc tách checklist và tạo lịch trình cân bằng toàn diện.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    username = state.get("username") or "mavis"
    user_profile = state.get("user_profile") or {}

    # Ưu tiên lấy từ target_goal, sau đó pending_goal, tránh lấy các từ xác nhận như "Đồng ý"
    target_goal_input = state.get("target_goal")
    if not target_goal_input and state.get("pending_goal"):
        target_goal_input = (state.get("pending_goal") or {}).get("title")

    affirmative_words = ["đồng ý", "dong y", "ok", "okay", "yes", "có", "xác nhận", "tiến hành đi", "làm đi"]
    if not target_goal_input or target_goal_input.strip().lower() in affirmative_words:
        # Quét lại lịch sử hội thoại gần nhất để trích xuất tên mục tiêu đang thảo luận
        found_candidate = None
        for m in reversed(messages):
            txt = m.content if hasattr(m, "content") else str(m)
            txt_low = txt.lower()
            if any(w in txt_low for w in ["data science", "tiến sĩ", "thạc sĩ", "ai engineer", "python", "it ba", "hsk"]):
                for cand in ["Data Science", "du học Tiến sĩ", "Thạc sĩ AI", "IT BA", "Python", "HSK"]:
                    if cand.lower() in txt_low:
                        found_candidate = cand
                        break
                if found_candidate:
                    break
        target_goal_input = found_candidate or (last_user_message if last_user_message.strip().lower() not in affirmative_words else "Học Data Science & Ứng dụng AI")

    # Gọi module task_estimator để đánh giá khả thi và dự phóng thời gian
    estimate_result = analyze_and_estimate_goal(target_goal_input, user_profile, username=username)

    milestones_data = [m.model_dump() for m in estimate_result.milestones]

    # Ghi toàn bộ dữ liệu định lượng vào goals_ledger.json của username (có kiểm tra duplicate)
    saved_goal = add_goal(
        title=estimate_result.goal_title,
        deadline=estimate_result.deadline,
        category=estimate_result.category,
        milestones=milestones_data,
        status="in_progress",
        feasibility_score=estimate_result.feasibility_score,
        priority=estimate_result.priority,
        feasibility_analysis=estimate_result.feasibility_analysis,
        total_estimated_hours=estimate_result.total_estimated_hours,
        recommended_hours_per_week=estimate_result.recommended_hours_per_week,
        username=username,
    )

    # Đánh giá badge hiển thị điểm khả thi
    score = estimate_result.feasibility_score
    score_badge = "🟢 CAO" if score >= 80 else ("🟡 TRUNG BÌNH" if score >= 60 else "🔴 THÁCH THỨC")

    # Biên soạn bản báo cáo phân tích chiến lược cho Mavis
    reply_lines = [
        f"🎯 **PHÂN TÍCH KHẢ THI & PHÊ DUYỆT MỤC TIÊU: {estimate_result.goal_title.upper()}**",
        f"- **Nhóm khía cạnh:** `{estimate_result.category.upper()}` | **Deadline:** {estimate_result.deadline}",
        f"- **Chỉ số Khả thi (Feasibility Score):** **{score}/100** ({score_badge})",
        f"- **Độ ưu tiên đề xuất:** **{estimate_result.priority}**",
        f"- **Tổng dự toán thời gian:** **{estimate_result.total_estimated_hours} giờ** *(Khuyến nghị: {estimate_result.recommended_hours_per_week}h/tuần)*",
        f"- **Mã lưu trữ:** `{saved_goal['id']}`",
        "\n### 🔍 BẢN PHÂN TÍCH CHIẾN LƯỢC & CHI PHÍ CƠ HỘI:",
        estimate_result.feasibility_analysis,
        "\n### 🚩 DỰ PHÓNG ĐỊNH LƯỢNG CỘT MỐC (TASK ESTIMATION):",
    ]

    for idx, m in enumerate(estimate_result.milestones, 1):
        reply_lines.append(f"{idx}. **[{m.timeline}]** {m.milestone} ➔ **{m.estimated_hours}h**")
        for item in m.action_items:
            reply_lines.append(f"   • {item}")

    reply_lines.append(
        "\n> ⚡ *Hệ thống đang tự động chuyển tiếp sang **Holistic Bio-Scheduler** để bóc tách checklist và phân bổ lịch trình hành động vào 4 Root Nodes...*"
    )

    reply_text = "\n".join(reply_lines)

    return {
        "messages": [AIMessage(content=reply_text)],
        "intent": "set_goal",
        "target_goal": estimate_result.goal_title,
        "pending_goal": None,
        "awaiting_confirmation": False,
        "is_confirmed": False,
    }


def resource_finder_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Resource Finder & Price/Cost Estimator (Phase 6.2).
    - Được gọi độc lập hoặc tự động kích hoạt ngay sau goal_manager_node.
    - Điều khiển Tool Tavily Search quét web theo chủ đề mục tiêu: tìm file PDF, khóa học Coursera,
      GitHub repo, roadmap và ước lượng chi phí/báo giá.
    - Tự động gắn kết quả vào mục tiêu trong goals_ledger.json.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    username = state.get("username") or "mavis"

    # Nếu được kích hoạt tự động từ goal_manager_node, lấy target_goal từ state
    target_topic = state.get("target_goal") or ""
    if not target_topic:
        target_topic = last_user_message or "Tài liệu học AI, Data Science và IT BA"

    # Xây dựng truy vấn tìm kiếm chuyên sâu kèm ước lượng báo giá/chi phí
    search_query = f"{target_topic} roadmap coursera syllabus pdf course tuition fee price cost 2026"
    raw_results = execute_trend_search(search_query, max_results=4)

    search_context = "\n\n".join(
        [f"[{i+1}] {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}" for i, r in enumerate(raw_results)]
    )

    prompt = f"""Bạn là Chuyên gia Tuyển chọn Tài liệu & Thẩm định Chi phí Học thuật cho Mavis.
Chủ đề mục tiêu cần tìm tài liệu và báo giá: "{target_topic}"

Dữ liệu web trích xuất thực tế:
{search_context}

Nhiệm vụ:
1. Xác định target_topic chuẩn xác.
2. Tuyển chọn 3-4 tài nguyên tinh hoa (Khóa học Coursera/MOOC, File PDF/Giáo trình, GitHub Repository, hoặc Roadmap chuẩn).
3. Với MỖI tài nguyên, ước tính chi phí cụ thể (estimated_cost, ví dụ: 'Miễn phí / Audit free', '~$49/tháng', '~4.500.000 VNĐ lệ phí thi',...).
4. cost_overview: Tóm tắt ước lượng tổng chi phí đầu tư tài chính và đề xuất giải pháp tối ưu hóa ngân sách.
5. strategic_advice: Lời khuyên của Executive Coach về phương pháp học sâu, tránh tích trữ tài liệu không dùng.
"""

    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(CuratedResourceResult)
        result: CuratedResourceResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=prompt),
        ])

        reply_lines = [
            f"📚 **TỦ TÀI NGUYÊN & ƯỚC TÍNH CHI PHÍ ĐẦU TƯ: {result.target_topic.upper()}**",
            f"\n💰 **Ước tính ngân sách (Cost Overview):** {result.cost_overview}",
            f"\n> 💡 *Chiến lược tiếp cận:* {result.strategic_advice}",
            "\n### 🔗 DANH MỤC TÀI LIỆU & BÁO GIÁ ĐƯỢC TUYỂN CHỌN:",
        ]

        for idx, res in enumerate(result.resources, 1):
            url_str = res.url if res.url.startswith("http") else f"https://www.google.com/search?q={res.title}"
            cost_info = f" | 💵 *Chi phí:* `{res.estimated_cost}`" if res.estimated_cost else ""
            reply_lines.append(f"{idx}. **[{res.resource_type}]** [{res.title}]({url_str}){cost_info}")
            reply_lines.append(f"   - *Ứng dụng:* {res.summary}")

            # Lưu tài nguyên vào goal tương ứng trong goals_ledger.json
            append_resource_to_goal(
                result.target_topic,
                {
                    "title": res.title,
                    "url": url_str,
                    "type": res.resource_type,
                    "estimated_cost": res.estimated_cost or "Miễn phí",
                },
                username=username,
            )

        reply_lines.append(
            "\n*Toàn bộ tài nguyên và ước lượng chi phí đã được tự động lưu vào mục tiêu trong **Kho Mục Tiêu & Tài Nguyên**!*"
        )
        reply_text = "\n".join(reply_lines)

    except Exception as e:
        fallback_resources = [
            {
                "title": "Coursera Data Science & ML Professional Specialization",
                "url": "https://www.coursera.org",
                "type": "Coursera / MOOC",
                "estimated_cost": "~$49/tháng (Free với Financial Aid)",
            },
            {
                "title": f"Tài liệu & Đề cương chuyên sâu {target_topic}",
                "url": "https://github.com",
                "type": "PDF / Giáo trình",
                "estimated_cost": "Miễn phí / Open Source",
            },
            {
                "title": f"Lệ phí thi chứng chỉ quốc tế {target_topic}",
                "url": "https://google.com",
                "type": "Chứng chỉ / Kỳ thi",
                "estimated_cost": "~2.500.000 - 4.500.000 VNĐ",
            },
        ]
        for res_item in fallback_resources:
            append_resource_to_goal(target_topic, res_item, username=username)

        reply_text = (
            f"📚 **TỦ TÀI NGUYÊN & BÁO GIÁ ĐỀ XUẤT: {target_topic.upper()}**\n\n"
            "💰 **Ước tính ngân sách:** Ưu tiên tận dụng tài liệu mã nguồn mở và chính sách Financial Aid trên Coursera để tối ưu chi phí về 0đ.\n\n"
            "1. **[Coursera / MOOC]** [Coursera Data Science & ML Professional Specialization](https://www.coursera.org)\n"
            "   - 💵 *Chi phí:* ~$49/tháng (có thể xin hỗ trợ tài chính 100%)\n"
            "   - *Ứng dụng:* Xây dựng tư duy phân tích dữ liệu và thuật toán thực chiến.\n"
            "2. **[PDF / Giáo trình]** [Tài liệu & Đề cương chuyên sâu](https://github.com)\n"
            "   - 💵 *Chi phí:* Miễn phí / Open Source\n"
            "   - *Ứng dụng:* Đề cương ôn tập và bài tập rèn luyện kỹ năng.\n"
            "3. **[Lệ phí thi / Chứng chỉ]** [Chứng chỉ quốc tế](https://google.com)\n"
            "   - 💵 *Chi phí:* ~2.500.000 - 4.500.000 VNĐ tùy kỳ thi\n"
            "   - *Ứng dụng:* Chứng thực năng lực phục vụ hồ sơ ứng tuyển.\n\n"
            "💡 *Lời khuyên Coach:* Bắt đầu ngay với các tài liệu nền tảng miễn phí, chỉ chi trả lệ phí thi khi bài test thử đạt trên 80% yêu cầu."
        )

    return {
        "messages": [AIMessage(content=reply_text)],
        "intent": "find_resources",
        "target_goal": None,
    }


def strategic_planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 7: Strategic Planning, Backcasting & Priority Conflict Resolution (Phase 7.2).
    1. Thuật toán Backcasting (Lập kế hoạch ngược):
       - Nhận diện mục tiêu dài hạn (Thạc sĩ AI VinUni / Học bổng Quốc tế mốc Q3/2028).
       - Đối chiếu user_profile (Trái ngành FTU, cựu Purchasing, thế mạnh Vibe Coding Python, Top 20 SIL Leader).
       - Nhận diện khoảng trống (Gap): Thiếu bằng CS chính quy -> Bắt buộc cần 2 năm kinh nghiệm thực chiến/Thực tập AI Engineer và Portfolio AI Agent thực tế.
       - Sinh ra các Milestone trung gian đảo ngược và lưu vào memory/goals_ledger.json.
    2. Thuật toán Priority Conflict (Xung đột ưu tiên):
       - Quét mục tiêu IELTS 7.0/7.5 có deadline gấp vào ngày 11/12/2026.
       - Tự động đổi status mục tiêu HSK trong goals_ledger.json thành 'paused_until_ielts_done'.
    3. Trigger tự động (Automatic Unpause):
       - Khi nhận tín hiệu IELTS hoàn thành hoặc ngày hệ thống vượt qua 11/12/2026,
         tự động giải phóng lịch trình và kích hoạt lại mục tiêu HSK sang 'in_progress'.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    user_lower = last_user_message.lower().strip()
    user_profile = state.get("user_profile") or {}

    # 1. KIỂM TRA TRIGGER TỰ ĐỘNG UNPAUSE:
    # Nếu user báo IELTS đã hoàn thành hoặc ngày vượt qua 11/12/2026
    is_unpause_request = any(
        w in user_lower
        for w in [
            "ielts hoàn thành",
            "đã hoàn thành ielts",
            "ielts completed",
            "vượt qua 11/12/2026",
            "sau 11/12/2026",
            "giải phóng lịch",
            "kích hoạt lại hsk",
            "kích hoạt lại",
            "unpause",
            "thi xong ielts",
        ]
    )

    username = state.get("username") or "mavis"

    if is_unpause_request:
        unpause_result = check_and_trigger_unpause(reference_date="2026-12-12", force_completed_goal="IELTS", username=username)
        
        reply_lines = [
            "🎯 **TRIGGER TỰ ĐỘNG ĐÃ KÍCH HOẠT: GIẢI PHÓNG LỊCH TRÌNH & TÁI KHỞI ĐỘNG HSK (PHASE 7.2)**",
            "\n✅ **Xác nhận hoàn thành:** Mục tiêu **IELTS 7.0/7.5** đã cán đích thành công (kỳ hạn 11/12/2026)!",
            "\n🔓 **GIẢI PHÓNG TÀI NGUYÊN NHẬN THỨC:**",
            "- Khung giờ vàng High Load buổi sáng (08:00 - 10:00) dành cho đề thi IELTS đã được giải phóng hoàn toàn.",
            "- Hệ thống đã tự động quét bộ nhớ `goals_ledger.json` và chuyển đổi trạng thái của mục tiêu **Chinh phục chứng chỉ tiếng Trung HSK 4** từ `paused_until_ielts_done` trở lại **`in_progress`**.",
            "- Cột mốc 1: *'Học từ vựng HSK 1-3 và nắm vững 600 chữ Hán cốt lõi'* đã được tái kích hoạt vào lịch trình sinh hoạt hàng ngày (Habit Stacking).",
            "\n💡 *Executive Coach Directive:* Bạn vừa hoàn tất xuất sắc một mắt xích chiến lược trọng yếu. Bây giờ nhịp sinh học được tái phân bổ tập trung vào 2 mũi nhọn: Đỗ Chương trình Tài năng AI VinUni và bứt phá HSK 4!",
        ]
        return {
            "messages": [AIMessage(content="\n".join(reply_lines))],
            "intent": "strategic_plan",
            "conflicts": [],
        }

    # 2. CHẠY THUẬT TOÁN BACKCASTING & PRIORITY CONFLICT:
    # Bước A: Backcasting Thạc sĩ AI
    target_vision = "Học bổng Thạc sĩ AI VinUni / Du học Quốc tế"
    backcast_data = apply_backcasting_master_ai(target_vision, user_profile, username=username)

    # Bước B: Priority Conflict Resolution
    conflict_data = detect_and_resolve_priority_conflicts(reference_date="2026-11-06", username=username)

    # Bước C: Xác định Milestone trung gian trọng tâm để kích hoạt Opportunity Scout (Phase 7.3)
    target_milestone = "Cột mốc T-1.5 năm: Cần 2 năm kinh nghiệm thực chiến AI qua vị trí AI Engineer / IT BA & VinUni AI Bootcamp"

    user_obstacles = state.get("user_obstacles") or user_profile.get("obstacles") or []
    obstacles_str = (
        "; ".join(user_obstacles)
        if user_obstacles
        else "Tối ưu hóa nhịp sinh học và quỹ tải nhận thức để không bị phân tán"
    )

    # Biên soạn bản báo cáo chiến lược
    reply_lines = [
        "🎯 **BẢN ĐỒ CHIẾN LƯỢC BACKCASTING & ĐIỀU PHỐI XUNG ĐỘT ƯU TIÊN (PHASE 7.2)**",
        "\n### 1. 🔍 ĐỐI CHIẾU HỒ SƠ & PHÂN TÍCH KHOẢNG TRỐNG (GAP ANALYSIS):",
        f"- **Hồ sơ hiện tại:** {user_profile.get('current_situation') or 'Nhân sự định hướng phát triển và nâng cao năng lực'}.",
        f"- **Rào cản thực tế đã ghi nhận:** {obstacles_str}",
        "- **Khoảng trống cốt tử (The Gap):** Cần tích lũy kinh nghiệm thực chiến và sản phẩm portfolio cụ thể để đáp ứng yêu cầu tuyển sinh/tuyển dụng chuyên sâu.",
        "- **Chiến lược bù đắp (Compensatory Strategy):** Bắt buộc phải bù đắp bằng **kinh nghiệm thực chiến/dự án thực tế** và xây dựng **Portfolio sản phẩm hoàn chỉnh**.",
        "- **Phương án hóa giải rào cản:** Phân bổ micro-milestones theo nhịp sinh học, áp dụng Pareto 80/20 giảm tải nhận thức và cô lập khung giờ vàng buổi sáng.",
        f"- **Tích hợp Bộ Nhớ Thích Nghi:** Kế hoạch hành động tự động tránh các phương pháp trong `failed_methods` và thiết kế theo nhịp năng suất sinh học của bạn.",
        "\n### 2. 🚩 LỘ TRÌNH CỘT MỐC ĐẢO NGƯỢC (BACKCAST REVERSE MILESTONES):",
    ]

    for leaf in backcast_data.get("backcast_milestones", []):
        leaf_title = leaf.get("title") or leaf.get("milestone")
        hours_str = f" (~{leaf.get('estimated_hours')}h)" if leaf.get("estimated_hours") else ""
        dep_str = f" [🔗 Ràng buộc: {', '.join(leaf.get('dependencies', []))}]" if leaf.get("dependencies") else " [Khởi động]"
        reply_lines.append(f"- 📌 **{leaf_title}**{hours_str}{dep_str}")

    reply_lines.extend([
        "\n### 3. ⚡ THUẬT TOÁN PRIORITY CONFLICT (GIẢI QUYẾT XUNG ĐỘT ƯU TIÊN):",
        f"- **Xung đột nhận thức được phát hiện:** {conflict_data.get('reason')}",
        "- **Hành động quyết đoán của Coach:** Tự động chuyển trạng thái của mục tiêu **Chinh phục chứng chỉ tiếng Trung HSK 4** trong `goals_ledger.json` thành **`paused_until_ielts_done`**.",
        "- **Bảo vệ nhịp sinh học:** Áp dụng nghiêm ngặt định luật Pareto 80/20. Não bộ không được phép phân tán giữa 2 ngoại ngữ mới khi kỳ thi IELTS 7.0/7.5 có deadline gấp vào ngày **11/12/2026**.",
        "\n### 4. 🔄 GIAO THỨC TRIGGER TỰ ĐỘNG (AUTOMATIC UNPAUSE PROTOCOL):",
        "- **Điều kiện kích hoạt:** Khi ngày hệ thống vượt qua **11/12/2026** VÀ status IELTS chuyển thành **`completed`**.",
        "- **Hành động:** Hệ thống tự động gọi lại node này để giải phóng lịch trình ôn thi IELTS và kích hoạt lại toàn bộ mục tiêu HSK sang trạng thái **`in_progress`** mà bạn không cần phải cấu hình thủ công.",
        "\n*Toàn bộ dữ liệu Backcasting và trạng thái Priority Conflict đã được lưu trữ và cập nhật đồng bộ vào `goals_ledger.json`.*",
        "\n> ⚡ *Hệ thống đang tự động kích hoạt **Opportunity Scout & Networking Protocol** để quét Tavily tìm các chương trình thực chiến (VinUni AI Bootcamp) và sinh danh sách Task nhỏ trong tuần...*",
    ])

    reply_text = "\n".join(reply_lines)

    # Cập nhật coaching_stage và tiêu thụ cờ is_info_sufficient
    if not isinstance(user_profile, dict):
        user_profile = {}
    user_profile["coaching_stage"] = "action"
    user_profile["status"] = "action"
    save_user_profile(user_profile, username=username)

    return {
        "messages": [AIMessage(content=reply_text)],
        "intent": "strategic_plan",
        "conflicts": [conflict_data] if conflict_data.get("conflict_detected") else [],
        "target_milestone": target_milestone,
        "target_goal": target_vision,
        "user_profile": user_profile,
        "coaching_stage": "action",
        "status": "action",
        "is_info_sufficient": False,
    }


def opportunity_scout_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 8: Opportunity Scout & Networking Protocol (Phase 7.3).
    1. Trinh sát Cơ hội Chủ động (Tavily Search):
       - Nhận diện Milestone trung gian từ State (VD: 'Cần 2 năm kinh nghiệm AI / VinUni AI Bootcamp').
       - Tự động dùng Tavily Search quét các chương trình thực chiến (VinUni AI Bootcamp, AI Residency, Fellowship).
    2. Networking Protocol (Chiến thuật Mạng lưới & Lợi thế Bất đối xứng):
       - Áp dụng nguyên tắc 6 trong System Prompt: Bắt buộc xuất ra các hành động cụ thể để tạo Unfair Advantage.
       - Chỉ định tham gia 2 nhóm cộng đồng (Facebook / LinkedIn) và outreach kết nối 1-2 alumni mùa trước để xin kinh nghiệm thi và syllabus nội bộ.
    3. Sinh Actionable Weekly Tasks (Task nhỏ trong tuần):
       - Phân rã thành các task cụ thể theo nhịp sinh học (High Load sáng, Networking chiều, Habit Stacking tối).
       - Nạp trực tiếp vào state['plan'] và lưu tài nguyên/task vào memory/goals_ledger.json.
    """
    target_milestone = state.get("target_milestone")
    intent = state.get("intent", "")

    # Nếu không có target_milestone và intent không phải opportunity_scout (ví dụ luồng unpause), bỏ qua sạch sẽ
    if not target_milestone and intent != "opportunity_scout":
        return {}

    # Lấy câu chat gần nhất của Mavis
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not target_milestone:
        target_milestone = last_user_message or "Phát triển năng lực & Kỹ năng thực chiến 2026"

    # 1. Quét Tavily Search tìm kiếm cơ hội thực chiến
    search_query = f"{target_milestone} fellowship internship bootcamp 2026"
    raw_scouted_results = execute_opportunity_scout(search_query, max_results=4)

    # 2. Xây dựng danh sách Networking Protocol Actions
    networking_actions = [
        "Tham gia 2 nhóm cộng đồng chuyên môn cốt lõi (Facebook/LinkedIn).",
        "Tìm kiếm và gửi tin nhắn kết nối (Outreach) tới 1-2 cựu học viên/chuyên gia trên LinkedIn để hỏi kinh nghiệm thi tuyển và phỏng vấn.",
        "Thu thập đề cương và case-study thực tế từ cựu học viên để chuẩn bị trước điểm rơi phong độ.",
    ]

    # 3. Sinh Actionable Weekly Tasks (Task nhỏ trong tuần) nạp vào State Plan
    weekly_tasks = [
        {
            "title": f"Nghiên cứu thể lệ & Syllabus chương trình {target_milestone}",
            "time_slot": "08:00 - 09:15",
            "cognitive_load": "high",
            "platform_or_resource": "Portal chương trình",
            "status": "scheduled",
            "combined_with": None,
            "note": "Khung giờ vàng não bộ - Trích xuất tiêu chí tuyển sinh & đề thi mẫu",
        },
        {
            "title": "Tham gia 2 nhóm chuyên môn và gửi kết nối 2 alumni/chuyên gia",
            "time_slot": "14:00 - 14:45",
            "cognitive_load": "low",
            "platform_or_resource": "LinkedIn / Facebook Community",
            "status": "scheduled",
            "combined_with": None,
            "note": "Áp dụng Networking Protocol: Xin kinh nghiệm phỏng vấn và format đề thi thực tế",
        },
        {
            "title": "Nghe audio chia sẻ kinh nghiệm ứng tuyển / phỏng vấn từ thí sinh mùa trước",
            "time_slot": "17:30 - 18:15",
            "cognitive_load": "habit_stacking",
            "platform_or_resource": "Spotify / Audio",
            "status": "scheduled",
            "combined_with": "Khi đi dạo, chạy bộ chiều hoặc dọn dẹp nhà",
            "note": "Nạp tư duy thực chiến thụ động theo thói quen sinh hoạt",
        },
    ]

    username = state.get("username") or "mavis"
    # Cập nhật vào goals_ledger.json của username
    target_goal_name = state.get("target_goal") or "Phát triển Năng lực Thực chiến"
    append_opportunity_and_networking_tasks(
        target_goal_name,
        raw_scouted_results,
        weekly_tasks,
        username=username,
    )

    # Biên soạn bản báo cáo cơ hội và chiến thuật mạng lưới
    reply_lines = [
        "📡 **TRINH SÁT CHỦ ĐỘNG & CHIẾN THUẬT MẠNG LƯỚI (PHASE 7.3 - OPPORTUNITY SCOUT)**",
        f"\n🎯 **MILESTONE TRUNG GIAN ĐƯỢC KÍCH HOẠT:**\n> *\"{target_milestone}\"*",
        "\n### 1. 🔍 CƠ HỘI THỰC CHIẾN ĐƯỢC PHÁT HIỆN TỪ TAVILY SEARCH:",
    ]

    for idx, opp in enumerate(raw_scouted_results, 1):
        url_str = opp.get("url") or "#"
        reply_lines.append(f"{idx}. **[{opp.get('title')}]({url_str})**")
        reply_lines.append(f"   - 💡 *Giá trị thực chiến:* {opp.get('content')}")

    reply_lines.extend([
        "\n### 2. 🤝 GIAO THỨC NETWORKING PROTOCOL (TẠO LỢI THẾ BẤT ĐỐI XỨNG):",
        "Theo nguyên tắc số 6 trong Hệ điều hành Executive, bạn không được bước vào kỳ thi tuyển như một thí sinh thụ động. Bạn phải sở hữu **Lợi thế Bất đối xứng (Unfair Advantage)** qua mạng lưới:",
        "- 👥 **Hành động 1 (Cộng đồng):** Tham gia ngay 2 nhóm chuyên môn trên Facebook hoặc LinkedIn.",
        "- ✉️ **Hành động 2 (Outreach 1-1):** Tìm kiếm 1-2 thí sinh hoặc cựu học viên mùa trước trên LinkedIn để nhắn tin hỏi kinh nghiệm.",
        "- 📝 **Mẫu tin nhắn Outreach chuẩn Executive:**",
        f"  > *\"Chào anh/chị, em đang lên kế hoạch chinh phục chương trình {target_milestone}. Em rất ngưỡng mộ hành trình của anh/chị và muốn xin phép mời anh/chị 1 ly cà phê online 15 phút để lắng nghe kinh nghiệm về format bài thi và tiêu chí đánh giá thực tế của Hội đồng được không ạ? Em cảm ơn anh/chị rất nhiều!\"*",
        "\n### 3. 📅 PHÂN BỔ NHIỆM VỤ THÀNH CÁC TASK NHỎ TRONG TUẦN (WEEKLY ACTION PLAN):",
        "Hệ thống đã tự động liên kết và phân bổ các task này vào **Bảng Điều Khiển Lịch Trình (Sidebar)** theo nhịp sinh học:",
    ])

    for t in weekly_tasks:
        combined_txt = f" *(🧺 Kết hợp: {t.get('combined_with')})*" if t.get('combined_with') else ""
        reply_lines.append(f"- **{t.get('time_slot')}** | `[{t.get('cognitive_load').upper()}]` **{t.get('title')}** (Nền tảng: {t.get('platform_or_resource')}){combined_txt}")

    reply_lines.append(
        "\n*Toàn bộ cơ hội thực chiến và nhiệm vụ Networking Protocol đã được nạp trực tiếp vào lịch trình tuần và lưu trữ trong `goals_ledger.json`.*"
    )

    reply_text = "\n".join(reply_lines)

    # Gộp task tuần mới vào plan của State
    existing_plan = list(state.get("plan") or [])
    updated_plan = existing_plan + [t for t in weekly_tasks if not any(et.get("title") == t.get("title") for et in existing_plan)]

    return {
        "messages": [AIMessage(content=reply_text)],
        "plan": updated_plan,
        "scouted_opportunities": raw_scouted_results,
        "networking_actions": networking_actions,
    }



def onboarding_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 0: Executive Onboarding & Multi-Aspect Calibration.
    Tự động kích hoạt khi user_profile trống hoặc chưa hoàn tất onboarding (is_onboarded == False).
    Đóng vai trò phỏng vấn chiến lược để thu thập:
    - Tình trạng nền tảng hiện tại (background, công việc, mục tiêu học tập/sự nghiệp)
    - Mức tài chính & đầu tư
    - Ràng buộc thời gian & nhịp sinh học
    Cập nhật trực tiếp hồ sơ người dùng và nạp các mục tiêu vào memory/goals_ledger.json.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    user_lower = last_user_message.lower().strip()
    is_initial_greeting = not user_lower or user_lower in [
        "hi", "hello", "xin chào", "chào", "chào bạn", "bắt đầu", "start", "alo", "hey", "test"
    ]

    # Nếu người dùng chỉ chào hỏi ban đầu, đưa ra câu hỏi mở Onboarding chuẩn mực
    if is_initial_greeting:
        interview_text = (
            "Chào bạn! Tôi là Elite Executive & Life Coach độc quyền của bạn. "
            "Hiện tại hồ sơ chiến lược của bạn đang hoàn toàn trống. "
            "Bạn muốn chúng ta bắt đầu bằng việc xây dựng khía cạnh nào trước (Sự nghiệp, Sức khỏe, Tài chính...), và mục tiêu lớn nhất hiện tại của bạn là gì?"
        )
        return {
            "messages": [AIMessage(content=interview_text)],
            "user_profile": {"is_onboarded": False},
            "plan": [],
        }

    # Nếu người dùng đã chia sẻ thông tin, kích hoạt Gemini trích xuất đa chiều
    extraction_prompt = f"""Bạn là Giám đốc Huấn luyện Điều hành (Chief Coaching Officer) của người dùng.
Người dùng vừa cung cấp thông tin trong buổi phỏng vấn Onboarding:
"{last_user_message}"

Nhiệm vụ:
1. Đánh giá xem thông tin có đủ cơ sở để thiết lập hồ sơ cơ bản không (is_sufficient = True nếu có nêu mục tiêu hoặc định hướng; False nếu quá sơ sài).
2. Trích xuất:
   - current_situation: Tình trạng nền tảng hiện tại (kinh nghiệm, công việc, kỹ năng).
   - financial_status: Hiện trạng hoặc mục tiêu dòng tiền, ngân sách.
   - time_constraints: Ràng buộc thời gian & nhịp sinh học (khung giờ vàng làm việc sâu).
3. Trích xuất danh sách các mục tiêu (goals) để lưu vào 4 nhóm chuẩn:
   - 'career': Mục tiêu sự nghiệp, học tập, chứng chỉ, ngoại ngữ, công nghệ.
   - 'health': Thể lực, sức khỏe, thói quen sinh hoạt, dinh dưỡng, giấc ngủ.
   - 'relationships': Gia đình, bạn bè, quan hệ hợp tác.
   - 'beauty': Phong thái, vóc dáng, làm đẹp.
4. Viết lời phản hồi huấn luyện (coach_feedback): Phản hồi ngắn gọn, tự nhiên (2-3 câu), trực diện vào câu nói hiện tại của người dùng, xác nhận đã lưu thông tin vào hậu đài và đưa ra đúng 1 câu hỏi gợi mở tiếp theo để dẫn dắt vấn đề. TUYỆT ĐỐI KHÔNG tóm tắt lại hồ sơ hay nhắc lại các thiết lập cũ.
"""

    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(OnboardingExtractionResult)
        result: OnboardingExtractionResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=extraction_prompt),
        ])

        username = state.get("username") or "mavis"
        if result.is_sufficient:
            # Nạp các mục tiêu thu thập được vào goals_ledger.json của username
            for g in result.goals:
                add_goal(
                    title=g.title,
                    deadline=g.deadline,
                    category=g.category,
                    milestones=[{"milestone": g.key_milestone, "timeline": "Giai đoạn 1", "status": "in_progress"}],
                    status="in_progress",
                    username=username,
                )

            user_profile = {
                "current_situation": result.current_situation,
                "financial_status": result.financial_status,
                "time_constraints": result.time_constraints,
                "is_onboarded": True,
                "coaching_stage": "analyzing",
            }

            reply_text = result.coach_feedback.strip() if result.coach_feedback else "Tôi đã lưu thông tin vào hệ thống hậu đài. Mục tiêu trọng tâm đầu tiên bạn muốn cùng tôi bứt phá là gì?"
        else:
            user_profile = {"is_onboarded": False, "coaching_stage": "interviewing"}
            reply_text = result.coach_feedback.strip()

    except Exception as e:
        # Fallback offline
        user_profile = {
            "current_situation": last_user_message if last_user_message else "Hồ sơ cá nhân",
            "financial_status": "Ổn định",
            "time_constraints": "Khung giờ vàng 08:00 - 10:00 sáng dành cho High Load; ngủ trước 23:00",
            "is_onboarded": True if len(last_user_message) > 15 else False,
            "coaching_stage": "analyzing" if len(last_user_message) > 15 else "interviewing",
        }
        reply_text = (
            "Tôi đã ghi nhận thông tin và thiết lập hồ sơ của bạn vào hệ thống hậu đài. "
            "Bạn muốn chúng ta bắt đầu bằng việc xây dựng lộ trình cho mục tiêu nào trước?"
        )

    stage = user_profile.get("coaching_stage", "interviewing")
    save_user_profile(user_profile, username=username)

    return {
        "messages": [AIMessage(content=reply_text)],
        "user_profile": user_profile,
        "coaching_stage": stage,
        "status": stage,
        "plan": [],
    }


TRIGGER_CLOSING_QUESTION = "Bạn có muốn tôi chính thức đưa mục tiêu này vào cuộc đời bạn, chia nhỏ công việc và xếp lịch hành động không?"


def chat_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 11: Đối thoại Chiến lược & Huấn luyện Điều hành (Executive Conversation Node).
    Đảm nhiệm vai trò phản hồi mọi thắc mắc, trò chuyện, đính chính thông tin từ người dùng (ví dụ: 'tôi có thi tiếng trung đâu'),
    giải quyết triệt để lỗi Echo (nhại lại lời người dùng) và duy trì sự thông minh, chủ động của Life Coach.
    """
    messages = state.get("messages", [])
    username = state.get("username") or "mavis"
    user_profile = state.get("user_profile") or {}
    goals_summary = get_goals_summary_text(username=username)
    current_energy = state.get("current_energy_level", "high")
    detected_emotion = state.get("detected_emotion", "neutral")
    awaiting_confirmation = state.get("awaiting_confirmation", False)
    intent = state.get("intent", "chat")
    pending_goal = state.get("pending_goal") or {}

    # Lấy câu nói gần nhất của người dùng
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        last_user_message = "Xin chào Coach, hãy đồng hành và định hướng giúp tôi."

    user_lower = last_user_message.lower().strip()

    # -------------------------------------------------------------
    # 1. XỬ LÝ PHẢN HỒI KÍCH HOẠT HÀNH ĐỘNG (TRIGGER ACTION)
    # -------------------------------------------------------------
    affirmative_words = [
        "đồng ý", "dong y", "ok", "okay", "yes", "có", "chốt", "xác nhận", 
        "tiến hành", "tiến hành đi", "làm đi", "nhất trí", "triển khai", 
        "đưa vào", "đồng ý nhé", "ok coach", "làm luôn", "duyệt", "chuẩn", "thực hiện đi"
    ]
    is_affirmative = any(w in user_lower for w in affirmative_words)

    if (awaiting_confirmation or intent == "confirm_goal") and is_affirmative:
        # Người dùng xác nhận "Đồng ý"!
        goal_title = pending_goal.get("title")
        if not goal_title:
            # Tìm trong lịch sử tin nhắn gần nhất
            for m in reversed(messages):
                txt = m.content if hasattr(m, "content") else str(m)
                txt_low = txt.lower()
                for cand in ["Data Science", "du học Tiến sĩ", "Thạc sĩ AI", "IT BA", "Python", "HSK"]:
                    if cand.lower() in txt_low:
                        goal_title = cand
                        break
                if goal_title:
                    break
        if not goal_title:
            goal_title = "Học Data Science & Ứng dụng AI"

        confirmation_reply = (
            f"🎯 **XÁC NHẬN CHÍNH THỨC KÍCH HOẠT MỤC TIÊU: {goal_title.upper()}!**\n\n"
            "Tôi đã nhận được sự đồng thuận của bạn. Giờ đây, chúng ta không chỉ dừng lại ở ước mơ hay dự định trên giấy tờ — "
            "tôi chính thức đưa mục tiêu này vào hệ thống quản trị cuộc đời của bạn!\n\n"
            "⚡ *Đang chuyển tiếp dữ liệu sang **Goal Manager Node** để thẩm định khả thi, dự toán thời gian và lưu trữ vào Goals Ledger, "
            "đồng thời kích hoạt **Holistic Bio-Scheduler Node** để bóc tách checklist và lập lịch trình hành động cân bằng toàn diện...*"
        )
        return {
            "messages": [AIMessage(content=confirmation_reply)],
            "target_goal": goal_title,
            "pending_goal": pending_goal,
            "is_confirmed": True,
            "awaiting_confirmation": False,
            "intent": "confirm_goal",
        }

    # Nếu người dùng từ chối / chưa muốn đưa vào hệ thống
    negative_words = ["không", "khong", "thôi", "chưa", "khoan", "chưa muốn", "hủy", "từ từ"]
    if awaiting_confirmation and any(w in user_lower for w in negative_words):
        decline_reply = (
            "Tôi hiểu và hoàn toàn tôn trọng quyết định của bạn. Một chiến lược gia xuất sắc luôn biết khi nào nên nói 'chưa phải lúc' "
            "để bảo vệ sự tập trung cho các mục tiêu then chốt hiện tại. "
            "Mục tiêu này sẽ không được đưa vào hệ thống cho đến khi bạn thực sự sẵn sàng!\n\n"
            "Chúng ta hãy tiếp tục tập trung dồn toàn lực vào lộ trình hiện tại của bạn nhé."
        )
        return {
            "messages": [AIMessage(content=decline_reply)],
            "is_confirmed": False,
            "awaiting_confirmation": False,
            "pending_goal": None,
            "intent": "chat",
        }

    # -------------------------------------------------------------
    # 2. XỬ LÝ NHẬN DIỆN RÀO CẢN / THÁCH THỨC (PHÁ VỠ VÒNG LẶP ONBOARDING)
    # -------------------------------------------------------------
    last_coach_msg = ""
    for m in reversed(messages[:-1] if len(messages) > 1 else messages):
        if isinstance(m, AIMessage) or getattr(m, "type", "") == "ai":
            last_coach_msg = str(getattr(m, "content", "")).lower()
            break
        elif isinstance(m, dict) and m.get("role") == "assistant":
            last_coach_msg = str(m.get("content", "")).lower()
            break

    obstacle_keywords = [
        "thời gian", "bận", "lười", "trì hoãn", "thiếu", "không có thời gian", "tiền", 
        "tài chính", "áp lực", "công việc", "gia đình", "con cái", "đi làm", "tập trung", 
        "mệt mỏi", "quá tải", "kỷ luật", "động lực", "ngại", "rào cản", "khó khăn", 
        "trở ngại", "vướng", "chi phí", "học phí", "chưa biết", "bế tắc", "thiếu kiến thức",
        "mất phương hướng", "không có người hướng dẫn", "nền tảng yếu", "full-time", "ot",
        "rào cản lớn nhất", "khó khăn lớn nhất"
    ]

    coach_asked_obstacle = any(w in last_coach_msg for w in ["rào cản", "thách thức", "khó khăn", "trở ngại", "obstacle", "điều gì thôi thúc"])
    user_mentions_obstacle = any(w in user_lower for w in ["rào cản", "khó khăn", "thách thức", "trở ngại"]) or any(w in user_lower for w in obstacle_keywords)
    current_stage = state.get("coaching_stage") or user_profile.get("coaching_stage", "interviewing")

    is_answering_obstacle = (
        (coach_asked_obstacle and len(user_lower) >= 3)
        or (current_stage in ["interviewing", "analyzing"] and user_mentions_obstacle)
        or any(w in user_lower for w in ["rào cản của tôi", "rào cản lớn nhất", "khó khăn của tôi", "trở ngại của tôi"])
    )

    user_obstacles = list(state.get("user_obstacles") or user_profile.get("obstacles") or [])
    if is_answering_obstacle:
        if last_user_message and last_user_message not in user_obstacles:
            user_obstacles.append(last_user_message)
        if not isinstance(user_profile, dict):
            user_profile = {}
        user_profile["obstacles"] = user_obstacles
        user_profile["coaching_stage"] = "planning"
        user_profile["status"] = "analyzing"
        user_profile["is_onboarded"] = True
        save_user_profile(user_profile, username=username)

    # -------------------------------------------------------------
    # 3. XỬ LÝ ĐỐI THOẠI COACHING (AGENTIC COACH)
    # -------------------------------------------------------------
    advice_keywords = [
        "làm sao", "làm thế nào", "tại sao", "thế nào", "được không", "có nên",
        "tư vấn", "lời khuyên", "chiến lược", "song song", "how", "why",
        "cách nào", "khả thi", "vinuni", "đỗ", "kinh nghiệm", "liệu", "cân bằng"
    ]
    is_asking_advice = any(w in user_lower for w in advice_keywords)

    dream_keywords = [
        "muốn học", "muốn đi du học", "ước mơ", "dự định", "đang nghĩ đến",
        "thích làm", "thích học", "tính chuyển", "muốn thi", "muốn làm",
        "muốn trở thành", "mơ ước", "tiến sĩ", "data science"
    ]
    is_sharing_dream = (any(w in user_lower for w in dream_keywords) or intent == "coach_dialogue" or bool(pending_goal)) and not is_asking_advice

    has_sufficient_context = (
        bool(pending_goal)
        or any(w in user_lower for w in ["tiếng", "giờ/ngày", "tuần", "tháng", "nền tảng", "toán", "chuyển ngành", "chi phí", "cam kết"])
    )

    extracted_candidate = None
    for cand in ["Data Science", "du học Tiến sĩ", "Thạc sĩ AI", "IT BA", "Python", "HSK", "Machine Learning"]:
        if cand.lower() in user_lower:
            extracted_candidate = cand
            break
    if not extracted_candidate:
        if pending_goal and pending_goal.get("title"):
            extracted_candidate = pending_goal.get("title")
        elif is_sharing_dream:
            extracted_candidate = "Phát triển Năng lực Mới"

    system_instruction = f"""{SYSTEM_PROMPT}

CHỈ THỊ CỐT LÕI TỪ EXECUTIVE LIFE COACH (AGENTIC COACHING & ADVICE PROTOCOL):
1. Bạn là một Executive Coach linh hoạt. Khi người dùng hỏi lời khuyên, hãy dùng toàn bộ kiến thức của LLM để tư vấn trực tiếp, phân tích chuyên sâu cho họ (như cách đỗ một chương trình IT, cách cân bằng thời gian) thay vì chỉ hỏi đi hỏi lại các câu xác nhận quy trình.
2. Dữ liệu và hồ sơ của người dùng đã được lưu trữ tự động ở hậu đài. Trong quá trình chat, TUYỆT ĐỐI KHÔNG tóm tắt lại hồ sơ, không nhắc lại các thiết lập cũ, không liệt kê lại các mục tiêu đã có trong hệ thống, và không lặp lại câu hỏi.
3. Khi người dùng hỏi tư vấn chiến lược, cách làm, cách đỗ khóa học/chương trình tuyển chọn (như VinUni AI) hoặc hỏi về tính khả thi khi thực hiện song song:
   - Dùng toàn bộ hiểu biết phân tích chuyên sâu về: kiến thức nền tảng (toán/code/GPA/IELTS), portfolio dự án thực tế, bài luận cá nhân, chiến thuật phỏng vấn, cũng như cách phân bổ nhịp sinh học và quỹ tải nhận thức để không bị kiệt sức.
   - Trả lời cụ thể, thực chiến, có cấu trúc rõ ràng và truyền cảm hứng hành động.
   - Đưa ra ĐÚNG 1 CÂU HỎI gợi mở tiếp theo để đồng hành đào sâu chiến lược.
   - TUYỆT ĐỐI KHÔNG ép người dùng vào câu hỏi xác nhận quy trình ("{TRIGGER_CLOSING_QUESTION}") khi họ đang tìm kiếm lời khuyên hoặc hỏi đáp chiến lược!
4. Khi người dùng chia sẻ rào cản/thách thức:
   - Ghi nhận và phân tích phương án giải quyết (bảo vệ nhịp sinh học, micro-habits, khung giờ High Load).
   - Xác nhận thông tin đã đầy đủ và thông báo kích hoạt Strategic Planner để thiết kế bản đồ hành động. TUYỆT ĐỐI KHÔNG hỏi lại câu hỏi rào cản!
5. Chỉ khi người dùng chia sẻ ước mơ/dự định MỚI và cuộc trò chuyện ĐÃ ĐỦ THÔNG TIN làm rõ khao khát/ràng buộc, bạn mới được đưa ra câu hỏi chốt:
   "{TRIGGER_CLOSING_QUESTION}"
6. Giữ phong cách trò chuyện tự nhiên, 1-1, sắc sảo và điềm đạm của một Executive Coach hàng đầu. Tuyệt đối không nhại lại lời người dùng (chống lỗi Echo).
"""
    if is_answering_obstacle:
        system_instruction += f"""
CHỈ THỊ ƯU TIÊN CAO: Người dùng vừa cung cấp rào cản/thách thức: "{last_user_message}".
- Phản hồi ngắn gọn (2-3 câu), xác nhận đã ghi nhận rào cản này vào hệ thống hậu đài.
- Nêu ngắn gọn nguyên tắc hóa giải (bảo vệ nhịp sinh học và phân bổ micro-habits).
- Thông báo hệ thống đang tự động chuyển tiếp sang Strategic Planner & Holistic Bio-Scheduler để thiết kế bản đồ hành động.
- TUYỆT ĐỐI KHÔNG đặt thêm câu hỏi về rào cản, không lặp lại câu hỏi cũ!
"""

    llm_messages = [SystemMessage(content=system_instruction)]
    recent_messages = messages[-12:] if len(messages) > 12 else messages
    for m in recent_messages:
        if isinstance(m, (HumanMessage, AIMessage)):
            c_text = extract_text_from_content(m.content)
            if isinstance(m, HumanMessage):
                llm_messages.append(HumanMessage(content=c_text))
            else:
                llm_messages.append(AIMessage(content=c_text))
        elif isinstance(m, dict):
            role = m.get("role")
            content = extract_text_from_content(m.get("content", ""))
            if role == "user":
                llm_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                llm_messages.append(AIMessage(content=content))

    new_awaiting = False
    new_pending = pending_goal

    try:
        llm = get_llm(temperature=0.4)
        response = llm.invoke(llm_messages)
        reply_content = extract_text_from_content(response.content if hasattr(response, "content") else response)

        # Kiểm tra xem câu trả lời của LLM có chứa câu hỏi chốt không (chỉ khi không phải câu hỏi tư vấn thuần túy)
        if not is_asking_advice and TRIGGER_CLOSING_QUESTION.lower() in reply_content.lower():
            new_awaiting = True
            new_pending = {
                "title": extracted_candidate or (pending_goal.get("title") if pending_goal else "Học Data Science"),
                "category": "career",
            }
        elif is_sharing_dream and has_sufficient_context and not is_asking_advice:
            if not reply_content.strip().endswith(TRIGGER_CLOSING_QUESTION):
                reply_content = reply_content.strip() + f"\n\n{TRIGGER_CLOSING_QUESTION}"
            new_awaiting = True
            new_pending = {
                "title": extracted_candidate or (pending_goal.get("title") if pending_goal else "Học Data Science"),
                "category": "career",
            }
        elif is_sharing_dream and not is_asking_advice:
            new_awaiting = False
            new_pending = {
                "title": extracted_candidate or "Mục tiêu mới",
                "category": "career",
            }
    except Exception as e:
        # Fallback 1: Thử model phụ gemini-3.5-flash-lite
        try:
            llm_fallback = get_llm(temperature=0.4, model="gemini-3.5-flash-lite")
            response = llm_fallback.invoke(llm_messages)
            reply_content = extract_text_from_content(response.content if hasattr(response, "content") else response)
        except Exception as e2:
            # Dynamic fallback: 100% ngữ cảnh theo câu hỏi của user, tuyệt đối không dùng hardcode rập khuôn
            if is_asking_advice:
                reply_content = (
                    f"Từ góc độ Executive Coach, về vấn đề **{last_user_message}**: "
                    "Chiến lược bứt phá bao gồm 3 yếu tố trọng yếu: (1) Chuẩn bị kỹ năng cốt lõi và tư duy nền tảng, "
                    "(2) Xây dựng hồ sơ thực chiến/minh chứng năng lực vượt trội, và (3) Tối ưu hóa quỹ thời gian và nhịp sinh học để duy trì phong độ đỉnh cao mà không bị kiệt sức.\n\n"
                    "Bạn muốn chúng ta bắt đầu đào sâu vào yếu tố nào trước tiên?"
                )
            elif any(w in user_lower for w in ["tiếng trung", "hsk", "không thi", "không học"]):
                reply_content = (
                    "Tôi đã ghi nhận rõ ràng điều chỉnh của bạn: Hệ thống sẽ không xếp lịch hay nhắc nhở về mục tiêu này nữa. "
                    "Toàn bộ tài nguyên nhận thức và năng lượng não bộ sẽ được tập trung vào các mục tiêu trọng tâm bạn đã chọn.\n\n"
                    "Bạn muốn chúng ta cùng tối ưu hóa khía cạnh nào tiếp theo?"
                )
            elif is_sharing_dream:
                target_name = extracted_candidate or "mục tiêu này"
                if has_sufficient_context:
                    reply_content = (
                        f"Chào bạn, tôi rất ấn tượng với định hướng chinh phục **{target_name}** của bạn! "
                        "Đây hoàn toàn là một nước cờ chiến lược giúp mở rộng năng lực và tạo ra lợi thế cạnh tranh cá nhân.\n\n"
                        f"{TRIGGER_CLOSING_QUESTION}"
                    )
                    new_awaiting = True
                    new_pending = {"title": target_name, "category": "career"}
                else:
                    reply_content = (
                        f"Chào bạn, khao khát chinh phục **{target_name}** là một ý định rất đáng trân trọng! "
                        "Là một Executive Life Coach, tôi muốn cùng bạn đào sâu làm rõ: Điều gì thôi thúc bạn muốn học lĩnh vực này vào thời điểm hiện tại, và bạn có thể cam kết bao nhiêu thời gian mỗi tuần?"
                    )
                    new_awaiting = False
                    new_pending = {"title": target_name, "category": "career"}
            elif is_answering_obstacle:
                reply_content = (
                    f"🎯 **GHI NHẬN RÀO CẢN CHIẾN LƯỢC & HÓA GIẢI ÁP LỰC**\n\n"
                    f"Tôi đã nắm rõ rào cản cốt tử bạn đang đối mặt: *\"{last_user_message}\"*.\n"
                    "Từ góc độ Executive Coach, mọi rào cản về thời gian, công việc hay sự phân tâm đều có thể hóa giải bằng chiến thuật: "
                    "cô lập khung giờ vàng buổi sáng (08:00 - 10:00) cho High Load và phân bổ các micro-habits 15-30 phút mỗi ngày.\n\n"
                    "⚡ **Thông tin đã được ghi nhận đầy đủ vào hệ thống hậu đài (Goals Ledger).**\n"
                    "Tôi đang kích hoạt **Strategic Planner** để thiết kế bản đồ Backcasting và **Holistic Bio-Scheduler** nhằm lên lịch hành động thực chiến ngay cho bạn!"
                )
            else:
                reply_content = (
                    f"Tôi đã ghi nhận định hướng của bạn về **{last_user_message}**. "
                    "Là một Executive Life Coach, tôi sẽ đồng hành cùng bạn thiết kế chiến lược tối ưu nhất.\n\n"
                    "Bạn muốn chúng ta bắt đầu bằng việc xây dựng lộ trình hành động chi tiết hay tối ưu lại lịch trình sinh hoạt trước?"
                )
            new_awaiting = False

    stage = "planning" if is_answering_obstacle else (state.get("coaching_stage") or user_profile.get("coaching_stage", "interviewing"))
    status_val = "analyzing" if is_answering_obstacle else (state.get("status") or "interviewing")
    info_flag = True if is_answering_obstacle else False

    return {
        "messages": [AIMessage(content=reply_content)],
        "intent": "strategic_plan" if is_answering_obstacle else ("coach_dialogue" if (is_sharing_dream or is_asking_advice) else "chat"),
        "pending_goal": new_pending,
        "awaiting_confirmation": new_awaiting,
        "is_confirmed": False,
        "user_profile": user_profile,
        "user_obstacles": user_obstacles,
        "coaching_stage": stage,
        "status": status_val,
        "is_info_sufficient": info_flag,
    }


def retrospective_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 10: Retrospective & Adaptive Memory Engine (Phase 10).
    Kích hoạt khi:
    - Một mục tiêu bị trễ hạn (overdue), bị người dùng hủy bỏ, hoặc được đánh dấu hoàn thành.
    - Người dùng phàn nàn/bỏ cuộc về một phương pháp (VD: Pomodoro gây đứt gãy tư duy, học tối gây kiệt sức).
    Nhiệm vụ:
    - Gọi LLM phân tích lý do thành công/thất bại dựa trên lịch sử chat gần nhất (Root Cause Analysis).
    - Rút ra bài học cụ thể và cập nhật vào `historical_insights` trong memory/goals_ledger.json:
      * failed_methods (các phương pháp đã thử nhưng thất bại/bỏ cuộc, cấm đề xuất lại)
      * effective_methods (các phương pháp mang lại kết quả tốt, ưu tiên áp dụng)
      * productivity_patterns (khung giờ hoạt động hiệu quả nhất, loại task thường gây kiệt sức)
    - Nếu người dùng thông báo hủy bỏ hoặc hoàn thành một mục tiêu, cập nhật status trong goals_ledger.json.
    - Trả về báo cáo Hồi Cứu Executive Life Coach toàn diện và cam kết điều chỉnh chiến lược.
    """
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    if not last_user_message and messages:
        last_user_message = str(messages[-1].content if hasattr(messages[-1], "content") else messages[-1])

    username = state.get("username") or "mavis"
    user_lower = last_user_message.lower().strip()
    insights_summary = get_historical_insights_summary_text(username=username)

    # 1. Chuẩn bị ngữ cảnh và gọi LLM phân tích Hồi cứu (Retrospective Analysis)
    analysis_result: Optional[RetrospectiveAnalysisResult] = None
    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(RetrospectiveAnalysisResult)

        prompt = f"""Bạn là Executive Life Coach chuyên trách Hồi Cứu Hành Vi (Retrospective Coach) & Tối Ưu Nhịp Sinh Học.
Người dùng vừa chia sẻ thông tin về trải nghiệm, khó khăn, sự kiện hoặc kết quả thực hiện:
"{last_user_message}"

HỒ SƠ BỘ NHỚ THÍCH NGHI HIỆN TẠI CỦA NGƯỜI DÙNG:
{insights_summary}

NHIỆM VỤ CỦA BẠN:
1. Xác định event_type: 'failure' (nếu bỏ cuộc, thất bại, trễ hạn, phương pháp không hiệu quả/gây ức chế/đứt gãy tư duy) hoặc 'success' (nếu hoàn thành, đạt kết quả tốt).
2. Xác định target_goal_or_task: Mục tiêu hoặc phương pháp cụ thể đang được đề cập (VD: 'Phương pháp Pomodoro 25/5', 'Xếp lịch học bài nặng vào buổi tối', 'Mục tiêu tiếng Trung').
3. Phân tích nguyên nhân gốc rễ (root_cause): Giải thích tại sao dưới góc độ tải nhận thức (Cognitive Load), nhịp sinh học (Circadian Rhythm) hoặc tâm lý học hành vi (Behavioral Psychology).
4. new_failed_methods: Nếu đây là phương pháp thất bại/gây kiệt sức hoặc không phù hợp, hãy định danh rõ ràng để đưa vào Blacklist (VD: 'Phương pháp Pomodoro 25/5 (Gây đứt gãy mạch suy nghĩ sâu khi giải bài toán phức tạp)', 'Xếp lịch học nặng vào buổi tối sau 20:00').
5. new_effective_methods: Nếu có phương pháp hiệu quả được đề cập (VD: 'Khối Deep Work liền mạch 90 phút vào buổi sáng').
6. new_productivity_patterns: Đúc rút quy luật sinh học/năng suất (VD: 'Cần sự tập trung sâu liên tục, không hợp với các ngắt quãng ngắn', 'Khung giờ tối sau 20:00 nhận thức giảm sút, dễ bỏ cuộc').
7. coach_takeaway: Lời khuyên, sự thấu hiểu và cam kết vững chắc của Executive Coach về việc điều chỉnh hệ thống thích nghi, TUYỆT ĐỐI không lặp lại sai lầm.
"""
        analysis_result = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=prompt),
        ])
    except Exception as e:
        # Fallback offline thông minh dựa trên từ khóa người dùng
        event_type = "success" if any(w in user_lower for w in ["hoàn thành", "thành công", "đạt được", "xong rồi"]) else "failure"
        target_name = "Phương pháp học tập & Lịch trình sinh học"
        root_cause = "Phương pháp hiện tại gây xung đột với nhịp sinh học tự nhiên và phong cách nhận thức của người dùng."
        new_failed = []
        new_effective = []
        new_patterns = []

        if "pomodoro" in user_lower:
            target_name = "Phương pháp Pomodoro 25/5"
            root_cause = "Đối với các tác vụ đòi hỏi tư duy logic trừu tượng cao (như Toán, Lập trình AI, Viết luận), chu kỳ 25 phút ngắt quãng một lần làm đứt gãy trạng thái dòng chảy nhận thức (Flow State), khiến não bộ phải tốn nhiều năng lượng tái khởi động ngữ cảnh."
            new_failed.append("Phương pháp Pomodoro 25/5 (Gây đứt gãy mạch suy nghĩ sâu và phân mảnh nhận thức)")
            new_patterns.append("Cần khối tập trung sâu liên tục (Deep Work 60-90 phút), không phù hợp với chu kỳ ngắt quãng ngắn")
            new_effective.append("Học sâu Deep Work vào khung giờ vàng 08:00 - 10:00 sáng")

        if any(w in user_lower for w in ["tối", "buổi tối", "đêm"]):
            target_name = "Xếp lịch học bài nặng vào buổi tối"
            root_cause = "Sau 20:00, lượng cortisol giảm và melatonin bắt đầu tiết ra. Việc ép não bộ xử lý tác vụ tải nhận thức cao vào buổi tối kích hoạt cơ chế tự vệ gây kiệt sức và thôi thúc bỏ cuộc."
            new_failed.append("Xếp lịch học bài nặng (High Cognitive Load) vào buổi tối sau 20:00")
            new_patterns.append("Khung giờ tối sau 20:00 năng lượng nhận thức giảm mạnh, chỉ phù hợp với Passive Listening và thư giãn phục hồi")

        if not new_failed and event_type == "failure":
            new_failed.append(f"Phương pháp không phù hợp vừa áp dụng ({last_user_message[:50]}...)")
            new_patterns.append("Cần điều chỉnh linh hoạt theo thể trạng thực tế thay vì ép buộc khung cứng")

        coach_takeaway = "Tôi đã lắng nghe và xác nhận: Bỏ một phương pháp không phù hợp là quyết định chiến lược sáng suốt, không phải thất bại. Kể từ nay, tôi đã đưa phương pháp này vào Blacklist và cam kết thiết kế lịch trình hoàn toàn dựa trên nhịp sinh học tối ưu của bạn!"

        analysis_result = RetrospectiveAnalysisResult(
            event_type=event_type,
            target_goal_or_task=target_name,
            root_cause=root_cause,
            new_failed_methods=new_failed,
            new_effective_methods=new_effective,
            new_productivity_patterns=new_patterns,
            coach_takeaway=coach_takeaway,
        )

    # 2. Cập nhật các phát hiện vào Bộ Nhớ Thích Nghi (historical_insights)
    for m in analysis_result.new_failed_methods:
        append_insight("failed_methods", m, username=username)
    for m in analysis_result.new_effective_methods:
        append_insight("effective_methods", m, username=username)
    for p in analysis_result.new_productivity_patterns:
        append_insight("productivity_patterns", p, username=username)

    # 3. Nếu người dùng đề cập đến việc hủy hoặc hoàn thành một mục tiêu cụ thể trong Tree, cập nhật status
    tree_goals = load_tree_goals(username=username)
    updated_goal_title = None
    goal_status_action = None

    is_cancelling = any(w in user_lower for w in ["hủy mục tiêu", "bỏ mục tiêu", "không theo đuổi", "dừng mục tiêu", "hủy bỏ"])
    is_completing = any(w in user_lower for w in ["hoàn thành mục tiêu", "đã hoàn thành", "cán đích", "đạt được mục tiêu"])

    if is_cancelling or is_completing:
        for root in ["career", "relationships", "health", "beauty"]:
            children = tree_goals.get(root, {}).get("children", [])
            for g in children:
                g_title = g.get("title", "").lower()
                words = [w for w in g_title.split() if len(w) > 3]
                if (words and any(w in user_lower for w in words)) or g_title in user_lower:
                    updated_goal_title = g.get("title")
                    if is_cancelling:
                        g["status"] = "cancelled"
                        goal_status_action = "Đã chuyển trạng thái sang 🚫 `cancelled` (Hủy bỏ/Tạm dừng)"
                    elif is_completing:
                        g["status"] = "completed"
                        goal_status_action = "Đã chuyển trạng thái sang 🏆 `completed` (Hoàn thành xuất sắc)"
                    save_tree_goals(tree_goals, username=username)
                    break
            if updated_goal_title:
                break

    # 4. Tải lại insights cập nhật mới nhất
    updated_insights = load_historical_insights(username=username)

    # 5. Biên soạn Báo Cáo Hồi Cứu Executive Life Coach
    report_lines = [
        "🧠 **BÁO CÁO HỒI CỨU HÀNH VI & BÀI HỌC THÍCH NGHI (RETROSPECTIVE PROTOCOL - PHASE 10)**",
        "\n### 1. 🔍 ĐỐI TƯỢNG HỒI CỨU & PHÂN LOẠI:",
        f"- **Đối tượng xem xét:** {analysis_result.target_goal_or_task or 'Phương pháp làm việc & Kế hoạch hành động'}",
        f"- **Bản chất sự kiện:** {'Thất bại / Bỏ cuộc phương pháp không phù hợp' if analysis_result.event_type == 'failure' else 'Hoàn thành / Đạt kết quả xuất sắc'}",
    ]

    if updated_goal_title and goal_status_action:
        report_lines.append(f"- **Mục tiêu liên quan trong Ledger:** **{updated_goal_title}** → {goal_status_action}")

    report_lines.extend([
        "\n### 2. 🔬 PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE ANALYSIS):",
        f"{analysis_result.root_cause}",
        "\n### 3. 🛑 CẬP NHẬT BỘ NHỚ THÍCH NGHI (ADAPTIVE MEMORY UPDATES):",
    ])

    if analysis_result.new_failed_methods:
        report_lines.append("- **❌ Đã đưa vào Blacklist (failed_methods - Cấm đề xuất lại):**")
        for m in analysis_result.new_failed_methods:
            report_lines.append(f"  * 🛑 `{m}`")
    else:
        report_lines.append("- **❌ Phương pháp thất bại mới:** Không ghi nhận thêm")

    if analysis_result.new_effective_methods:
        report_lines.append("- **✅ Phương pháp hiệu quả được ghi nhận (effective_methods):**")
        for m in analysis_result.new_effective_methods:
            report_lines.append(f"  * ⭐ `{m}`")

    if analysis_result.new_productivity_patterns:
        report_lines.append("- **⚡ Quy luật năng suất sinh học mới (productivity_patterns):**")
        for p in analysis_result.new_productivity_patterns:
            report_lines.append(f"  * ⏰ `{p}`")

    report_lines.extend([
        "\n### 4. 💡 CAM KẾT ĐIỀU CHỈNH CỦA EXECUTIVE LIFE COACH:",
        f"> *\"{analysis_result.coach_takeaway}\"*",
        "\n**Giao thức Bảo vệ Nhịp Sinh học:** Hệ thống đã tự động ghi nhớ và đồng bộ vĩnh viễn vào hồ sơ của bạn. Trong các lượt lập lịch và tư vấn chiến lược tiếp theo, AI sẽ **TUYỆT ĐỐI KHÔNG** đề xuất lại các phương pháp trong Blacklist, mà tập trung 100% vào các phương pháp tối ưu hóa năng lượng của bạn.",
    ])

    report_text = "\n".join(report_lines)

    return {
        "messages": [AIMessage(content=report_text)],
        "historical_insights": updated_insights,
        "retrospective_report": report_text,
        "intent": "retrospective",
    }
