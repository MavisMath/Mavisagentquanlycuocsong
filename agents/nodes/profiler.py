# agents/nodes/profiler.py
# Chuyên trách: Phân tích ý định đầu vào, Onboarding, Quản lý mục tiêu & Profiler đa mục tiêu
import json
import uuid
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agents.state import AgentState, CoachState
from agents.nodes.base import (
    SYSTEM_PROMPT,
    ACHIEVEMENT_LEDGER,
    safe_dict,
    safe_list,
    get_llm,
    invoke_llm_resilient,
    scan_and_retrieve_context,
    analyze_and_estimate_goal,
    load_user_goals,
    save_user_goals,
    load_user_goal_profile,
    save_user_profile,
    add_goal,
    InputAnalysisResult,
    OnboardingExtractionResult,
    MultiGoalExtraction,
)


def analyze_input_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Phân tích câu chat của Mavis để gán giá trị cho intent, detected_emotion, current_energy_level và is_emergency.
    Cấu trúc lại Bộ định tuyến thành Executive Agentic Coach:
    - Phân biệt giữa tin nhắn 'tâm sự/dự định' (coach_dialogue) và 'lệnh thực thi'.
    - Khi người dùng phản hồi 'Đồng ý' / 'Xác nhận' cho câu hỏi chốt của Coach, nhận diện intent = 'confirm_goal'.
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    messages = state.get("messages", [])
    if not messages:
        return {
            "intent": "chat",
            "detected_emotion": "neutral",
            "current_energy_level": "high",
            "is_emergency": False,
            "username": username,
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
            "username": username,
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
   - 'coach_dialogue': Nếu người dùng hỏi lời khuyên, tư vấn chiến lược, hỏi cách làm/phương pháp thực thi, hoặc chia sẻ ước mơ, dự định. Toàn bộ các câu hỏi How / Why / Làm thế nào / Được không / Tư vấn chiến lược BẮT BUỘC phải được phân loại là 'coach_dialogue'.
   - 'retrospective': Nếu người dùng chia sẻ về việc bỏ cuộc, hủy mục tiêu, mục tiêu bị trễ hạn (overdue), phàn nàn phương pháp không hiệu quả / thất bại, hoặc thông báo hoàn thành mục tiêu.
   - 'confirm_goal': Nếu người dùng trả lời 'Đồng ý', 'Ok', 'Xác nhận', 'Tiến hành đi', 'Làm đi' khi Coach đã đưa ra câu hỏi chốt về việc đưa mục tiêu vào cuộc đời và xếp lịch.
   - 'holistic_schedule': Nếu Mavis yêu cầu lập lịch cân bằng sinh học toàn diện, dung hòa 4 Root Nodes, quy tắc cân bằng động (Dynamic Equilibrium) khi chạy bộ 30 phút và thâm hụt calo.
   - 'strategic_plan': Nếu Mavis hỏi về lập kế hoạch ngược (Backcasting), hoạch định lộ trình học Thạc sĩ AI, giải quyết xung đột mục tiêu (Priority Conflict).
   - 'opportunity_scout': Nếu Mavis yêu cầu trinh sát cơ hội thực chiến, tìm kiếm chương trình VinUni AI Bootcamp, hoặc hướng dẫn Networking Protocol.
   - 'schedule': Nếu Mavis yêu cầu lên lịch, dời lịch, hoãn lịch, xếp lại lịch (reschedule), xử lý lịch đột xuất, hoặc phân bổ lại task trong ngày.
   - 'motivate': Nếu Mavis than mệt, nản, đuối, áp lực, bế tắc, bug code thuần túy để giải tỏa cảm xúc.
   - 'set_goal': CHỈ CHỌN khi người dùng ra LỆNH THỰC THI TRỰC TIẾP yêu cầu lưu ngay mục tiêu mới vào hệ thống/ledger.
   - 'find_resources': Nếu Mavis cần tìm tài liệu học tập, giáo trình, file PDF, khóa học Coursera, github repo, roadmap cho một mục tiêu hay kỹ năng.
   - 'explore_trend': Nếu Mavis hỏi về xu hướng công nghệ, tin tức AI, startup, thị trường, dòng tiền.
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
        
        advice_keywords = [
            "làm sao", "làm thế nào", "tại sao", "thế nào", "được không", "có nên",
            "tư vấn", "lời khuyên", "chiến lược", "song song", "how", "why",
            "cách nào", "khả thi không", "có được không", "liệu có", "đỗ khóa", "đỗ vinuni", "vinuni ai"
        ]
        if any(w in user_lower for w in advice_keywords):
            intent = "coach_dialogue"
            emotion = "neutral"
            energy = "high"
        elif awaiting_confirmation or any(user_lower.startswith(w) for w in ["đồng ý", "ok", "xác nhận", "tiến hành", "làm đi"]):
            intent = "confirm_goal"
            emotion = "determined"
            energy = "high"
        elif any(w in user_lower for w in [
            "bỏ cuộc", "hủy mục tiêu", "không hợp phương pháp", "không hợp pomodoro",
            "thất bại rồi", "đuối quá không học nổi", "trễ hạn rồi", "quá hạn", "overdue",
            "hoàn thành xuất sắc", "hoàn thành mục tiêu", "rút kinh nghiệm", "hồi cứu",
            "retrospective", "tổng kết bài học", "không hiệu quả", "bỏ mục tiêu", "không dùng pomodoro"
        ]):
            intent = "retrospective"
            emotion = "neutral"
            energy = "low" if any(w in user_lower for w in ["thất bại", "bỏ cuộc", "đuối", "trễ hạn", "hủy"]) else "high"
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
            "username": username,
        }


