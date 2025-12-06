
from __future__ import annotations

from datetime import date, timedelta
from collections.abc import Iterable
from typing import Any

from habit_tracker.models import Habit

# ----------------------------------------------------------------------
# Basic list operations
# ----------------------------------------------------------------------
def list_all_habits(habits: Iterable[Habit]) -> list[Habit]:
    """Return all habits as a new list (pure, no mutation)."""
    return list(habits)


def list_habits_by_periodicity(
    habits: Iterable[Habit],
    periodicity: str,
) -> list[Habit]:
    """Return habits filtered by periodicity (case-insensitive)."""
    p = periodicity.lower()
    return [h for h in habits if h.periodicity.lower() == p]

# ----------------------------------------------------------------------
# Streak calculation helpers
# ----------------------------------------------------------------------
def _longest_daily_streak(dates: list[date]) -> int:
    """Return the longest run of consecutive calendar days."""
    if not dates:
        return 0

    longest = 1
    current = 1

    for prev, curr in zip(dates, dates[1:]):
        if curr == prev + timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def _longest_weekly_streak(dates: list[date]) -> int:
    """Return the longest run of consecutive ISO weeks."""
    if not dates:
        return 0

    # Convert to unique (year, week) pairs
    weeks = sorted({(d.isocalendar().year, d.isocalendar().week) for d in dates})

    longest = 1
    current = 1

    for (y1, w1), (y2, w2) in zip(weeks, weeks[1:]):
        # Consecutive weeks, including year rollover
        if (y2 == y1 and w2 == w1 + 1) or (y2 == y1 + 1 and w1 in (52, 53) and w2 == 1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest

# ----------------------------------------------------------------------
# Public streak API
# ----------------------------------------------------------------------
def calculate_streak(habit) -> int:
    """Calculate the longest streak for a habit based on its periodicity."""
    if not habit.completion_dates:
        return 0

    # Unique sorted dates
    dates = sorted({dt.date() for dt in habit.completion_dates})

    if habit.periodicity.lower() == "weekly":
        return _longest_weekly_streak(dates)
    else:
        return _longest_daily_streak(dates)


def longest_streak_overall(habits: Iterable[Habit]) -> dict[str, Any]:
    """
    Return ALL habits that share the longest overall streak.

    Returns:
        {
            "habits": list[Habit],   # all habits with longest streak
            "streak": int            # the streak value
        }
    """
    longest_streak = 0
    best_habits: list[Habit] = []

    for habit in habits:
        streak = calculate_streak(habit)

        if streak > longest_streak:
            # Found a new maximum — reset the list
            longest_streak = streak
            best_habits = [habit]

        elif streak == longest_streak and streak > 0:
            # Same as current max — append
            best_habits.append(habit)

    return {
        "habits": best_habits,
        "streak": longest_streak,
    }

def longest_streak_by_habit(habits: list, habit_id: int) -> int:
    habit = next((h for h in habits if h.habit_id == habit_id), None)
    if habit is None:
        return 0
    return calculate_streak(habit)