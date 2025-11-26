import questionary
from habit_tracker.services import HabitService 
import habit_tracker.ui.actions as actions
import habit_tracker.ui.screens as screens

def main_menu(service: HabitService):
    screens.welcome_banner()

    while True:
        choice = questionary.select(
            "Choose an action:",
            choices=[
                "Add Habit",
                "Remove Habit",
                "View Habits",
                "Log completion",
                "Analytics",
                "Exit"
            ]
        ).ask()

        if choice == "Add Habit":
            actions.add_habit(service)
        elif choice == "Remove Habit":
            actions.remove_habit(service)
        elif choice == "View Habits":
            actions.view_habits(service)
        elif choice == "Log completion":
            actions.log_completion(service)
        elif choice == "Analytics":        # 👈 NEW
            actions.analytics_menu(service)
        elif choice == "Exit":
            print("\n👋 Goodbye!\n")
            exit()