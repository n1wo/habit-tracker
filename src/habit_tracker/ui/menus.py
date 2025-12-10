import questionary
from habit_tracker.services import HabitService
import habit_tracker.ui.actions as actions
import habit_tracker.ui.screens as screens


def analytics_menu(service: HabitService):
    """Show analytics options and run selected analysis."""

    while True:
        choice = questionary.select(
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

        if choice == "List all habits":
            # Reuse the existing view_habits implementation
            actions.view_habits(service)
        elif choice == "List daily habits":
            actions.list_daily_habits(service)
        elif choice == "List weekly habits":
            actions.list_weekly_habits(service)
        elif choice == "Show longest streak (overall)":
            actions.show_longest_streak_overall(service)
        elif choice == "Show longest streak for a habit":
            actions.show_longest_streak_by_habit(service)
        elif choice == "Back to main menu":
            return  # exit analytics submenu and go back


def main_menu(service: HabitService):
    screens.welcome_banner()

    while True:
        choice = questionary.select(
            "Choose an action:",
            choices=[
                "Add Habit",
                "Remove Habit",
                "Log completion",
                "Analytics",
                "Exit",
            ],
        ).ask()
        if choice == "Add Habit":
            actions.add_habit(service)
        elif choice == "Remove Habit":
            actions.remove_habit(service)
        elif choice == "Log completion":
            actions.log_completion(service)
        elif choice == "Analytics":
            # Call the local analytics_menu defined above
            analytics_menu(service)
        elif choice == "Exit":
            return
