from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from agents.state import AgentState
from agents.brain import (
    onboarding_node,
    analyze_input_node,
    motivate_node,
    schedule_node,
    trend_node,
    goal_manager_node,
    resource_finder_node,
    strategic_planner_node,
    opportunity_scout_node,
    holistic_scheduler_node,
    chat_node,
    retrospective_node,
)


def check_profile_router(state: AgentState) -> str:
    """
    Conditional Edge đầu tiên của đồ thị:
    Kiểm tra xem người dùng đã hoàn thành onboarding / có thông tin nền tảng chưa.
    - Nếu người dùng đang hỏi tư vấn / chiến lược / thắc mắc thực thi (How/Why/Làm thế nào/Được không/VinUni...):
      Bỏ qua onboarding để chuyển thẳng vào 'analyze' -> 'chat' (Coaching node) giải đáp chuyên sâu.
    - Nếu user_profile trống hoặc is_onboarded == False:
      Kiểm tra thêm trong goals_ledger.json của username. Nếu đã hoàn tất onboarding -> 'analyze', ngược lại -> 'onboarding'.
    - Nếu đã có đầy đủ hồ sơ nền tảng: Cho phép đi tiếp vào 'analyze'.
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
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
        "cách nào", "khả thi", "vinuni", "đỗ", "kinh nghiệm", "liệu", "cân bằng"
    ]
    if any(w in last_lower for w in advice_triggers):
        return "analyze"

    profile = state.get("user_profile")
    if not profile or not profile.get("is_onboarded", False):
        try:
            from memory.goals import load_user_profile
            saved_prof = load_user_profile(username)
            if saved_prof and isinstance(saved_prof, dict) and saved_prof.get("is_onboarded"):
                return "analyze"
        except Exception:
            pass
        return "onboarding"
    return "analyze"


def route_by_intent(state: AgentState) -> str:
    """
    Hàm định tuyến điều kiện dựa trên ý định (intent) được phân tích từ câu chat của Mavis.
    Cấu trúc lại Router dạng Agentic Coach (Phase 9):
    - Phân biệt rõ giữa tin nhắn 'tâm sự / chia sẻ dự định' (coach_dialogue), 'xác nhận kích hoạt' (confirm_goal)
      và 'lệnh thực thi'.
    - 'coach_dialogue', 'chat', 'confirm_goal': Điều hướng vào node giao tiếp (chat_node) để đối thoại coaching.
    - 'set_goal': Điều hướng sang node Quản lý & Phân rã mục tiêu (Goal Manager).
    - 'schedule': Điều hướng sang node Lập lịch tối ưu nhịp sinh học.
    - 'holistic_schedule': Điều hướng sang node Cân bằng Sinh học Toàn diện (Dynamic Equilibrium).
    - 'explore_trend': Điều hướng sang node Trinh sát xu hướng & Dòng tiền công nghệ (Tavily).
    - 'find_resources': Điều hướng sang node Trinh sát & Tuyển chọn tài nguyên học tập (Resource Finder).
    - 'strategic_plan': Điều hướng sang node Lập kế hoạch ngược Backcasting & Xung đột ưu tiên.
    - 'opportunity_scout': Điều hướng sang node Trinh sát cơ hội thực chiến & Networking Protocol.
    """
    intent = state.get("intent", "chat")
    if intent in ["coach_dialogue", "chat", "confirm_goal"]:
        return "chat"
    elif intent == "motivate":
        return "motivate"
    elif intent in ["schedule", "reschedule"]:
        return "schedule"
    elif intent in ["holistic_schedule", "balance", "dynamic_equilibrium", "can_bang"]:
        return "holistic_scheduler"
    elif intent in ["explore_trend", "search"]:
        return "trend"
    elif intent == "set_goal":
        return "goal_manager"
    elif intent == "find_resources":
        return "resource_finder"
    elif intent in ["strategic_plan", "backcasting", "conflict"]:
        return "strategic_planner"
    elif intent in ["opportunity_scout", "scout", "networking"]:
        return "opportunity_scout"
    elif intent in ["retrospective", "review", "hoi_cuu"]:
        return "retrospective"
    return "chat"


def route_from_chat(state: AgentState) -> str:
    """
    Conditional Edge từ node giao tiếp (chat_node - Phase 9):
    Cơ chế Kích hoạt Hành động & Điều hướng Kế hoạch:
    - Nếu người dùng trả lời 'Đồng ý' (is_confirmed == True):
      Rẽ nhánh truyền dữ liệu sang goal_manager_node.
    - Nếu đã thu thập đầy đủ thông tin rào cản / mục tiêu (is_info_sufficient == True hoặc coaching_stage in ["planning"]):
      Rẽ nhánh sang strategic_planner_node để lập kế hoạch ngược (Backcasting) và giải quyết rào cản.
    - Ngược lại (đang trò chuyện coaching bình thường):
      Kết thúc luồng tại END.
    """
    if state.get("is_confirmed"):
        return "goal_manager"
    if state.get("is_info_sufficient") or state.get("coaching_stage") in ["planning"]:
        return "strategic_planner"
    return END


def route_from_strategic_planner(state: AgentState) -> str:
    """
    Conditional Edge nối từ strategic_planner sang opportunity_scout (Phase 7.3):
    - Nếu có target_milestone (từ thuật toán Backcasting) -> Tự động chuyển tiếp sang opportunity_scout
      để trinh sát cơ hội thực chiến (VinUni AI Bootcamp) và sinh task nhỏ trong tuần.
    - Nếu không có milestone -> chuyển tiếp sang holistic_scheduler để cập nhật nhịp sinh học.
    """
    if state.get("target_milestone"):
        return "opportunity_scout"
    return "holistic_scheduler"


# 1. Khởi tạo StateGraph với schema AgentState
workflow = StateGraph(AgentState)

# 2. Đăng ký các node chức năng vào đồ thị
workflow.add_node("onboarding", onboarding_node)
workflow.add_node("analyze", analyze_input_node)
workflow.add_node("motivate", motivate_node)
workflow.add_node("schedule", schedule_node)
workflow.add_node("trend", trend_node)
workflow.add_node("goal_manager", goal_manager_node)
workflow.add_node("resource_finder", resource_finder_node)
workflow.add_node("strategic_planner", strategic_planner_node)
workflow.add_node("opportunity_scout", opportunity_scout_node)
workflow.add_node("holistic_scheduler", holistic_scheduler_node)
workflow.add_node("chat", chat_node)
workflow.add_node("retrospective", retrospective_node)

# 3. THIẾT LẬP CONDITIONAL EDGE ĐẦU TIÊN TỪ START:
# Nếu thiếu thông tin nền tảng (user_profile trống) -> bắt buộc rẽ nhánh vào onboarding trước.
workflow.add_conditional_edges(
    START,
    check_profile_router,
    {
        "onboarding": "onboarding",
        "analyze": "analyze",
    },
)

# 4. Thiết lập Conditional Edges từ node analyze
workflow.add_conditional_edges(
    "analyze",
    route_by_intent,
    {
        "motivate": "motivate",
        "schedule": "schedule",
        "holistic_scheduler": "holistic_scheduler",
        "trend": "trend",
        "goal_manager": "goal_manager",
        "resource_finder": "resource_finder",
        "strategic_planner": "strategic_planner",
        "opportunity_scout": "opportunity_scout",
        "chat": "chat",
        "retrospective": "retrospective",
    },
)

# 5. Thiết lập Normal & Conditional Edges từ các node:
# goal_manager tự động móc nối sang resource_finder để quét tài liệu & báo giá ngay sau khi phê duyệt mục tiêu
workflow.add_edge("onboarding", END)
workflow.add_edge("motivate", END)
workflow.add_edge("schedule", END)
workflow.add_edge("holistic_scheduler", END)
workflow.add_edge("trend", END)
workflow.add_edge("retrospective", END)
# Node giao tiếp (chat) rẽ nhánh có điều kiện:
# - Nếu user trả lời 'Đồng ý' (is_confirmed == True) -> truyền dữ liệu sang goal_manager
# - Nếu đã thu thập đủ thông tin rào cản -> truyền dữ liệu sang strategic_planner
# - Ngược lại: kết thúc tại END
workflow.add_conditional_edges(
    "chat",
    route_from_chat,
    {
        "goal_manager": "goal_manager",
        "strategic_planner": "strategic_planner",
        END: END,
    },
)

# goal_manager truyền dữ liệu sang holistic_scheduler để bóc tách checklist và tạo lịch (Phase 9)
workflow.add_edge("goal_manager", "holistic_scheduler")
workflow.add_edge("resource_finder", END)

# strategic_planner tự động móc nối sang opportunity_scout khi nhận diện Milestone trung gian cần trinh sát
workflow.add_conditional_edges(
    "strategic_planner",
    route_from_strategic_planner,
    {
        "opportunity_scout": "opportunity_scout",
        "holistic_scheduler": "holistic_scheduler",
        END: END,
    },
)
workflow.add_edge("opportunity_scout", "holistic_scheduler")

# 6. CẤU HÌNH BỘ NHỚ HỘI THOẠI (MEMORYSAVER CHECKPOINTER)
# Tích hợp MemorySaver giúp đồ thị LangGraph ghi nhớ ngữ cảnh hội thoại liên tục
memory_checkpointer = MemorySaver()
compiled_graph = workflow.compile(checkpointer=memory_checkpointer)


class MavisAgentWrapper:
    """
    Wrapper tích hợp MemorySaver quản lý chat_history xuyên suốt phiên làm việc.
    Tự động gắn thread_id theo username để cô lập phiên trò chuyện từng người dùng.
    Đảm bảo 100% username luôn hiện diện trong AgentState ở cả invoke() và stream().
    """
    def __init__(self, graph):
        self.graph = graph

    def _prepare_call(self, state, config):
        config = dict(config or {})
        configurable = dict(config.get("configurable", {}))

        # 1. Trích xuất username chuẩn mực từ state hoặc config
        user = "mavis"
        if isinstance(state, dict):
            raw_user = state.get("username")
            if raw_user and str(raw_user).strip():
                user = str(raw_user).strip().lower()
        if user == "mavis" and "thread_id" in configurable:
            tid_parts = str(configurable["thread_id"]).replace("thread_", "").split("_")
            if tid_parts and tid_parts[0].strip():
                user = tid_parts[0].strip().lower()

        # 2. Đảm bảo state dict luôn mang username chính xác
        if isinstance(state, dict):
            state["username"] = user

        # 3. Đồng bộ thread_id
        if "thread_id" not in configurable:
            configurable["thread_id"] = f"thread_{user}"
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


mavis_agent = MavisAgentWrapper(compiled_graph)

