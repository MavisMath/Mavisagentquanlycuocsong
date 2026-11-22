"""
ui/components package - Modularized Streamlit UI Components for Mavis Executive Life Coach.
"""

from ui.components.styles import inject_custom_css
from ui.components.auth import render_auth_screen
from ui.components.sidebar import render_sidebar
from ui.components.mascot_banner import render_mascot_banner
from ui.components.tab_ceo import render_tab_ceo
from ui.components.tab_architect import render_tab_architect
from ui.components.tab_scheduler import render_tab_scheduler
from ui.components.tab_retrospective import render_tab_retrospective
from ui.components.helpers import (
    safe_dict,
    safe_list,
    shorten_task_name,
    push_undo_state,
    save_undo_snapshot,
    apply_undo,
    apply_redo,
    generate_gcal_link,
    generate_ics_calendar,
    generate_ics_from_master_schedule,
    extract_text_from_content,
    load_categorized_goals,
    get_brain_modules,
    get_mavis_agent,
    ceo_coach_chat,
    architect_chat,
    scheduler_chat,
    retrospective_chat,
    chat_node,
    get_authenticator,
    get_default_redirect_uri,
    exchange_code_and_save_token,
    load_user_goals,
    load_user_profile,
    load_user_resources,
    load_user_roadmap,
    load_master_schedule,
    load_retrospective_logs,
    OPENING_GREETING,
)

__all__ = [
    "inject_custom_css",
    "render_auth_screen",
    "render_sidebar",
    "render_mascot_banner",
    "render_tab_ceo",
    "render_tab_architect",
    "render_tab_scheduler",
    "render_tab_retrospective",
    "safe_dict",
    "safe_list",
    "shorten_task_name",
    "push_undo_state",
    "save_undo_snapshot",
    "apply_undo",
    "apply_redo",
    "generate_gcal_link",
    "generate_ics_calendar",
    "generate_ics_from_master_schedule",
    "extract_text_from_content",
    "load_categorized_goals",
    "get_brain_modules",
    "get_mavis_agent",
    "ceo_coach_chat",
    "architect_chat",
    "scheduler_chat",
    "retrospective_chat",
    "chat_node",
    "get_authenticator",
    "get_default_redirect_uri",
    "exchange_code_and_save_token",
    "load_user_goals",
    "load_user_profile",
    "load_user_resources",
    "load_user_roadmap",
    "load_master_schedule",
    "load_retrospective_logs",
    "OPENING_GREETING",
]
