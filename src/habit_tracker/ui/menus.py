"""
UI menus for the Habit Tracker CLI.

This module contains menu navigation only (questionary prompts and routing).
All behavior is delegated to functions in `habit_tracker.ui.actions` and
`habit_tracker.ui.screens`.
"""

from typing import Optional

import questionary

from habit_tracker.services import HabitService
import habit_tracker.ui.actions as actions
import habit_tracker.ui.screens as screens


def analytics_menu(service: HabitService) -> None:
    """
    Show analytics options and run the selected analysis.

    Args:
        service: Habit service providing access to habit data and operations.
    """
    while True:
        choice: Optional[str] = questionary.select(
            "Analytics – choose an option:",
            choices=[
                "List all habits",
                "List daily habits",
                "List weekly habits",
                "Show longest streak (overall)",
                "Show longest streak for a habit",
                "Back to main menu",
            ],
        ).ask()

        # Handle cancelled prompt (e.g. ESC / Ctrl+C)
        if choice is None or choice == "Back to main menu":
            return

        if choice == "List all habits":
            actions.view_habits(service)
        elif choice == "List daily habits":
            actions.list_daily_habits(service)
        elif choice == "List weekly habits":
            actions.list_weekly_habits(service)
        elif choice == "Show longest streak (overall)":
            actions.show_longest_streak_overall(service)
        elif choice == "Show longest streak for a habit":
            actions.show_longest_streak_by_habit(service)


def main_menu(service: HabitService) -> None:
    """
    Show the main menu loop and route user actions.

    Args:
        service: Habit service providing access to habit data and operations.
    """
    screens.welcome_banner()

    while True:
        choice: Optional[str] = questionary.select(
            "Choose an action:",
            choices=[
                "Add Habit",
                "Remove Habit",
                "Log completion",
                "Analytics",
                "Exit",
            ],
        ).ask()

        # Handle cancelled prompt
        if choice is None or choice == "Exit":
            return

        if choice == "Add Habit":
            actions.add_habit(service)
        elif choice == "Remove Habit":
            actions.remove_habit(service)
        elif choice == "Log completion":
            actions.log_completion(service)
        elif choice == "Analytics":
            analytics_menu(service)