def goal_manager_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Multi-Goal Management & Feasibility Analyzer (Phase 6.2 & Phase 9).
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

    user_profile = state.get("user_profile") or {}

    target_goal_input = state.get("target_goal")
    if not target_goal_input and state.get("pending_goal"):
        target_goal_input = (state.get("pending_goal") or {}).get("title")

    affirmative_words = ["đồng ý", "dong y", "ok", "okay", "yes", "có", "xác nhận", "tiến hành đi", "làm đi"]
    if not target_goal_input or target_goal_input.strip().lower() in affirmative_words:
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

    estimate_result = analyze_and_estimate_goal(target_goal_input, user_profile, username=username)
    milestones_data = [m.model_dump() for m in estimate_result.milestones]

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

    score = estimate_result.feasibility_score
    score_badge = "🟢 CAO" if score >= 80 else ("🟡 TRUNG BÌNH" if score >= 60 else "🔴 THÁCH THỨC")

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


def onboarding_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 0: Executive Onboarding & Multi-Aspect Calibration.
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

    user_lower = last_user_message.lower().strip()
    is_initial_greeting = not user_lower or user_lower in [
        "hi", "hello", "xin chào", "chào", "chào bạn", "bắt đầu", "start", "alo", "hey", "test"
    ]

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
            "username": username,
        }

    extraction_prompt = f"""Bạn là Giám đốc Huấn luyện Điều hành (Chief Coaching Officer) của người dùng.
Người dùng vừa cung cấp thông tin trong buổi phỏng vấn Onboarding:
"{last_user_message}"

Nhiệm vụ:
1. Đánh giá xem thông tin có đủ cơ sở để thiết lập hồ sơ cơ bản không (is_sufficient = True nếu có nêu mục tiêu hoặc định hướng; False nếu quá sơ sài).
2. Trích xuất:
   - current_situation: Tình trạng nền tảng hiện tại (kinh nghiệm, công việc, kỹ năng).
   - financial_status: Hiện trạng hoặc mục tiêu dòng tiền, ngân sách.
   - time_constraints: Ràng buộc thời gian & nhịp sinh học (khung giờ vàng làm việc sâu).
3. Trích xuất danh sách các mục tiêu (goals) để lưu vào 4 nhóm chuẩn: 'career', 'health', 'relationships', 'beauty'.
4. Viết lời phản hồi huấn luyện (coach_feedback): Phản hồi ngắn gọn, tự nhiên (2-3 câu), trực diện vào câu nói hiện tại của người dùng.
"""

    try:
        llm = get_llm(temperature=0.2)
        structured_llm = llm.with_structured_output(OnboardingExtractionResult)
        result: OnboardingExtractionResult = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT + "\n\n" + ACHIEVEMENT_LEDGER),
            HumanMessage(content=extraction_prompt),
        ])

        if result.is_sufficient:
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
        "username": username,
    }


