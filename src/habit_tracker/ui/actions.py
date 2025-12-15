import questionary
from habit_tracker.services import HabitService
from questionary import Choice
from habit_tracker.analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    longest_streak_overall as analytics_longest_streak_overall,
    longest_streak_by_habit as analytics_longest_streak_by_habit,
    calculate_current_streak,
)

def add_habit(service: HabitService):
    """Add a new habit via CLI prompts."""
    name = questionary.text("Enter habit name:").ask()
    if not name:
        print("No name entered.")
        return

    periodicity = questionary.select(
        "Choose periodicity:",
        choices=["Daily", "Weekly"],
    ).ask()
    if not periodicity:
        print("No periodicity selected.")
        return

    # Map UI -> backend format ("daily" | "weekly")
    period_val = periodicity.lower()

    description = questionary.text("Enter description (optional):").ask()

    habit = service.add_habit(
        name=name,
        periodicity=period_val,
        description=description or None,
    )

    print(
        f"\n✅ Habit added: "
        f"(id={getattr(habit, 'habit_id', '?')}) {habit.name} [{period_val}] "
        f"- {habit.description or 'No description'}\n"
    )


def remove_habit(service: HabitService):
    """Remove an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to remove.\n")
        return

    choices = [f"(id={getattr(h, 'habit_id', '?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to remove:",
        choices=choices,
    ).ask()

    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(")")[0].strip("(id=")
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
    """View all existing habits and inspect completion history for a chosen habit."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits yet.\n")
        return

    # Use analytics helper (pure, functional) to get a list copy
    all_habits = list_all_habits(habits)

    choices = [
        Choice(
            title=f"{h.habit_id}: {h.name} ({h.periodicity})",
            value=h.habit_id,
        )
        for h in all_habits
    ]
    # Cancel option with a special sentinel value
    choices.append(Choice("Cancel", value="__CANCEL__"))

    selected_id = questionary.select(
        "\n📋 All habits\nWhich habit do you want to inspect?",
        choices=choices,
        qmark="",
    ).ask()

    # Handle cancel or aborted prompt
    if selected_id is None or selected_id == "__CANCEL__":
        print("\n🔙 Returning to analytics menu...\n")
        return

    # Get the selected habit from the list
    habit = next((h for h in all_habits if h.habit_id == selected_id), None)
    if habit is None:
        print("❌ Error: Habit not found.")
        return

    # ------------------------------------------------------------------
    # 3) Show detail view: info, completion list, and streak
    # ------------------------------------------------------------------
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📌 Habit: {habit.name}")
    print(f"🆔 ID: {habit.habit_id}")
    print(f"🕒 Periodicity: {habit.periodicity}")

    created = getattr(habit, "created_date", None)
    if created is not None:
        print(f"📅 Created: {created.strftime('%Y-%m-%d %H:%M')}")

    streak = analytics_longest_streak_by_habit(all_habits, habit.habit_id)
    print(f"🔥 Longest streak: {streak} period(s)")

    current = calculate_current_streak(habit)
    print(f"⚡ Current streak: {current} period(s)")

    print("\n✅ Completion dates:")
    completion_dates = getattr(habit, "completion_dates", None)

    if not completion_dates:
        print("   — No completions yet —")
    else:
        for dt in sorted(completion_dates):
            print(f"   • {dt.strftime('%Y-%m-%d %H:%M')}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def log_completion(service: HabitService):
    """Log a completion for an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to log.\n")
        return

    choices = [f"(id={getattr(h, 'habit_id', '?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to log:",
        choices=choices,
    ).ask()

    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(")")[0].strip("(id=")
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


# ---------------------------------------------------------------------------
# Analytics wrappers
# ---------------------------------------------------------------------------

def list_daily_habits(service: HabitService):
    """List all daily habits."""
    habits = service.list_habits()
    daily = list_habits_by_periodicity(habits, "daily")

    if not daily:
        print("\n📋 No daily habits found.\n")
    else:
        print("\n📋 Daily habits:")
        for h in daily:
            print(f" • id:{h.habit_id} name:{h.name}")
        print()


def list_weekly_habits(service: HabitService):
    """List all weekly habits."""
    habits = service.list_habits()
    weekly = list_habits_by_periodicity(habits, "weekly")

    if not weekly:
        print("\n📋 No weekly habits found.\n")
    else:
        print("\n📋 Weekly habits:")
        for h in weekly:
            print(f" • id:{h.habit_id} name:{h.name}")
        print()


def show_longest_streak_overall(service: HabitService):
    """Display all habits that share the longest streak across all habits."""
    habits = service.list_habits()
    if not habits:
        print("\n📊 No habits yet. Add some habits first.\n")
        return

    result = analytics_longest_streak_overall(habits)
    best_habits = result["habits"]
    streak = result["streak"]

    if not best_habits or streak == 0:
        print("\n📊 No streaks yet. Start completing your habits!\n")
        return

    print(f"\n📊 Longest streak (overall): {streak} periods\n")
    print("🏆 Habits with this streak:")

    for h in best_habits:
        print(f" • {h.name} (id:{h.habit_id}, period:{h.periodicity})")

    print()


def show_longest_streak_by_habit(service: HabitService):
    """Display the longest streak for a selected habit."""
    habits = service.list_habits()
    if not habits:
        print("\n📊 No habits yet.\n")
        return

    choices = [f"(id={h.habit_id}) {h.name}" for h in habits]
    habit_choice = questionary.select(
        "Select a habit:",
        choices=choices,
    ).ask()

    if not habit_choice:
        print("No habit selected.\n")
        return

    habit_id_str = habit_choice.split(")")[0].strip("(id=")
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        print("Invalid habit ID.\n")
        return

    streak = analytics_longest_streak_by_habit(habits, habit_id)
    if streak == 0:
        print(f"\n📊 Habit {habit_choice} has no streak yet.\n")
    else:
        print(f"\n📊 Longest streak for {habit_choice}: {streak} periods\n")
