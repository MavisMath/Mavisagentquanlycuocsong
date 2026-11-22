"""
agents/nodes/retrospective.py - Phase 10 & Stage 3 Retrospective Analysis & Adaptive Memory.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.state import AgentState
from agents.nodes.base import (
    SYSTEM_PROMPT,
    ACHIEVEMENT_LEDGER,
    RetrospectiveAnalysisResult,
    get_llm,
    invoke_llm_resilient,
    load_master_schedule,
    load_user_goals,
    save_user_goals,
    load_retrospective_logs,
    append_retrospective_log,
    load_historical_insights,
    save_historical_insights,
    append_insight,
    load_tree_goals,
    save_tree_goals,
    get_historical_insights_summary_text,
)


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
    if not last_user_message and messages:
        last_user_message = str(messages[-1].content if hasattr(messages[-1], "content") else messages[-1])

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
        "username": username,
    }


# ------------------------------------------------------------------------------
# 4. RETROSPECTIVE CHAT (GIAI ĐOẠN 3: HỒI CỨU, CHECK-IN CẢM XÚC & KHÉP KÍN VÒNG LẶP)
# ------------------------------------------------------------------------------

class UncompletedTaskReason(BaseModel):
    task_detail: str = Field(description="Nhiệm vụ chưa hoàn thành")
    goal_title: str = Field(default="", description="Thuộc mục tiêu nào")
    reason: str = Field(description="Nguyên nhân chính: 'quá khó', 'quá tải', 'bận việc đột xuất', 'thiếu tập trung', 'mệt mỏi'")
    specific_bottleneck: str = Field(description="Điểm nghẽn cụ thể")


class HistoricalPatternAnalysis(BaseModel):
    frequent_missed_slots: List[str] = Field(
        default=[],
        description="Các khung giờ hoặc buổi thường xuyên bị trễ/bỏ lỡ nhất trong 7 ngày qua (VD: '19:30 - 21:30 Tối')"
    )
    overwhelming_resource_types: List[str] = Field(
        default=[],
        description="Các dạng tài liệu hoặc task gây ngợp/quá tải (VD: 'Tài liệu hàn lâm tiếng Anh > 50 trang', 'Video lý thuyết dài > 2h')"
    )
    key_observations: str = Field(
        default="",
        description="Nhận định quy luật sinh học và nhịp độ năng lượng của người dùng đúc kết từ lịch sử 7 ngày"
    )


class ProposedBreakdownAdjustment(BaseModel):
    target_goal_id: Optional[str] = Field(None, description="ID mục tiêu cần điều chỉnh lại trong goals.breakdown")
    target_goal_title: Optional[str] = Field(None, description="Tên mục tiêu cần điều chỉnh")
    adjustment_type: str = Field(description="'reduce_daily_hours', 'reschedule_time_slot', 'simplify_resources', 'extend_duration', hoặc 'keep_as_is'")
    recommended_daily_hours: Optional[float] = Field(None, description="Số giờ mới đề xuất nếu bị quá tải")
    recommended_preferred_time: Optional[str] = Field(None, description="Khung giờ mới đề xuất nếu khung giờ cũ hay bị bỏ lỡ (VD: '08:00 - 10:00 Sáng' hoặc '17:30 - 18:30 Chiều')")
    recommended_sleep_time: Optional[str] = Field(None, description="Giờ đi ngủ mới đề xuất nếu thức khuya/mệt mỏi (VD: '22:15')")
    recommended_resource_additions: List[Dict[str, str]] = Field(default=[], description="Tài liệu bổ trợ dễ hơn nếu task quá khó")
    updated_strategy_summary: Optional[str] = Field(None, description="Phương pháp chiến lược mới đề xuất cập nhật vào Giai đoạn 1")
    adjustment_explanation: str = Field(description="Lý do điều chỉnh chiến lược")


class RetrospectiveChatOutput(BaseModel):
    detected_emotion: str = Field(description="'motivated', 'overwhelmed', 'tired', 'neutral', 'satisfied', hoặc 'discouraged'")
    completion_rate: float = Field(description="Tỷ lệ hoàn thành ước tính (0.0 đến 100.0%)")
    pattern_analysis: HistoricalPatternAnalysis = Field(description="Phân tích nhận diện quy luật lịch sử 7 ngày gần nhất")
    uncompleted_tasks_analysis: List[UncompletedTaskReason] = Field(description="Phân tích chi tiết từng task chưa hoàn thành và lý do")
    coaching_reflection: str = Field(description="Lời trò chuyện khai vấn (Socratic reflection) thấu cảm, khích lệ tinh thần và định hướng phục hồi")
    proposed_adjustment: ProposedBreakdownAdjustment = Field(description="Đề xuất điều chỉnh ngược lại goals.breakdown")
    should_apply_adjustment: bool = Field(description="True nếu cần tự động cập nhật ngay đề xuất vào goals.breakdown")


def retrospective_chat(
    user_message: str,
    username: str = "mavis",
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Hàm Chatbot 4: Retrospective Chat (Chuyên trách Giai đoạn 3).
    Sử dụng gemini-2.5-flash để khai vấn thấu cảm và phân tích quy luật lịch sử 7 ngày gần nhất.
    Phân tích các task chưa 'is_done' từ master_schedule, tự động nhận diện quy luật (khung giờ hay bỏ lỡ,
    tài liệu gây ngợp), lưu check-in log vào retrospective_logs và sinh đề xuất điều chỉnh ngược lại goals.breakdown.
    """
    username = (username or "mavis").strip().lower()
    master_schedule = load_master_schedule(username)
    goals = load_user_goals(username)
    recent_logs = load_retrospective_logs(username)[-7:]

    done_tasks = [t for t in master_schedule if t.get("is_done") is True]
    uncompleted_tasks = [t for t in master_schedule if t.get("is_done") is False]
    total_count = len(master_schedule) if master_schedule else 1
    actual_rate = (len(done_tasks) / total_count) * 100.0

    # 1. Thống kê quy luật khung giờ hay bị bỏ lỡ
    slot_stats = {}
    overwhelming_candidates = set()
    for t in master_schedule:
        slot = t.get("time_slot") or t.get("session") or "Khung giờ khác"
        if slot not in slot_stats:
            slot_stats[slot] = {"total": 0, "missed": 0}
        slot_stats[slot]["total"] += 1
        if t.get("is_done") is False:
            slot_stats[slot]["missed"] += 1
            r_title = t.get("resource_title") or ""
            r_url = t.get("resource_url") or ""
            if "youtube.com" in r_url or "sách" in r_title.lower() or "giáo trình" in r_title.lower() or "coursera" in r_url.lower():
                overwhelming_candidates.add(r_title or "Tài liệu lý thuyết dài")

    missed_slot_summaries = [
        f"{s}: trượt {d['missed']}/{d['total']} task (tỷ lệ trễ {(d['missed']/d['total'])*100:.0f}%)"
        for s, d in slot_stats.items()
        if d["missed"] > 0
    ]

    uncompleted_sample = [
        {"task_detail": t.get("task_detail"), "goal_title": t.get("goal_title"), "date": t.get("date"), "slot": t.get("time_slot")}
        for t in uncompleted_tasks[:6]
    ]

    retro_prompt = f"""Bạn là Chuyên Gia Khai Vấn Hồi Cứu & Bảo Vệ Năng Lượng (AI Retrospective Coach) của hệ thống Mavis.
Nhiệm vụ: Chuyên trách GIAI ĐOẠN 3 — Đánh giá các task chưa hoàn thành, phân tích quy luật 7 ngày gần nhất (khung giờ hay bỏ lỡ, tài liệu gây ngợp), thấu cảm cảm xúc và sinh đề xuất điều chỉnh ngược lại goals.breakdown để khép kín vòng lặp điều phối.

DỮ LIỆU HIỆN TẠI TỪ MASTER SCHEDULE CỦA USER:
- Tổng số task trong lịch: {len(master_schedule)}
- Số task đã hoàn thành (is_done=True): {len(done_tasks)}
- Số task chưa hoàn thành (is_done=False): {len(uncompleted_tasks)}
- Tỷ lệ hoàn thành thực tế: {actual_rate:.1f}%

THỐNG KÊ QUY LUẬT KHUNG GIỜ BỎ LỠ 7 NGÀY QUA:
{json.dumps(missed_slot_summaries, ensure_ascii=False, indent=2) if missed_slot_summaries else "Chưa có quy luật trễ khung giờ rõ rệt."}

DẤU HIỆU TÀI LIỆU CÓ THỂ GÂY NGỢP:
{json.dumps(list(overwhelming_candidates), ensure_ascii=False, indent=2) if overwhelming_candidates else "Không phát hiện tài liệu gây ngợp rõ rệt."}

DANH SÁCH TASK CHƯA HOÀN THÀNH GẦN ĐÂY:
{json.dumps(uncompleted_sample, ensure_ascii=False, indent=2)}

LỊCH SỬ CHECK-IN 7 NGÀY GẦN NHẤT:
{json.dumps([{'date': l.get('date'), 'emotion': l.get('emotion'), 'rate': l.get('completion_rate'), 'adjustments': l.get('recommended_adjustments')} for l in recent_logs], ensure_ascii=False, indent=2)}

DANH SÁCH MỤC TIÊU HIỆN CÓ:
{json.dumps([{'id': g.get('id'), 'title': g.get('title') or g.get('goal_name'), 'preferred_time': g.get('preferred_time'), 'daily_hours': g.get('daily_hours')} for g in goals], ensure_ascii=False, indent=2)}

CHIA SẺ / PHẢN HỒI CỦA NGƯỜI DÙNG:
"{user_message}"

CHỈ THỊ KHAI VẤN (RETROSPECTIVE PROTOCOL):
1. Phân tích quy luật 7 ngày (pattern_analysis):
   - Chỉ rõ các khung giờ người dùng thường xuyên bị bỏ lỡ nhất (frequent_missed_slots).
   - Chỉ rõ loại tài liệu khiến người dùng bị ngợp hoặc bỏ cuộc (overwhelming_resource_types).
   - Nhận định đúc kết (key_observations): Thấu hiểu nhịp sinh học và nguyên nhân gốc rễ.
2. Thấu cảm tuyệt đối: Không phán xét. Đặt câu hỏi mở (Socratic) và công nhận nỗ lực.
3. Sinh đề xuất điều chỉnh cụ thể (proposed_adjustment):
   - Nếu khung giờ sáng sớm hay bị bỏ lỡ (do thức khuya/dậy muộn): đề xuất đổi giờ đi ngủ sang sớm hơn (VD: '22:15') hoặc dời preferred_time sang khung giờ chiều muộn (VD: '17:30 - 18:30 Chiều').
   - Nếu khung giờ tối hay bị bỏ lỡ (do cạn kiệt năng lượng sau cả ngày): đề xuất dời preferred_time sang sáng 08:30 - 10:00 hoặc chiều 14:00.
   - Nếu quá tải thời gian: đề xuất giảm daily_hours (VD: từ 2h xuống 1.5h hoặc 1h).
   - Nếu bài tập/tài liệu quá khó/dài gây nản lòng: đề xuất tài liệu bổ trợ ngắn gọn, video thực hành dễ tiếp thu hơn.
   - BẮT BUỘC cung cấp updated_strategy_summary: 1-2 câu phương pháp chiến lược mới đã điều chỉnh để cập nhật thẳng vào Giai đoạn 1.
   - Ghi rõ target_goal_id, target_goal_title, recommended_preferred_time, recommended_daily_hours, recommended_sleep_time.
   - Đặt should_apply_adjustment = True nếu xác định được mục tiêu cần điều chỉnh.
"""

    try:
        output: RetrospectiveChatOutput = invoke_llm_resilient(
            preferred_model="gemini-2.5-flash",
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=retro_prompt),
            ],
            structured_schema=RetrospectiveChatOutput,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Lỗi invoke trong retrospective_chat: {e}")
        target_g = goals[0] if goals else {}
        g_title = target_g.get("title") or target_g.get("goal_name", "Mục tiêu")
        output = RetrospectiveChatOutput(
            detected_emotion="tired",
            completion_rate=actual_rate,
            pattern_analysis=HistoricalPatternAnalysis(
                frequent_missed_slots=missed_slot_summaries[:2] or ["06:30 - 07:30 (Sáng)", "20:00 - 21:15 (Tối)"],
                overwhelming_resource_types=["Khối lượng bài tập lý thuyết dồn ứ cuối ngày"],
                key_observations="Khung giờ sáng sớm và tối muộn hay bị trượt do năng lượng suy giảm và thói quen thức khuya.",
            ),
            uncompleted_tasks_analysis=[
                UncompletedTaskReason(
                    task_detail="Bài tập sáng sớm / Tối muộn",
                    goal_title=g_title,
                    reason="mệt mỏi do thức khuya hoặc quá tải năng lượng",
                    specific_bottleneck="Thiếu ngủ khiến sáng dậy muộn và tối cạn kiệt năng lượng",
                )
            ],
            coaching_reflection="Chào bạn! Tôi nhận thấy bạn rất nỗ lực trong tuần qua, nhưng khung giờ sáng sớm hoặc tối muộn đang hay bị trượt lịch. Bạn có đang cảm thấy áp lực hoặc thức khuya làm ảnh hưởng đến nhịp sinh học không? Coach đề xuất chúng ta dời giờ tập/học sang khung giờ vàng buổi chiều (17:30) hoặc sáng 08:30 và ngủ sớm lúc 22:15 để bạn luôn tràn đầy năng lượng!",
            proposed_adjustment=ProposedBreakdownAdjustment(
                target_goal_id=target_g.get("id") if target_g else None,
                target_goal_title=g_title,
                adjustment_type="reschedule_time_slot",
                recommended_daily_hours=1.5,
                recommended_preferred_time="17:30 - 18:30 (Chiều)",
                recommended_sleep_time="22:15",
                updated_strategy_summary=f"Tái cấu trúc nhịp sinh học: chuyển giờ rèn luyện sang 17:30 Chiều, ngủ sớm lúc 22:15 và tối ưu 1.5h Deep Work.",
                adjustment_explanation="Chuyển khung giờ sang 17:30 chiều khi cơ thể có độ dẻo dai cao nhất, điều chỉnh giờ ngủ 22:15 để bảo vệ nhịp sinh học và giảm áp lực nhận thức.",
            ),
            should_apply_adjustment=True,
        )

    # 1. Lưu bản ghi check-in vào collection user_states (retrospective_logs)
    log_entry = {
        "log_id": f"retro_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "emotion": output.detected_emotion,
        "completion_rate": output.completion_rate,
        "completed_tasks": [t.get("task_detail") for t in done_tasks],
        "uncompleted_tasks": [u.model_dump() for u in output.uncompleted_tasks_analysis],
        "pattern_analysis": output.pattern_analysis.model_dump(),
        "reflection_notes": output.coaching_reflection,
        "recommended_adjustments": output.proposed_adjustment.adjustment_explanation,
        "proposed_adjustment": output.proposed_adjustment.model_dump(),
    }
    append_retrospective_log(log_entry, username=username)

    # 2. Khép kín vòng lặp: Cập nhật ngược lại goals nếu should_apply_adjustment == True
    if output.should_apply_adjustment and (output.proposed_adjustment.target_goal_id or output.proposed_adjustment.target_goal_title):
        tid = output.proposed_adjustment.target_goal_id
        t_title = (output.proposed_adjustment.target_goal_title or "").lower().strip()
        for g in goals:
            gid = g.get("id") or g.get("goal_id")
            g_title = (g.get("title") or g.get("goal_name") or "").lower().strip()
            if (tid and gid == tid) or (t_title and (t_title in g_title or g_title in t_title)):
                if output.proposed_adjustment.recommended_daily_hours:
                    g["daily_hours"] = float(output.proposed_adjustment.recommended_daily_hours)
                if output.proposed_adjustment.recommended_preferred_time:
                    g["preferred_time"] = output.proposed_adjustment.recommended_preferred_time
                if output.proposed_adjustment.updated_strategy_summary:
                    g["strategy_summary"] = output.proposed_adjustment.updated_strategy_summary
                if output.proposed_adjustment.recommended_resource_additions:
                    bd = g.setdefault("breakdown", {})
                    res_list = bd.setdefault("resources", [])
                    res_list.extend(output.proposed_adjustment.recommended_resource_additions)
                break
        save_user_goals(goals, username=username)

    return {
        "response": output.coaching_reflection,
        "completion_rate": output.completion_rate,
        "pattern_analysis": output.pattern_analysis.model_dump(),
        "retrospective_log": log_entry,
        "proposed_adjustments": output.proposed_adjustment.model_dump(),
        "updated_goals": load_user_goals(username),
    }
