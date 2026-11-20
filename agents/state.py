from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class CoachState(TypedDict):
    """
    Trạng thái cốt lõi của Mavis Multi-Agent Executive & Life Coach (LangGraph + Gemini API).
    Quản lý ngữ cảnh và dữ liệu xuyên suốt 4 Agent Nodes:
    1. profiler_node -> profile (GoalProfile)
    2. research_node -> resources
    3. strategic_planner_node -> roadmap (Backcasting)
    4. scheduler_node -> schedule (Circadian Bio-Schedule)
    """
    # Lịch sử hội thoại (tự động gộp message mới qua add_messages reducer)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Danh sách các mục tiêu song song (GoalProfile: goal_id, category, goal_name, current_level, duration_days, daily_hours, preferred_slots, priority, is_complete)
    goals: Optional[List[Dict[str, Any]]]
    
    # Hồ sơ mục tiêu đơn lẻ / mục tiêu trọng tâm (Tương thích ngược)
    profile: Optional[Dict[str, Any]]
    
    # Danh sách tài nguyên/công cụ thực tế đã thẩm định (title, url, type, estimated_hours, how_to_use)
    resources: Optional[List[Dict[str, Any]]]
    
    # Bản đồ lộ trình Backcasting phân cấp (Quý/Tháng -> Tuần -> Ngày)
    roadmap: Optional[Dict[str, Any]]
    
    # Lịch trình hành động chi tiết theo nhịp sinh học
    schedule: Optional[List[Dict[str, Any]]]
    
    # Định danh tài khoản người dùng trong nền tảng SaaS Multi-user
    username: Optional[str]
    user_id: Optional[str]
    
    # Lời khuyên, phản hồi chiến lược hoặc câu hỏi điều hướng từ Coach
    coaching_feedback: Optional[str]
    
    # Cờ trạng thái thông tin mục tiêu đã đầy đủ để chuyển sang lập kế hoạch
    is_complete: Optional[bool]
    
    # Mức năng lượng sinh học hiện tại: "high" | "low"
    current_energy_level: Optional[str]
    
    # Cảm xúc phát hiện được: "negative", "tired", "overwhelmed", "neutral", "positive", "motivated"
    detected_emotion: Optional[str]
    
    # Ý định người dùng
    intent: Optional[str]
    
    # Kế hoạch công việc / danh sách task phân rã chi tiết
    plan: Optional[List[Dict[str, Any]]]
    
    # Hồ sơ người dùng đa khía cạnh (legacy profile sync)
    user_profile: Optional[Dict[str, Any]]
    
    # Mục tiêu trọng tâm đang được xử lý trong luồng
    target_goal: Optional[str]
    
    # Cảm biến sự kiện đột xuất / quá tải cần kích hoạt thuật toán Reschedule
    is_emergency: Optional[bool]
    
    # Ngữ cảnh tri thức tải lên từ tài liệu PDF hoặc Link URL do user cung cấp (Động cơ RAG)
    uploaded_context: Optional[str]
    
    # Danh sách các xung đột ưu tiên được phát hiện & xử lý
    conflicts: Optional[List[Dict[str, Any]]]
    
    # Milestone trung gian cần trinh sát cơ hội thực chiến
    target_milestone: Optional[str]
    
    # Danh sách các cơ hội thực chiến, bootcamp, fellowship trinh sát được từ Tavily
    scouted_opportunities: Optional[List[Dict[str, Any]]]
    
    # Danh sách các hành động Networking Protocol tạo lợi thế bất đối xứng
    networking_actions: Optional[List[str]]
    
    # Mục tiêu dự thảo trong quá trình đối thoại Coaching trước khi người dùng xác nhận
    pending_goal: Optional[Dict[str, Any]]
    
    # Cờ trạng thái chờ người dùng xác nhận câu hỏi chốt của Executive Coach
    awaiting_confirmation: Optional[bool]
    
    # Cờ trạng thái đã xác nhận đồng ý
    is_confirmed: Optional[bool]
    
    # Hồ sơ hành vi & bài học thích nghi Adaptive Memory
    historical_insights: Optional[Dict[str, List[str]]]
    
    # Báo cáo hồi cứu gần nhất
    retrospective_report: Optional[str]
    
    # Giai đoạn hội thoại Coaching: "interviewing" | "analyzing" | "planning" | "action"
    coaching_stage: Optional[str]
    
    # Danh sách các rào cản / thách thức của người dùng đã thu thập
    user_obstacles: Optional[List[str]]
    
    # Cờ trạng thái thông tin đã thu thập đầy đủ
    is_info_sufficient: Optional[bool]
    
    # Trạng thái tổng quát của phiên làm việc
    status: Optional[str]


# Bí danh tương thích ngược cho các module hiện có
AgentState = CoachState
