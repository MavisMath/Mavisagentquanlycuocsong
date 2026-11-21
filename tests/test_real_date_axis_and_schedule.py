import unittest
from datetime import datetime, date, timedelta
from memory.goals import (
    standardize_goal_schema,
    compute_target_date,
    get_vietnam_today,
    get_vietnam_today_str,
    generate_detailed_master_schedule,
    ensure_schedule_covers_date,
    load_master_schedule,
    save_master_schedule,
    defer_master_schedule_task_to_tomorrow,
    VIETNAM_WEEKDAYS,
)
from tools.google_calendar import _convert_task_to_datetime_range, exchange_code_and_save_token


class TestRealDateAxisAndDetailedSchedule(unittest.TestCase):
    def setUp(self):
        self.test_username = "test_user_schedule_axis"

    def test_start_and_target_date_calculation(self):
        """Kiểm tra tự động tính target_date từ start_date và duration_days."""
        target = compute_target_date("2026-11-21", 90)
        self.assertEqual(target, "2027-02-19")

        raw_goal = {
            "title": "Giảm 15kg trong 90 ngày",
            "category": "Sức khỏe",
            "duration_days": 90,
        }
        std_goal = standardize_goal_schema(raw_goal)
        self.assertIn("start_date", std_goal)
        self.assertIn("target_date", std_goal)
        self.assertEqual(std_goal["start_date"], get_vietnam_today_str())
        self.assertEqual(std_goal["target_date"], compute_target_date(std_goal["start_date"], 90))

    def test_generate_detailed_master_schedule_slots(self):
        """Kiểm tra bóc tách chi tiết từng khung giờ sinh hoạt (Tập luyện, Bữa 1, Bữa 2, Uống nước, Ngủ)."""
        active_goals = [{
            "id": "g_health",
            "title": "Giảm 15kg trong 90 ngày",
            "category": "Sức khỏe",
            "strategy_summary": "Ăn theo IF 16:8 và tập kháng lực 3 buổi + cardio 3 buổi",
            "start_date": "2026-11-21",
            "duration_days": 90,
        }]
        sched = generate_detailed_master_schedule(
            active_goals=active_goals,
            start_date_str="2026-11-21",
            num_days=7,
            username=self.test_username,
        )
        self.assertGreaterEqual(len(sched), 7 * 4)

        # Kiểm tra ngày 2026-11-21
        d1_tasks = [t for t in sched if t.get("date") == "2026-11-21"]
        self.assertGreaterEqual(len(d1_tasks), 4)

        # Kiểm tra các khung giờ bắt buộc
        time_slots = [t.get("time_slot") for t in d1_tasks]
        self.assertTrue(any("12:00 - 12:30" in s for s in time_slots), "Thiếu khung giờ Bữa 1 12:00 - 12:30")
        self.assertTrue(any("19:00 - 19:30" in s for s in time_slots), "Thiếu khung giờ Bữa 2 19:00 - 19:30")
        self.assertTrue(any("22:15 - 22:30" in s or "22:30" in s for s in time_slots), "Thiếu khung giờ đi ngủ 22:30")

        # Kiểm tra nội dung chi tiết: Bữa 1 có định lượng gram/calo
        bua_1 = next(t for t in d1_tasks if "12:00" in t.get("time_slot", ""))
        self.assertTrue("150g" in bua_1["task_detail"] or "kcal" in bua_1["task_detail"])

        # Kiểm tra nội dung tập luyện có bài tập cụ thể
        workout_tk = next(t for t in d1_tasks if "07:00 - 08:00" in t.get("time_slot", ""))
        self.assertTrue(any(k in workout_tk["task_detail"].lower() for k in ["chạy bộ", "kháng lực", "push-up", "zone 2"]))

    def test_ensure_schedule_covers_date(self):
        """Kiểm tra tự động sinh dữ liệu khi user chọn ngày chưa có trong lịch."""
        target_d = date(2026, 12, 15)
        sched = ensure_schedule_covers_date(target_d, active_goals=[], username=self.test_username)
        self.assertTrue(any(t.get("date") == "2026-12-15" for t in sched))

    def test_convert_task_to_datetime_range_iso(self):
        """Kiểm tra Google Calendar converter phân tích chính xác ngày YYYY-MM-DD."""
        s_dt, e_dt = _convert_task_to_datetime_range("2026-11-21", "12:00 - 12:30")
        self.assertEqual(s_dt.year, 2026)
        self.assertEqual(s_dt.month, 11)
        self.assertEqual(s_dt.day, 21)
        self.assertEqual(s_dt.hour, 12)
        self.assertEqual(s_dt.minute, 0)
        self.assertEqual(e_dt.hour, 12)
        self.assertEqual(e_dt.minute, 30)


    def test_defer_master_schedule_task_to_tomorrow(self):
        """Kiểm tra dời task sang ngày mai trong master_schedule."""
        test_task = {
            "task_detail": "Chạy bộ Zone 2 40 phút",
            "time_slot": "07:00 - 07:40",
            "date": "2026-11-21",
            "day_name": "Thứ Bảy",
            "is_done": False,
        }
        save_master_schedule([test_task], username=self.test_username)
        ok, next_d = defer_master_schedule_task_to_tomorrow("Chạy bộ Zone 2", "2026-11-21", username=self.test_username)
        self.assertTrue(ok)
        self.assertEqual(next_d, "2026-11-22")

        updated_sched = load_master_schedule(self.test_username)
        self.assertEqual(len(updated_sched), 1)
        self.assertEqual(updated_sched[0]["date"], "2026-11-22")
        self.assertEqual(updated_sched[0]["day_name"], "Chủ Nhật")


if __name__ == "__main__":
    unittest.main()
