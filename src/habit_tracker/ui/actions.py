"""
CLI helper functions for interacting with habits and analytics.

This module contains only user I/O and menu logic (questionary prompts + printing).
All business logic is delegated to the HabitService. Analytics are computed via
pure functions in habit_tracker.analytics.
"""

from typing import Optional

import questionary
from questionary import Choice

from habit_tracker.services import HabitService
from habit_tracker.analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    longest_streak_overall as analytics_longest_streak_overall,
    longest_streak_by_habit as analytics_longest_streak_by_habit,
    calculate_current_streak,
)


# ---------------------------------------------------------------------------
# Habit actions
# ---------------------------------------------------------------------------
def add_habit(service: HabitService) -> None:
    """Prompt the user for habit data and create a new habit."""
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

    description = questionary.text("Enter description (optional):").ask()

    habit = service.add_habit(
        name=name,
        periodicity=periodicity.lower(),
        description=description or None,
    )

    print(
        f"\n✅ Habit added: (id={habit.habit_id}) {habit.name} [{habit.periodicity}] "
        f"- {habit.description or 'No description'}\n"
    )


def remove_habit(service: HabitService) -> None:
    """Prompt the user to select and remove an existing habit."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to remove.\n")
        return

    choices = [
        Choice(title=f"(id={h.habit_id}) {h.name}", value=h.habit_id)
        for h in habits
    ]
    choices.append(Choice("Cancel", value=None))

    selected_id: Optional[int] = questionary.select(
        "Select a habit to remove:",
        choices=choices,
    ).ask()

    if selected_id is None:
        print("\n🔙 Cancelled.\n")
        return

    success = service.remove_habit(selected_id)
    if success:
        print(f"\n🗑️ Habit removed: (id={selected_id})\n")
    else:
        print("\n❌ Habit not found.\n")


def view_habits(service: HabitService) -> None:
    """View all habits and inspect completion history for a chosen habit."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits yet.\n")
        return

    all_habits = list_all_habits(habits)

    choices = [
        Choice(
            title=f"{h.habit_id}: {h.name} ({h.periodicity})",
            value=h.habit_id,
        )
        for h in all_habits
    ]
    choices.append(Choice("Cancel", value=None))

    selected_id: Optional[int] = questionary.select(
        "\n📋 All habits\nWhich habit do you want to inspect?",
        choices=choices,
        qmark="",
    ).ask()

    if selected_id is None:
        print("\n🔙 Returning...\n")
        return

    habit = next((h for h in all_habits if h.habit_id == selected_id), None)
    if habit is None:
        print("❌ Error: Habit not found.")
        return

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📌 Habit: {habit.name}")
    print(f"🆔 ID: {habit.habit_id}")
    print(f"🕒 Periodicity: {habit.periodicity}")
    print(f"📝 Description: {habit.description or '—'}")

    if habit.created_date is not None:
        print(f"📅 Created: {habit.created_date.strftime('%Y-%m-%d %H:%M')}")

    streak = analytics_longest_streak_by_habit(all_habits, habit.habit_id)
    print(f"🔥 Longest streak: {streak} period(s)")

    current = calculate_current_streak(habit)
    print(f"⚡ Current streak: {current} period(s)")

    print("\n✅ Completion dates:")
    if not habit.completion_dates:
        print("   — No completions yet —")
    else:
        for dt in sorted(habit.completion_dates):
            print(f"   • {dt.strftime('%Y-%m-%d %H:%M')}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def log_completion(service: HabitService) -> None:
    """Prompt the user to select a habit and log a completion event."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to log.\n")
        return

    choices = [
        Choice(title=f"(id={h.habit_id}) {h.name}", value=h.habit_id)
        for h in habits
    ]
    choices.append(Choice("Cancel", value=None))

    selected_id: Optional[int] = questionary.select(
        "Select a habit to log:",
        choices=choices,
    ).ask()

    if selected_id is None:
        print("\n🔙 Cancelled.\n")
        return

    success = service.log_completion(selected_id)
    if success:
        print(f"\n✅ Habit logged: (id={selected_id})\n")
        return

    # If not successful, try to distinguish why.
    exists = any(h.habit_id == selected_id for h in service.list_habits())
    if exists:
        print("\nℹ️ Habit already logged for this period.\n")
    else:
        print("\n❌ Habit not found.\n")


# ---------------------------------------------------------------------------
# Analytics wrappers
# ---------------------------------------------------------------------------
def list_daily_habits(service: HabitService) -> None:
    """List all habits with daily periodicity."""
    habits = service.list_habits()
    daily = list_habits_by_periodicity(habits, "daily")

    if not daily:
        print("\n📋 No daily habits found.\n")
        return

    print("\n📋 Daily habits:")
    for h in daily:
        print(f" • id:{h.habit_id} name:{h.name}")
    print()


def list_weekly_habits(service: HabitService) -> None:
    """List all habits with weekly periodicity."""
    habits = service.list_habits()
    weekly = list_habits_by_periodicity(habits, "weekly")

    if not weekly:
        print("\n📋 No weekly habits found.\n")
        return

    print("\n📋 Weekly habits:")
    for h in weekly:
        print(f" • id:{h.habit_id} name:{h.name}")
    print()


def show_longest_streak_overall(service: HabitService) -> None:
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


def show_longest_streak_by_habit(service: HabitService) -> None:
    """Display the longest streak for a selected habit."""
    habits = service.list_habits()
    if not habits:
        print("\n📊 No habits yet.\n")
        return

    choices = [
        Choice(title=f"(id={h.habit_id}) {h.name}", value=h.habit_id)
        for h in habits
    ]
    choices.append(Choice("Cancel", value=None))

    selected_id: Optional[int] = questionary.select(
        "Select a habit:",
        choices=choices,
    ).ask()

    if selected_id is None:
        print("\n🔙 Cancelled.\n")
        return

    streak = analytics_longest_streak_by_habit(habits, selected_id)
    if streak == 0:
        print(f"\n📊 Habit (id={selected_id}) has no streak yet.\n")
    else:
        print(f"\n📊 Longest streak for (id={selected_id}): {streak} periods\n")
