from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from agents.state import CoachState, AgentState
from agents.brain import (
    profiler_node,
    research_node,
    strategic_planner_node,
    scheduler_node,
    chat_node,
    # Hỗ trợ tương thích ngược cho các node mở rộng
    motivate_node,
    trend_node,
    retrospective_node,
    onboarding_node,
    analyze_input_node,
    schedule_node,
    goal_manager_node,
    resource_finder_node,
    opportunity_scout_node,
    holistic_scheduler_node,
)


def route_entry(state: CoachState) -> str:
    """
    Bộ định tuyến khởi đầu (Entry Router):
    - Nếu người dùng đặt câu hỏi tư vấn / chiến lược / thắc mắc thực thi (Làm sao/Tại sao/Được không/VinUni...):
      VÀ người dùng đã có mục tiêu hoàn chỉnh -> chuyển thẳng vào 'chat' (Coaching node) tư vấn chuyên sâu.
    - Nếu có intent đặc thù (motivate, trend, retrospective) -> điều hướng tương ứng.
    - Mặc định: Chuyển vào 'profiler' (Node 1) để khai thác, tích lũy và chốt hồ sơ mục tiêu có cấu trúc.
    """
    messages = state.get("messages", [])
    last_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "content"):
            last_msg = str(msg.content)
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_msg = str(msg.get("content", ""))
            break

    last_lower = last_msg.lower().strip()
    advice_triggers = [
        "làm sao", "làm thế nào", "tại sao", "thế nào", "được không", "có nên",
        "tư vấn", "lời khuyên", "chiến lược", "song song", "how", "why",
        "cách nào", "khả thi", "vinuni", "đỗ", "kinh nghiệm", "liệu", "cân bằng",
        "speaking", "writing", "reading", "listening", "mẹo", "phương pháp"
    ]
    is_advice = any(w in last_lower for w in advice_triggers)

    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    profile = state.get("profile") or {}
    if not profile or not profile.get("goal_name"):
        try:
            from memory.goals import load_user_goal_profile
            saved = load_user_goal_profile(username)
            if saved and isinstance(saved, dict) and saved.get("goal_name"):
                profile = saved
        except Exception:
            pass

    # Nếu người dùng đang hỏi tư vấn và đã có mục tiêu hoặc profile đầy đủ
    if is_advice and profile.get("is_complete"):
        return "chat"

    # Kiểm tra intent đặc thù
    intent = state.get("intent")
    if intent == "motivate":
        return "motivate"
    elif intent in ["explore_trend", "search"]:
        return "trend"
    elif intent in ["retrospective", "review"]:
        return "retrospective"

    return "profiler"


def route_after_profiler(state: CoachState) -> str:
    """
    Conditional Edge sau profiler_node:
    - Nếu is_complete == True: Đã thu thập đủ 5 thông số cốt lõi -> Kích hoạt research_node (Node 2)
      để thẩm định tài nguyên thực tế.
    - Nếu is_complete == False: Còn thiếu dữ liệu -> Dừng tại END để người dùng trả lời câu hỏi còn thiếu.
    """
    if state.get("is_complete") is True:
        return "research"
    return END


# ==============================================================================
# HÀM XÂY DỰNG VÀ BIÊN DỊCH ĐỒ THỊ LANGGRAPH MULTI-AGENT
# ==============================================================================

class MavisAgentWrapper:
    """
    Wrapper tích hợp MemorySaver quản lý chat_history và State xuyên suốt phiên làm việc.
    Tự động gắn thread_id cố định theo username để bảo toàn ngữ cảnh và mục tiêu qua mọi lượt chat.
    """
    def __init__(self, graph):
        self.graph = graph

    def _prepare_call(self, state, config):
        config = dict(config or {})
        configurable = dict(config.get("configurable", {}))

        # 1. Trích xuất username chuẩn xác từ state hoặc config
        user = "mavis"
        if isinstance(state, dict):
            raw_user = state.get("username")
            if raw_user and str(raw_user).strip():
                user = str(raw_user).strip().lower()
        if user == "mavis" and "thread_id" in configurable:
            tid_parts = str(configurable["thread_id"]).replace("thread_", "").split("_")
            if tid_parts and tid_parts[0].strip():
                user = tid_parts[0].strip().lower()

        if isinstance(state, dict):
            state["username"] = user
            state["user_id"] = user

        # 2. Cố định thread_id theo user
        if "thread_id" not in configurable or not configurable["thread_id"]:
            configurable["thread_id"] = user
        config["configurable"] = configurable
        return state, config

    def invoke(self, state, config=None, **kwargs):
        state, config = self._prepare_call(state, config)
        return self.graph.invoke(state, config=config, **kwargs)

    def stream(self, state, config=None, **kwargs):
        state, config = self._prepare_call(state, config)
        return self.graph.stream(state, config=config, **kwargs)

    def __getattr__(self, name):
        return getattr(self.graph, name)


def build_graph(checkpointer=None) -> MavisAgentWrapper:
    """
    Khởi tạo và biên dịch đồ thị LangGraph Multi-Agent hoàn chỉnh.
    Tích hợp MemorySaver checkpointer để lưu trữ trạng thái phiên làm việc theo từng user.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    workflow = StateGraph(CoachState)

    # 1. Đăng ký 4 Multi-Agent Nodes cốt lõi + Chat Node
    workflow.add_node("profiler", profiler_node)
    workflow.add_node("research", research_node)
    workflow.add_node("strategic_planner", strategic_planner_node)
    workflow.add_node("scheduler", scheduler_node)
    workflow.add_node("chat", chat_node)

    # Các node hỗ trợ tương thích
    workflow.add_node("motivate", motivate_node)
    workflow.add_node("trend", trend_node)
    workflow.add_node("retrospective", retrospective_node)

    # 2. Thiết lập Conditional Edge từ START
    workflow.add_conditional_edges(
        START,
        route_entry,
        {
            "profiler": "profiler",
            "chat": "chat",
            "motivate": "motivate",
            "trend": "trend",
            "retrospective": "retrospective",
        },
    )

    # 3. Thiết lập Conditional Edge sau profiler_node
    workflow.add_conditional_edges(
        "profiler",
        route_after_profiler,
        {
            "research": "research",
            END: END,
        },
    )

    # 4. Chuỗi phối hợp tuần tự giữa các Agent Nodes:
    # research_node -> strategic_planner_node -> scheduler_node -> END
    workflow.add_edge("research", "strategic_planner")
    workflow.add_edge("strategic_planner", "scheduler")
    workflow.add_edge("scheduler", END)
    workflow.add_edge("chat", END)
    workflow.add_edge("motivate", END)
    workflow.add_edge("trend", END)
    workflow.add_edge("retrospective", END)

    compiled_graph = workflow.compile(checkpointer=checkpointer)
    return MavisAgentWrapper(compiled_graph)


# Khởi tạo instance mặc định
mavis_agent = build_graph()

