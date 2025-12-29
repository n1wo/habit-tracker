"""
UI screen helpers for the Habit Tracker CLI.

This module contains simple prompt-based screens that guide high-level
application flow (mode selection, banners, etc.).
"""

from typing import Optional

import questionary


def choose_mode() -> Optional[str]:
    """
    Prompt the user to choose how they want to use the Habit Tracker.

    Options:
    - Log into the real habit tracker (persistent data)
    - Try the demo with example data (resets every run)
    - Exit the application

    Returns:
        The selected option as a string, or None if the prompt is cancelled.
    """
    return questionary.select(
        "How would you like to use the Habit Tracker today?",
        choices=[
            "🔐 Log into my habit tracker (real data)",
            "🧪 Try demo with example data (resets every time)",
            "🚪 Exit application",
        ],
    ).ask()