def profiler_node(state: CoachState) -> Dict[str, Any]:
    """
    Node 1: Multi-Goal Profiler Agent (Khai thác & Chốt hồ sơ ĐA MỤC TIÊU song song).
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    
    current_goals = safe_list(state.get("goals") or load_user_goals(username))
    if not current_goals:
        single_p = safe_dict(state.get("profile") or load_user_goal_profile(username))
        if single_p.get("goal_name"):
            copy_p = dict(single_p)
            if "goal_id" not in copy_p: copy_p["goal_id"] = "g1"
            if "category" not in copy_p: copy_p["category"] = "Học tập"
            if "priority" not in copy_p: copy_p["priority"] = "high"
            current_goals = [copy_p]

    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human":
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    user_lower = (last_user_message or "").strip().lower()

    if not current_goals and (not user_lower or user_lower in ["hi", "hello", "xin chào", "chào", "start", "bắt đầu", "alo", "hey", "test"]):
        welcome_prompt = (
            "Chào bạn! Tôi là Elite Executive & Life Coach của bạn. "
            "Hiện tại bạn đang muốn đồng thời chinh phục các mục tiêu trọng tâm nào nhất "
            "(ví dụ: vừa học IELTS 7.0, vừa học HSK, vừa build dự án AI, hay rèn luyện sức khỏe)?"
        )
        return {
            "messages": [AIMessage(content=welcome_prompt)],
            "goals": [],
            "profile": {},
            "is_complete": False,
            "username": username,
        }

    history_lines = []
    for m in messages:
        m_type = getattr(m, 'type', '') or ('user' if isinstance(m, HumanMessage) else 'coach')
        m_content = getattr(m, 'content', str(m))
        history_lines.append(f"- {m_type}: {m_content}")
    history_str = "\n".join(history_lines) if history_lines else f"- user: {last_user_message}"

    extraction_prompt = f"""Bạn là Hệ thống Khai thác & Chốt hồ sơ ĐA MỤC TIÊU (Multi-Goal Profiler Agent).
Dưới đây là danh sách các mục tiêu hiện tại đã ghi nhận được từ các lượt trước (nếu có):
{json.dumps(current_goals, ensure_ascii=False, indent=2)}

Tin nhắn mới nhất từ người dùng:
"{last_user_message}"

Toàn bộ lịch sử trao đổi từ đầu phiên:
{history_str}

NHIỆM VỤ:
1. Trích xuất và CỘNG DỒN TẤT CẢ các mục tiêu mà người dùng muốn thực hiện song song (Học tập, Sự nghiệp, Sức khỏe, Tài chính, Dự án...):
   - Nếu người dùng nhắc mục tiêu mới: tạo mục tiêu mới với goal_id riêng (VD: 'g_ielts', 'g_hsk', 'g_ai').
   - Nếu người dùng bổ sung thông tin cho mục tiêu đã có: cập nhật vào mục tiêu tương ứng, giữ nguyên goal_id, không làm mất dữ liệu lượt trước.
2. Với TỪNG mục tiêu, trích xuất:
   - goal_id, category, goal_name, current_level, duration_days, daily_hours, preferred_slots, priority.
3. Đánh giá is_complete cho TỪNG mục tiêu:
   - CHỈ CẦN THU THẬP ĐỦ 4 THÔNG SỐ CỐT LÕI (goal_name, current_level, duration_days, daily_hours) LÀ ĐẶT is_complete = True CHO MỤC TIÊU ĐÓ.
4. Sinh missing_info_question:
   - Nếu TẤT CẢ các mục tiêu đều đã đủ 4 thông số cốt lõi: để None hoặc chuỗi rỗng.
   - Nếu còn ít nhất 1 mục tiêu chưa hoàn thiện: Viết đúng 1 câu hỏi Socratic ngắn gọn, tự nhiên, nhắm thẳng vào các thông số còn thiếu.
