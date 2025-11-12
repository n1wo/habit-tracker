from habit_tracker.services import HabitManager
from habit_tracker.ui.cli import main_menu

if __name__ == "__main__":
    manager = HabitManager()        # concrete implementation
    main_menu(manager)              # passed as HabitService