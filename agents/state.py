from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Trạng thái cốt lõi của Mavis AI Executive Life Coach Agent.
    Quản lý ngữ cảnh xuyên suốt các node trong LangGraph.
    """
    # Lịch sử hội thoại (tự động gộp message mới qua add_messages reducer)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Mức năng lượng sinh học hiện tại: "high" (08:00-10:00 sáng) | "low" (sau 14:00 hoặc khi mệt mỏi)
    current_energy_level: str
    
    # Cảm xúc phát hiện được: "negative", "tired", "overwhelmed", "neutral", "positive", "motivated"
    detected_emotion: str
    
    # Ý định người dùng: "schedule" | "motivate" | "explore_trend" | "set_goal" | "find_resources" | "chat"
    intent: str
    
    # Kế hoạch công việc / danh sách task phân rã chi tiết
    plan: List[Dict[str, Any]]
    
    # Hồ sơ người dùng đa khía cạnh: tình trạng hiện tại, mức tài chính, ràng buộc thời gian, trạng thái onboarding
    user_profile: Dict[str, Any]
    
    # Mục tiêu trọng tâm đang được xử lý trong luồng (dùng cho móc nối goal_manager -> resource_finder)
    target_goal: Optional[str]
    
    # Cảm biến sự kiện đột xuất / quá tải cần kích hoạt thuật toán Reschedule
    is_emergency: Optional[bool]
    
    # Ngữ cảnh tri thức tải lên từ tài liệu PDF hoặc Link URL do user cung cấp (Động cơ RAG)
    uploaded_context: Optional[str]
    
    # Danh sách các xung đột ưu tiên được phát hiện & xử lý (Phase 7.2)
    conflicts: Optional[List[Dict[str, Any]]]
    
    # Milestone trung gian cần trinh sát cơ hội thực chiến (Phase 7.3)
    target_milestone: Optional[str]
    
    # Danh sách các cơ hội thực chiến, bootcamp, fellowship trinh sát được từ Tavily (Phase 7.3)
    scouted_opportunities: Optional[List[Dict[str, Any]]]
    
    # Danh sách các hành động Networking Protocol tạo lợi thế bất đối xứng (Phase 7.3)
    networking_actions: Optional[List[str]]
    
    # Định danh tài khoản người dùng trong nền tảng SaaS Multi-user (Phase 8)
    username: Optional[str]

    # Mục tiêu dự thảo trong quá trình đối thoại Coaching trước khi người dùng xác nhận (Phase 9)
    pending_goal: Optional[Dict[str, Any]]

    # Cờ trạng thái chờ người dùng xác nhận câu hỏi chốt của Executive Coach (Phase 9)
    awaiting_confirmation: Optional[bool]

    # Cờ trạng thái đã xác nhận đồng ý để kích hoạt Conditional Edge rẽ nhánh sang Goal Manager & Scheduler (Phase 9)
    is_confirmed: Optional[bool]

    # Hồ sơ hành vi & bài học thích nghi Adaptive Memory (Phase 10)
    historical_insights: Optional[Dict[str, List[str]]]

    # Báo cáo hồi cứu gần nhất (Phase 10 Retrospective Report)
    retrospective_report: Optional[str]
