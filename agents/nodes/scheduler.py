# agents/nodes/scheduler.py
# Chuyên trách: Xếp lịch trình nhịp sinh học, Master Schedule, Dời lịch & Tối ưu năng lượng
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.state import AgentState, CoachState
from agents.nodes.base import (
    SYSTEM_PROMPT,
    ACHIEVEMENT_LEDGER,
    safe_dict,
    safe_list,
    get_llm,
    invoke_llm_resilient,
    get_active_tasks_and_milestones,
    get_goals_summary_text,
    get_historical_insights_summary_text,
    load_historical_insights,
    load_user_goals,
    load_user_goal_profile,
    load_user_resources,
    load_user_roadmap,
    load_master_schedule,
    save_master_schedule,
    get_vietnam_today_str,
    compute_target_date,
    generate_detailed_master_schedule,
    VIETNAM_WEEKDAYS,
    TaskItem,
    SchedulePlanResult,
)


class MasterScheduleTaskItem(BaseModel):
    date: str = Field(description="Ngày lịch thực tế định dạng YYYY-MM-DD (VD: '2026-11-21')")
    day_name: Optional[str] = Field(default="", description="Tên thứ trong tuần (VD: 'Thứ Bảy')")
    session: str = Field(description="'Sáng', 'Chiều', hoặc 'Tối'")
    time_slot: str = Field(description="Khung giờ cụ thể không trùng lặp (VD: '06:30 - 07:00', '12:00 - 12:30', '19:00 - 19:30')")
    goal_id: str = Field(description="ID mục tiêu tương ứng (hoặc 'life_nutrition_meal1', 'life_fitness', 'life_sleep')")
    goal_title: str = Field(description="Tên mục tiêu tương ứng")
    task_detail: str = Field(description="Nhiệm vụ cụ thể chi tiết kèm bài tập/nội dung hoặc thực đơn định lượng gram/calo")
    energy_level: str = Field(default="🔴 Deep Work", description="Nhãn độ nặng não: '🔴 Deep Work', '🟡 Shallow Work', hoặc '🟢 Recharge'")
    definition_of_done: str = Field(default="", description="Tiêu chí hoàn thành (DoD) cụ thể của buổi đó")
    resource_link: str = Field(default="", description="Link tài liệu hoặc tài nguyên đi kèm")
    resource_url: str = Field(default="", description="Link tài liệu chính thức 1-Click")
    resource_title: str = Field(default="", description="Tên gói tài liệu")
    is_done: bool = Field(default=False, description="Trạng thái hoàn thành (True/False)")


class MasterScheduleOutput(BaseModel):
    is_reschedule_request: bool = Field(description="True nếu người dùng báo bận, hoãn lịch hoặc dời task; False nếu tạo lịch mới")
    rescheduled_task_names: List[str] = Field(default=[], description="Danh sách các task đã được dời sang ngày khác")
    master_schedule: List[MasterScheduleTaskItem] = Field(description="Lịch trình tổng hợp gộp tất cả active goals, không trùng lặp giờ giấc")
    scheduler_response: str = Field(description="Lời phản hồi của AI Scheduler: phân bổ nhịp sinh học, bảo vệ năng lượng")