"""

    try:
        extracted: MultiGoalExtraction = invoke_llm_resilient(
            preferred_model="gemini-2.5-flash",
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=extraction_prompt),
            ],
            structured_schema=MultiGoalExtraction,
            temperature=0.1,
        )

        extracted_goals_dict = [g.model_dump() for g in extracted.goals] if extracted.goals else []
        merged_goals = []

        def find_existing(name, gid):
            name_norm = (name or "").lower().strip()
            for eg in current_goals:
                eg_id = eg.get("goal_id", "")
                eg_name = eg.get("goal_name", "").lower().strip()
                if (gid and gid == eg_id) or (name_norm and (name_norm in eg_name or eg_name in name_norm)):
                    return eg
            return None

        seen_ids = set()
        for g in extracted_goals_dict:
            g_name = g.get("goal_name")
            if not g_name or not str(g_name).strip():
                continue
            eg = find_existing(g_name, g.get("goal_id"))
            g_id = g.get("goal_id") or (eg.get("goal_id") if eg else None) or f"g_{uuid.uuid4().hex[:6]}"
            category = g.get("category") or (eg.get("category") if eg else "Học tập")
            level = g.get("current_level") or (eg.get("current_level") if eg else None)
            duration = g.get("duration_days") or (eg.get("duration_days") if eg else None)
            hours = g.get("daily_hours") or (eg.get("daily_hours") if eg else None)
            slots = g.get("preferred_slots") or (eg.get("preferred_slots") if eg else None)
            if not slots or not str(slots).strip():
                slots = "Tối ưu theo nhịp sinh học (08:00 - 10:00 sáng & tối linh hoạt)"
            priority = g.get("priority") or (eg.get("priority") if eg else "medium")

            has_4_core = bool(g_name and level and duration and hours)

            goal_item = {
                "goal_id": g_id,
                "category": category,
                "goal_name": g_name,
                "current_level": level,
                "duration_days": int(duration) if duration else None,
                "daily_hours": float(hours) if hours else None,
                "preferred_slots": slots,
                "priority": priority,
                "is_complete": has_4_core,
            }
            seen_ids.add(g_id)
            merged_goals.append(goal_item)

        for eg in current_goals:
            eg_id = eg.get("goal_id")
            if eg_id not in seen_ids and eg.get("goal_name"):
                merged_goals.append(eg)
                seen_ids.add(eg_id)

        if not merged_goals and current_goals:
            merged_goals = current_goals

        save_user_goals(merged_goals, username=username)

        all_complete = bool(merged_goals and all(g.get("is_complete") for g in merged_goals))

        if not all_complete:
            incomplete_goals = [g for g in merged_goals if not g.get("is_complete")]
            q = extracted.missing_info_question
            if not q or not q.strip() or "khung giờ" in q.lower() or "thời gian trong ngày" in q.lower():
                missing_prompts = []
                for g in incomplete_goals:
                    m_items = []
                    if not g.get("current_level"): m_items.append("trình độ hiện tại")
                    if not g.get("duration_days"): m_items.append("thời gian hoàn thành")
                    if not g.get("daily_hours"): m_items.append("quỹ thời gian rảnh mỗi ngày")
                    missing_prompts.append(f"mục tiêu '{g.get('goal_name')}' ({', '.join(m_items)})")
                q = f"Để thiết kế lộ trình phân bổ thời gian tối ưu, bạn có thể chia sẻ thêm về: {'; '.join(missing_prompts)} không?"

            return {
                "goals": merged_goals,
                "profile": merged_goals[0] if merged_goals else {},
                "is_complete": False,
                "messages": [AIMessage(content=q.strip())],
                "username": username,
            }

        return {
            "goals": merged_goals,
            "profile": merged_goals[0] if merged_goals else {},
            "is_complete": True,
            "username": username,
        }

    except Exception as e:
        print(f"Lỗi trong profiler_node: {e}")
        return {
            "goals": current_goals,
            "profile": current_goals[0] if current_goals else {},
            "is_complete": False,
            "messages": [AIMessage(content="Tôi đã lắng nghe chia sẻ của bạn. Để thiết kế lộ trình cân bằng cho các mục tiêu, bạn có thể cho tôi biết rõ hơn về trình độ hiện tại, thời gian dự kiến và số giờ bạn có thể dành ra mỗi ngày không?")],
            "username": username,
        }
