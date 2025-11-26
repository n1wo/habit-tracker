import questionary
from habit_tracker.services import HabitService
from habit_tracker.analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    longest_streak_overall,
    longest_streak_by_habit,
)

def add_habit(service: HabitService):
    """Add a new habit via CLI prompts."""
    name = questionary.text("Enter habit name:").ask()
    if not name:
        print("No name entered.")
        return

    periodicity = questionary.select(
        "Choose periodicity:",
        choices=["Daily", "Weekly"]
    ).ask()
    # Map UI -> backend format
    period_val = periodicity.lower()  # "daily" | "weekly"

    description = questionary.text("Enter description (optional):").ask()
    print(f"\n✅ Habit added: {name} ({periodicity}) - {description or 'No description'}\n")

    habit = service.add_habit(name=name, periodicity=period_val, description=description or None)
    print(f"\n✅ Habit added: (id={getattr(habit,'habit_id','?')}) {habit.name} [{period_val}]"
          f" - {habit.description or 'No description'}\n")
    
def remove_habit(service: HabitService):
    """Remove an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to remove.\n")
        return

    choices = [f"(id={getattr(h,'habit_id','?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to remove:",
        choices=choices
    ).ask()
    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(')')[0].strip('(id=')
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        print("Invalid habit ID.")
        return

    success = service.remove_habit(habit_id)
    if success:
        print(f"\n🗑️ Habit removed: {choice}\n")
    else:
        print("\n❌ Habit not found.\n")


def view_habits(service: HabitService):
    """View all existing habits."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits yet.\n")
        return

    print("\n📋 Your habits:")
    for h in habits:
        hid = getattr(h, "habit_id", "?")
        desc = getattr(h, "description", "") or "—"
        period = getattr(h, "periodicity", "?")
        created = getattr(h, "created_date", "")
        created_txt = getattr(created, "strftime", lambda *_: str(created))("%Y-%m-%d %H:%M") if created else ""

        # Created date formatting
        created = getattr(h, "created_date", None)
        created_txt = created.strftime("%Y-%m-%d %H:%M") if created else "—"

        # Completion dates formatting
        completion_dates = getattr(h, "completion_dates", [])
        if isinstance(completion_dates, list) and completion_dates:
            completion_dates_txt = ", ".join(
                dt.strftime("%Y-%m-%d %H:%M") for dt in completion_dates
            )
        else:
            completion_dates_txt = "—"

        print(f" • id:{hid} name:{h.name} period:{period} — description:{desc}  created:{created_txt} completions:{completion_dates_txt}")
    print()

def log_completion(service: HabitService):
    """Remove an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to log.\n")
        return

    choices = [f"(id={getattr(h,'habit_id','?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to log:",
        choices=choices
    ).ask()
    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(')')[0].strip('(id=')
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        print("Invalid habit ID.")
        return

    success = service.log_completion(habit_id)
    if success:
        print(f"\n✅ Habit logged: {choice}\n")
    else:
        # Distinguish between "not found" and "already logged this period"
        current_habits = service.list_habits()
        exists = any(getattr(h, "habit_id", None) == habit_id for h in current_habits)

        if exists:
            print("\nℹ️ Habit already logged for this period.\n")
        else:
            print("\n❌ Habit not found.\n")

def analytics_menu(service: HabitService) -> None:
    """Show analytics options and run selected analysis."""
    habits = service.list_habits()
    if not habits:
        print("\n📊 No habits available for analytics.\n")
        return

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

        if choice is None or choice == "Back to main menu":
            print()
            return

        # 1) List all habits
        if choice == "List all habits":
            all_habits = list_all_habits(habits)
            print("\n📋 All habits:")
            for h in all_habits:
                print(f" • id:{h.habit_id} name:{h.name} period:{h.periodicity}")
            print()

        # 2) List daily habits
        elif choice == "List daily habits":
            daily = list_habits_by_periodicity(habits, "daily")
            if not daily:
                print("\n📋 No daily habits found.\n")
            else:
                print("\n📋 Daily habits:")
                for h in daily:
                    print(f" • id:{h.habit_id} name:{h.name}")
                print()

        # 3) List weekly habits
        elif choice == "List weekly habits":
            weekly = list_habits_by_periodicity(habits, "weekly")
            if not weekly:
                print("\n📋 No weekly habits found.\n")
            else:
                print("\n📋 Weekly habits:")
                for h in weekly:
                    print(f" • id:{h.habit_id} name:{h.name}")
                print()

        # 4) Longest streak overall
        elif choice == "Show longest streak (overall)":
            result = longest_streak_overall(habits)
            best = result["habit"]
            streak = result["streak"]

            if best is None or streak == 0:
                print("\n📊 No streaks yet. Start completing your habits!\n")
            else:
                print("\n📊 Longest streak (overall):")
                print(f" • Habit: {best.name} (id:{best.habit_id}, period:{best.periodicity})")
                print(f" • Streak: {streak} periods\n")

        # 5) Longest streak for a specific habit
        elif choice == "Show longest streak for a habit":
            # Reuse the usual id-selection pattern
            choices = [f"(id={h.habit_id}) {h.name}" for h in habits]
            habit_choice = questionary.select(
                "Select a habit:",
                choices=choices,
            ).ask()

            if not habit_choice:
                print("No habit selected.\n")
                continue

            habit_id_str = habit_choice.split(")")[0].strip("(id=")
            try:
                habit_id = int(habit_id_str)
            except ValueError:
                print("Invalid habit ID.\n")
                continue

            streak = longest_streak_by_habit(habits, habit_id)
            if streak == 0:
                print(f"\n📊 Habit {habit_choice} has no streak yet.\n")
            else:
                print(f"\n📊 Longest streak for {habit_choice}: {streak} periods\n")
