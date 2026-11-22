"""
tests/test_sidebar_and_adaptive_memory.py - Test optimized Sidebar layout and Adaptive Memory tab.
"""

import unittest
from unittest.mock import patch, MagicMock
import streamlit as st

from ui.components.sidebar import render_sidebar
from ui.components.tab_adaptive_memory import render_tab_adaptive_memory


class TestSidebarAndAdaptiveMemory(unittest.TestCase):
    def setUp(self):
        self.username = "test_user_sidebar"
        self.name = "Test Executive"
        if not hasattr(st, "session_state"):
            st.session_state = {}

    def test_sidebar_contains_only_required_sections_and_no_technical_jargon(self):
        """Kiểm tra Sidebar chỉ chứa 4 mục chính và đã loại bỏ hoàn toàn các biến nội bộ."""
        markdown_outputs = []
        subheader_outputs = []

        def mock_markdown(text, *args, **kwargs):
            markdown_outputs.append(str(text))

        def mock_subheader(text, *args, **kwargs):
            subheader_outputs.append(str(text))

        mock_sidebar_ctx = MagicMock()
        mock_sidebar_ctx.__enter__.return_value = None
        mock_sidebar_ctx.__exit__.return_value = None

        mock_popover_ctx = MagicMock()
        mock_popover_ctx.__enter__.return_value = None
        mock_popover_ctx.__exit__.return_value = None

        with patch("streamlit.sidebar", mock_sidebar_ctx), \
             patch("streamlit.markdown", side_effect=mock_markdown), \
             patch("streamlit.subheader", side_effect=mock_subheader), \
             patch("streamlit.caption"), \
             patch("streamlit.success"), \
             patch("streamlit.warning"), \
             patch("streamlit.info"), \
             patch("streamlit.popover", return_value=mock_popover_ctx) as mock_pop, \
             patch("streamlit.checkbox", return_value=False) as mock_chk, \
             patch("streamlit.button", return_value=False), \
             patch("ui.components.sidebar.load_master_schedule", return_value=[]), \
             patch("ui.components.sidebar.load_user_goals", return_value=[]):

            render_sidebar(self.username, self.name)

        all_rendered_text = " ".join(markdown_outputs + subheader_outputs)

        # 1. Bảo đảm KHÔNG xuất hiện các thông số nội bộ / tên biến tiếng Anh
        self.assertNotIn("CẢM XÚC NHẬN DIỆN", all_rendered_text)
        self.assertNotIn("INTENT", all_rendered_text)
        self.assertNotIn("failed_methods", all_rendered_text)
        self.assertNotIn("effective_methods", all_rendered_text)
        self.assertNotIn("productivity_patterns", all_rendered_text)

        # 2. Bảo đảm có mặt các tiêu đề chuẩn
        self.assertTrue(any("Năng Lượng" in s for s in subheader_outputs), f"Thiếu mục Năng Lượng trong {subheader_outputs}")
        self.assertTrue(any("Task Hôm Nay" in s for s in subheader_outputs), f"Thiếu mục Task Hôm Nay trong {subheader_outputs}")
        self.assertTrue(any("Mục Tiêu" in s for s in subheader_outputs), f"Thiếu mục Mục Tiêu trong {subheader_outputs}")

        # 3. Bảo đảm nút Reset All dùng popover và có checkbox xác nhận
        self.assertTrue(mock_pop.called, "Nút Reset All phải dùng st.popover để có 2 bước xác nhận")
        self.assertTrue(mock_chk.called, "Popover Reset All phải có checkbox xác nhận 2 lần")

    def test_classify_goal_category_case_insensitivity_and_health_beauty_merge(self):
        """Bảo đảm classify_goal_category gom đúng Sức khỏe & Sắc vóc không phân biệt hoa thường."""
        from memory.goals import classify_goal_category

        cases = [
            ({"category": "Sức khỏe"}, "health_beauty"),
            ({"category": "Sức Khỏe"}, "health_beauty"),
            ({"category": "sức khoẻ"}, "health_beauty"),
            ({"category": "Sắc Vóc"}, "health_beauty"),
            ({"domain": "beauty"}, "health_beauty"),
            ({"category": "Health"}, "health_beauty"),
            ({"category": "Học tập & Sự nghiệp"}, "career"),
            ({"category": "Sự nghiệp"}, "career"),
            ({"domain": "Tài chính"}, "career"),
            ({"category": "Mối quan hệ"}, "relationships"),
            ({"category": "Gia đình"}, "relationships"),
            ({"title": "Chạy bộ 5km mỗi sáng"}, "health_beauty"),
        ]
        for goal_dict, expected_grp in cases:
            res = classify_goal_category(goal_dict)
            self.assertEqual(res, expected_grp, f"Lỗi phân loại {goal_dict}: nhận {res}, kỳ vọng {expected_grp}")

    def test_sidebar_reads_directly_from_user_goals_and_shows_health_goal(self):
        """Kiểm tra Sidebar đọc trực tiếp user_goals và hiển thị ngay mục tiêu 'Sức khỏe'."""
        sample_goals = [
            {
                "id": "g_health_1",
                "title": "Chạy bộ 5km & Ăn uống IF 16:8",
                "category": "Sức khỏe",
                "status": "active",
                "daily_hours": 1.0,
                "preferred_time": "06:30 - 07:30",
            },
            {
                "id": "g_career_1",
                "title": "Chinh phục IELTS 7.5",
                "category": "Học tập",
                "status": "active",
                "daily_hours": 2.0,
                "preferred_time": "08:30 - 10:30",
            },
        ]

        tabs_created = []
        def mock_tabs(tab_names):
            tabs_created.append(list(tab_names))
            return [MagicMock(), MagicMock(), MagicMock()]

        mock_sidebar_ctx = MagicMock()
        mock_sidebar_ctx.__enter__.return_value = None
        mock_sidebar_ctx.__exit__.return_value = None

        mock_popover_ctx = MagicMock()
        mock_popover_ctx.__enter__.return_value = None
        mock_popover_ctx.__exit__.return_value = None

        with patch("streamlit.sidebar", mock_sidebar_ctx), \
             patch("streamlit.markdown"), \
             patch("streamlit.subheader"), \
             patch("streamlit.caption"), \
             patch("streamlit.success"), \
             patch("streamlit.warning"), \
             patch("streamlit.info"), \
             patch("streamlit.tabs", side_effect=mock_tabs), \
             patch("streamlit.expander", return_value=MagicMock()), \
             patch("streamlit.popover", return_value=mock_popover_ctx), \
             patch("streamlit.checkbox", return_value=False), \
             patch("streamlit.button", return_value=False), \
             patch("ui.components.sidebar.load_master_schedule", return_value=[]), \
             patch("ui.components.sidebar.load_user_goals", return_value=sample_goals):

            render_sidebar(self.username, self.name)

        self.assertTrue(len(tabs_created) > 0, "Sidebar phải render các tab mục tiêu")
        tab_titles = " ".join(tabs_created[0])
        self.assertIn("Sự Nghiệp", tab_titles)
        self.assertIn("Mối Quan Hệ", tab_titles)
        self.assertIn("Sức Khỏe & Sắc Vóc", tab_titles)
        # Số lượng đếm trong tab title: Sự nghiệp (1), Sức khỏe & Sắc vóc (1)
        self.assertIn("Sự Nghiệp (1)", tab_titles)
        self.assertIn("Sức Khỏe & Sắc Vóc (1)", tab_titles)

    def test_load_categorized_goals_syncs_with_user_goals(self):
        """Bảo đảm memory/goals.py load_categorized_goals tự động đồng bộ từ load_user_goals."""
        from memory.goals import load_categorized_goals

        test_user = "test_user_sync_cat"
        mock_user_goals = [
            {
                "id": "mock_g_health",
                "title": "Chạy bộ sáng",
                "category": "Sức Khỏe",
                "status": "active",
            }
        ]

        with patch("memory.goals.load_user_goals", return_value=mock_user_goals):
            cat_result = load_categorized_goals(username=test_user)
            self.assertIn("health", cat_result)
            self.assertIn("health_beauty", cat_result)
            titles = [g.get("title") for g in cat_result["health_beauty"]]
            self.assertIn("Chạy bộ sáng", titles)

    def test_adaptive_memory_renders_natural_vietnamese(self):
        """Kiểm tra Bộ Nhớ Thích Nghi hiển thị chuẩn 100% tiếng Việt tự nhiên."""
        rendered_texts = []

        def mock_markdown(text, *args, **kwargs):
            rendered_texts.append(str(text))

        mock_metrics = []
        def mock_metric(label, value, *args, **kwargs):
            mock_metrics.append((str(label), str(value)))

        def mock_cols(spec, *args, **kwargs):
            count = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(count)]

        with patch("streamlit.markdown", side_effect=mock_markdown), \
             patch("streamlit.metric", side_effect=mock_metric), \
             patch("streamlit.caption"), \
             patch("streamlit.info"), \
             patch("streamlit.columns", side_effect=mock_cols), \
             patch("ui.components.tab_adaptive_memory.load_historical_insights", return_value={
                 "failed_methods": ["Học sau 22h"],
                 "effective_methods": ["Pomodoro 25p"],
                 "productivity_patterns": ["Đỉnh cao lúc 8h sáng"],
             }):

            render_tab_adaptive_memory(self.username, self.name)

        all_text = " ".join(rendered_texts)
        metric_labels = [m[0] for m in mock_metrics]

        # Kiểm tra tiêu đề tiếng Việt tự nhiên
        self.assertTrue(any("Cần tránh" in ml for ml in metric_labels))
        self.assertTrue(any("Hiệu quả cao" in ml for ml in metric_labels))
        self.assertTrue(any("Quy luật năng suất" in ml for ml in metric_labels))

        # Kiểm tra nội dung không chứa biến tiếng Anh thô
        self.assertNotIn("failed_methods", all_text)
        self.assertNotIn("effective_methods", all_text)
        self.assertNotIn("productivity_patterns", all_text)


if __name__ == "__main__":
    unittest.main()
