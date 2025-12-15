from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

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

# ---------------------------
# Current streak helpers
# ---------------------------
def _current_daily_streak(dates: list[date], *, today: date) -> int:
    """
    Current daily streak as of `today`.

    Rules:
    - If completed today: streak ends at today.
    - If not completed today but completed yesterday: streak ends at yesterday
      (still "alive" until you miss today).
    - Otherwise: 0
    """
    if not dates:
        return 0

    completed = set(dates)

    # Decide where the streak "ends" (the latest day that still keeps it alive).
    if today in completed:
        end = today
    elif (today - timedelta(days=1)) in completed:
        end = today - timedelta(days=1)
    else:
        return 0

    # Count backwards day-by-day.
    streak = 0
    cur = end
    while cur in completed:
        streak += 1
        cur -= timedelta(days=1)

    return streak


def _iso_week_key(d: date) -> tuple[int, int]:
    iso = d.isocalendar()
    return (iso.year, iso.week)


def _prev_iso_week(year: int, week: int) -> tuple[int, int]:
    """
    Return the previous ISO week key (year, week), handling year rollovers.
    """
    # Monday of the given ISO week
    monday = date.fromisocalendar(year, week, 1)
    prev_monday = monday - timedelta(days=7)
    iso = prev_monday.isocalendar()
    return (iso.year, iso.week)


def _current_weekly_streak(dates: list[date], *, today: date) -> int:
    """
    Current weekly streak as of `today` (ISO weeks).

    Rules:
    - If completed in this ISO week: streak ends at this week.
    - If not completed this week but completed last ISO week: streak ends at last week
      (still "alive" until you miss this week).
    - Otherwise: 0
    """
    if not dates:
        return 0

    completed_weeks = {_iso_week_key(d) for d in dates}

    this_week = _iso_week_key(today)
    last_week = _prev_iso_week(*this_week)

    if this_week in completed_weeks:
        end = this_week
    elif last_week in completed_weeks:
        end = last_week
    else:
        return 0

    # Count backwards week-by-week.
    streak = 0
    cur = end
    while cur in completed_weeks:
        streak += 1
        cur = _prev_iso_week(*cur)

    return streak

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

def calculate_current_streak(habit: Habit, *, today: Optional[date] = None) -> int:
    """
    Current streak for a habit based on its periodicity, relative to `today`.
    `today` is injectable for deterministic tests.
    """
    if not habit.completion_dates:
        return 0

    today = today or date.today()

    # Unique sorted dates (strip times)
    dates = sorted({dt.date() for dt in habit.completion_dates})

    if habit.periodicity.lower() == "weekly":
        return _current_weekly_streak(dates, today=today)
    else:
        return _current_daily_streak(dates, today=today)