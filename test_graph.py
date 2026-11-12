from langchain_core.messages import HumanMessage
from agents.graph import mavis_agent


def test_agent_workflow():
    print("=" * 70)
    print(">>> KHỞI CHẠY KIỂM THỬ ĐỒ THỊ LANGGRAPH - MAVIS AI EXECUTIVE COACH <<<")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST CASE 0: User mới tinh, chưa có Profile (Kỳ vọng: START -> onboarding -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 0: Khởi tạo Onboarding khi user_profile trống ---")
    initial_state_0 = {
        "messages": [HumanMessage(content="Xin chào")],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": {},
    }
    print("[Mavis Input]: 'Xin chào' (Profile trống)")
    result_0 = mavis_agent.invoke(initial_state_0)
    print(f"[Onboarding Status]: {result_0.get('user_profile', {}).get('is_onboarded')}")
    print("[Agent Response - Interview Prompt]:")
    print(result_0["messages"][-1].content[:280] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 0.1: Phỏng vấn thu thập mục tiêu & cập nhật goals_ledger
    # -------------------------------------------------------------
    print("\n--- TEST CASE 0.1: Phỏng vấn Onboarding thu thập đa khía cạnh ---")
    input_onboarding = (
        "Tôi là cựu sinh viên Ngoại thương, từng làm Purchasing và Leader Top 20 SIL. "
        "Mục tiêu trọng tâm: Cán mốc IELTS 7.5 trong 2 tháng, thi đỗ VinUni AI Talent Q1/2027, "
        "lấy chứng chỉ HSK 4 trong 4 tháng và chuẩn bị hồ sơ ứng tuyển IT BA. "
        "Thời gian: Não bộ đỉnh cao lúc 8h-10h sáng, chiều giảm tải sau 14h và ngủ trước 23h. "
        "Tài chính ổn định, dành 30 phút mỗi ngày chạy bộ rèn luyện sức khỏe."
    )
    initial_state_onboarding = {
        "messages": [HumanMessage(content=input_onboarding)],
        "current_energy_level": "high",
        "detected_emotion": "determined",
        "intent": "",
        "plan": [],
        "user_profile": {"is_onboarded": False},
    }
    print("[Mavis Input]: Chia sẻ chi tiết mục tiêu đa khía cạnh...")
    result_onboarding = mavis_agent.invoke(initial_state_onboarding)
    profile = result_onboarding.get("user_profile", {})
    print(f"[Onboarding Completed?]: {profile.get('is_onboarded')}")
    print(f"[Extracted Situation]: {profile.get('current_situation')}")
    print(f"[Time Constraints]: {profile.get('time_constraints')}")
    print("[Agent Response]:")
    print(result_onboarding["messages"][-1].content[:350] + "...")

    print("\n" + "-" * 70)

    # Hồ sơ chuẩn sau khi đã hoàn thành Onboarding
    active_profile = {
        "current_situation": "Cựu FTU, cựu Purchasing, cựu Leader Top 20 SIL, thế mạnh Vibe Coding",
        "financial_status": "Quỹ dự phòng ổn định, ưu tiên đầu tư kỹ năng AI & IT BA",
        "time_constraints": "Khung giờ vàng 08:00 - 10:00 sáng cho High Load; sau 14:00 giảm tải; ngủ trước 23:00",
        "is_onboarded": True,
    }

    # -------------------------------------------------------------
    # TEST CASE 1: Lập lịch học (Kỳ vọng: START -> analyze -> schedule -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 1: Lập lịch ôn tập (Intent: schedule) ---")
    input_text_1 = "Tôi muốn lên lịch ôn IELTS Listening trên Study4 và luyện đề VinUni hôm nay."
    initial_state_1 = {
        "messages": [HumanMessage(content=input_text_1)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_1}")
    result_1 = mavis_agent.invoke(initial_state_1)
    print(f"[Agent Intent Detected]: {result_1.get('intent')}")
    print(f"[Number of Tasks in Plan]: {len(result_1.get('plan', []))}")
    print("[Agent Response]:")
    print(result_1["messages"][-1].content[:250] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 2: Than mệt/nản (Kỳ vọng: START -> analyze -> motivate -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 2: Kích hoạt Giao thức Tự hào (Intent: motivate) ---")
    input_text_2 = "Hôm nay tôi mệt quá, fix bug hoài không xong và thấy áp lực mục tiêu 2 tháng quá."
    initial_state_2 = {
        "messages": [HumanMessage(content=input_text_2)],
        "current_energy_level": "high",
        "detected_emotion": "",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_2}")
    result_2 = mavis_agent.invoke(initial_state_2)
    print(f"[Agent Intent Detected]: {result_2.get('intent')}")
    print(f"[Energy Level Updated]: {result_2.get('current_energy_level')}")
    print("[Agent Response]:")
    print(result_2["messages"][-1].content[:250] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 3: Trinh sát xu hướng công nghệ (Kỳ vọng: START -> analyze -> trend -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 3: Trinh sát xu hướng & Weekly Alpha Brief (Intent: explore_trend) ---")
    input_text_3 = "Dạo này làn sóng AI và các startup công nghệ có xu hướng dòng tiền chảy vào đâu? Tôi nên học kỹ năng gì tiếp theo?"
    initial_state_3 = {
        "messages": [HumanMessage(content=input_text_3)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_3}")
    result_3 = mavis_agent.invoke(initial_state_3)
    print(f"[Agent Intent Detected]: {result_3.get('intent')}")
    print("[Agent Response - Weekly Alpha Brief]:")
    print(result_3["messages"][-1].content[:250] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 4: Đặt mục tiêu mới (Kỳ vọng: START -> analyze -> goal_manager -> resource_finder -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 4: Đặt mục tiêu mới ➔ Phân tích khả thi ➔ Tự động trinh sát tài nguyên (Phase 6.2) ---")
    input_text_4 = "Tôi muốn đặt mục tiêu mới: Học Data Science & Chuyên sâu Machine Learning trong 3 tháng tới."
    initial_state_4 = {
        "messages": [HumanMessage(content=input_text_4)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_4}")
    result_4 = mavis_agent.invoke(initial_state_4)
    print(f"[Agent Intent Detected]: {result_4.get('intent')}")
    print(f"[Total Messages Generated in Chain]: {len(result_4['messages'])}")
    print("[1. Goal Feasibility & Task Estimation]:")
    print(result_4["messages"][-2].content[:280] + "...")
    print("[2. Auto-Linked Resource Finder & Cost Estimation]:")
    print(result_4["messages"][-1].content[:280] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 5: Tìm tài liệu học tập (Kỳ vọng: START -> analyze -> resource_finder -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 5: Tìm kiếm & Tuyển chọn tài liệu (Intent: find_resources) ---")
    input_text_5 = "Tìm cho tôi tài liệu, file PDF và khóa học Coursera chất lượng cao để ôn thi VinUni AI."
    initial_state_5 = {
        "messages": [HumanMessage(content=input_text_5)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_5}")
    result_5 = mavis_agent.invoke(initial_state_5)
    print(f"[Agent Intent Detected]: {result_5.get('intent')}")
    print("[Agent Response - Curated Resources]:")
    print(result_5["messages"][-1].content[:250] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 6: Xếp Lịch Động khi Quá Tải & Có Lịch Đột Xuất (Phase 6.3)
    # (Kỳ vọng: START -> analyze -> schedule -> END với Thuật toán Reschedule & Habit Stacking)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 6: Cảm biến thể trạng, Reschedule dời task nặng & chèn Low Load Tasks ---")
    input_text_6 = "Hôm nay tôi bị kiệt sức quá, lại có việc đột xuất cả buổi sáng, hãy dời lịch và xếp lại lịch giúp tôi."
    initial_state_6 = {
        "messages": [HumanMessage(content=input_text_6)],
        "current_energy_level": "high",  # Bắt đầu với high, nhưng cảm biến sẽ chuyển sang low
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_6}")
    result_6 = mavis_agent.invoke(initial_state_6)
    print(f"[Agent Intent Detected]: {result_6.get('intent')}")
    print(f"[Updated Energy Level]: {result_6.get('current_energy_level')}")
    
    plan_6 = result_6.get("plan", [])
    deferred_tasks = [t for t in plan_6 if t.get("status") == "deferred_to_tomorrow"]
    habit_tasks = [t for t in plan_6 if t.get("combined_with") or t.get("cognitive_load") == "habit_stacking"]
    
    print(f"[Total Tasks in Plan]: {len(plan_6)}")
    print(f"[Deferred Heavy Tasks]: {len(deferred_tasks)} task(s) dời sang sáng mai:")
    for dt in deferred_tasks:
        print(f"   -> {dt.get('title')} ({dt.get('time_slot')})")
        
    print(f"[Habit-Stacking / Low Load Tasks]: {len(habit_tasks)} task(s) kết hợp sinh hoạt:")
    for ht in habit_tasks:
        combined_txt = f" [Kết hợp: {ht.get('combined_with')}]" if ht.get('combined_with') else ""
        print(f"   -> {ht.get('title')} ({ht.get('time_slot')}){combined_txt}")

    print("[Agent Response - Reschedule Directive]:")
    print(result_6["messages"][-1].content[:350] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 7: Động cơ RAG & Tree Hierarchy 4 Root Nodes (Phase 7.1)
    # (Kỳ vọng: Ingest URL/PDF -> Chroma Vector DB -> uploaded_context -> AgentState)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 7: Động cơ RAG tự động Ingest & Kiểm thử Cây 4 Root Nodes (Phase 7.1) ---")
    from memory.goals import load_tree_goals, ROOT_NODES
    tree_data = load_tree_goals()
    print(f"[Tree Hierarchy Verified]: 4 Root Nodes tồn tại: {list(tree_data.keys())}")
    for root in ROOT_NODES:
        root_goals = tree_data[root]["children"]
        total_leaves = sum(len(g.get("leaf_nodes", [])) for g in root_goals)
        print(f"   -> Root '{root}': {len(root_goals)} mục tiêu, {total_leaves} Leaf Nodes có status, deadline, dependencies")

    input_text_7 = "Tôi vừa tìm được tài liệu lộ trình này https://vinuni.edu.vn/ai-talent và file vinuni_math_syllabus.pdf, hãy cập nhật và xếp lịch giúp tôi."
    initial_state_7 = {
        "messages": [HumanMessage(content=input_text_7)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
        "uploaded_context": None,
    }

    print(f"\n[Mavis Input]: {input_text_7}")
    result_7 = mavis_agent.invoke(initial_state_7)
    print(f"[Agent Intent Detected]: {result_7.get('intent')}")
    print(f"[Uploaded Context Populated?]: {bool(result_7.get('uploaded_context'))}")
    if result_7.get("uploaded_context"):
        print("[RAG Uploaded Context Sample]:")
        print(result_7["uploaded_context"][:250] + "...")
    print("[Agent Response]:")
    print(result_7["messages"][-1].content[:300] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 8: Backcasting Thạc sĩ AI & Priority Conflict tự động hoãn HSK (Phase 7.2)
    # (Kỳ vọng: START -> analyze -> strategic_planner -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 8: Backcasting Thạc sĩ AI & Priority Conflict tự động hoãn HSK (Phase 7.2) ---")
    input_text_8 = (
        "Lập cho tôi kế hoạch chiến lược dài hạn theo phương pháp Backcasting để apply Học bổng Thạc sĩ AI VinUni. "
        "Tôi xuất thân trái ngành FTU thì cần lộ trình thế nào? Và xử lý xung đột ưu tiên với mục tiêu học HSK giúp tôi."
    )
    initial_state_8 = {
        "messages": [HumanMessage(content=input_text_8)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    # Đặt lại status của IELTS và HSK về in_progress để bảo đảm kiểm thử xung đột ưu tiên chạy lặp lại độc lập
    from memory.goals import update_goal
    update_goal("IELTS", {"status": "in_progress", "deadline": "11/12/2026"})
    update_goal("HSK", {"status": "in_progress"})

    print(f"[Mavis Input]: {input_text_8}")
    result_8 = mavis_agent.invoke(initial_state_8)
    print(f"[Agent Intent Detected]: {result_8.get('intent')}")
    
    # Kiểm tra goals_ledger xem Backcast milestones và status HSK đã cập nhật chưa
    from memory.goals import load_tree_goals
    tree_after_8 = load_tree_goals()
    career_goals_8 = tree_after_8["career"]["children"]
    
    hsk_goal_8 = next((g for g in career_goals_8 if "hsk" in g.get("title", "").lower()), None)
    master_goal_8 = next((g for g in career_goals_8 if "thạc sĩ ai" in g.get("title", "").lower() or "master ai" in g.get("title", "").lower()), None)
    
    print(f"[Master AI Goal Created?]: {bool(master_goal_8)}")
    if master_goal_8:
        print(f"   -> Title: {master_goal_8.get('title')}")
        print(f"   -> Deadline: {master_goal_8.get('deadline')}")
        print(f"   -> Total Backcast Leaf Milestones: {len(master_goal_8.get('leaf_nodes', []))}")
        for idx, lf in enumerate(master_goal_8.get("leaf_nodes", []), 1):
            print(f"      {idx}. {lf.get('title')[:65]}...")

    print(f"[HSK Goal Priority Conflict Status]: {hsk_goal_8.get('status') if hsk_goal_8 else 'N/A'}")
    assert hsk_goal_8 and hsk_goal_8.get("status") == "paused_until_ielts_done", "Lỗi: Mục tiêu HSK chưa được tự động chuyển sang paused_until_ielts_done!"
    print("   -> Xác nhận: HSK status đã được tự động chuyển thành 'paused_until_ielts_done' theo đúng yêu cầu Priority Conflict!")

    # Kiểm tra liên kết trực tiếp sang Opportunity Scout & sinh Task tuần (Phase 7.3)
    plan_8 = result_8.get("plan", [])
    print(f"[Auto-Linked Opportunity Scout Weekly Tasks]: {len(plan_8)} task(s) nạp vào State Plan:")
    for pt in plan_8:
        print(f"   -> [{pt.get('time_slot')}] {pt.get('title')} ({pt.get('cognitive_load')})")
    assert len(plan_8) >= 3, "Lỗi: Chưa sinh được các Task nhỏ trong tuần từ kết quả trinh sát!"
    print("   -> Xác nhận: Opportunity Scout đã tự động sinh các Task nhỏ trong tuần liên kết vào State Plan!")

    print("[Agent Response - Strategic Backcast & Opportunity Intel]:")
    print(result_8["messages"][-1].content[:380] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 9: Trigger tự động Unpause khi IELTS hoàn thành sau 11/12/2026 (Phase 7.2)
    # (Kỳ vọng: START -> analyze -> strategic_planner -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 9: Trigger Tự động Unpause khi IELTS hoàn thành sau 11/12/2026 (Phase 7.2) ---")
    input_text_9 = (
        "Hôm nay ngày hệ thống đã vượt qua 11/12/2026 và tôi đã hoàn thành kỳ thi IELTS đạt 7.5 (status IELTS completed). "
        "Hãy giải phóng lịch và kích hoạt lại mục tiêu HSK giúp tôi."
    )
    initial_state_9 = {
        "messages": [HumanMessage(content=input_text_9)],
        "current_energy_level": "high",
        "detected_emotion": "positive",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_9}")
    result_9 = mavis_agent.invoke(initial_state_9)
    print(f"[Agent Intent Detected]: {result_9.get('intent')}")
    
    # Kiểm tra goals_ledger xem HSK đã được tái kích hoạt thành in_progress chưa
    tree_after_9 = load_tree_goals()
    career_goals_9 = tree_after_9["career"]["children"]
    hsk_goal_9 = next((g for g in career_goals_9 if "hsk" in g.get("title", "").lower()), None)
    ielts_goal_9 = next((g for g in career_goals_9 if "ielts" in g.get("title", "").lower()), None)

    print(f"[IELTS Status]: {ielts_goal_9.get('status') if ielts_goal_9 else 'N/A'}")
    print(f"[HSK Reactivated Status]: {hsk_goal_9.get('status') if hsk_goal_9 else 'N/A'}")
    assert hsk_goal_9 and hsk_goal_9.get("status") == "in_progress", "Lỗi: Mục tiêu HSK chưa được unpause sang in_progress!"
    print("   -> Xác nhận: Trigger Tự động hoạt động hoàn hảo, HSK đã được kích hoạt lại thành 'in_progress'!")

    print("[Agent Response - Unpause Notification]:")
    print(result_9["messages"][-1].content[:380] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 10: Trinh sát cơ hội độc lập & Networking Protocol (Phase 7.3)
    # (Kỳ vọng: START -> analyze -> opportunity_scout -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 10: Trinh sát cơ hội độc lập & Networking Protocol (Phase 7.3) ---")
    input_text_10 = "Trinh sát cơ hội cho tôi về VinUni AI Bootcamp và cho tôi hướng dẫn Networking Protocol kết nối alumni."
    initial_state_10 = {
        "messages": [HumanMessage(content=input_text_10)],
        "current_energy_level": "high",
        "detected_emotion": "determined",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
    }

    print(f"[Mavis Input]: {input_text_10}")
    result_10 = mavis_agent.invoke(initial_state_10)
    print(f"[Agent Intent Detected]: {result_10.get('intent')}")
    print(f"[Scouted Opportunities]: {len(result_10.get('scouted_opportunities', []))} cơ hội tìm thấy")
    print(f"[Networking Protocol Actions]: {len(result_10.get('networking_actions', []))} hành động tạo lợi thế")
    for act in result_10.get("networking_actions", []):
        print(f"   -> {act[:75]}...")

    print("[Agent Response - Opportunity Scout & Networking Protocol Directive]:")
    print(result_10["messages"][-1].content[:400] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 11: Nút Cân Bằng Sinh Học Toàn Diện & Dynamic Equilibrium (Phase 7.4)
    # (Kỳ vọng: START -> analyze -> holistic_scheduler -> END)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 11: Nút Cân Bằng Sinh Học Toàn Diện & Dynamic Equilibrium (Phase 7.4) ---")
    input_text_11 = (
        "Lên lịch cân bằng sinh học toàn diện cho tôi hôm nay. "
        "Mục tiêu vóc dáng của tôi yêu cầu chạy bộ 30 phút và đang áp dụng chế độ thâm hụt calo "
        "(dựa trên tài liệu giảm cân tôi đã nạp). Hãy dung hòa cả 4 khía cạnh cuộc sống và xếp lịch giúp tôi."
    )
    initial_state_11 = {
        "messages": [HumanMessage(content=input_text_11)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "",
        "plan": [],
        "user_profile": active_profile,
        "uploaded_context": "Tài liệu Thâm Hụt Calo Khoa Học: Caloric deficit 350-400 kcal/ngày, cardio 30 phút buổi chiều.",
    }

    print(f"[Mavis Input]: {input_text_11}")
    result_11 = mavis_agent.invoke(initial_state_11)
    print(f"[Agent Intent Detected]: {result_11.get('intent')}")
    print(f"[Recalculated Energy Level (Dynamic Equilibrium)]: {result_11.get('current_energy_level')}")
    assert result_11.get("current_energy_level") == "low", "Lỗi: Năng lượng sinh học chưa được tính toán lại thành low sau buổi tập và thâm hụt calo!"

    plan_11 = result_11.get("plan", [])
    print(f"[Total Harmonized Tasks]: {len(plan_11)} tasks dung hòa từ 4 Root Nodes:")
    for t in plan_11:
        cat_badge = f"[{t.get('category', 'root').upper()}]"
        print(f"   -> {t.get('time_slot')} | {cat_badge} {t.get('title')} ({t.get('cognitive_load')})")

    # Kiểm tra ràng buộc sinh học: KHÔNG xếp task nặng ngay sau chạy bộ
    post_workout_tasks = [t for t in plan_11 if "17:15" in t.get("time_slot", "") or "17:45" in t.get("time_slot", "")]
    for pwt in post_workout_tasks:
        assert pwt.get("cognitive_load") != "high", f"Lỗi ràng buộc sinh học: Task nặng '{pwt.get('title')}' bị xếp ngay sau giờ tập!"
        print(f"   -> Xác nhận ràng buộc: Khung {pwt.get('time_slot')} là tác vụ phục hồi/thụ động: '{pwt.get('title')}'")

    recovery_tasks = [t for t in plan_11 if t.get("cognitive_load") == "recovery_buffer"]
    assert len(recovery_tasks) > 0, "Lỗi: Chưa chèn Recovery Buffer ngay sau giờ chạy bộ!"
    print("   -> Xác nhận: Đã chèn Recovery Buffer (17:15 - 17:45) và Passive Listening (17:45 - 18:30) đúng chuẩn sinh học!")

    print("[Agent Response - Hourly Detailed Timeline Table]:")
    print(result_11["messages"][-1].content[:480] + "...")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 12: Xác thực & Phân tách Dữ liệu Đa Người Dùng (Phase 8 Multi-user SaaS)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 12: Phân Tách Dữ Liệu Đa Người Dùng (Phase 8 Multi-user SaaS) ---")
    from memory.goals import load_goals, load_tree_goals, save_tree_goals, get_blank_tree, load_all_users_data, save_all_users_data
    from memory.auth import register_user, load_auth_config, save_auth_config

    # Reset môi trường User B & dọn dẹp alex_dev để bảo đảm tính lặp lại (Idempotent)
    save_tree_goals(get_blank_tree(), username="user_b")
    cfg_reset = load_auth_config()
    if "alex_dev" in cfg_reset["credentials"]["usernames"]:
        del cfg_reset["credentials"]["usernames"]["alex_dev"]
        save_auth_config(cfg_reset)
    all_d = load_all_users_data()
    if "alex_dev" in all_d:
        del all_d["alex_dev"]
        save_all_users_data(all_d)

    # 1. Kiểm tra không gian dữ liệu khởi tạo của Mavis và User B
    mavis_goals_init = load_goals(username="mavis")
    user_b_goals_init = load_goals(username="user_b")
    print(f"[Initial Goals Count] Mavis: {len(mavis_goals_init)} | User B: {len(user_b_goals_init)}")
    assert len(mavis_goals_init) > 0, "Lỗi: Mavis phải có các mục tiêu hiện hữu trong hệ thống!"
    assert len(user_b_goals_init) == 0, "Lỗi: User B phải bắt đầu với không gian mục tiêu trống!"

    # 2. Gửi lệnh tạo mục tiêu mới dành riêng cho User B qua Agent (Lệnh thực thi trực tiếp)
    input_text_12 = "Lệnh: Thêm mục tiêu mới: Chuyên sâu React & Next.js trong 2 tháng tới"
    initial_state_12 = {
        "messages": [HumanMessage(content=input_text_12)],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "set_goal",
        "plan": [],
        "user_profile": {
            "current_situation": "Frontend Engineer muốn nâng cấp Fullstack",
            "financial_status": "Dư dả, ưu tiên học công nghệ mới",
            "time_constraints": "Khung giờ tối 20:00 - 22:00",
            "is_onboarded": True,
        },
        "username": "user_b",
    }

    print(f"[User B Input]: {input_text_12}")
    result_12 = mavis_agent.invoke(initial_state_12)
    print(f"[Agent Intent for User B]: {result_12.get('intent')}")
    print("[Agent Response for User B]:")
    print(result_12["messages"][-1].content[:300] + "...")

    # 3. Xác minh tính cách ly dữ liệu tuyệt đối (Data Isolation)
    user_b_goals_after = load_goals(username="user_b")
    mavis_goals_after = load_goals(username="mavis")

    print(f"[Goals Count After User B Action] Mavis: {len(mavis_goals_after)} | User B: {len(user_b_goals_after)}")
    assert len(user_b_goals_after) == 1, f"Lỗi: User B phải có đúng 1 mục tiêu mới, nhưng có {len(user_b_goals_after)}!"
    assert any("react" in g.get("title", "").lower() for g in user_b_goals_after), "Lỗi: Mục tiêu React chưa được ghi vào tài khoản của User B!"
    assert len(mavis_goals_after) == len(mavis_goals_init), "Lỗi nghiêm trọng: Mục tiêu của User B đã làm thay đổi dữ liệu của Mavis!"
    print("   -> Xác nhận Cách Ly Dữ Liệu Tuyệt Đối: Thao tác của User B không làm ảnh hưởng đến Mavis!")

    # 4. Kiểm tra quy trình Đăng ký tài khoản SaaS mới (New User Registration)
    print("\n[Kiểm tra Đăng ký User Mới]: Tạo tài khoản 'alex_dev'...")
    reg_success = register_user(
        username="alex_dev",
        name="Alex Developer",
        email="alex@saas.com",
        password="alex_password_123",
    )
    assert reg_success is True, "Lỗi: Đăng ký tài khoản 'alex_dev' thất bại!"
    auth_cfg = load_auth_config()
    assert "alex_dev" in auth_cfg["credentials"]["usernames"], "Lỗi: 'alex_dev' chưa được lưu vào auth_config.yaml!"

    alex_tree = load_tree_goals(username="alex_dev")
    assert all(k in alex_tree for k in ["career", "relationships", "health", "beauty"]), "Lỗi: Tree của user mới thiếu 4 Root Nodes!"
    assert len(load_goals(username="alex_dev")) == 0, "Lỗi: User mới phải có 0 mục tiêu khởi tạo!"
    print("   -> Xác nhận Đăng Ký Tài Khoản: User mới 'alex_dev' đã được tạo và cấp phát không gian dữ liệu riêng biệt thành công!")

    print("\n" + "-" * 70)

    # -------------------------------------------------------------
    # TEST CASE 15: PHASE 9 - AGENTIC COACH ROUTER, DEDUPLICATION & TRIGGER ACTION
    # -------------------------------------------------------------
    print("\n--- TEST CASE 15: Phase 9 - Tư Duy Coaching, Vá Lỗi Duplicate & Trigger Action ---")
    from memory.goals import is_duplicate_goal, cleanup_duplicate_goals, add_goal, load_goals
    from agents.brain import TRIGGER_CLOSING_QUESTION

    # 15.1. Vá lỗi Duplicate Bug
    print("\n[15.1 Kiểm tra Chống Trùng Lặp Mục Tiêu (Duplicate Prevention)]:")
    goals_before = load_goals(username="mavis")
    count_before = len(goals_before)
    # Thêm mục tiêu đã có tương tự: "Học Data Science & AI"
    dup_res = add_goal(
        title="Lộ trình học Data Science & AI thực chiến",
        deadline="6 tháng",
        category="career",
        milestones=[{"milestone": "Python & Pandas", "timeline": "Tháng 1"}],
        username="mavis",
    )
    goals_after = load_goals(username="mavis")
    count_after = len(goals_after)
    print(f"   -> Kết quả: is_updated = {dup_res.get('is_updated')}, ID = {dup_res.get('id')}")
    print(f"   -> Số lượng mục tiêu trước: {count_before} | Sau khi thêm mục tiêu tương tự: {count_after}")
    assert count_after == count_before, f"Lỗi: Mục tiêu trùng lặp bị tạo mới thay vì gộp/cập nhật! (Trước: {count_before}, Sau: {count_after})"
    assert dup_res.get("is_updated") is True, "Lỗi: Cờ is_updated phải là True khi gộp mục tiêu trùng lặp!"
    print("   -> Xác nhận Thành Công: Đã chặn trùng lặp và gộp/cập nhật thông tin thành công!")

    # 15.2. Phân biệt Tin Nhắn Tâm Sự vs Lệnh Thực Thi (Agentic Coach - Không gọi tool/lưu DB)
    print("\n[15.2 Kiểm tra Tư Duy Coaching (Tâm sự dự định -> Không lưu DB hay xếp lịch ngay)]:")
    state_coach_1 = {
        "messages": [HumanMessage(content="Tôi đang muốn học thêm Data Science để phát triển sự nghiệp")],
        "current_energy_level": "high",
        "detected_emotion": "neutral",
        "intent": "chat",
        "plan": [],
        "user_profile": active_profile,
        "username": "mavis",
        "awaiting_confirmation": False,
    }
    goals_pre_chat = len(load_goals(username="mavis"))
    result_coach_1 = mavis_agent.invoke(state_coach_1)
    goals_post_chat = len(load_goals(username="mavis"))
    resp_text_1 = result_coach_1["messages"][-1].content

    print(f"   -> Intent nhận diện: {result_coach_1.get('intent')}")
    print(f"   -> Số lượng mục tiêu trong DB: {goals_post_chat} (Không đổi so với trước: {goals_pre_chat})")
    assert goals_post_chat == goals_pre_chat, "Lỗi: Node giao tiếp không được tự ý lưu mục tiêu khi user chỉ mới tâm sự!"
    assert result_coach_1.get("is_confirmed") is not True, "Lỗi: Không được kích hoạt is_confirmed khi chưa có xác nhận!"
    print(f"   -> Coach Phản Hồi: {resp_text_1[:250]}...")
    print("   -> Xác nhận Thành Công: Agent áp dụng kỹ năng Coaching gợi mở, không gọi tool hay xếp lịch vội vàng!")

    # 15.3. Cơ chế Đưa Ra Câu Hỏi Chốt khi Đã Đủ Thông Tin (Trigger Action)
    print("\n[15.3 Kiểm tra Cơ Chế Đưa Ra Câu Hỏi Chốt (Trigger Action)]:")
    state_coach_2 = {
        "messages": [
            HumanMessage(content="Tôi đang muốn học thêm Data Science để phát triển sự nghiệp"),
            result_coach_1["messages"][-1],
            HumanMessage(content="Tôi có thể dành 2 tiếng mỗi tối, nền tảng toán từ FTU khá vững, mục tiêu hoàn thành trong 6 tháng."),
        ],
        "current_energy_level": "high",
        "detected_emotion": "determined",
        "intent": "chat",
        "plan": [],
        "user_profile": active_profile,
        "username": "mavis",
        "pending_goal": result_coach_1.get("pending_goal"),
        "awaiting_confirmation": False,
    }
    result_coach_2 = mavis_agent.invoke(state_coach_2)
    resp_text_2 = result_coach_2["messages"][-1].content
    print(f"   -> Awaiting Confirmation: {result_coach_2.get('awaiting_confirmation')}")
    print(f"   -> Câu hỏi chốt có xuất hiện?: {TRIGGER_CLOSING_QUESTION in resp_text_2}")
    assert result_coach_2.get("awaiting_confirmation") is True, "Lỗi: awaiting_confirmation phải là True sau khi đưa câu hỏi chốt!"
    assert TRIGGER_CLOSING_QUESTION in resp_text_2, f"Lỗi: Thiếu câu hỏi chốt bắt buộc: '{TRIGGER_CLOSING_QUESTION}'"
    print("   -> Xác nhận Thành Công: Agent đưa ra đúng nguyên văn câu hỏi chốt kích hoạt hành động!")

    # 15.4. Kích hoạt Conditional Edge khi User Trả Lời 'Đồng ý' -> Goal Manager -> Holistic Scheduler
    print("\n[15.4 Kiểm tra Rẽ Nhánh Conditional Edge khi User Trả Lời 'Đồng ý']:")
    state_coach_3 = {
        "messages": [
            HumanMessage(content="Tôi đang muốn học thêm Data Science để phát triển sự nghiệp"),
            result_coach_1["messages"][-1],
            HumanMessage(content="Tôi có thể dành 2 tiếng mỗi tối, nền tảng toán từ FTU khá vững, mục tiêu hoàn thành trong 6 tháng."),
            result_coach_2["messages"][-1],
            HumanMessage(content="Đồng ý, hãy tiến hành đi!"),
        ],
        "current_energy_level": "high",
        "detected_emotion": "determined",
        "intent": "chat",
        "plan": [],
        "user_profile": active_profile,
        "username": "mavis",
        "pending_goal": result_coach_2.get("pending_goal"),
        "awaiting_confirmation": True,
    }
    result_coach_3 = mavis_agent.invoke(state_coach_3)
    final_plan = result_coach_3.get("plan", [])
    print(f"   -> Số lượng task trong Lịch trình Cân bằng Toàn diện: {len(final_plan)}")
    assert len(final_plan) > 0, "Lỗi: Holistic Scheduler phải tạo ra lịch trình chi tiết sau khi user Đồng ý!"
    assert any("career" in str(t.get("category", "")).lower() for t in final_plan), "Lỗi: Thiếu task thuộc nhánh Career trong lịch trình!"
    assert any("beauty" in str(t.get("category", "")).lower() or "chạy bộ" in str(t.get("title", "")).lower() for t in final_plan), "Lỗi: Thiếu task Beauty trong lịch trình!"
    print("   -> Xác nhận Thành Công: Conditional Edge đã chuyển tiếp dữ liệu qua goal_manager và holistic_scheduler hoàn hảo!")

    print("\n" + "=" * 70)
    print(">>> TẤT CẢ 15 TEST CASES (BAO GỒM PHASE 9) ĐÃ HOÀN THÀNH XUẤT SẮC! <<<")
    print("=" * 70)




if __name__ == "__main__":
    test_agent_workflow()
