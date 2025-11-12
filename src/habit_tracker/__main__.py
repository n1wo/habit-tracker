from habit_tracker.services import HabitManager
from habit_tracker.ui import main_menu

def main():
    manager = HabitManager()
    main_menu(manager)

if __name__ == "__main__":
    main()