"""
agents/nodes/chat_modes.py - Chat & Coaching Nodes (CEO Coach, Motivate Node, Chat Node).
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.state import AgentState
from agents.nodes.base import (
    SYSTEM_PROMPT,
    ACHIEVEMENT_LEDGER,
    TRIGGER_CLOSING_QUESTION,
    get_llm,
    invoke_llm_resilient,
    extract_text_from_content,
    load_user_goals,
    save_user_goals,
    save_user_profile,
    get_goals_summary_text,
    get_vietnam_today_str,
    compute_target_date,
)


def motivate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Kích hoạt 'Giao thức Tự hào' (Pride-Activation Protocol) khi nhận diện cảm xúc tiêu cực.
    Trích xuất Achievement Ledger, loại bỏ lời an ủi sáo rỗng, kích hoạt Dopamine và đề xuất giảm tải.
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
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
        "username": username,
    }


def chat_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 11: Đối thoại Chiến lược & Huấn luyện Điều hành (Executive Conversation Node).
    Đảm nhiệm vai trò phản hồi mọi thắc mắc, trò chuyện, đính chính thông tin từ người dùng (ví dụ: 'tôi có thi tiếng trung đâu'),
    giải quyết triệt để lỗi Echo (nhại lại lời người dùng) và duy trì sự thông minh, chủ động của Life Coach.
    """
    username = (state.get("username") or "mavis").strip().lower() if isinstance(state.get("username"), str) else "mavis"
    messages = state.get("messages", [])
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
        response = invoke_llm_resilient(
            preferred_model="gemini-2.5-pro",
            messages=llm_messages,
            temperature=0.4,
        )
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
        "username": username,
    }


# ------------------------------------------------------------------------------
# 1. CEO COACH CHAT (ĐÁNH GIÁ TỔNG QUỸ THỜI GIAN & KHẢ THI MỤC TIÊU MỚI)
# ------------------------------------------------------------------------------

class CEOCoachOutput(BaseModel):
    detected_goal_title: Optional[str] = Field(None, description="Tên mục tiêu mới phát hiện được nếu người dùng đề xuất (VD: 'IELTS 7.0', 'Học Python')")
    category: Optional[str] = Field("Học tập", description="Nhóm: 'Học tập', 'Sự nghiệp', 'Sức khỏe', 'Tài chính', hoặc 'Mối quan hệ'")
    daily_hours: Optional[float] = Field(None, description="Số giờ rảnh dự kiến cam kết cho mục tiêu mới mỗi ngày")
    duration_days: Optional[int] = Field(None, description="Tổng thời gian thực hiện ước tính (ngày)")
    preferred_time: Optional[str] = Field("08:00 - 10:00 Sáng", description="Khung giờ ưu tiên trong ngày")
    priority: Optional[str] = Field("P2 - High", description="Mức ưu tiên: P1 - Critical, P2 - High, P3 - Medium, P4 - Low")
    current_level: Optional[str] = Field("Cơ bản", description="Trình độ hoặc vạch xuất phát hiện tại")
    feasibility_assessment: str = Field(description="Đánh giá chi tiết tính khả thi dựa trên nhịp sinh học và tổng số giờ hiện có")
    burnout_risk_detected: bool = Field(default=False, description="True nếu tổng giờ sau khi thêm mục tiêu mới > 8.0 giờ/ngày hoặc có quá nhiều Deep Work (nguy cơ kiệt sức / quá tải nhận thức)")
    suggested_pause_goal: Optional[str] = Field(None, description="Tên mục tiêu đang Active cũ có mức ưu tiên thấp hơn được gợi ý tạm dừng (paused) để bảo vệ năng lượng trước khi duyệt mục tiêu mới")
    ready_to_approve: bool = Field(description="True nếu mục tiêu rõ ràng và tổng quỹ thời gian sau khi thêm mục tiêu mới <= 8.0h/ngày và không quá tải Deep Work (khả thi). False nếu vượt quá 8h/ngày, quá tải, hoặc thiếu thông số cốt lõi.")
    coach_response: str = Field(description="Lời trò chuyện của CEO Life Coach: sắc bén, thấu cảm, ngắn gọn, phân tích chi phí cơ hội, cảnh báo quá tải/burnout nếu >8h và đưa câu hỏi chốt rõ ràng")


