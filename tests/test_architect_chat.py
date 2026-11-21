import unittest
import uuid
from memory.goals import (
    load_master_schedule,
    save_master_schedule,
    load_user_goals,
    save_user_goals,
    delete_user_goal,
)
from agents.brain import (
    ceo_coach_chat,
    architect_chat,
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


if __name__ == "__main__":
    unittest.main()
