# agents/nodes/planner.py
# Chuyên trách: Nghiên cứu, Lập lộ trình Backcasting, Trinh sát cơ hội, Xu hướng & Strategy Architect
import json
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.state import AgentState, CoachState
from agents.nodes.base import (
    SYSTEM_PROMPT,
    ACHIEVEMENT_LEDGER,
    extract_text_from_content,
    safe_dict,
    safe_list,
    get_llm,
    invoke_llm_resilient,
    execute_trend_search,
    execute_opportunity_scout,
    execute_resource_search,
    load_user_goals,
    save_user_goals,
    load_user_goal_profile,
    load_user_resources,
    save_user_resources,
    save_user_roadmap,
    add_goal,
    append_resource_to_goal,
    append_opportunity_and_networking_tasks,
    save_master_schedule,
    detect_goal_domain,
    DOMAIN_TERMINOLOGY,
    get_vietnam_today_str,
    compute_target_date,
    generate_detailed_master_schedule,
    CuratedResources,
    StrategicRoadmap,
    CuratedResourceResult,
)


class ResourceItemDetail(BaseModel):
    title: str = Field(description="Tên tài liệu, giáo trình, bộ đề hoặc công cụ")
    url: str = Field(description="Đường link chính thức uy tín")
    type: str = Field(description="'Giáo trình', 'Bộ đề', 'Khóa học', hoặc 'Công cụ'")
    how_to_use: str = Field(description="Hướng dẫn khai thác cụ thể")


class WeeklyTaskItem(BaseModel):
    task_name: str = Field(description="Tên nhiệm vụ/bài tập cụ thể (VD: 'Giải đề Reading Cam 18 Test 1')")
    energy_level: str = Field(
        default="🔴 Deep Work",
        description="Nhãn độ nặng não: '🔴 Deep Work', '🟡 Shallow Work', hoặc '🟢 Recharge'",
    )
    resource_title: str = Field(default="", description="Tên gói tài liệu 1-Click đi kèm")
    resource_url: str = Field(default="", description="Đường link chính thức uy tín tới tài liệu thực tế")
    definition_of_done: str = Field(
        default="",
        description="Tiêu chí hoàn thành (Definition of Done - DoD) cụ thể, đo lường được",
    )


class WeeklyMilestoneItem(BaseModel):
    week: str = Field(description="Tuần (VD: 'Tuần 1', 'Tuần 2')")
    milestone: str = Field(description="Cột mốc trọng tâm của tuần")
    tasks: List[WeeklyTaskItem] = Field(
        default=[],
        description="Danh sách các task cụ thể trong tuần",
    )
    action_items: List[str] = Field(
        default=[],
        description="Tóm tắt ngắn gọn các gạch đầu dòng hành động",
    )
    estimated_hours: float = Field(default=7.0, description="Số giờ dự kiến")
    resources: str = Field(default="", description="Tài liệu bổ trợ cho tuần")


class MonthlyMilestoneItem(BaseModel):
    month: str = Field(description="Tháng (VD: 'Tháng 1', 'Tháng 2')")
    milestone: str = Field(description="Mục tiêu cốt lõi của tháng")
    resources: str = Field(default="", description="Tài liệu trọng tâm")


class QuarterlyMilestoneItem(BaseModel):
    quarter: str = Field(description="Quý (VD: 'Quý 1', 'Quý 2')")
    focus: str = Field(description="Trọng tâm chiến lược")
    target_outcome: str = Field(description="Kết quả đầu ra kỳ vọng")


class StrategicMethodOption(BaseModel):
    method_name: str = Field(description="Tên chiến lược/phương pháp tiếp cận")
    core_principle: str = Field(description="Nguyên lý cốt lõi & cơ chế vận hành của phương pháp")
    time_allocation: str = Field(description="Cách phân bổ thời gian và nhịp độ")
    suitability: str = Field(description="Tại sao phương pháp này tối ưu cho mục tiêu")


class ArchitectConsultationOutput(BaseModel):
    strategic_analysis: str = Field(description="Phân tích sâu sắc bối cảnh mục tiêu")
    proposed_methods: List[StrategicMethodOption] = Field(description="2-3 phương pháp/chiến lược tiếp cận tối ưu nhất")
    strategy_summary: str = Field(description="Tóm tắt ngắn gọn súc tích phương pháp chiến lược")
    ready_to_breakdown: bool = Field(default=False, description="True nếu người dùng đã đồng ý chốt phương pháp")
    architect_response: str = Field(description="Phản hồi đối thoại sắc sảo, tự nhiên của Strategy Architect")


class ArchitectGoalBreakdown(BaseModel):
    strategy_summary: Optional[str] = Field(default="", description="Tóm tắt phương pháp chiến lược đã chốt")
    updated_preferred_time: Optional[str] = Field(None, description="Khung giờ ưu tiên được cập nhật")
    updated_priority: Optional[str] = Field(None, description="Độ ưu tiên được cập nhật")
    updated_daily_hours: Optional[float] = Field(None, description="Số giờ mỗi ngày được cập nhật")
    yearly: str = Field(description="Tầm nhìn dài hạn / mục tiêu cốt lõi năm")
    quarterly: List[QuarterlyMilestoneItem] = Field(description="Phân kỳ các Quý (quarterly)")
    monthly: List[MonthlyMilestoneItem] = Field(description="Phân kỳ các Tháng (monthly)")
    weekly: List[WeeklyMilestoneItem] = Field(description="Phân rã chi tiết các Tuần (weekly)")
    resources: List[ResourceItemDetail] = Field(description="Danh sách tài liệu và link chính thức thẩm định")
    architect_response: str = Field(description="Phản hồi chi tiết của AI Architect về lộ trình")


