"""
tests/test_mascot_banner.py - Unit tests for Mavis Duolingo-style Mascot Banner component.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from ui.components.mascot_banner import _load_mascot_media, render_mascot_banner


class TestMascotBanner(unittest.TestCase):

    def test_load_mascot_media_reads_svg_or_fallback(self):
        """Kiểm tra hàm _load_mascot_media trả về chuỗi ảnh/SVG hợp lệ."""
        media_html = _load_mascot_media("celebrate")
        self.assertIsInstance(media_html, str)
        self.assertTrue("<svg" in media_html or "<img" in media_html)

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
        mock_session_state[f"master_schedule_testuser"] = [
            {"date": today_iso, "title": "Deep Work Module 1", "time_slot": "08:00 - 10:00", "is_done": True},
            {"date": today_iso, "title": "Tập thể dục Cardio", "time_slot": "16:30 - 17:30", "is_done": False},
        ]

        render_mascot_banner("testuser", "Nguyen Van A")

        self.assertTrue(mock_markdown.called)
        rendered_html = mock_markdown.call_args[0][0]

        # Kiểm tra sự hiện diện của các thành phần giao diện Duolingo
        self.assertIn("mavis-mascot-banner", rendered_html)
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
        mock_session_state[f"master_schedule_newbie"] = []

        render_mascot_banner("newbie", "Người Mới")

        self.assertTrue(mock_markdown.called)
        rendered_html = mock_markdown.call_args[0][0]

        self.assertIn("mavis-mascot-banner", rendered_html)
        self.assertIn("CHÀO MỪNG TRỞ LẠI! ✨", rendered_html)
        self.assertIn("0/0 việc", rendered_html)
        self.assertIn("(0%)", rendered_html)


if __name__ == "__main__":
    unittest.main()
