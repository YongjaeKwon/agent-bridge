from __future__ import annotations

from config.settings import get_env


SUPPORTED_LOCALES = {"en", "ko"}


UI_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "refresh": "Refresh",
        "overview": "Overview",
        "setup": "Setup",
        "agents": "Agents",
        "work": "Work",
        "events": "Events",
        "meetings": "Meetings",
        "integration_status": "Integration status",
        "recent_work": "Recent work",
        "agent_roster": "Agent roster",
        "one_prompt_control": "One prompt control",
        "goal_placeholder": "Describe the goal. The planner will split work and start the worker loop.",
        "create_run": "Create + Run",
        "create_only": "Create only",
        "start_worker_loop": "Start worker loop",
        "create_run_help": "Create + Run creates a planner task, starts the planner, then starts the dispatch loop for workers. Compact prompts are used by default.",
        "task_queue": "Task queue",
        "agent_events": "Agent events",
        "meeting_digest": "Meeting digest",
        "meeting_task_placeholder": "Optional task id scope",
        "create_digest": "Create digest",
        "digest_help": "Digest includes agent contributions, decisions, blockers, outcomes, and next actions. Sync the created meeting to Notion with the existing Notion sync flow.",
        "save": "Save",
        "load_linear_projects": "Load Linear projects",
        "linear_projects": "Linear Projects",
        "linear_help": "Save a Linear API key first.",
        "saved_placeholder": "Saved. Enter a value only to change it.",
        "no_tasks": "No tasks yet.",
        "no_events": "No events yet.",
        "run": "Run",
    },
    "ko": {
        "refresh": "\uc0c8\ub85c\uace0\uce68",
        "overview": "\uac1c\uc694",
        "setup": "\uc124\uc815",
        "agents": "\uc5d0\uc774\uc804\ud2b8",
        "work": "\uc5c5\ubb34",
        "events": "\uc774\ubca4\ud2b8",
        "meetings": "\ud68c\uc758\ub85d",
        "integration_status": "\uc5f0\ub3d9 \uc0c1\ud0dc",
        "recent_work": "\ucd5c\uadfc \uc791\uc5c5",
        "agent_roster": "\uc5d0\uc774\uc804\ud2b8 \uad6c\uc131",
        "one_prompt_control": "\ub2e8\uc77c \ud504\ub86c\ud504\ud2b8 \uc2e4\ud589",
        "goal_placeholder": "\ubaa9\ud45c\ub97c \uc785\ub825\ud558\uc138\uc694. PM\uc774 \uc5c5\ubb34\ub97c \ub098\ub204\uace0 \uc6cc\ucee4 \ub8e8\ud504\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4.",
        "create_run": "\uc0dd\uc131 + \uc2e4\ud589",
        "create_only": "\uc0dd\uc131\ub9cc",
        "start_worker_loop": "\uc6cc\ucee4 \ub8e8\ud504 \uc2dc\uc791",
        "create_run_help": "\uc0dd\uc131 + \uc2e4\ud589\uc740 PM \uc791\uc5c5\uc744 \ub9cc\ub4e4\uace0 PM\uc744 \uc2e4\ud589\ud55c \ub4a4 \uc6cc\ucee4 \uc790\ub3d9 \ubd84\ubc30 \ub8e8\ud504\ub97c \uc2dc\uc791\ud569\ub2c8\ub2e4. \uae30\ubcf8\uc801\uc73c\ub85c compact prompt\ub97c \uc0ac\uc6a9\ud569\ub2c8\ub2e4.",
        "task_queue": "\uc791\uc5c5 \ub300\uae30\uc5f4",
        "agent_events": "\uc5d0\uc774\uc804\ud2b8 \uc774\ubca4\ud2b8",
        "meeting_digest": "\ud68c\uc758\ub85d \uc694\uc57d",
        "meeting_task_placeholder": "\uc120\ud0dd: \ud2b9\uc815 task id",
        "create_digest": "\ud68c\uc758\ub85d \uc0dd\uc131",
        "digest_help": "\ud68c\uc758\ub85d\uc5d0\ub294 \uc5d0\uc774\uc804\ud2b8\ubcc4 \uae30\uc5ec, \uacb0\uc815, blocker, \uacb0\uacfc, \ub2e4\uc74c \uc561\uc158\uc774 \ud3ec\ud568\ub429\ub2c8\ub2e4. \uc0dd\uc131 \ud6c4 \uae30\uc874 Notion sync\ub85c \uc62c\ub9b4 \uc218 \uc788\uc2b5\ub2c8\ub2e4.",
        "save": "\uc800\uc7a5",
        "load_linear_projects": "Linear \ud504\ub85c\uc81d\ud2b8 \ubd88\ub7ec\uc624\uae30",
        "linear_projects": "Linear \ud504\ub85c\uc81d\ud2b8",
        "linear_help": "\uba3c\uc800 Linear API \ud0a4\ub97c \uc800\uc7a5\ud558\uc138\uc694.",
        "saved_placeholder": "\uc800\uc7a5\ub428. \ubcc0\uacbd\ud560 \ub54c\ub9cc \uc785\ub825\ud558\uc138\uc694.",
        "no_tasks": "\uc544\uc9c1 \uc791\uc5c5\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.",
        "no_events": "\uc544\uc9c1 \uc774\ubca4\ud2b8\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.",
        "run": "\uc2e4\ud589",
    },
}


LANGUAGE_NAMES = {
    "en": "English",
    "ko": "Korean",
}


SECTION_LABELS = {
    "en": {
        "goal": "Goal",
        "context": "Context",
        "owner": "Owner",
        "source": "Source",
        "deliverables": "Deliverables",
        "acceptance": "Acceptance Criteria",
        "planner_instructions": "Planner Instructions",
    },
    "ko": {
        "goal": "\ubaa9\ud45c",
        "context": "\ubc30\uacbd",
        "owner": "\ub2f4\ub2f9",
        "source": "\ucd9c\ucc98",
        "deliverables": "\uc0b0\ucd9c\ubb3c",
        "acceptance": "\uc644\ub8cc \uae30\uc900",
        "planner_instructions": "PM \uc9c0\uc2dc\uc0ac\ud56d",
    },
}


def locale() -> str:
    value = get_env("ECC_LOCALE", "en").lower()
    return value if value in SUPPORTED_LOCALES else "en"


def language_name() -> str:
    return LANGUAGE_NAMES[locale()]


def ui_messages() -> dict[str, str]:
    return UI_MESSAGES[locale()]


def section_labels() -> dict[str, str]:
    return SECTION_LABELS[locale()]
