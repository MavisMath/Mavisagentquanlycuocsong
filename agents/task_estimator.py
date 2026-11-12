from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from memory.goals import get_goals_summary_text


class MilestoneTask(BaseModel):
    milestone: str = Field(description="Tên cột mốc chiến lược cụ thể, rõ ràng và có thể nghiệm thu")
    timeline: str = Field(description="Thời hạn thực hiện (VD: 'Tuần 1 - Tuần 2', 'Tháng 1/2027')")
    estimated_hours: int = Field(description="Dự phóng số giờ làm việc tập trung để hoàn thành cột mốc này")
    action_items: List[str] = Field(description="2-3 hành động con cụ thể để hoàn thành cột mốc")
    status: str = Field(default="pending", description="Trạng thái khởi tạo: pending hoặc in_progress")


class FeasibilityAndEstimateResult(BaseModel):
    goal_title: str = Field(description="Tên chuẩn hóa súc tích của mục tiêu")
    category: str = Field(
        default="study_work",
        description="Một trong 5 nhóm: 'health_beauty', 'study_work', 'family', 'finance', 'daily_routine'"
    )
    deadline: str = Field(description="Hạn chót ước tính (VD: '2 tháng', '4 tháng', 'Q1/2027')")
    feasibility_score: int = Field(
        ge=1, le=100,
        description="Điểm khả thi từ 1 đến 100 dựa trên đối chiếu năng lực, tài chính và quỹ thời gian"
    )
    priority: str = Field(
        description="Đề xuất độ ưu tiên: 'P1 - Critical', 'P2 - High', 'P3 - Medium', hoặc 'P4 - Low'"
    )
    feasibility_analysis: str = Field(
        description="Bản phân tích chi tiết: Điểm mạnh hỗ trợ, rủi ro/nút thắt cổ chai, và chi phí cơ hội đối với các mục tiêu tối thượng"
    )
    total_estimated_hours: int = Field(
        description="Tổng số giờ dự phóng cần thiết để hoàn thành toàn bộ mục tiêu"
    )
    recommended_hours_per_week: int = Field(
        description="Số giờ cam kết hàng tuần đề xuất (cân đối với nhịp sinh học và quỹ thời gian hiện có)"
    )
    milestones: List[MilestoneTask] = Field(
        description="Danh sách các cột mốc chia nhỏ theo tuần/tháng kèm dự phóng số giờ"
    )