def schedule_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Dynamic Scheduling & Biometric Sensing (Phase 6.3).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
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

    if any(w in user_msg.lower() for w in ["cân bằng sinh học", "cân bằng động", "dynamic equilibrium", "holistic", "dung hòa", "chạy bộ 30 phút", "thâm hụt calo", "giảm cân"]):
        return holistic_scheduler_node(state)

    goals_summary = get_goals_summary_text(username=username)
    active_tasks = get_active_tasks_and_milestones(username=username)
    uploaded_context = state.get("uploaded_context") or ""
    context_note = f"\n\n[DỮ LIỆU TÀI LIỆU RAG ĐÃ TẢI LÊN - KNOWLEDGE BASE]:\n{uploaded_context}\n" if uploaded_context else ""

    insights_summary = get_historical_insights_summary_text(username=username)
    user_insights = load_historical_insights(username=username)
    failed_methods = user_insights.get("failed_methods", [])
    effective_methods = user_insights.get("effective_methods", [])
    productivity_patterns = user_insights.get("productivity_patterns", [])

    adaptive_prompt_block = f"""
BỘ NHỚ THÍCH NGHI ĐẶC BIỆT (ADAPTIVE MEMORY PROTOCOL - PHASE 10):
{insights_summary}

QUY TẮC RÀNG BUỘC BẮT BUỘC TỪ EXECUTIVE COACH:
1. TUYỆT ĐỐI KHÔNG đề xuất lại các phương pháp trong failed_methods: {failed_methods}.
2. BẮT BUỘC ưu tiên áp dụng các phương pháp trong effective_methods ({effective_methods}) và productivity_patterns ({productivity_patterns}).
"""

    user_goal_prof = state.get("profile") or load_user_goal_profile(username)
    if not active_tasks and not user_goal_prof.get("goal_name"):
        reply_text = (
            "Hiện tại hệ thống chưa ghi nhận mục tiêu hành động cụ thể nào. "
            "Bạn muốn chúng ta cùng thiết lập mục tiêu nào trước (như chứng chỉ IELTS, chuyên môn AI, hoặc nâng cao thể lực)?"
        )
        return {
            "messages": [AIMessage(content=reply_text)],
            "plan": [],
            "current_energy_level": state.get("current_energy_level", "high"),
        }

    plan_tasks: List[Dict[str, Any]] = []

    if is_overloaded_or_emergency:
        schedule_instruction = f"""Yêu cầu của người dùng: "{user_msg}"{context_note}
TRẠNG THÁI THỂ TRẠNG & TÌNH HUỐNG:
- Cảm xúc ghi nhận: {detected_emotion} (Phát hiện kiệt sức / quá tải / việc đột xuất)
- Năng lượng sinh học: LOW (Cần kích hoạt Giao thức Giảm tải ngay lập tức)
- Lịch đột xuất / Việc gấp: {is_emergency or has_emergency_keyword}

DỮ LIỆU CÁC MỤC TIÊU VÀ CỘT MỐC ĐANG ACTIVE TRONG GOALS LEDGER:
{goals_summary}

{adaptive_prompt_block}

ÁP DỤNG QUY TẮC QUẢN TRỊ HIỆU SUẤT ĐỈNH CAO:
1. THUẬT TOÁN RESCHEDULE TỰ ĐỘNG: DỜI các task nặng (High Cognitive Load) sang NGÀY HÔM SAU vào khung giờ vàng 08:00 - 10:00 sáng.
2. TỰ ĐỘNG CHÈN 'LOW LOAD TASK' & THÓI QUEN SINH HOẠT (HABIT STACKING).
3. Đặt is_rescheduled = True.
"""
    else:
        schedule_instruction = f"""Yêu cầu của người dùng: "{user_msg}"{context_note}
Mức năng lượng sinh học ghi nhận: HIGH (Não bộ đạt đỉnh cao nhận thức)

DỮ LIỆU CÁC MỤC TIÊU VÀ CỘT MỐC ĐANG ACTIVE TRONG GOALS LEDGER:
{goals_summary}

{adaptive_prompt_block}

Áp dụng nguyên tắc lập lịch nhịp sinh học tối ưu:
1. KHUNG GIỜ VÀNG (08:00 - 10:00 sáng): Deep Work nhiệm vụ nhận thức cao.
2. KHUNG GIỜ CHIỀU (Sau 14:00): Nhiệm vụ nhẹ tải (Low Cognitive Load).
3. KHUNG CHIỀU TỐI (17:30 - 18:30): Habit Stacking (podcast/audio sách).
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

    user_msg_lower = (last_user_message or "").lower()
    uploaded_context = (state.get("uploaded_context") or "").lower()

    active_tasks = get_active_tasks_and_milestones(username=username)

    user_goal_prof = state.get("profile") or load_user_goal_profile(username)
    if not active_tasks and not user_goal_prof.get("goal_name"):
        reply_text = (
            "Hiện tại hệ thống chưa ghi nhận mục tiêu hành động cụ thể nào trong 4 khía cạnh cuộc sống. "
            "Bạn muốn chúng ta bắt đầu bằng việc xây dựng mục tiêu trọng tâm nào trước?"
        )
        return {
            "messages": [AIMessage(content=reply_text)],
            "plan": [],
            "current_energy_level": state.get("current_energy_level", "high"),
        }

    has_running_and_deficit = any(
        w in user_msg_lower or w in uploaded_context
        for w in [
            "chạy bộ 30 phút", "chạy bộ", "thâm hụt calo", "calo", "giảm cân",
            "giảm mỡ", "cardio", "calorie deficit", "vóc dáng", "eat clean",
        ]
    )

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
            "note": "Khung giờ vàng não bộ: Năng lượng nhận thức đỉnh cao",
        },
        {
            "title": task_2_title,
            "time_slot": "08:55 - 10:00",
            "cognitive_load": "high",
            "category": "career",
            "platform_or_resource": task_2_platform,
            "status": "scheduled",
            "combined_with": None,
            "note": "Tập trung giải quyết bài toán logic phức tạp",
        },
        {
            "title": "Review tiến độ công việc & Networking Protocol kết nối chuyên môn",
            "time_slot": "14:00 - 14:45",
            "cognitive_load": "low",
            "category": "career",
            "platform_or_resource": "LinkedIn / Cộng đồng chuyên môn",
            "status": "scheduled",
            "combined_with": None,
            "note": "Tác vụ hạ tải buổi chiều: Mở rộng mạng lưới quan hệ",
        },
        {
            "title": "Chạy bộ Cardio 30 phút ngoài trời & Thâm hụt calo (Eat Clean)",
            "time_slot": "16:30 - 17:15",
            "cognitive_load": "physical",
            "category": "beauty",
            "platform_or_resource": "Công viên / Đồng hồ đo Calo",
            "status": "scheduled",
            "combined_with": None,
            "note": "Đốt cháy ~350-400 kcal theo tài liệu thâm hụt calo",
        },
        {
            "title": "Đệm Phục Hồi (Recovery Buffer): Giãn cơ, bù điện giải & tắm nước ấm",
            "time_slot": "17:15 - 17:45",
            "cognitive_load": "recovery_buffer",
            "category": "health",
            "platform_or_resource": "Không gian thư giãn",
            "status": "scheduled",
            "combined_with": "Uống 500ml nước bù khoáng, giãn cơ bắp, hạ nhịp tim",
            "note": "Ràng buộc sinh học: Glycogen cạn kiệt, cấm tuyệt đối xử lý logic nặng",
        },
        {
            "title": "Nghe Podcast phản xạ thụ động / Audio sách tư duy",
            "time_slot": "17:45 - 18:30",
            "cognitive_load": "habit_stacking",
            "category": "health",
            "platform_or_resource": "Spotify / Audio Podcast",
            "status": "scheduled",
            "combined_with": "Khi thả lỏng sau đệm phục hồi và chuẩn bị bữa tối",
            "note": "Passive Listening: Hấp thu kiến thức thụ động",
        },
        {
            "title": "Bữa cơm tối gia đình ấm cúng & Trò chuyện kết nối người thân",
            "time_slot": "19:00 - 20:00",
            "cognitive_load": "low",
            "category": "relationships",
            "platform_or_resource": "Bàn ăn gia đình",
            "status": "scheduled",
            "combined_with": None,
            "note": "Chế độ thâm hụt calo lành mạnh, gắn kết tình cảm gia đình",
        },
        {
            "title": "Quy trình Skincare khoa học 15 phút & Chăm sóc sắc vóc Executive",
            "time_slot": "22:00 - 22:30",
            "cognitive_load": "low",
            "category": "beauty",
            "platform_or_resource": "Bàn trang điểm / Cá nhân",
            "status": "scheduled",
            "combined_with": None,
            "note": "Massage thư giãn cơ mặt, dưỡng ẩm phục hồi làn da",
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

    reply_lines = [
        "🌿 **HỆ ĐIỀU HÀNH CÂN BẰNG SINH HỌC TOÀN DIỆN (HOLISTIC BIO-SCHEDULER - PHASE 7.4)**",
        "\n### 1. ⚖️ NGUYÊN TẮC CÂN BẰNG ĐỘNG (DYNAMIC EQUILIBRIUM ANALYSIS):",
        "- **Nhận diện Thể trạng & Dinh dưỡng:** Phát hiện mục tiêu **Chạy bộ 30 phút & Thâm hụt calo**.",
        f"- **Tính toán lại Mức Năng Lượng:** `{'LOW (Hạ nhiệt sinh học sau Cardio & Thâm hụt calo)' if has_running_and_deficit else 'BALANCED'}`.",
        "\n### 2. 🛑 RÀNG BUỘC SINH HỌC BẮT BUỘC:",
        "- ⛔ Không xếp tác vụ **Học tập cường độ cao** vào khung **17:15 - 19:00** ngay sau tập thể dục.",
        "- 🟢 Chèn Recovery Buffer (17:15 - 17:45) và Passive Listening (17:45 - 18:30).",
        "\n### 3. 📋 BẢNG LỊCH TRÌNH CHIA GIỜ CHI TIẾT:",
    ]

    for t in holistic_tasks:
        reply_lines.append(f"- **{t['time_slot']}** | `[{t['category'].upper()}]` **{t['title']}**")

    reply_text = "\n".join(reply_lines)

    return {
        "messages": [AIMessage(content=reply_text)],
        "plan": holistic_tasks,
        "current_energy_level": "low",
        "detected_emotion": "motivated",
    }


def scheduler_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 4: Scheduler & Execution Briefing (Phase 11 Multi-Agent System).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    goals = safe_list(state.get("goals") or load_user_goals(username))
    if not goals:
        single_p = safe_dict(state.get("profile") or load_user_goal_profile(username))
        if single_p.get("goal_name"):
            goals = [single_p]

    resources = safe_list(state.get("resources") or load_user_resources(username))
    roadmap = safe_dict(state.get("roadmap") or load_user_roadmap(username))

    total_daily_hours = sum(float(g.get("daily_hours", 1.5)) for g in goals)
    weekly_ms = safe_list(roadmap.get("weekly_milestones", []))
    w1 = safe_dict(weekly_ms[0]) if weekly_ms else {}
    w1_tasks = safe_list(w1.get("daily_tasks", []))

    schedule_items = []
    day1_tasks = [t for t in w1_tasks if safe_dict(t).get("day_number") == 1]
    if not day1_tasks and w1_tasks:
        day1_tasks = w1_tasks[:len(goals)]

    if day1_tasks:
        for t in day1_tasks:
            t_dict = safe_dict(t)
            schedule_items.append({
                "time": t_dict.get("time_slot", "08:00 - 10:00"),
                "task": f"[{t_dict.get('goal_name', 'Mục tiêu')}] {t_dict.get('task_title')}",
                "duration": f"{t_dict.get('duration_minutes', 90)} phút",
                "resource": t_dict.get("attached_resource", "Tài liệu chính thức"),
                "goal": t_dict.get("goal_name"),
                "type": "Deep Work / High Cognitive Focus" if t_dict.get("cognitive_load") == "high" else "Focused Work",
            })
    else:
        for g_idx, g in enumerate(goals):
            schedule_items.append({
                "time": g.get("preferred_slots", "08:00 - 10:00" if g_idx == 0 else "20:00 - 21:30"),
                "task": f"[{g.get('goal_name')}] Bắt đầu bài tập khởi động",
                "duration": f"{int(float(g.get('daily_hours', 1.5)) * 60)} phút",
                "resource": "Tài liệu chính thức",
                "goal": g.get("goal_name"),
                "type": "Focused Work",
            })

    goals_lines = []
    for g in goals:
        p_badge = "🔥 High" if g.get("priority") == "high" else ("⚡ Medium" if g.get("priority") == "medium" else "🌱 Low")
        goals_lines.append(
            f"- 🎯 **{g.get('goal_name')}** ({g.get('category', 'Học tập')}) | *Ưu tiên:* `{p_badge}` | *Vạch xuất phát:* {g.get('current_level')} | *Thời hạn:* {g.get('duration_days')} ngày | *Quỹ thời gian:* {g.get('daily_hours')}h/ngày"
        )
    goals_text = "\n".join(goals_lines)

    res_lines = []
    for r in resources:
        r_dict = safe_dict(r)
        g_tag = f"[{r_dict.get('goal_name')}] " if r_dict.get("goal_name") else ""
        res_lines.append(
            f"- **{g_tag}[{r_dict.get('title', 'Tài liệu')}]({r_dict.get('url', '#')})** ({r_dict.get('type', 'Tài liệu')}) - *Ước tính: {r_dict.get('estimated_hours', 'N/A')}h*"
        )
    res_text = "\n".join(res_lines) if res_lines else "Đang cập nhật danh mục tài liệu."

    ms_lines = []
    for w in weekly_ms[:4]:
        w_dict = safe_dict(w)
        ms_lines.append(f"- **Tuần {w_dict.get('week_number', 1)}:** {w_dict.get('milestone_title', '')}")
    ms_text = "\n".join(ms_lines) if ms_lines else "Đang phân bổ các mốc tuần."

    sched_lines = []
    for item in schedule_items:
        sched_lines.append(f"- **Khung giờ:** `{item.get('time')}` ({item.get('duration')})\n  *Nhiệm vụ:* {item.get('task')}\n  *Tài liệu:* {item.get('resource')}")
    sched_text = "\n".join(sched_lines)

    balance_strategy = roadmap.get("balance_strategy", "Phân bổ luân phiên giữa các khung giờ sáng và tối.")

    briefing = f"""🎯 **HỒ SƠ ĐA MỤC TIÊU ĐÃ ĐƯỢC THIẾT LẬP THÀNH CÔNG!**

