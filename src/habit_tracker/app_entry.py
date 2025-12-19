from __future__ import annotations

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
    Run a demo session using ONLY in-memory data.

    • Uses HabitManager(storage=None) so nothing touches the real DB.
    • Seeds habits and completion dates from ExampleDataFactory.
    • All data is lost when the user exits the main menu.
    """
    manager = HabitManager(storage=None)

    # Build perfect example habit dicts.
    example_dicts = ExampleDataFactory(weeks=4).build()

    # Create habits in the manager and replay completion dates.
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

    # When main_menu returns, we go back to the mode selection in run_app()
    main_menu(manager)


def _run_real_session() -> None:
    """
    Run the normal authenticated session against the real persistent backend.
    """
    storage = SQLStore()
    auth = AuthManager(storage)

    # First run → password setup. Later runs → login.
    if auth.is_first_run():
        if not initial_password_setup(auth):
            return  # back to mode selection
    else:
        if not login_flow(auth):
            return  # back to mode selection

    manager = HabitManager(storage)
    main_menu(manager)


def run_app() -> None:
    """
    Top-level application entry point (composition root).

    Loop:
      • Ask user if they want real mode, demo mode, or exit.
      • Run the chosen session.
      • When the session returns (user exited main menu), show the menu again.
    """
    while True:
        screens.welcome_banner()
        mode = choose_mode()

        # User aborted with ESC / Ctrl+C or chose explicit Exit.
        if mode is None or mode.startswith("🚪"):
            print("\nGoodbye!\n")
            sys.exit(0)

        if mode.startswith("🧪"):
            _run_demo_session()
        else:
            _run_real_session()