def trend_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Autonomous Trend Scouting (Trinh sát Tiền tệ & Cơ hội Công nghệ).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
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

    search_query = f"{last_user_message} AI trends startup opportunities 2026"
    search_results = execute_trend_search(search_query, max_results=3)

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
2. **ĐỐI CHIẾU SKILL-SET CỦA MAVIS:** Phân tích điểm chạm với lợi thế của Mavis.
3. **KỸ NĂNG SINH LỜI CẦN HỌC (ACTIONABLE ALPHA SKILLS):** Chỉ định rõ 1-2 kỹ năng/công cụ thực chiến.
4. **ĐỀ XUẤT TIME-BLOCKING:** Gợi ý khung giờ hợp lý trong tuần.
"""

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
            "- Làn sóng **Autonomous Agentic Workflows** (Multi-Agent System, LangGraph, Tool Calling) đang thu hút dòng vốn đầu tư mạo hiểm AI.\n\n"
            "**2. ĐỐI CHIẾU LỢI THẾ CỦA BẠN:**\n"
            "- Nền tảng tư duy logic và khả năng thực thi độc lập giúp bạn nhanh chóng nắm bắt công nghệ mới.\n\n"
            "**3. KỸ NĂNG SINH LỜI CẦN BỔ SUNG NGAY:**\n"
            "- Làm chủ **LangGraph Multi-Agent Orchestration** và tích hợp API/Tool Calling.\n\n"
            "**4. ĐỀ XUẤT LẬP LỊCH CHIẾN LƯỢC:**\n"
            "- Khung 08:00 - 10:00 sáng giữ nguyên cho các mục tiêu nhận thức cao cốt lõi."
        )

    return {
        "messages": [AIMessage(content=brief_reply)],
        "intent": "explore_trend",
    }


def resource_finder_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Resource Finder & Price/Cost Estimator (Phase 6.2).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    target_topic = state.get("target_goal") or ""
    if not target_topic:
        target_topic = last_user_message or "Tài liệu học AI, Data Science và IT BA"

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
1. Tuyển chọn 3-4 tài nguyên tinh hoa.
2. Với MỖI tài nguyên, ước tính chi phí cụ thể.
3. cost_overview: Tóm tắt ước lượng tổng chi phí đầu tư.
4. strategic_advice: Lời khuyên của Executive Coach về phương pháp học sâu.
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
        ]
        for res_item in fallback_resources:
            append_resource_to_goal(target_topic, res_item, username=username)

        reply_text = (
            f"📚 **TỦ TÀI NGUYÊN & BÁO GIÁ ĐỀ XUẤT: {target_topic.upper()}**\n\n"
            "💰 **Ước tính ngân sách:** Ưu tiên tận dụng tài liệu mã nguồn mở và chính sách Financial Aid.\n\n"
            "1. **[Coursera / MOOC]** [Coursera Data Science & ML Professional Specialization](https://www.coursera.org)\n"
            "   - 💵 *Chi phí:* ~$49/tháng\n"
            "2. **[PDF / Giáo trình]** [Tài liệu & Đề cương chuyên sâu](https://github.com)\n"
            "   - 💵 *Chi phí:* Miễn phí / Open Source\n\n"
            "💡 *Lời khuyên Coach:* Bắt đầu ngay với các tài liệu nền tảng miễn phí."
        )

    return {
        "messages": [AIMessage(content=reply_text)],
        "intent": "find_resources",
        "target_goal": None,
    }


def research_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 2: Research Node (Tìm kiếm & Thẩm định tài liệu thực tế cho ĐA MỤC TIÊU).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    goals = safe_list(state.get("goals") or load_user_goals(username))
    if not goals:
        single_p = safe_dict(state.get("profile") or load_user_goal_profile(username))
        if single_p.get("goal_name"):
            goals = [single_p]

    all_resources = []
    for g in goals:
        g_name = g.get("goal_name", "IELTS 7.0")
        g_level = g.get("current_level", "Cơ bản")
        g_hours = g.get("daily_hours", 1.5)

        search_query = f"{g_name} {g_level} tài liệu giáo trình bộ đề chính thức"
        raw_results = execute_resource_search(search_query, max_results=3)

        research_prompt = f"""Bạn là Chuyên gia Thẩm định & Tuyển chọn Tài liệu Giáo trình (Curated Research Specialist).
Khách hàng có mục tiêu:
- Tên mục tiêu: {g_name}
- Điểm xuất phát: {g_level}
- Quỹ thời gian: {g_hours} giờ/ngày

Dữ liệu tìm kiếm thực tế thu thập được:
{json.dumps(raw_results, ensure_ascii=False, indent=2)}

NHIỆM VỤ:
Tuyển chọn 2 đến 3 tài liệu, bộ đề, giáo trình hoặc công cụ thực tế, uy tín và chuẩn mực nhất.
Xuất ra danh sách tài nguyên chuẩn: goal_name, title, url, type, estimated_hours, how_to_use.
"""
        try:
            curated_obj: CuratedResources = invoke_llm_resilient(
                preferred_model="gemini-2.5-pro",
                messages=[
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=research_prompt),
                ],
                structured_schema=CuratedResources,
                temperature=0.2,
            )
            for r in curated_obj.resources:
                r_dict = r.model_dump()
                r_dict["goal_name"] = g_name
                all_resources.append(r_dict)
        except Exception as e:
            print(f"Lỗi trong research_node cho {g_name}: {e}")
            for r in raw_results[:2]:
                all_resources.append({
                    "goal_name": g_name,
                    "title": r.get("title", f"Tài liệu chuẩn cho {g_name}"),
                    "url": r.get("url", "https://cambridgeenglish.org"),
                    "type": "Tài liệu học tập",
                    "estimated_hours": 30.0,
                    "how_to_use": f"Dành 1-1.5 giờ mỗi ngày để học theo cấp độ {g_level}.",
                })

    save_user_resources(all_resources, username=username)
    return {
        "resources": all_resources,
        "goals": goals,
        "username": username,
    }


def strategic_planner_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 3: Strategic Planning & Multi-Goal Backcasting (Phase 11+).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    goals = safe_list(state.get("goals") or load_user_goals(username))
    if not goals:
        single_p = safe_dict(state.get("profile") or load_user_goal_profile(username))
        if single_p.get("goal_name"):
            goals = [single_p]

    resources = safe_list(state.get("resources") or load_user_resources(username))
    total_daily_hours = sum(float(g.get("daily_hours", 1.5)) for g in goals)
    total_daily_minutes = int(total_daily_hours * 60)

    planner_prompt = f"""Bạn là Giám đốc Chiến lược Huấn luyện Điều hành (Chief Strategic Planner).
Áp dụng tư duy Backcasting cho khách hàng có {len(goals)} MỤC TIÊU SONG SONG:
{json.dumps(goals, ensure_ascii=False, indent=2)}

TỔNG QUỸ THỜI GIAN CAM KẾT: {total_daily_hours} giờ/ngày ({total_daily_minutes} phút/ngày).
Danh mục tài nguyên thực tế đã thẩm định:
{json.dumps(resources, ensure_ascii=False, indent=2)}

