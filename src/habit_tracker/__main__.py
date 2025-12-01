# src/habit_tracker/__main__.py

from habit_tracker.storage import SQLStore
from habit_tracker.services import HabitManager
from habit_tracker.services.auth_manager import AuthManager

from habit_tracker.ui.main_menu import main_menu
from habit_tracker.ui.auth_flow import initial_password_setup, login_flow

import sys


def main():
    # 1. Initialize SQLite storage
    storage = SQLStore()

    # 2. Authentication manager
    auth = AuthManager(storage)

    # 3. First run → password setup
    if auth.is_first_run():
        if not initial_password_setup(auth):
            sys.exit(1)
    else:
        # 4. Later runs → login
        if not login_flow(auth):
            sys.exit(1)

    # 5. Auth OK → launch habit manager and menu
    manager = HabitManager(storage)
    main_menu(manager)


if __name__ == "__main__":
    main()
