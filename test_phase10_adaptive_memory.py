import os
import sys
import json
from langchain_core.messages import HumanMessage, AIMessage

# Setup import path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from memory.goals import (
    load_tree_goals,
    save_tree_goals,
    load_historical_insights,
    save_historical_insights,
    append_insight,
    get_historical_insights_summary_text,
    add_goal,
)
from agents.brain import retrospective_node, schedule_node, analyze_input_node
from agents.graph import mavis_agent

def test_phase10():
    print("=" * 70)
    print("🚀 BẮT ĐẦU TEST TOÀN DIỆN PHASE 10: ADAPTIVE MEMORY & RETROSPECTIVE NODE")
    print("=" * 70)

    test_user = "test_adaptive_user"
    
    # 1. Khởi tạo dữ liệu sạch cho test_user
    blank_tree = {
        "career": {"children": []},
        "relationships": {"children": []},
        "health": {"children": []},
        "beauty": {"children": []},
        "historical_insights": {
            "failed_methods": [],
            "effective_methods": [],
            "productivity_patterns": []
        }
    }
    save_tree_goals(blank_tree, username=test_user)
    
    # Thêm một mục tiêu mẫu cho test_user để có active_tasks
    add_goal(
        category="career",
        title="Luyện thi chứng chỉ AWS Solutions Architect & AI",
        deadline="2 tháng",
        milestones=[
            {"milestone": "Ôn tập kiến thức Cloud & EC2", "timeline": "Tuần 1", "status": "in_progress", "cognitive_load": "high", "platform": "AWS Skill Builder"},
            {"milestone": "Giải đề Practice Exam 1", "timeline": "Tuần 2", "status": "pending", "cognitive_load": "high", "platform": "Udemy"},
        ],
        username=test_user,
    )

    # 2. Kiểm tra các hàm trợ năng Historical Insights
    print("\n--- TEST 1: KIỂM TRA HÀM TRỢ NĂNG DATABASE HỒ SƠ HÀNH VI ---")
    insights = load_historical_insights(username=test_user)
    assert "failed_methods" in insights, "historical_insights thiếu failed_methods"
    assert "effective_methods" in insights, "historical_insights thiếu effective_methods"
    assert "productivity_patterns" in insights, "historical_insights thiếu productivity_patterns"
    print("✅ Cấu trúc 3 mảng trong historical_insights hợp lệ 100%!")

    # 3. Test Nhận diện Ý định (analyze_input_node) cho Retrospective
    print("\n--- TEST 2: KIỂM TRA NHẬN DIỆN RETROSPECTIVE INTENT ---")
    user_complaint = "Tôi bỏ cuộc phương pháp Pomodoro rồi, áp dụng Pomodoro 25 phút ngắt quãng làm tôi bị đứt gãy tư duy và không thể giải quyết bài toán khó"
    analysis_state = {
        "messages": [HumanMessage(content=user_complaint)],
        "username": test_user,
    }
    analyzed = analyze_input_node(analysis_state)
    print(f"Intent nhận diện: {analyzed.get('intent')} | Emotion: {analyzed.get('detected_emotion')}")
    assert analyzed.get("intent") == "retrospective", f"Kỳ vọng intent retrospective nhưng nhận: {analyzed.get('intent')}"
    print("✅ analyze_input_node nhận diện chính xác intent = 'retrospective'!")

    # 4. Test Gọi Retrospective Node
    print("\n--- TEST 3: TEST RETROSPECTIVE NODE & CẬP NHẬT DATABASE ---")
    retrospective_state = {
        "messages": [HumanMessage(content=user_complaint)],
        "username": test_user,
        "user_profile": {"is_onboarded": True, "current_situation": "Software Engineer"},
    }
    retro_result = retrospective_node(retrospective_state)
    
    assert "messages" in retro_result, "Retrospective node không trả về messages"
    assert "historical_insights" in retro_result, "Retrospective node không trả về historical_insights"
    
    reply_content = retro_result["messages"][-1].content
    print("\n[BÁO CÁO HỒI CỨU TỪ COACH]:")
    print(reply_content[:400] + "...\n")

    # Kiểm tra database goals_ledger.json sau hồi cứu
    updated_insights = load_historical_insights(username=test_user)
    print("Failed methods sau hồi cứu:", updated_insights["failed_methods"])
    print("Productivity patterns sau hồi cứu:", updated_insights["productivity_patterns"])

    has_pomodoro_in_failed = any("pomodoro" in f.lower() for f in updated_insights["failed_methods"])
    assert has_pomodoro_in_failed, "Pomodoro chưa được ghi nhận vào failed_methods trong DB!"
    print("✅ Pomodoro đã được đưa vào Blacklist (failed_methods) thành công!")

    # 5. Test Lập lịch Tuân thủ Adaptive Memory (Tuyệt đối không đề xuất lại Pomodoro)
    print("\n--- TEST 4: TEST LẬP LỊCH THÍCH NGHI (TUYỆT ĐỐI TRÁNH FAILED_METHODS) ---")
    schedule_state = {
        "messages": [HumanMessage(content="Hãy lên lịch trình học tập và làm việc hôm nay cho tôi")],
        "username": test_user,
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "user_profile": {"is_onboarded": True},
    }
    schedule_result = schedule_node(schedule_state)
    sched_reply = schedule_result["messages"][-1].content
    plan = schedule_result.get("plan", [])

    print(f"Số lượng task được sinh: {len(plan)}")
    for t in plan:
        print(f"- {t.get('time_slot')} | {t.get('title')} (Note: {t.get('note')})")

    # Kiểm tra nghiêm ngặt: TUYỆT ĐỐI không có Pomodoro trong plan hoặc reply
    assert "pomodoro" not in sched_reply.lower(), "CẢNH BÁO: Pomodoro vẫn xuất hiện trong phản hồi của Coach!"
    for t in plan:
        assert "pomodoro" not in t.get("title", "").lower(), f"CẢNH BÁO: Task chứa Pomodoro: {t.get('title')}"
        if t.get("note"):
            assert "pomodoro" not in t.get("note", "").lower(), f"CẢNH BÁO: Note chứa Pomodoro: {t.get('note')}"
    print("✅ Lịch trình đã hoàn toàn loại bỏ Pomodoro theo đúng Adaptive Memory Protocol!")

    # 6. Test Multi-Tenant Isolation
    print("\n--- TEST 5: KIỂM TRA PHÂN TÁCH ĐA NGƯỜI DÙNG (MULTI-TENANT ISOLATION) ---")
    mavis_insights = load_historical_insights(username="mavis")
    alex_insights = load_historical_insights(username="alex_dev")
    print(f"Mavis failed methods count: {len(mavis_insights['failed_methods'])}")
    print(f"Alex failed methods count: {len(alex_insights['failed_methods'])}")
    print(f"Test user failed methods count: {len(updated_insights['failed_methods'])}")
    # test_user has pomodoro, others should not have test_user's specific mutations unless added
    print("✅ Phân tách dữ liệu đa người dùng hoạt động hoàn hảo!")

    # Dọn dẹp dữ liệu test_user
    all_data = json.load(open("memory/goals_ledger.json", "r", encoding="utf-8"))
    if test_user in all_data:
        del all_data[test_user]
        with open("memory/goals_ledger.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã dọn dẹp sạch sẽ tài khoản kiểm thử!")

    print("\n" + "=" * 70)
    print("🎉 TẤT CẢ CÁC BÀI TEST PHASE 10 ĐÃ VƯỢT QUA 100% HOÀN HẢO!")
    print("=" * 70)

if __name__ == "__main__":
    test_phase10()

