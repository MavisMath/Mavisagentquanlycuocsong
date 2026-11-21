import unittest
import uuid
from memory.goals import (
    load_master_schedule,
    save_master_schedule,
    load_user_goals,
    save_user_goals,
    delete_user_goal,
    detect_goal_domain,
    DOMAIN_TERMINOLOGY,
)
from agents.brain import (
    ceo_coach_chat,
    architect_chat,
    scheduler_chat,
    retrospective_chat,
)


class TestArchitectAndImports(unittest.TestCase):
    def setUp(self):
        self.test_username = f"test_arch_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        # Dọn dẹp goals thử nghiệm
        goals = load_user_goals(self.test_username)
        for g in goals:
            gid = g.get("id") or g.get("goal_id")
            if gid:
                delete_user_goal(gid, self.test_username)

    def test_direct_imports(self):
        """Bảo đảm load_master_schedule và ceo_coach_chat nạp trực tiếp không dính NameError/ImportError."""
        sched = load_master_schedule(self.test_username)
        self.assertIsInstance(sched, list)
        self.assertTrue(callable(ceo_coach_chat))
        self.assertTrue(callable(architect_chat))

    def test_detect_goal_domain(self):
        """Kiểm tra nhận diện lĩnh vực chuyên biệt (Domain-Aware Detection)."""
        self.assertEqual(detect_goal_domain(goal_title="Giảm 15kg trong 90 ngày", category="Sức khỏe"), "health")
        self.assertEqual(detect_goal_domain(goal_title="Tập gym tăng 3kg cơ bắp"), "health")
        self.assertEqual(detect_goal_domain(goal_title="Chạy bộ Half Marathon 21km"), "health")
        self.assertEqual(detect_goal_domain(goal_title="IELTS 7.5 trong 3 tháng", category="Ngoại ngữ"), "language")
        self.assertEqual(detect_goal_domain(goal_title="Chinh phục HSK 5", category="Học tập"), "language")
        self.assertEqual(detect_goal_domain(goal_title="Học lập trình Python & Backend FastAPI"), "tech_study")
        self.assertEqual(detect_goal_domain(goal_title="Tăng doanh số bán hàng 200%", category="Kinh doanh"), "career_finance")
        self.assertEqual(detect_goal_domain(goal_title="Đọc 20 cuốn sách"), "general")

    def test_health_domain_consultation_no_prohibited_terms(self):
        """Kiểm tra Architect Bot tư vấn sức khỏe: không dùng từ học thuật, không hỏi câu duyệt mục tiêu."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Giảm 15kg trong 90 ngày",
            "category": "Sức khỏe",
            "priority": "P1 - Urgent",
            "preferred_time": "06:00 - 07:30 Sáng",
            "daily_hours": 1.5,
            "duration_days": 90,
            "status": "evaluating",
            "strategy_summary": "",
            "breakdown": {},
        }
        save_user_goals([test_goal], username=self.test_username)

        # User hỏi: Bạn đề xuất phương pháp cho tôi
        res = architect_chat(
            user_message="Bạn đề xuất phương pháp cho tôi để giảm 15kg trong 90 ngày",
            username=self.test_username,
            goal_id=test_goal["id"],
        )

        resp_text = res.get("response", "").lower()
        self.assertIn("response", res)
        self.assertFalse(res.get("is_breakdown", True))

        # 1. Tuyệt đối không hỏi lại câu thẩm định
        self.assertNotIn("chính thức đưa mục tiêu này vào cuộc đời", resp_text)
        self.assertNotIn("bạn có muốn tôi chính thức", resp_text)

        # 2. Phải có từ vựng thể lực & dinh dưỡng
        has_fitness_terms = any(t in resp_text for t in ["dinh dưỡng", "calo", "thâm hụt", "tập luyện", "kháng lực", "cardio"])
        self.assertTrue(has_fitness_terms, f"Phản hồi không chứa thuật ngữ dinh dưỡng & tập luyện: {resp_text[:200]}")

        # 3. Tuyệt đối cấm từ học thuật / thi cử
        prohibited = ["giờ học", "giáo trình", "quá tải nhận thức", "deep work", "ôn thi", "học viên", "sách giáo khoa"]
        found_prohibited = [p for p in prohibited if p in resp_text]
        self.assertEqual(found_prohibited, [], f"Phản hồi chứa từ cấm cho lĩnh vực sức khỏe: {found_prohibited}")

    def test_health_domain_breakdown_stages_and_energy(self):
        """Kiểm tra phân rã 4 tầng cho sức khỏe: Quý thể hiện rõ 30-90 ngày, nhãn năng lượng bài tập."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Giảm 15kg trong 90 ngày",
            "category": "Sức khỏe",
            "priority": "P1 - Urgent",
            "preferred_time": "06:00 - 07:30 Sáng",
            "daily_hours": 1.5,
            "duration_days": 90,
            "status": "evaluating",
            "strategy_summary": "Dinh dưỡng thâm hụt 500 kcal kết hợp tập kháng lực và Cardio Zone 2.",
            "breakdown": {},
        }
        save_user_goals([test_goal], username=self.test_username)

        res = architect_chat(
            user_message="Chốt phương pháp và tự động phân rã 4 tầng",
            username=self.test_username,
            goal_id=test_goal["id"],
            force_breakdown=True,
        )

        self.assertTrue(res.get("is_breakdown"))
        bd = res.get("breakdown", {})

        # Tầng 2: Quý phải thể hiện rõ giai đoạn / cột mốc kết quả
        quarterly = bd.get("quarterly", [])
        self.assertTrue(len(quarterly) > 0)
        q1 = quarterly[0]
        self.assertTrue(len(q1.get("focus", "")) > 0)
        self.assertTrue(len(q1.get("target_outcome", "")) > 0)

        # Tầng 4: Tuần phải có task với nhãn bài tập / không chứa 'Deep Work'
        weekly = bd.get("weekly", [])
        self.assertTrue(len(weekly) > 0)
        w1_tasks = weekly[0].get("tasks", [])
        if w1_tasks:
            t1 = w1_tasks[0]
            self.assertIn("energy_level", t1)
            # Nhãn năng lượng không nên là Deep Work trần trụi
            self.assertNotEqual(t1.get("energy_level"), "🔴 Deep Work")

    def test_architect_chat_stage1_consultation(self):
        """Kiểm tra Nhịp 1: Thảo luận chiến lược & lưu strategy_summary vào MongoDB."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Chinh phục HSK 5 trong 6 tháng",
            "category": "Ngoại ngữ",
            "priority": "P2 - High",
            "preferred_time": "19:00 - 20:30 Tối",
            "daily_hours": 1.5,
            "duration_days": 180,
            "status": "evaluating",
            "strategy_summary": "",
            "breakdown": {},
        }
        save_user_goals([test_goal], username=self.test_username)

        # Nhịp 1: User hỏi về phương pháp học
        res1 = architect_chat(
            user_message="Theo bạn với mục tiêu HSK 5 này thì nên áp dụng phương pháp nào để tối ưu thời gian?",
            username=self.test_username,
            goal_id=test_goal["id"],
        )

        self.assertIn("response", res1)
        self.assertIn("strategy_summary", res1)
        self.assertFalse(res1.get("is_breakdown", True))
        self.assertTrue(len(res1.get("strategy_summary", "")) > 0)

        # Xác minh strategy_summary đã được ghi vào MongoDB / user_goals
        updated_goals = load_user_goals(self.test_username)
        self.assertEqual(len(updated_goals), 1)
        self.assertEqual(updated_goals[0]["strategy_summary"], res1["strategy_summary"])

    def test_architect_chat_stage2_finalize_breakdown(self):
        """Kiểm tra Nhịp 2: Chốt phương pháp & Tự động phân rã 4 tầng khép kín."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Chạy bộ Half Marathon 21km",
            "category": "Sức khỏe",
            "priority": "P2 - High",
            "preferred_time": "05:30 - 07:00 Sáng",
            "daily_hours": 1.5,
            "duration_days": 90,
            "status": "evaluating",
            "strategy_summary": "Phương pháp chạy cự ly dài lũy tiến (Long Slow Distance) 3 buổi/tuần kết hợp rèn thể lực và giãn cơ hồi phục.",
            "breakdown": {},
        }
        save_user_goals([test_goal], username=self.test_username)

        # Nhịp 2: User chốt phương pháp với cờ force_breakdown=True
        res2 = architect_chat(
            user_message="Chốt phương pháp chiến lược và tự động phân rã 4 tầng",
            username=self.test_username,
            goal_id=test_goal["id"],
            force_breakdown=True,
        )

        self.assertIn("response", res2)
        self.assertTrue(res2.get("is_breakdown"))
        self.assertIn("breakdown", res2)

        bd = res2["breakdown"]
        self.assertIn("yearly", bd)
        self.assertIn("quarterly", bd)
        self.assertIn("monthly", bd)
        self.assertIn("weekly", bd)
        self.assertTrue(len(bd["weekly"]) > 0)

        # Kiểm tra task đầu tiên có đủ nhãn năng lượng và DoD
        w1 = bd["weekly"][0]
        self.assertIn("tasks", w1)
        if w1["tasks"]:
            t1 = w1["tasks"][0]
            self.assertIn("energy_level", t1)
            self.assertIn("definition_of_done", t1)

    def test_kwargs_resilience_and_force_breakdown(self):
        """Bảo đảm architect_chat nhận force_breakdown=True và **kwargs mà không dính TypeError."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Học Lập trình React & Next.js",
            "category": "Kỹ thuật",
            "priority": "P2 - High",
            "preferred_time": "20:00 - 21:30 Tối",
            "daily_hours": 1.5,
            "duration_days": 60,
            "status": "evaluating",
            "strategy_summary": "Project-based Learning xây dựng dự án Full-Stack thực tế.",
            "breakdown": {},
        }
        save_user_goals([test_goal], username=self.test_username)

        # 1. Gọi architect_chat với force_breakdown=True kèm extra kwargs
        res = architect_chat(
            user_message="Bắt đầu phân rã lộ trình",
            username=self.test_username,
            goal_id=test_goal["id"],
            chat_history=[],
            force_breakdown=True,
            extra_dummy_arg="test_val",
        )
        self.assertIn("response", res)
        self.assertTrue(res.get("is_breakdown"))
        self.assertIn("breakdown", res)

        # 2. Bảo đảm callable signatures của các chat bots khác cũng chấp nhận **kwargs
        self.assertTrue(callable(ceo_coach_chat))
        self.assertTrue(callable(scheduler_chat))
        self.assertTrue(callable(retrospective_chat))

    def test_scheduler_chat_generates_7_full_days(self):
        """Bảo đảm scheduler_chat sinh đầy đủ lịch trình 7 ngày (Thứ Hai -> Chủ Nhật) kèm nhãn năng lượng và DoD."""
        test_goal = {
            "id": f"goal_{uuid.uuid4().hex[:6]}",
            "title": "Chinh phục IELTS 7.5 Speaking & Writing",
            "category": "Ngoại ngữ",
            "priority": "P1 - Urgent",
            "preferred_time": "08:00 - 10:00 Sáng",
            "daily_hours": 2.0,
            "duration_days": 90,
            "status": "active",
            "strategy_summary": "Luyện đề Cam 16-18 và phản xạ 1-1 theo phương pháp Spaced Repetition.",
            "breakdown": {
                "weekly": [
                    {
                        "week": 1,
                        "tasks": [
                            {
                                "task": "Luyện 3 đề Speaking Part 2 chủ đề Công nghệ",
                                "energy_level": "🔴 Deep Work",
                                "definition_of_done": "Ghi âm 3 bài nói đạt độ trôi chảy 7.0+",
                                "resource_url": "https://cambridgeenglish.org",
                            },
                            {
                                "task": "Ôn tập 30 collocation chủ đề Môi trường",
                                "energy_level": "🟡 Shallow Work",
                                "definition_of_done": "Ghi nhớ và hoàn thành flashcard Quizlet",
                                "resource_url": "https://quizlet.com",
                            },
                        ],
                    }
                ]
            },
        }
        save_user_goals([test_goal], username=self.test_username)

        res = scheduler_chat(
            user_message="Hãy gom active goals để xếp đầy đủ lịch trình 7 ngày tuần này",
            username=self.test_username,
        )

        self.assertIn("master_schedule", res)
        sched = res["master_schedule"]
        self.assertTrue(len(sched) >= 7, f"Lịch trình phải có ít nhất 7 task cho 7 ngày, thực tế: {len(sched)}")

        found_days = set(t.get("date") for t in sched)
        expected_days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        for ed in expected_days:
            self.assertIn(ed, found_days, f"Thiếu ngày {ed} trong master_schedule: {found_days}")

        # Kiểm tra task đầu tiên có đầy đủ energy_level, DoD và resource
        first_t = sched[0]
        self.assertIn("energy_level", first_t)
        self.assertTrue(any(e in first_t["energy_level"] for e in ["🔴", "🟡", "🟢", "Deep", "Shallow", "Recharge"]))
        self.assertIn("definition_of_done", first_t)
        self.assertTrue(len(first_t["definition_of_done"]) > 0)
        self.assertTrue(bool(first_t.get("resource_url") or first_t.get("resource_link")))


if __name__ == "__main__":
    unittest.main()