NHIỆM VỤ CHIẾN LƯỢC:
1. target_vision: Tuyên ngôn mục tiêu tổng hợp.
2. total_phases: Phân kỳ Quý / Tháng tổng quan.
3. balance_strategy: Chiến lược phân bổ thời gian trong ngày và điều hòa tải nhận thức.
4. total_daily_hours: {total_daily_hours}
5. weekly_milestones: Chi tiết 4 tuần đầu tiên.
"""

    try:
        roadmap_obj: StrategicRoadmap = invoke_llm_resilient(
            preferred_model="gemini-2.5-pro",
            messages=[
                SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
                HumanMessage(content=planner_prompt),
            ],
            structured_schema=StrategicRoadmap,
            temperature=0.2,
        )
        roadmap_dict = roadmap_obj.model_dump()
    except Exception as e:
        print(f"Lỗi trong strategic_planner_node: {e}")
        first_res = resources[0] if resources else {"title": "Tài liệu học tập chuẩn", "url": "https://cambridgeenglish.org"}
        fallback_tasks = []
        start_h = 8
        for g_idx, g in enumerate(goals):
            g_title = g.get("goal_name", f"Mục tiêu {g_idx + 1}")
            g_dur = int(float(g.get("daily_hours", 1.0)) * 60)
            end_h = start_h + (g_dur // 60)
            time_slot = f"{start_h:02d}:00 - {end_h:02d}:00"
            fallback_tasks.append({
                "day_number": 1,
                "goal_name": g_title,
                "task_title": f"Khởi động kế hoạch và đánh giá xuất phát điểm cho {g_title}",
                "duration_minutes": g_dur,
                "time_slot": time_slot,
                "attached_resource": first_res.get("title", "Tài liệu chuẩn"),
                "cognitive_load": "high" if g_idx == 0 else "medium",
            })
            start_h = end_h + 1

        roadmap_dict = {
            "target_vision": f"Cán đích toàn diện {len(goals)} mục tiêu song song",
            "total_phases": "Giai đoạn 1: Xây nền tảng song hành -> Giai đoạn 2: Bứt phá chuyên sâu -> Giai đoạn 3: Thực chiến & Cán đích",
            "balance_strategy": f"Phân bổ tổng {total_daily_hours}h/ngày: Khung sáng cho mục tiêu ưu tiên cao, Khung tối cho mục tiêu thứ 2.",
            "total_daily_hours": total_daily_hours,
            "weekly_milestones": [
                {
                    "week_number": 1,
                    "milestone_title": "Khởi động và thiết lập thói quen học tập song hành",
                    "daily_tasks": fallback_tasks,
                }
            ],
        }

    save_user_goals(goals, username=username)
    save_user_roadmap(roadmap_dict, username=username)

    for g in goals:
        g_name = g.get("goal_name", "Mục tiêu")
        g_days = g.get("duration_days", 90)
        g_cat = g.get("category", "career")
        add_goal(
            title=f"{g_name} (Lộ trình {g_days} ngày)",
            deadline=f"{g_days} ngày tới",
            category="education" if "học" in g_cat.lower() or "ielts" in g_name.lower() or "hsk" in g_name.lower() else "career",
            milestones=[{"milestone": f"Cán đích {g_name}", "timeline": f"{g_days} ngày"}],
            status="in_progress",
            username=username,
        )

    return {
        "roadmap": roadmap_dict,
        "goals": goals,
        "profile": goals[0] if goals else {},
        "target_goal": roadmap_dict.get("target_vision", "Đa mục tiêu"),
        "username": username,
    }


def opportunity_scout_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 8: Opportunity Scout & Networking Protocol (Phase 7.3).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    target_milestone = state.get("target_milestone")
    intent = state.get("intent", "")

    if not target_milestone and intent != "opportunity_scout":
        return {}

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

    search_query = f"{target_milestone} fellowship internship bootcamp 2026"
    raw_scouted_results = execute_opportunity_scout(search_query, max_results=4)

    networking_actions = [
        "Tham gia 2 nhóm cộng đồng chuyên môn cốt lõi (Facebook/LinkedIn).",
        "Tìm kiếm và gửi tin nhắn kết nối (Outreach) tới 1-2 cựu học viên/chuyên gia trên LinkedIn để hỏi kinh nghiệm thi tuyển và phỏng vấn.",
        "Thu thập đề cương và case-study thực tế từ cựu học viên để chuẩn bị trước điểm rơi phong độ.",
    ]

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

    target_goal_name = state.get("target_goal") or "Phát triển Năng lực Thực chiến"
    append_opportunity_and_networking_tasks(
        target_goal_name,
        raw_scouted_results,
        weekly_tasks,
        username=username,
    )

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
    existing_plan = list(state.get("plan") or [])
    updated_plan = existing_plan + [t for t in weekly_tasks if not any(et.get("title") == t.get("title") for et in existing_plan)]

    return {
        "messages": [AIMessage(content=reply_text)],
        "plan": updated_plan,
        "scouted_opportunities": raw_scouted_results,
        "networking_actions": networking_actions,
    }


def architect_chat(
    user_message: str,
    username: str = "mavis",
    goal_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    force_breakdown: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Hàm Chatbot 2: Strategy Architect (Chuyên trách Giai đoạn 1).
    """
    if "force_breakdown" in kwargs and kwargs["force_breakdown"] is not None:
        force_breakdown = bool(kwargs["force_breakdown"])
    if not goal_id and kwargs.get("goal_id"):
        goal_id = kwargs.get("goal_id")
    if not username and kwargs.get("username"):
        username = kwargs.get("username")
    if not chat_history and kwargs.get("chat_history"):
        chat_history = kwargs.get("chat_history")
    username = (username or "mavis").strip().lower()
    goals = load_user_goals(username)

    target_goal = None
    target_idx = None

    if goal_id:
        for idx, g in enumerate(goals):
            if g.get("id") == goal_id or g.get("goal_id") == goal_id:
                target_goal = g
                target_idx = idx
                break

    if target_goal is None:
        msg_lower = user_message.lower()
        for idx, g in enumerate(goals):
            g_title = str(g.get("title") or g.get("goal_name", "")).lower()
            if g_title and g_title in msg_lower:
                target_goal = g
                target_idx = idx
                break

    if target_goal is None:
        for idx, g in enumerate(goals):
            if g.get("status") == "evaluating":
                target_goal = g
                target_idx = idx
                break
        if target_goal is None and goals:
            target_goal = goals[0]
            target_idx = 0

    if target_goal is None:
        target_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Mục tiêu hành động mới",
            "category": "Học tập",
            "priority": "P2 - High",
            "preferred_time": "08:00 - 10:00 Sáng",
            "daily_hours": 1.5,
            "duration_days": 90,
            "status": "evaluating",
            "strategy_summary": "",
            "breakdown": {},
        }
        goals.append(target_goal)
        target_idx = len(goals) - 1

    goal_title = target_goal.get("title") or target_goal.get("goal_name", "Mục tiêu phát triển")
    current_bd = target_goal.get("breakdown", {})
    existing_strategy = target_goal.get("strategy_summary", "")

    target_domain = detect_goal_domain(target_goal, goal_title, target_goal.get("category", ""))
    domain_terms = DOMAIN_TERMINOLOGY.get(target_domain, DOMAIN_TERMINOLOGY.get("general", {}))

    prohibited_note = ""
    if domain_terms.get("prohibited_terms"):
        prohibited_str = ", ".join(f"'{p}'" for p in domain_terms["prohibited_terms"])
        prohibited_note = f"\n- TUYỆT ĐỐI CẤM (STRICT PROHIBITION): TUYỆT ĐỐI KHÔNG DÙNG các từ sau: {prohibited_str}."

    preferred_note = ""
    if domain_terms.get("preferred_terms"):
        pref_str = ", ".join(f"'{p}'" for p in domain_terms["preferred_terms"])
        preferred_note = f"\n- TỪ NGỮ CHUẨN MỰC BẮT BUỘC SỬ DỤNG: {pref_str}."

    domain_guideline = ""
    if target_domain == "health":
        domain_guideline = """
- BẮT BUỘC ÁP DỤNG CÔNG THỨC VÀNG CHO SỨC KHỎE & GIẢM CÂN / THỂ CHẤT:
  1. 70% DINH DƯỠNG:
     * Kiểm soát calo khoa học: Calo In < Calo Out với mức thâm hụt an toàn (~500 kcal/ngày dưới mức TDEE).
     * Nhịn ăn gián đoạn (Intermittent Fasting 16/8): Cửa sổ ăn 8 tiếng (12:00 - 20:00), nhịn 16 tiếng.
     * Tỷ lệ Macro: Nạp đủ 1.6 - 2.0g protein/kg thể trọng, ưu tiên tinh bột chậm và rau xanh nhiều xơ.
  2. 30% TẬP LUYỆN:
     * Tập kháng lực: 3-4 buổi/tuần.
     * Cardio Zone 2 (30-45 phút đi bộ dốc / đạp xe): Giữ nhịp tim ở 60-70% max để đốt mỡ bền vững.
  3. LỘ TRÌNH 3 GIAI ĐOẠN 30-90 NGÀY RÕ RÀNG:
     * Giai đoạn 1 (Tháng 1 / 30 ngày đầu): Thích nghi thể trạng & Giảm 5kg đầu.
     * Giai đoạn 2 (Tháng 2 / Ngày 31-60): Tăng tiến cường độ (Progressive Overload) & Đốt mỡ lì lợm.
     * Giai đoạn 3 (Tháng 3 / Ngày 61-90): Siết nét cơ bắp & Về đích (thiết lập calo duy trì chống Yo-yo).
"""
    elif target_domain == "language":
        domain_guideline = """
- BẮT BUỘC ÁP DỤNG CHIẾN LƯỢC HỌC NGOẠI NGỮ KHOA HỌC: Spaced Repetition, Active Recall & Deep Work 90/20.
"""
    elif target_domain == "tech_study":
        domain_guideline = """
- BẮT BUỘC ÁP DỤNG CHIẾN LƯỢC KỸ THUẬT: Project-Based Learning: 30% lý thuyết + 70% code thực chiến.
"""
    elif target_domain == "career_finance":
        domain_guideline = """
- BẮT BUỘC ÁP DỤNG CHIẾN LƯỢC ĐIỀU HÀNH & QUẢN TRỊ: Khung OKRs/KPIs & tối ưu hóa dòng tiền.
"""

    architect_system_prompt = f"""Bạn là {domain_terms.get('role_title', 'Trưởng Kiến Trúc Sư Chiến Lược')} của hệ thống Mavis.
MỤC TIÊU NÀY ĐÃ ĐƯỢC CEO COACH CHÍNH THỨC PHÊ DUYỆT ĐƯA VÀO CUỘC ĐỜI NGƯỜI DÙNG.
NGHIÊM CẤM TUYỆT ĐỐI hỏi lại câu hỏi thẩm định.{prohibited_note}{preferred_note}
VAI TRÒ CỦA BẠN: Trực tiếp tư vấn chiến lược chuyên sâu, đề xuất phương pháp tối ưu và thiết kế lộ trình 4 tầng.
{domain_guideline}
"""

    msg_clean = user_message.strip().lower()
    explicit_triggers = ["chốt phương pháp", "đồng ý", "xuất bản lộ trình", "chốt lộ trình", "chốt chiến lược", "đồng ý phương pháp"]
    breakdown_triggers = [
        "chốt phương pháp", "chốt lộ trình", "chốt chiến lược", "chốt luôn", "chốt",
        "đồng ý phương pháp", "đồng ý lộ trình", "đồng ý", "ok chốt", "ok",
        "xuất bản lộ trình", "xuất bản", "phân rã 4 tầng", "phân rã bốn tầng",
        "tự động phân rã", "bắt đầu phân rã", "lập kế hoạch 4 tầng",
        "triển khai 4 tầng", "tạo lộ trình 4 tầng", "finalize", "breakdown"
    ]
    has_trigger = any(trig in msg_clean for trig in breakdown_triggers) or (
        any(w in msg_clean.split() for w in ["chốt", "chốt!", "chốt.", "đồng ý", "đồng ý!"])
    ) or any(t in msg_clean for t in explicit_triggers)
    has_existing_breakdown = bool(current_bd and current_bd.get("quarterly") and current_bd.get("weekly"))
    edit_keywords = ["đổi giờ", "chuyển giờ", "đổi khung giờ", "tăng giờ", "giảm giờ", "thêm tài liệu", "bớt tài liệu", "đổi ưu tiên", "chỉnh sửa"]
    is_editing_existing = has_existing_breakdown and any(k in msg_clean for k in edit_keywords)

    should_breakdown = force_breakdown or has_trigger or is_editing_existing

    search_query = f"{goal_title} tài liệu giáo trình lộ trình chính thức uy tín bài tập thực hành"
    if target_domain == "health":
        search_query = f"{goal_title} giáo án bài tập kháng lực cardio thực đơn thâm hụt calo khoa học"
    raw_search = execute_resource_search(search_query, max_results=5)

    busy_calendar_info = ""
    try:
        from tools.google_calendar import is_calendar_connected, get_busy_events_text_summary
        if is_calendar_connected(username):
            busy_calendar_info = get_busy_events_text_summary(username, days=7)
    except Exception:
        pass

    if not should_breakdown:
        is_continuation = bool(chat_history and len(chat_history) > 0)
        history_context_text = ""
        langchain_history = []
        if chat_history:
            recent_msgs = chat_history[-6:]
            history_lines = []
            for m in recent_msgs:
                role = m.get("role", "user")
                content = m.get("content", "").strip()
                if role == "user":
                    langchain_history.append(HumanMessage(content=content))
                    history_lines.append(f"Người dùng: {content}")
                elif role == "assistant":
                    langchain_history.append(AIMessage(content=content))
                    history_lines.append(f"Architect: {content}")
            history_context_text = "\n".join(history_lines)

        if has_existing_breakdown:
            breakdown_guidance = (
                "5. MỤC TIÊU NÀY ĐÃ CÓ LỘ TRÌNH 4 TẦNG TRONG HỆ THỐNG:\n"
                "   - TUYỆT ĐỐI KHÔNG kêu gọi người dùng nhắn 'chốt phương pháp' hay bấm nút xuất bản lộ trình nữa.\n"
                "   - Hãy xác nhận rõ ràng: '✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang Tab Giai đoạn 2 (Lịch Trình Thực Thi) để xem và tinh chỉnh lịch chi tiết từng ngày.'\n"
                "   - Trả lời thẳng thắn câu hỏi hoặc yêu cầu của người dùng về phương pháp."
            )
        else:
            breakdown_guidance = (
                f"5. Nhắc người dùng: 'Khi bạn hài lòng với phương pháp này, hãy nhắn \"chốt phương pháp\", \"đồng ý\" hoặc bấm nút \"{domain_terms.get('finalize_btn')}\" ngay bên dưới để AI tự động xuất bản toàn bộ lộ trình 4 tầng!'"
            )

        anti_repetition_rule = (
            "QUY TẮC CHỐNG LẶP & GIAO TIẾP TỰ NHIÊN (STRICT ANTI-REPETITION):\n"
            "- Đây là lượt trao đổi tiếp theo trong hội thoại. TUYỆT ĐỐI KHÔNG lặp lại đoạn chào mở đầu.\n"
            if is_continuation else
            "- Chào hỏi mở đầu chuyên nghiệp và đi thẳng vào phân tích chiến lược."
        )

        consultation_prompt = f"""Bạn là {domain_terms.get('role_title', 'Trưởng Kiến Trúc Sư Chiến Lược')} của hệ thống Mavis.
Nhiệm vụ: NHỊP 1 — TƯ VẤN CHIẾN LƯỢC & PHƯƠNG PHÁP TỔNG THỂ CHO MỤC TIÊU:
- Tên mục tiêu: {goal_title}
- Lĩnh vực: {target_goal.get('category', domain_terms.get('domain_name', 'Học tập'))}
- Mức ưu tiên: {target_goal.get('priority', 'P2 - High')}
- Khung giờ ưu tiên: {target_goal.get('preferred_time', '08:00 - 10:00 Sáng')}
- Quỹ thời gian: {target_goal.get('daily_hours', 1.5)} giờ/ngày
- Thời hạn: {target_goal.get('duration_days', 90)} ngày
- Phương pháp chiến lược hiện tại: {existing_strategy or 'Chưa có, cần đề xuất mới'}

LỊCH SỬ TRAO ĐỔI GẦN NHẤT VỚI NGƯỜI DÙNG:
{history_context_text if history_context_text else "Chưa có tin nhắn trước đó (đây là lượt đầu tiên)."}

LỊCH BẬN THỰC TẾ TRÊN GOOGLE CALENDAR:
{busy_calendar_info if busy_calendar_info else "Hiện chưa có sự kiện bận nào trên Google Calendar."}

TÀI NGUYÊN / GIÁO ÁN THỰC TẾ THAM KHẢO TÌM KIẾM ĐƯỢC:
{json.dumps(raw_search, ensure_ascii=False, indent=2)}

TIN NHẮN HIỆN TẠI CỦA NGƯỜI DÙNG:
"{user_message}"

CHỈ THỊ TƯ VẤN CHIẾN LƯỢC (NHỊP 1):
{anti_repetition_rule}
1. Phân tích bối cảnh và thách thức cốt lõi theo đúng lĩnh vực của mục tiêu ({domain_terms.get('domain_name')}).
2. Đề xuất hoặc tinh chỉnh 2-3 phương pháp/chiến lược tiếp cận tối ưu nhất.
3. Tóm tắt súc tích phương pháp chiến lược đang định hình vào `strategy_summary`.
{breakdown_guidance}
"""
        try:
            cons_output: ArchitectConsultationOutput = invoke_llm_resilient(
                preferred_model="gemini-2.5-pro",
                messages=[
                    SystemMessage(content=architect_system_prompt),
                    *langchain_history,
                    HumanMessage(content=consultation_prompt),
                ],
                structured_schema=ArchitectConsultationOutput,
                temperature=0.3,
            )
        except Exception as e:
            print(f"Lỗi invoke tư vấn chiến lược trong architect_chat: {e}")
            if target_domain == "health":
                fb_intro = (
                    f"Tôi đã ghi nhận ý kiến của bạn về mục tiêu **'{goal_title}'**. "
                    "Chiến lược tiếp tục bám sát: 70% Dinh dưỡng (thâm hụt 500 kcal, ăn đủ 1.6-2g protein/kg) + 30% Tập luyện (kháng lực 3-4 buổi kết hợp Cardio Zone 2)."
                    if is_continuation else
                    f"Chào bạn! Đối với mục tiêu **'{goal_title}'**, tôi đề xuất chiến lược rèn luyện & dinh dưỡng chuẩn khoa học:\n\n"
                    "🥗 **1. Chế độ Dinh Dưỡng (70%):** Thâm hụt calo ~500 kcal/ngày dưới mức TDEE kết hợp IF 16/8.\n"
                    "🏋️ **2. Giáo Án Tập Luyện (30%):** 3-4 buổi kháng lực/tuần + 2-3 buổi Cardio Zone 2.\n\n"
                    "📅 **Lộ trình 3 Giai đoạn 90 ngày:**\n"
                    "- Tháng 1: Thích nghi thể trạng & Giảm 5kg đầu.\n"
                    "- Tháng 2: Tăng cường độ (Progressive Overload) & Đốt mỡ lì lợm.\n"
                    "- Tháng 3: Siết nét cơ bắp & Về đích."
                )
                fb_closing = (
                    "\n\n✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang Tab Giai đoạn 2 (Lịch Trình Thực Thi) để xem và tinh chỉnh lịch chi tiết từng ngày."
                    if has_existing_breakdown else
                    f"\n\n💡 *Bạn thấy chế độ dinh dưỡng và giáo án tập luyện này thế nào?* Khi bạn đồng ý, hãy nhắn **'chốt phương pháp'**, **'đồng ý'** hoặc bấm nút **'{domain_terms.get('finalize_btn')}'** ngay bên dưới!"
                )
                cons_output = ArchitectConsultationOutput(
                    strategic_analysis=f"Mục tiêu '{goal_title}' đòi hỏi kỷ luật dinh dưỡng nghiêm ngặt (70%) và giáo án tập luyện khoa học (30%).",
                    proposed_methods=[
                        StrategicMethodOption(
                            method_name="Chiến Lược Thâm Hụt Calo Khoa Học & Nhịn Ăn Gián Đoạn (IF 16/8)",
                            core_principle="Kiểm soát Calo In < Calo Out với mức thâm hụt ~500 kcal/ngày, nạp đủ 1.6-2g protein/kg và nhịn ăn 16 tiếng.",
                            time_allocation="Cửa sổ ăn uống 12:00 - 20:00, nhịn từ 20:00 đến 12:00 trưa hôm sau.",
                            suitability="Giảm mỡ nhanh, cải thiện độ nhạy insulin, không gây mệt mỏi.",
                        ),
                        StrategicMethodOption(
                            method_name="Giáo Án Kháng Lực Kết Hợp Cardio Zone 2 Đốt Mỡ Tối Đa",
                            core_principle="Tập kháng lực 3-4 buổi/tuần + 30-45 phút Cardio Zone 2.",
                            time_allocation=f"{target_goal.get('daily_hours', 1.5)}h/ngày vào khung giờ {target_goal.get('preferred_time', '06:00 - 07:30 Sáng')}.",
                            suitability="Tối ưu hóa vóc dáng săn chắc, tăng trao đổi chất.",
                        ),
                    ],
                    strategy_summary=f"Dinh dưỡng thâm hụt 500 kcal (IF 16/8) kết hợp {target_goal.get('daily_hours', 1.5)}h/ngày tập kháng lực và Cardio Zone 2.",
                    ready_to_breakdown=False,
                    architect_response=f"{fb_intro}{fb_closing}",
                )
            else:
                fb_intro = (
                    f"Tôi đã ghi nhận ý kiến của bạn về mục tiêu **'{goal_title}'**. "
                    f"Chiến lược tiếp tục tập trung vào {target_goal.get('daily_hours', 1.5)}h/ngày Deep Work vào khung giờ {target_goal.get('preferred_time', '08:00 - 10:00')}."
                    if is_continuation else
                    f"Chào bạn! Đối với mục tiêu **'{goal_title}'**, tôi đề xuất 2 chiến lược tiếp cận tối ưu:\n\n1. **Deep Work Sprint (90/20):** Tập trung sâu vào khung giờ vàng.\n2. **Spaced Repetition & Project-Based:** Học qua bài tập thực tế."
                )
                fb_closing = (
                    "\n\n✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang Tab Giai đoạn 2 (Lịch Trình Thực Thi) để xem và tinh chỉnh lịch chi tiết từng ngày."
                    if has_existing_breakdown else
                    f"\n\nBạn cảm thấy phương pháp này đã phù hợp chưa? Khi đồng ý, hãy nhắn **'chốt phương pháp'**, **'đồng ý'** hoặc bấm nút **'{domain_terms.get('finalize_btn')}'** ngay bên dưới!"
                )
                cons_output = ArchitectConsultationOutput(
                    strategic_analysis=f"Mục tiêu '{goal_title}' thuộc nhóm {target_goal.get('category', 'Học tập')}.",
                    proposed_methods=[
                        StrategicMethodOption(
                            method_name="Phương pháp Deep Work Sprint (90/20)",
                            core_principle="Tập trung 100% nhận thức trong 90 phút liên tục vào khung giờ vàng.",
                            time_allocation=f"{target_goal.get('daily_hours', 1.5)}h vào khung giờ {target_goal.get('preferred_time', '08:00 - 10:00')}.",
                            suitability="Phù hợp tối đa với các mục tiêu đòi hỏi tư duy logic.",
                        ),
                    ],
                    strategy_summary=f"Ứng dụng Deep Work Sprint {target_goal.get('daily_hours', 1.5)}h/ngày vào khung giờ {target_goal.get('preferred_time', '08:00 - 10:00')}.",
                    ready_to_breakdown=False,
                    architect_response=f"{fb_intro}{fb_closing}",
                )

        target_goal["strategy_summary"] = cons_output.strategy_summary
        if target_idx is not None and target_idx < len(goals):
            goals[target_idx] = target_goal
        else:
            goals.append(target_goal)
        save_user_goals(goals, username=username)

        return {
            "response": cons_output.architect_response,
            "strategy_summary": cons_output.strategy_summary,
            "proposed_methods": [m.model_dump() for m in cons_output.proposed_methods],
            "ready_to_breakdown": cons_output.ready_to_breakdown,
            "is_breakdown": False,
            "updated_goal": target_goal,
            "goals": load_user_goals(username),
            "goal_id": target_goal.get("id"),
        }

    # NHỊP 2: XUẤT BẢN LỘ TRÌNH 4 TẦNG
    if target_domain == "health":
        final_strat = existing_strategy or f"Dinh dưỡng thâm hụt 500 kcal kết hợp {target_goal.get('daily_hours', 1.5)}h tập luyện kháng lực và Cardio Zone 2 vào khung giờ {target_goal.get('preferred_time', '06:00 - 07:30')}."
        energy_breakdown_instruction = f"""
   - Nhãn năng lượng & độ nặng (energy_level):
     * '{domain_terms["energy_deep"]}': Bài tập kháng lực trọng tâm (Push/Pull/Legs hoặc Full-Body), tạ hoặc Calisthenics cường độ cao.
     * '{domain_terms["energy_shallow"]}': Vận động nhẹ, đi bộ dốc Cardio Zone 2 (30-45 phút), chuẩn bị bữa ăn Meal Prep.
     * '{domain_terms["energy_recharge"]}': Giãn cơ tĩnh, lăn bọt (Foam rolling), tắm nước ấm, ngủ sâu phục hồi cơ bắp.
"""
    else:
        final_strat = existing_strategy or f"Ứng dụng Deep Work {target_goal.get('daily_hours', 1.5)}h/ngày vào khung giờ {target_goal.get('preferred_time', '08:00 - 10:00')} kết hợp thực hành chuẩn mực."
        energy_breakdown_instruction = """
   - Nhãn độ nặng não (energy_level):
     * '🔴 Deep Work': Tập trung nhận thức cao độ, học kiến thức mới/khó, giải đề thi chuẩn.
     * '🟡 Shallow Work': Ôn tập nhẹ nhàng, luyện phát âm, flashcard từ vựng.
     * '🟢 Recharge': Vận động thể chất, đi bộ, giãn cơ, phục hồi nhận thức.
"""

    architect_prompt = f"""Bạn là {domain_terms.get('role_title', 'Trưởng Kiến Trúc Sư Chiến Lược')} của hệ thống Mavis.
Nhiệm vụ: NHỊP 2 — XUẤT BẢN LỘ TRÌNH 4 TẦNG TỪ PHƯƠNG PHÁP ĐÃ CHỐT:
- Tên mục tiêu: {goal_title}
- Phân loại: {target_goal.get('category', domain_terms.get('domain_name', 'Học tập'))}
- Lĩnh vực chuyên biệt: {domain_terms.get('domain_name', 'Tổng quát')}
- Mức ưu tiên hiện tại: {target_goal.get('priority', 'P2 - High')}
- Khung giờ ưu tiên hiện tại: {target_goal.get('preferred_time', '08:00 - 10:00 Sáng')}
- Quỹ thời gian: {target_goal.get('daily_hours', 1.5)} giờ/ngày
- Thời hạn: {target_goal.get('duration_days', 90)} ngày

PHƯƠNG PHÁP CHIẾN LƯỢC ĐÃ THỐNG NHẤT:
"{final_strat}"

KHO TÀI LIỆU / CÔNG CỤ THỰC TẾ TÌM KIẾM ĐƯỢC:
{json.dumps(raw_search, ensure_ascii=False, indent=2)}

YÊU CẦU CỦA NGƯỜI DÙNG:
"{user_message}"

CHỈ THỊ KIẾN TRÚC & PHÂN CẤP 4 TẦNG:
1. Xây dựng phân cấp chi tiết khép kín 4 tầng: strategy_summary, yearly, quarterly, monthly, weekly.
2. BẮT BUỘC GẮN ĐỦ 3 THUỘC TÍNH CHO MỖI TASK TRONG TUẦN (WeeklyTaskItem):
{energy_breakdown_instruction}
   - Gói tài liệu / công cụ 1-Click (resource_title, resource_url).
   - Tiêu chí hoàn thành (definition_of_done - DoD).
3. resources: 2-3 tài nguyên, giáo án, công cụ hoặc tài liệu chuẩn mực nhất.
"""

    try:
        result: ArchitectGoalBreakdown = invoke_llm_resilient(
            preferred_model="gemini-2.5-pro",
            messages=[
                SystemMessage(content=architect_system_prompt),
                HumanMessage(content=architect_prompt),
            ],
            structured_schema=ArchitectGoalBreakdown,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Lỗi invoke trong architect_chat (Nhịp 2): {e}")
        if target_domain == "health":
            e_deep_val = domain_terms.get("energy_deep", "🔴 Deep Work")
            e_shallow_val = domain_terms.get("energy_shallow", "🟡 Shallow Work")
            e_recharge_val = domain_terms.get("energy_recharge", "🟢 Recharge")
            sample_tasks_w1 = [
                WeeklyTaskItem(
                    task_name=f"Tập kháng lực toàn thân cho {goal_title}",
                    energy_level=e_deep_val,
                    resource_title="Giáo án Kháng Lực Nền Tảng (Full Body 3 Buổi)",
                    resource_url="https://muscleandstrength.com",
                    definition_of_done="Hoàn thành 4 bài tập (Squat, Push-up, Row, Plank) 3 hiệp x 10-12 lần chuẩn form.",
                ),
                WeeklyTaskItem(
                    task_name="Đi bộ dốc Cardio Zone 2 & Chuẩn bị bữa ăn Meal Prep (High Protein)",
                    energy_level=e_shallow_val,
                    resource_title="Bảng tính Calo TDEE & Thực đơn 1.500 kcal",
                    resource_url="https://tdeecalculator.net",
                    definition_of_done="Hoàn thành 35 phút đi bộ dốc nhịp tim Zone 2 và chuẩn bị sẵn 3 hộp ăn trưa đủ 30g protein/hộp.",
                ),
                WeeklyTaskItem(
                    task_name="Giãn cơ tĩnh & Ngủ đủ 8 tiếng",
                    energy_level=e_recharge_val,
                    resource_title="Bài tập Giãn Cơ & Phục Hồi Thể Lực Chuẩn Khoa Học",
                    resource_url="https://youtube.com",
                    definition_of_done="Thực hiện 20 phút giãn cơ tĩnh các nhóm cơ chính và ngủ sâu giấc trước 22:30.",
                ),
            ]
            result = ArchitectGoalBreakdown(
                strategy_summary=final_strat,
                yearly=f"Chinh phục vóc dáng lý tưởng và hoàn thành xuất sắc mục tiêu {goal_title}",
                quarterly=[
                    QuarterlyMilestoneItem(
                        quarter="Giai đoạn 1 (30 ngày đầu): Thích Nghi Thể Chất & Giảm 5kg Đầu",
                        focus="Thiết lập kỷ luật thâm hụt 500 kcal, ăn giàu protein và tập kháng lực 3 buổi/tuần",
                        target_outcome="Cân nặng giảm 5kg, cơ thể săn chắc, giảm mỡ bụng rõ rệt",
                    ),
                    QuarterlyMilestoneItem(
                        quarter="Giai đoạn 2 (Ngày 31-60): Tăng Tiến Cường Độ & Đốt Mỡ Lì Lợm",
                        focus="Áp dụng Progressive Overload trong các bài tập và tăng thời lượng Cardio Zone 2",
                        target_outcome="Giảm thêm 5kg (tổng 10kg), tỷ lệ mỡ cơ thể giảm 4-5%",
                    ),
                    QuarterlyMilestoneItem(
                        quarter="Giai đoạn 3 (Ngày 61-90): Siết Cơ Nét & Về Đích 15kg Bền Vững",
                        focus="Hoàn thành chỉ tiêu cân nặng, siết cơ nét và chuyển dịch về calo duy trì TDEE mới",
                        target_outcome="Cân nặng giảm trọn vẹn 15kg, hình thành vóc dáng lý tưởng và chống hoàn cân",
                    ),
                ],
                monthly=[
                    MonthlyMilestoneItem(month="Tháng 1", milestone="Thích nghi ăn thâm hụt calo và rèn luyện thể lực cơ bản", resources="Thực đơn thâm hụt calo & Bảng tính TDEE"),
                    MonthlyMilestoneItem(month="Tháng 2", milestone="Tăng tải kháng lực và tối ưu hóa đốt mỡ thừa Zone 2", resources="Giáo án Progressive Overload & Timer Cardio"),
                    MonthlyMilestoneItem(month="Tháng 3", milestone="Siết nét vóc dáng và thiết lập chế độ giữ cân bền vững", resources="Kế hoạch duy trì TDEE dài hạn chống Yo-yo"),
                ],
                weekly=[
                    WeeklyMilestoneItem(
                        week="Tuần 1",
                        milestone="Thích nghi nhịp sinh hoạt, tính calo TDEE và tập bài mở đầu",
                        tasks=sample_tasks_w1,
                        action_items=[f"[{t.energy_level}] {t.task_name} — DoD: {t.definition_of_done}" for t in sample_tasks_w1],
                        estimated_hours=7.0,
                    ),
                ],
                resources=[
                    ResourceItemDetail(
                        title="Bảng Tính TDEE & Thâm Hụt Calo Khoa Học",
                        url="https://tdeecalculator.net",
                        type="Công cụ",
                        how_to_use="Nhập chỉ số cân nặng, chiều cao hàng tuần để cân chỉnh mức calo nạp vào.",
                    ),
                ],
                architect_response=f"Tôi đã xuất bản toàn diện lộ trình 4 tầng dựa trên phương pháp '{final_strat}' cho mục tiêu '{goal_title}'. Trạng thái mục tiêu đã kích hoạt và sẵn sàng thực thi!",
            )
        else:
            sample_tasks_w1 = [
                WeeklyTaskItem(
                    task_name=f"Học lý thuyết nền tảng & kỹ năng cốt lõi cho {goal_title}",
                    energy_level="🔴 Deep Work",
                    resource_title=f"Giáo trình chuẩn mực {goal_title}",
                    resource_url="https://cambridgeenglish.org",
                    definition_of_done="Hoàn thành đọc 20 trang giáo trình và ghi chú tóm tắt 5 nguyên lý cốt lõi.",
                ),
                WeeklyTaskItem(
                    task_name="Học từ vựng & thuật ngữ chuyên ngành qua Flashcard",
                    energy_level="🟡 Shallow Work",
                    resource_title="Kho thuật ngữ & từ vựng trích xuất",
                    resource_url="https://quizlet.com",
                    definition_of_done="Ghi nhớ 30 từ vựng mới và vượt qua bài test ôn tập đạt 90%.",
                ),
            ]
            result = ArchitectGoalBreakdown(
                strategy_summary=final_strat,
                yearly=f"Chinh phục toàn diện {goal_title}",
                quarterly=[
                    QuarterlyMilestoneItem(
                        quarter="Giai đoạn 1 (Quý 1): Nền Tảng & Củng Cố Cốt Lõi",
                        focus="Xây dựng nền tảng vững chắc và hình thành phản xạ",
                        target_outcome="Hoàn thiện 50% kiến thức và kỹ năng trọng tâm",
                    ),
                ],
                monthly=[
                    MonthlyMilestoneItem(month="Tháng 1", milestone="Củng cố kiến thức gốc và phương pháp", resources="Tài liệu chuyên ngành chuẩn"),
                ],
                weekly=[
                    WeeklyMilestoneItem(
                        week="Tuần 1",
                        milestone="Đánh giá năng lực và học module mở đầu",
                        tasks=sample_tasks_w1,
                        action_items=[f"[{t.energy_level}] {t.task_name} — DoD: {t.definition_of_done}" for t in sample_tasks_w1],
                        estimated_hours=7.0,
                    ),
                ],
                resources=[
                    ResourceItemDetail(
                        title=f"Giáo trình chuẩn mực cho {goal_title}",
                        url="https://cambridgeenglish.org",
                        type="Giáo trình",
                        how_to_use="Học đều đặn theo khung giờ vàng đã thiết lập.",
                    )
                ],
                architect_response=f"Tôi đã phân rã toàn diện lộ trình 4 tầng dựa trên phương pháp chiến lược '{final_strat}' cho mục tiêu '{goal_title}'.",
            )

    weekly_dicts = []
    for w in result.weekly:
        w_dict = w.model_dump()
        if not w_dict.get("action_items") and w_dict.get("tasks"):
            w_dict["action_items"] = [
                f"[{t.get('energy_level', '🔴 Deep Work')}] {t.get('task_name')} — DoD: {t.get('definition_of_done', 'Hoàn thành')}"
                for t in w_dict["tasks"]
            ]
        weekly_dicts.append(w_dict)

    updated_bd = {
        "yearly": result.yearly,
        "quarterly": [q.model_dump() for q in result.quarterly],
        "monthly": [m.model_dump() for m in result.monthly],
        "weekly": weekly_dicts,
        "resources": [r.model_dump() for r in result.resources],
    }
    target_goal["breakdown"] = updated_bd
    target_goal["strategy_summary"] = result.strategy_summary or final_strat

    if result.updated_preferred_time:
        target_goal["preferred_time"] = result.updated_preferred_time
        target_goal["preferred_slots"] = result.updated_preferred_time
    if result.updated_priority:
        target_goal["priority"] = result.updated_priority
    if result.updated_daily_hours:
        target_goal["daily_hours"] = float(result.updated_daily_hours)

    if not target_goal.get("start_date"):
        target_goal["start_date"] = get_vietnam_today_str()
    d_days = int(target_goal.get("duration_days", 90))
    target_goal["target_date"] = compute_target_date(target_goal["start_date"], d_days)

    target_goal["status"] = "active"
    target_goal["is_complete"] = True

    if target_idx is not None and target_idx < len(goals):
        goals[target_idx] = target_goal
    else:
        goals.append(target_goal)

    save_user_goals(goals, username=username)
    save_user_resources(updated_bd["resources"], username=username)

    try:
        detailed_sched = generate_detailed_master_schedule(
            active_goals=[target_goal],
            start_date_str=target_goal["start_date"],
            num_days=14,
            username=username,
        )
        save_master_schedule(detailed_sched, username=username)
    except Exception as e_sched:
        print(f"Lỗi tự động sinh Master Schedule trong architect_chat: {e_sched}")

    success_notice = "✅ Lộ trình 4 tầng đã được xuất bản ở cột bên trái! Hãy chuyển sang Tab Giai đoạn 2 (Lịch Trình Thực Thi) để xem và tinh chỉnh lịch chi tiết từng ngày."
    final_resp = result.architect_response or ""
    if success_notice not in final_resp:
        final_resp = f"{success_notice}\n\n{final_resp}"

    return {
        "response": final_resp,
        "strategy_summary": target_goal["strategy_summary"],
        "is_breakdown": True,
        "updated_goal": target_goal,
        "goals": load_user_goals(username),
        "goal_id": target_goal.get("id"),
        "breakdown": updated_bd,
    }