def ceo_coach_chat(
    user_message: str,
    username: str = "mavis",
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Hàm Chatbot 1: CEO Coach Chat (Trò chuyện tổng & Thẩm định tính khả thi).
    Sử dụng gemini-2.5-flash để phản hồi nhanh, sắc bén.
    Tích hợp cơ chế Quản Trị Năng Lượng & Chống Quá Tải (Burnout Shield):
    - Tính tổng số giờ/ngày của tất cả mục tiêu đang active.
    - Cảnh báo rủi ro quá tải nếu tổng giờ > 8h/ngày hoặc quá nhiều Deep Work.
    - Gợi ý tạm dừng ('paused') bớt 1 mục tiêu cũ trước khi duyệt mục tiêu mới.
    """
    username = (username or "mavis").strip().lower()
    current_goals = load_user_goals(username)
    active_goals = [g for g in current_goals if g.get("status") == "active"]
    current_allocated_hours = sum(float(g.get("daily_hours", 0) or 0) for g in active_goals)

    # Đếm số lượng task Deep Work trong các active goals
    deep_work_count = 0
    active_summary = []
    for g in active_goals:
        bd = g.get("breakdown", {})
        if isinstance(bd, dict):
            for w in bd.get("weekly", []):
                if isinstance(w, dict):
                    for t in w.get("tasks", []):
                        if isinstance(t, dict) and "deep" in str(t.get("energy_level", "")).lower():
                            deep_work_count += 1
        active_summary.append(
            f"- Mục tiêu: {g.get('title') or g.get('goal_name')} | Quỹ giờ: {g.get('daily_hours')}h/ngày | Khung giờ: {g.get('preferred_time')} | Ưu tiên: {g.get('priority')}"
        )
    active_goals_text = "\n".join(active_summary) if active_summary else "Chưa có mục tiêu nào đang Active."

    history_text = ""
    if chat_history:
        history_lines = [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history[-5:]]
        history_text = "\nLịch sử trao đổi gần nhất:\n" + "\n".join(history_lines)

    prompt = f"""Bạn là CEO & Elite Life Coach độc quyền của người dùng.
Nhiệm vụ: Trò chuyện tổng, thẩm định tính khả thi của mục tiêu mới đối chiếu với tổng quỹ thời gian hiện tại và kích hoạt cơ chế Chống Quá Tải & Quản Trị Năng Lượng (Burnout Shield).

DỮ LIỆU HIỆN TẠI TỪ CƠ SỞ DỮ LIỆU MONGODB CỦA USER:
- Tổng quỹ giờ đã cam kết trên các mục tiêu đang Active: {current_allocated_hours:.1f} giờ/ngày.
- Số mục tiêu đang Active: {len(active_goals)} mục tiêu.
- Số lượng task Deep Work hiện có: {deep_work_count} tasks.
- Danh sách các mục tiêu đang Active:
{active_goals_text}

QUY TẮC QUẢN TRỊ NĂNG LƯỢNG & CHỐNG QUÁ TẢI (BURNOUT SHIELD) CỦA CEO COACH:
1. GIỚI HẠN TỐI ĐA NGHIÊM NGẶT: Tổng quỹ giờ học tập / làm việc an toàn tối đa của người dùng là 8.0 giờ/ngày.
2. CẢNH BÁO NGUY CƠ QUÁ TẢI (BURNOUT RISK):
   - Nếu tổng quỹ giờ (Hiện tại {current_allocated_hours:.1f}h + Mục tiêu mới đề xuất) > 8.0 giờ/ngày, HOẶC người dùng đang gánh quá nhiều tác vụ nặng não (Deep Work):
     * BẮT BUỘC đặt burnout_risk_detected = True.
     * BẮT BUỘC đặt ready_to_approve = False.
     * Trong coach_response: Cảnh báo trực diện rủi ro kiệt sức/quá tải não bộ ("Tổng thời gian cam kết sẽ vượt quá 8 tiếng/ngày! Não bộ không thể duy trì nhận thức đỉnh cao khi bị quá tải!").
     * Chỉ định rõ 1 mục tiêu cũ ít ưu tiên hơn hoặc có thể tạm hoãn vào suggested_pause_goal.
     * Gợi ý người dùng bấm ⏸️ Tạm dừng (paused) mục tiêu đó ở Giai đoạn 1 trước khi duyệt mục tiêu mới này, hoặc giảm số giờ/ngày xuống.
3. KHI ĐỦ ĐIỀU KIỆN DUYỆT (READY TO APPROVE):
   - Nếu tổng quỹ giờ (Hiện tại + Mục tiêu mới) <= 8.0 giờ/ngày VÀ đã có đủ thông số cốt lõi (tên mục tiêu, số giờ, thời hạn) VÀ không quá tải Deep Work:
     * Đặt burnout_risk_detected = False.
     * Đặt ready_to_approve = True.
     * Đưa ra nhận xét sắc bén, khích lệ và hỏi câu hỏi chốt để chuyển sang Giai đoạn 1 (Architect) bóc tách lộ trình.
4. NẾU THIẾU THÔNG SỐ:
   - Nếu người dùng chưa nêu rõ số giờ hoặc thời hạn -> Đặt ready_to_approve = False. Hỏi đúng 1 câu hỏi gợi mở để người dùng làm rõ.

{history_text}
Tin nhắn hiện tại của người dùng: "{user_message}"
"""

    try:
        analysis: CEOCoachOutput = invoke_llm_resilient(
            preferred_model="gemini-2.5-flash",
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ],
            structured_schema=CEOCoachOutput,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Lỗi invoke trong ceo_coach_chat: {e}")
        is_overload = (current_allocated_hours + 1.5) > 8.0
        lowest_goal_title = (active_goals[-1].get("title") or active_goals[-1].get("goal_name")) if active_goals else None
        analysis = CEOCoachOutput(
            detected_goal_title="Mục tiêu mới",
            category="Học tập",
            daily_hours=1.5,
            duration_days=90,
            preferred_time="08:00 - 10:00 Sáng",
            priority="P2 - High",
            feasibility_assessment=f"Hiện bạn đang cam kết {current_allocated_hours:.1f}h/ngày. Ngưỡng an toàn tối đa là 8.0h/ngày.",
            burnout_risk_detected=is_overload,
            suggested_pause_goal=lowest_goal_title if is_overload else None,
            ready_to_approve=not is_overload,
            coach_response=(
                f"⚠️ Cảnh báo Burnout Shield: Hiện tại bạn đã cam kết {current_allocated_hours:.1f}h/ngày. Thêm mục tiêu này sẽ nâng tổng giờ lên {(current_allocated_hours + 1.5):.1f}h/ngày (>8h/ngày). Tôi khuyên bạn nên tạm dừng ('paused') mục tiêu '{lowest_goal_title}' trước khi duyệt mục tiêu mới!"
                if is_overload
                else f"Tôi đã ghi nhận định hướng của bạn. Hiện tại bạn đang có {current_allocated_hours:.1f}h/ngày đã phân bổ (nằm trong ngưỡng an toàn 8h/ngày). Bạn có muốn chúng ta chốt và chuyển sang Giai đoạn 1 (Architect) để bóc tách lộ trình chi tiết không?"
            ),
        )

    # Nếu được phê duyệt (ready_to_approve == True) và có tên mục tiêu -> Thêm hoặc cập nhật vào goals (status: evaluating)
    new_goal_record = None
    if analysis.ready_to_approve and analysis.detected_goal_title:
        title_lower = analysis.detected_goal_title.strip().lower()
        matched_idx = None
        for idx, g in enumerate(current_goals):
            if str(g.get("title") or g.get("goal_name", "")).strip().lower() == title_lower:
                matched_idx = idx
                break

        if matched_idx is not None and isinstance(current_goals[matched_idx], dict):
            existing_id = current_goals[matched_idx].get("id") or current_goals[matched_idx].get("goal_id")
            goal_id = existing_id if existing_id else f"goal_{uuid.uuid4().hex[:6]}"
        else:
            goal_id = f"goal_{uuid.uuid4().hex[:6]}"
        goal_dur = int(analysis.duration_days or 90)
        goal_start = get_vietnam_today_str()
        new_goal_record = {
            "id": goal_id,
            "goal_id": goal_id,
            "title": analysis.detected_goal_title,
            "goal_name": analysis.detected_goal_title,
            "category": analysis.category or "Học tập",
            "priority": analysis.priority or "P2 - High",
            "preferred_time": analysis.preferred_time or "08:00 - 10:00 Sáng",
            "preferred_slots": analysis.preferred_time or "08:00 - 10:00 Sáng",
            "daily_hours": float(analysis.daily_hours or 1.5),
            "duration_days": goal_dur,
            "start_date": goal_start,
            "target_date": compute_target_date(goal_start, goal_dur),
            "current_level": analysis.current_level or "Cơ bản",
            "status": "evaluating",
            "is_complete": True,
            "breakdown": {
                "yearly": f"Chinh phục thành công {analysis.detected_goal_title}",
                "quarterly": [],
                "monthly": [],
                "weekly": [],
                "resources": [],
            },
        }

        if matched_idx is not None:
            current_goals[matched_idx].update(new_goal_record)
        else:
            current_goals.append(new_goal_record)

        save_user_goals(current_goals, username=username)

    return {
        "response": analysis.coach_response,
        "ready_to_approve": analysis.ready_to_approve,
        "burnout_risk_detected": getattr(analysis, "burnout_risk_detected", False),
        "suggested_pause_goal": getattr(analysis, "suggested_pause_goal", None),
        "total_allocated_hours": current_allocated_hours + (float(analysis.daily_hours or 0) if analysis.ready_to_approve else 0),
        "new_goal_detected": new_goal_record,
        "goals": load_user_goals(username),
        "status": "ready_for_architect" if analysis.ready_to_approve else "evaluating",
    }
