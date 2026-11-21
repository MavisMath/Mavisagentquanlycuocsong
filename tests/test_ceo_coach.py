import unittest
import os
from agents.brain import ceo_coach_chat
from memory.goals import load_user_goals, save_user_goals, delete_user_goal


class TestCEOCoachChat(unittest.TestCase):
    def setUp(self):
        self.test_user = "test_unit_ceo_runner"
        save_user_goals([], username=self.test_user)

    def tearDown(self):
        goals = load_user_goals(self.test_user)
        for g in goals:
            gid = g.get("id") or g.get("goal_id")
            if gid:
                delete_user_goal(gid, username=self.test_user)

    def test_create_new_goal_no_name_error(self):
        """Kiểm tra gọi trực tiếp ceo_coach_chat tạo mục tiêu mới, bảo đảm không văng NameError."""
        message = "Tôi muốn học chứng chỉ AWS Cloud Practitioner trong 60 ngày, mỗi ngày học 1.5 tiếng vào buổi sáng 08:00 - 09:30"
        result = ceo_coach_chat(
            user_message=message,
            username=self.test_user,
        )

        self.assertIsInstance(result, dict)
        self.assertIn("response", result)
        self.assertIn("ready_to_approve", result)
        self.assertIn("goals", result)
        self.assertIn("status", result)

        if result.get("ready_to_approve"):
            new_goal = result.get("new_goal_detected")
            self.assertIsNotNone(new_goal)
            self.assertTrue(new_goal.get("id", "").startswith("goal_"))
            self.assertEqual(new_goal.get("status"), "evaluating")

    def test_burnout_shield_trigger(self):
        """Kiểm tra khi user đã có > 8h/ngày, Burnout Shield phải cảnh báo quá tải."""
        heavy_goals = [
            {"id": "g_heavy1", "title": "Dự án A", "daily_hours": 5.0, "status": "active"},
            {"id": "g_heavy2", "title": "Dự án B", "daily_hours": 4.0, "status": "active"},
        ]
        save_user_goals(heavy_goals, username=self.test_user)

        message = "Tôi muốn học thêm tiếng Trung HSK 3 trong 3 tháng, mỗi ngày 2 tiếng"
        result = ceo_coach_chat(
            user_message=message,
            username=self.test_user,
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("burnout_risk_detected", False))
        self.assertFalse(result.get("ready_to_approve", True))


if __name__ == "__main__":
    unittest.main()