Chúc mừng bạn! Chúng ta đã hoàn tất việc chốt thông số và thiết lập hồ sơ chiến lược cho **{len(goals)} mục tiêu song song**.

---

### 📋 **1. Bảng Tổng Quan Đa Mục Tiêu Song Song**
{goals_text}

⚡ **Tổng quỹ thời gian cam kết:** `{total_daily_hours} giờ/ngày`
💡 **Chiến lược cân bằng nhịp sinh học:** {balance_strategy}

---

### 📚 **2. Danh Mục Tài Liệu & Công Cụ Thực Tế Đã Thẩm Định**
{res_text}

---

### 🗺️ **3. Lộ Trình Backcasting & Phân Kỳ Chiến Lược**
- **Tầm nhìn:** {roadmap.get('target_vision', 'Chinh phục toàn diện các mục tiêu')}
- **Phân kỳ:** {roadmap.get('total_phases', 'Tháng 1 Nền tảng -> Tháng 2 Tăng tốc -> Tháng 3 Đạt chuẩn')}

**Các mốc tuần trọng tâm:**
{ms_text}

---

### ⚡ **4. Kế Hoạch Hành Động Ngày 1 (Hôm nay - Không Xung Đột Giờ Giấc)**
{sched_text}
"""

    return {
        "schedule": schedule_items,
        "messages": [AIMessage(content=briefing.strip())],
        "goals": goals,
        "profile": goals[0] if goals else {},
        "username": username,
    }


def scheduler_chat(
    user_message: str,
    username: str = "mavis",
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Hàm Chatbot 3: Scheduler Chat (Chuyên trách Giai đoạn 2).
    """
    username = (username or "mavis").strip().lower()
    goals = load_user_goals(username)
    active_goals = [g for g in goals if g.get("status") == "active"]
    if not active_goals:
        active_goals = [g for g in goals if g.get("status") not in ("paused", "completed", "evaluating")]

    existing_schedule = load_master_schedule(username)

    if not active_goals:
        return {
            "response": "Bạn chưa có mục tiêu nào đang kích hoạt (Active). Hãy thiết lập và chốt phương pháp mục tiêu ở Giai đoạn 1 trước nhé!",
            "schedule": existing_schedule or [],
            "rescheduled_tasks": [],
            "is_rescheduled": False,
        }

    active_summary = []
    for g in active_goals:
        bd = g.get("breakdown", {})
        weekly = bd.get("weekly", [])
        w1_tasks = weekly[0].get("tasks", []) if weekly else []
        active_summary.append({
            "goal_id": g.get("id"),
            "goal_title": g.get("title") or g.get("goal_name"),
            "category": g.get("category"),
            "priority": g.get("priority"),
            "preferred_time": g.get("preferred_time"),
            "daily_hours": g.get("daily_hours"),
            "strategy_summary": g.get("strategy_summary"),
            "start_date": g.get("start_date", get_vietnam_today_str()),
            "target_date": g.get("target_date", compute_target_date(get_vietnam_today_str(), 90)),
            "immediate_tasks": w1_tasks,
        })

    busy_calendar_info = ""
    try:
        from tools.google_calendar import is_calendar_connected, get_busy_events_text_summary
        if is_calendar_connected(username):
            busy_calendar_info = get_busy_events_text_summary(username, days=7)
    except Exception:
        pass

    today_str = get_vietnam_today_str()
    scheduler_prompt = f"""Bạn là Bậc Thầy Phân Bổ Lịch Trình Điều Hành (AI Master Scheduler) của hệ thống Mavis.
Nhiệm vụ: Chuyên trách GIAI ĐOẠN 2 — Gom toàn bộ mục tiêu đang Active để xếp lịch không trùng lặp vào master_schedule theo TRỤC THỜI GIAN THỰC (YYYY-MM-DD), hoặc dời lịch linh hoạt khi người dùng báo bận.

DANH SÁCH MỤC TIÊU ACTIVE CẦN XẾP LỊCH TỪ MONGODB:
{json.dumps(active_summary, ensure_ascii=False, indent=2)}

LỊCH HIỆN CÓ TRONG MASTER SCHEDULE (NẾU ĐÃ CÓ):
{json.dumps(existing_schedule[:10], ensure_ascii=False, indent=2) if existing_schedule else "Chưa có lịch, cần sinh mới."}

THÔNG TIN LỊCH BẬN THỰC TẾ TRÊN GOOGLE CALENDAR CỦA NGƯỜI DÙNG:
{busy_calendar_info if busy_calendar_info else "Hiện tại không có sự kiện bận nào trên Google Calendar."}

QUY TẮC NHỊP SINH HỌC & XẾP LỊCH ĐIỀU HÀNH BẮT BUỘC:
1. KHÔNG TRÙNG LẶP: Mỗi khung giờ trong ngày chỉ xếp DUY NHẤT 1 mục tiêu.
2. TRỤC NGÀY LỊCH THỰC TẾ: Trường 'date' bắt buộc ghi ngày dương lịch thực tế định dạng YYYY-MM-DD bắt đầu từ hôm nay ({today_str}). Trường 'day_name' ghi tên thứ ('Thứ Hai'..'Chủ Nhật').
3. BÓC TÁCH CHI TIẾT TỪNG KHUNG GIỜ SINH HOẠT TRONG NGÀY (CẤM GỘP 1 DÒNG CHUNG CHUNG):
   - Khung Tập luyện / Vận động thể chất (06:30 - 07:30 hoặc 07:00 - 08:00).
   - Khung Học tập / Làm việc chuyên sâu Deep Work (08:30 - 11:30).
   - Khung Dinh dưỡng IF 16:8: Bữa 1 (12:00 - 12:30) & Bữa 2 (19:00 - 19:30).
   - Khung Uống nước: Sáng 06:30 - 07:00 & Chiều 15:30 - 16:00.
   - Khung Giấc ngủ phục hồi: 22:15 - 22:30.
4. KHI NGƯỜI DÙNG BÁO BẬN: Đặt is_reschedule_request = True, nhận diện các task bị ảnh hưởng dời sang ngày tiếp theo, thêm tên các task đã dời vào rescheduled_task_names.

YÊU CẦU CỦA NGƯỜI DÙNG:
"{user_message}"
"""

    try:
        output: MasterScheduleOutput = invoke_llm_resilient(
            preferred_model="gemini-2.5-flash",
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=scheduler_prompt),
            ],
            structured_schema=MasterScheduleOutput,
            temperature=0.2,
        )
        schedule_dicts = [item.model_dump() for item in output.master_schedule]
        rescheduled_tasks = output.rescheduled_task_names
        response_text = output.scheduler_response
        is_rescheduled = output.is_reschedule_request
    except Exception as e:
        print(f"Lỗi invoke trong scheduler_chat: {e}")
        schedule_dicts = generate_detailed_master_schedule(
            active_goals=active_goals,
            start_date_str=get_vietnam_today_str(),
            num_days=14,
            username=username,
        )
        rescheduled_tasks = []
        is_rescheduled = False
        response_text = "Tôi đã phân rã toàn bộ các mục tiêu Active vào Master Schedule chi tiết từng ngày theo trục thời gian thực (YYYY-MM-DD), bóc tách riêng từng khung giờ Ăn gì, Tập gì, Uống gì và Ngủ mấy giờ mà không trùng lặp!"

    if not is_rescheduled:
        existing_covered_dates = set(t.get("date") for t in schedule_dicts if t.get("date"))
        all_details_check = " ".join(str(t.get("task_detail", "")) for t in schedule_dicts).lower()
        has_routine = (
            ("ăn" in all_details_check or "bữa" in all_details_check)
            and ("ngủ" in all_details_check or "22:30" in all_details_check)
            and ("uống" in all_details_check or "nước" in all_details_check)
        )
        if len(existing_covered_dates) < 7 or not has_routine:
            try:
                supp_tasks = generate_detailed_master_schedule(
                    active_goals=active_goals,
                    start_date_str=today_str,
                    num_days=max(7, len(existing_covered_dates)),
                    username=username,
                )
                existing_keys = set((str(t.get("date")), str(t.get("time_slot"))) for t in schedule_dicts)
                for st_item in supp_tasks:
                    key = (str(st_item.get("date")), str(st_item.get("time_slot")))
                    if key not in existing_keys:
                        # Nếu thiếu ngày hoàn toàn, hoặc là task nhịp sinh học (ăn/uống/ngủ/tập) chưa có trong khung giờ đó
                        if st_item.get("date") not in existing_covered_dates or not has_routine:
                            schedule_dicts.append(st_item)
                            existing_keys.add(key)
            except Exception as _e_supp:
                print(f"Lỗi bổ sung ngày vào master_schedule: {_e_supp}")

    for item in schedule_dicts:
        if not item.get("day_name") and item.get("date"):
            try:
                dt_tmp = datetime.strptime(str(item["date"])[:10], "%Y-%m-%d")
                item["day_name"] = VIETNAM_WEEKDAYS.get(dt_tmp.weekday(), "")
            except Exception:
                pass

        if not item.get("resource_url") and not item.get("resource_link"):
            td_lower = str(item.get("task_detail", "")).lower()
            if "nước" in td_lower or "nắng" in td_lower:
                item["resource_url"] = "https://hubermanlab.com"
                item["resource_link"] = "https://hubermanlab.com"
                item["resource_title"] = item.get("resource_title") or "Huberman Protocol: Tối ưu nhịp sinh học"
            elif "ngủ" in td_lower:
                item["resource_url"] = "https://sleepfoundation.org"
                item["resource_link"] = "https://sleepfoundation.org"
                item["resource_title"] = item.get("resource_title") or "Sleep Protocol: Tối ưu giấc ngủ sâu"
            elif "ăn" in td_lower or "bữa" in td_lower:
                item["resource_url"] = "https://eatthismuch.com"
                item["resource_link"] = "https://eatthismuch.com"
                item["resource_title"] = item.get("resource_title") or "Macro Nutrition Guide"
            elif any(w in td_lower for w in ["tập", "chạy", "squat", "push-up", "cardio", "kháng lực"]):
                item["resource_url"] = "https://muscleandstrength.com"
                item["resource_link"] = "https://muscleandstrength.com"
                item["resource_title"] = item.get("resource_title") or "Giáo án thể lực chuẩn"

    for item in schedule_dicts:
        if "task_detail" in item and item["task_detail"]:
            item["task_detail"] = str(item["task_detail"]).replace("**", "").replace("__", "").replace("~~", "").strip()
        if "definition_of_done" in item and item["definition_of_done"]:
            item["definition_of_done"] = str(item["definition_of_done"]).replace("**", "").replace("__", "").replace("~~", "").strip()
        if "time_slot" in item and item["time_slot"]:
            item["time_slot"] = str(item["time_slot"]).replace("**", "").replace("__", "").strip()
        if "resource_title" in item and item["resource_title"]:
            item["resource_title"] = str(item["resource_title"]).replace("**", "").replace("__", "").strip()

    save_master_schedule(schedule_dicts, username=username)

    if is_rescheduled and rescheduled_tasks:
        try:
            from tools.google_calendar import is_calendar_connected, update_rescheduled_calendar_event
            if is_calendar_connected(username):
                for r_name in rescheduled_tasks:
                    matching_tk = next((tk for tk in schedule_dicts if r_name.lower() in tk.get("task_detail", "").lower()), None)
                    if matching_tk:
                        update_rescheduled_calendar_event(
                            username=username,
                            task_identifier=r_name,
                            new_date=matching_tk.get("date", "Thứ Hai"),
                            new_time_slot=matching_tk.get("time_slot", "08:00 - 10:00"),
                        )
        except Exception as e:
            print(f"Lỗi đồng bộ Google Calendar khi dời lịch: {e}")

    return {
        "response": response_text,
        "master_schedule": schedule_dicts,
        "rescheduled_tasks": rescheduled_tasks,
        "is_rescheduled": is_rescheduled,
    }
