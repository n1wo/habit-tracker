"""
Application composition root for the Habit Tracker CLI.

This module wires together storage, services, authentication, and UI flows.
It decides whether the app runs in demo mode or real (persistent) mode and
controls the top-level application loop.
"""

import sys

from habit_tracker.storage import SQLStore
from habit_tracker.services import HabitManager
from habit_tracker.services.auth_manager import AuthManager
from habit_tracker.fixtures.example_data import ExampleDataFactory

import habit_tracker.ui.screens as screens
from habit_tracker.ui.mode_select import choose_mode
from habit_tracker.ui.menus import main_menu
from habit_tracker.ui.auth_flow import initial_password_setup, login_flow


def _run_demo_session() -> None:
    """
    Run a demo session using only in-memory data.

    Characteristics:
    - Uses HabitManager(storage=None), so nothing touches the real database.
    - Seeds habits and completion dates from ExampleDataFactory.
    - All data is discarded when the user exits the main menu.
    """
    manager = HabitManager(storage=None)

    example_dicts = ExampleDataFactory(weeks=4).build()

    for habit_dict in example_dicts:
        habit = manager.add_habit(
            name=habit_dict["name"],
            periodicity=habit_dict["periodicity"],
            description=habit_dict["description"],
        )
        for dt in habit_dict["completion_dates"]:
            manager.log_completion(habit.habit_id, when=dt)

    print("\n🧪 Demo mode: working with in-memory example habits.")
    print("   All changes here will be lost when you leave demo mode.\n")

    main_menu(manager)


def _run_real_session() -> None:
    """
    Run the authenticated session against the persistent backend.

    Flow:
    - Initialize storage and authentication manager
    - On first run: prompt for password setup
    - On subsequent runs: require login
    - Load habits and seed predefined ones if applicable
    """
    storage = SQLStore()
    auth = AuthManager(storage)

    if auth.is_first_run():
        if not initial_password_setup(auth):
            return
    else:
        if not login_flow(auth):
            return

    manager = HabitManager(storage)
    manager.seed_predefined_habits()

    main_menu(manager)


def run_app() -> None:
    """
    Top-level application entry point.

    Loop:
    - Display welcome banner
    - Ask user to choose demo mode, real mode, or exit
    - Run the selected session
    - When a session ends, return to mode selection
    """
    while True:
        screens.welcome_banner()
        mode = choose_mode()

        if mode is None or mode.startswith("🚪"):
            print("\nGoodbye!\n")
            sys.exit(0)

        if mode.startswith("🧪"):
            _run_demo_session()
        else:
            _run_real_session()
