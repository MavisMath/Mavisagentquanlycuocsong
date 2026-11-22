"""
tests/test_mascot_banner.py - Unit tests for Mavis Duolingo-style Mascot Banner component.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from ui.components.mascot_banner import _load_mascot_media, render_mascot_banner


class TestMascotBanner(unittest.TestCase):

    def test_load_mascot_media_reads_all_4_expressions(self):
        """Kiểm tra hàm _load_mascot_media load đúng 4 file biểu cảm."""
        for mood in ["welcome", "thinking", "celebrate", "remind"]:
            media_html = _load_mascot_media(mood)
            self.assertIsInstance(media_html, str)
            self.assertIn("<img", media_html)
            self.assertIn("data:image/png;base64,", media_html)

    def test_load_mascot_media_fallback_when_empty_dir(self):
        """Kiểm tra fallback trả về SVG khi không tìm thấy file."""
        with patch("os.path.exists", return_value=False):
            media_html = _load_mascot_media("default")
            self.assertIn("<svg", media_html)
            self.assertIn("url(#bodyGrad_fb)", media_html)

    @patch("streamlit.markdown")
    @patch("streamlit.session_state", new_callable=dict)
    def test_render_mascot_banner_with_tasks(self, mock_session_state, mock_markdown):
        """Kiểm tra render banner khi có danh sách công việc trong ngày."""
        today_iso = datetime.now().strftime("%Y-%m-%d")
        mock_session_state["master_schedule_testuser"] = [
            {"date": today_iso, "title": "Deep Work Module 1", "time_slot": "08:00 - 10:00", "is_done": True},
            {"date": today_iso, "title": "Tập thể dục Cardio", "time_slot": "16:30 - 17:30", "is_done": False},
        ]

        render_mascot_banner("testuser", "Nguyen Van A")

        self.assertTrue(mock_markdown.called)
        rendered_html = mock_markdown.call_args[0][0]

        # Kiểm tra sự hiện diện của các thành phần giao diện Duolingo & animation float
        self.assertIn("mavis-mascot-banner", rendered_html)
        self.assertIn("@keyframes float", rendered_html)
        self.assertIn("badge-streak", rendered_html)
        self.assertIn("badge-xp", rendered_html)
        self.assertIn("progress-track", rendered_html)
        self.assertIn("progress-fill", rendered_html)
        self.assertIn("1/2 việc", rendered_html)
        self.assertIn("(50%)", rendered_html)

    @patch("streamlit.markdown")
    @patch("streamlit.session_state", new_callable=dict)
    def test_render_mascot_banner_empty_tasks(self, mock_session_state, mock_markdown):
        """Kiểm tra render banner khi user chưa có task nào hôm nay."""
        mock_session_state["master_schedule_newbie"] = []

        render_mascot_banner("newbie", "Người Mới")

        self.assertTrue(mock_markdown.called)
        rendered_html = mock_markdown.call_args[0][0]

        self.assertIn("mavis-mascot-banner", rendered_html)
        self.assertIn("CHÀO MỪNG TRỞ LẠI! ✨", rendered_html)
        self.assertIn("0/0 việc", rendered_html)
        self.assertIn("(0%)", rendered_html)

    @patch("streamlit.balloons")
    @patch("streamlit.markdown")
    @patch("streamlit.session_state", new_callable=dict)
    def test_balloons_triggered_once_on_100_percent(self, mock_session_state, mock_markdown, mock_balloons):
        """Kiểm tra st.balloons() được kích hoạt đúng 1 lần/ngày khi hoàn thành 100% task."""
        today_iso = datetime.now().strftime("%Y-%m-%d")
        mock_session_state["master_schedule_champion"] = [
            {"date": today_iso, "title": "Task 1", "time_slot": "08:00 - 10:00", "is_done": True},
            {"date": today_iso, "title": "Task 2", "time_slot": "10:30 - 11:30", "is_done": True},
        ]

        # Lần 1: Chưa có cờ -> st.balloons() phải được gọi
        render_mascot_banner("champion", "Chiến Thần")
        self.assertEqual(mock_balloons.call_count, 1)
        self.assertTrue(mock_session_state.get(f"balloons_shown_{today_iso}_champion"))

        # Lần 2 (Rerun trong cùng ngày): Đã có cờ -> st.balloons() KHÔNG được gọi thêm
        render_mascot_banner("champion", "Chiến Thần")
        self.assertEqual(mock_balloons.call_count, 1)


if __name__ == "__main__":
    unittest.main()