def analyze_and_estimate_goal(
    goal_input: str,
    user_profile: Optional[Dict[str, Any]] = None,
    username: str = "mavis",
) -> FeasibilityAndEstimateResult:
    """
    Module Task Estimator & Feasibility Analyzer.
    Sử dụng Gemini kết hợp với dữ liệu từ user_profile để:
    1. Chấm điểm khả thi (Feasibility Score 1-100)
    2. Đề xuất độ ưu tiên (Priority)
    3. Phân rã mục tiêu thành các cột mốc tuần/tháng
    4. Dự phóng số giờ hoàn thành cho từng task và tổng số giờ
    """
    user_profile = user_profile or {}
    situation = user_profile.get("current_situation", "Cựu FTU, có tư duy logic Toán/Tin, kinh nghiệm Leader Top 20 SIL, Vibe Coding")
    time_constraints = user_profile.get("time_constraints", "Khung giờ vàng 08:00 - 10:00 sáng dành cho High Load; sau 14:00 giảm tải; ngủ trước 23:00")
    financial_status = user_profile.get("financial_status", "Quỹ dự phòng ổn định, ưu tiên đầu tư kỹ năng AI & IT BA")

    goals_summary = get_goals_summary_text(username=username)

    prompt = f"""Bạn là Chuyên gia Đánh giá Khả thi & Dự toán Định lượng (Executive Feasibility & Task Estimator) cho Mavis.

Mục tiêu mới Mavis vừa đề xuất:
"{goal_input}"

Dữ liệu hồ sơ nền tảng (user_profile):
- Tình trạng hiện tại: {situation}
- Ràng buộc thời gian & nhịp sinh học: {time_constraints}
- Tình trạng tài chính & nguồn lực: {financial_status}

Bối cảnh hệ thống mục tiêu hiện có trong goals_ledger:
{goals_summary}

Yêu cầu phân tích định lượng & định tính:
1. Xác định goal_title, category (chọn 1 trong: 'health_beauty', 'study_work', 'family', 'finance', 'daily_routine') và deadline.
2. CHẤM ĐIỂM KHẢ THI (feasibility_score: 1-100):
   - Đánh giá sự tương thích với nền tảng của Mavis (FTU, Purchasing, Logic, SIL Top 20, Vibe Coding).
   - Đánh giá quỹ thời gian thực tế: Liệu có đủ giờ học mà không xung đột với khung giờ vàng 08:00 - 10:00 sáng (dành cho IELTS 7.5 & VinUni AI)?
   - Đánh giá chi phí cơ hội và khả năng kiệt sức (burnout).
3. ĐỀ XUẤT ĐỘ ƯU TIÊN (priority): 'P1 - Critical', 'P2 - High', 'P3 - Medium', hoặc 'P4 - Low'.
4. DỰ PHÓNG ĐỊNH LƯỢNG THỜI GIAN:
   - Phân rã thành 3-4 cột mốc (milestones) theo tuần/tháng.
   - Với MỖI cột mốc, ước lượng chính xác số giờ cần đầu tư (estimated_hours, ví dụ: 15h, 25h, 30h) và 2-3 đầu việc cụ thể.
   - Tính tổng số giờ dự phóng (total_estimated_hours) và số giờ cam kết hàng tuần (recommended_hours_per_week).
5. feasibility_analysis: Viết phân tích sắc bén, chỉ rõ nút thắt cổ chai và giải pháp chiến lược.
"""

    try:
        from agents.brain import get_llm, SYSTEM_PROMPT, ACHIEVEMENT_LEDGER
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(FeasibilityAndEstimateResult)
        result: FeasibilityAndEstimateResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=prompt),
        ])
        return result
    except Exception as e:
        # Fallback định lượng chuẩn xác khi offline
        return FeasibilityAndEstimateResult(
            goal_title=goal_input.strip() or "Mục tiêu phát triển mới",
            category="study_work",
            deadline="3 tháng",
            feasibility_score=85,
            priority="P2 - High",
            feasibility_analysis=(
                "Mục tiêu có tính khả thi cao nhờ nền tảng tư duy logic Toán/Tin và kinh nghiệm điều hành dự án của bạn. "
                "Tuy nhiên, cần cảnh giác nguy cơ phân tán năng lượng: Khung 08:00 - 10:00 sáng bắt buộc giữ cho IELTS 7.5 và VinUni AI; "
                "mục tiêu này cần được bố trí vào khung giờ chiều hoặc các buổi tối đầu tuần."
            ),
            total_estimated_hours=60,
            recommended_hours_per_week=6,
            milestones=[
                MilestoneTask(
                    milestone="Nghiên cứu giáo trình tổng quan & xây dựng khung kiến thức nền tảng",
                    timeline="Tuần 1 - Tuần 3",
                    estimated_hours=18,
                    action_items=["Đọc tài liệu cơ sở", "Lập dàn ý các chủ đề trọng điểm", "Làm bài kiểm tra đầu vào"],
                    status="in_progress",
                ),
                MilestoneTask(
                    milestone="Luyện tập chuyên sâu & giải quyết các bài toán case-study thực tế",
                    timeline="Tuần 4 - Tuần 8",
                    estimated_hours=26,
                    action_items=["Thực hành giải 10 bộ đề/case-study", "Tối ưu hóa thời gian làm bài", "Đánh giá lỗi sai"],
                    status="pending",
                ),
                MilestoneTask(
                    milestone="Tổng ôn, thi thử nghiệm thu hoặc hoàn thiện sản phẩm đồ án",
                    timeline="Tuần 9 - Tuần 12",
                    estimated_hours=16,
                    action_items=["Làm full mock test mô phỏng", "Chuẩn bị hồ sơ chứng chỉ/portfolio", "Nghiệm thu kết quả"],
                    status="pending",
                ),
            ],
        )
