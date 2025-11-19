from habit_tracker.storage import SQLStore
from habit_tracker.services import HabitManager
from habit_tracker.ui import main_menu

def main():

    # set up storage (SQLite)
    storage = SQLStore()

    # pass storage into HabitManager so it can load/save from DB
    manager = HabitManager(storage=storage)

    # start the CLI
    main_menu(manager)

if __name__ == "__main__":
    main()