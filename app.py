"""
Mavis Executive AI - Root Entrypoint Forwarder
Đảm bảo tính tương thích tuyệt đối cho Streamlit Cloud dù cấu hình chạy từ 'app.py' hay 'ui/app.py'.
"""
import os
import sys

# Đảm bảo đường dẫn gốc luôn nằm trong sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

UI_DIR = os.path.join(ROOT_DIR, "ui")
if UI_DIR not in sys.path:
    sys.path.insert(0, UI_DIR)

# Thực thi ứng dụng chính từ ui/app.py
import runpy
target_app_path = os.path.join(UI_DIR, "app.py")
runpy.run_path(target_app_path, run_name="__main__")
