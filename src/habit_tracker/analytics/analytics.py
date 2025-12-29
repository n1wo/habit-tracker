"""
Functional analytics for the Habit Tracker app.

This module contains pure functions that operate on Habit data and return
computed results (no I/O, no persistence, no mutation of inputs).

Key features:
- List habits (all / by periodicity)
- Compute longest streak (per habit / overall)
- Compute current streak (per habit), with injectable "today" for testing

Streak rules:
- Daily streaks use consecutive calendar days.
- Weekly streaks use consecutive ISO weeks (year/week), handling year rollovers.
"""

from datetime import date, timedelta
from collections.abc import Iterable
from typing import Any, Optional

from habit_tracker.models import Habit


# ----------------------------------------------------------------------
# Basic list operations
# ----------------------------------------------------------------------
def list_all_habits(habits: Iterable[Habit]) -> list[Habit]:
    """
    Return all habits as a new list.

    This function is pure: it does not mutate the input iterable.
    """
    return list(habits)


def list_habits_by_periodicity(habits: Iterable[Habit], periodicity: str) -> list[Habit]:
    """
    Filter habits by periodicity (case-insensitive).

    Args:
        habits: An iterable of Habit objects.
        periodicity: The periodicity string to filter by (e.g. "daily", "weekly").

    Returns:
        A list of habits whose periodicity matches the given value.
    """
    p = periodicity.lower()
    return [h for h in habits if h.periodicity.lower() == p]


# ----------------------------------------------------------------------
# Longest streak calculation helpers
# ----------------------------------------------------------------------
def _longest_daily_streak(dates: list[date]) -> int:
    """
    Return the longest run of consecutive calendar days.

    Args:
        dates: Sorted list of unique completion dates (date objects).

    Returns:
        The maximum consecutive-day streak length.
    """
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
    """
    Return the longest run of consecutive ISO weeks.

    Args:
        dates: Sorted list of unique completion dates (date objects).

    Returns:
        The maximum consecutive-week streak length, measured in ISO weeks.
    """
    if not dates:
        return 0

    # Convert to unique (year, week) pairs.
    weeks = sorted({(d.isocalendar().year, d.isocalendar().week) for d in dates})

    longest = 1
    current = 1

    for (y1, w1), (y2, w2) in zip(weeks, weeks[1:]):
        # Consecutive weeks, including year rollover (week 52/53 -> week 1).
        if (y2 == y1 and w2 == w1 + 1) or (y2 == y1 + 1 and w1 in (52, 53) and w2 == 1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


# ----------------------------------------------------------------------
# Current streak helpers
# ----------------------------------------------------------------------
def _current_daily_streak(dates: list[date], *, today: date) -> int:
    """
    Return the current daily streak as of `today`.

    "Current streak" means the streak is still alive:
    - If completed today: streak ends at today.
    - Else if completed yesterday: streak ends at yesterday (still alive today).
    - Else: streak is broken => 0.

    Args:
        dates: Sorted list of unique completion dates.
        today: Reference date (injectable for deterministic tests).

    Returns:
        Current daily streak length.
    """
    if not dates:
        return 0

    completed = set(dates)

    if today in completed:
        end = today
    elif (today - timedelta(days=1)) in completed:
        end = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    cur = end
    while cur in completed:
        streak += 1
        cur -= timedelta(days=1)

    return streak


def _iso_week_key(d: date) -> tuple[int, int]:
    """Return an ISO week key as (year, week)."""
    iso = d.isocalendar()
    return (iso.year, iso.week)


def _prev_iso_week(year: int, week: int) -> tuple[int, int]:
    """
    Return the previous ISO week key (year, week), handling year rollovers.

    Args:
        year: ISO year.
        week: ISO week number.

    Returns:
        The ISO (year, week) of the previous week.
    """
    monday = date.fromisocalendar(year, week, 1)
    prev_monday = monday - timedelta(days=7)
    iso = prev_monday.isocalendar()
    return (iso.year, iso.week)


def _current_weekly_streak(dates: list[date], *, today: date) -> int:
    """
    Return the current weekly streak as of `today` (ISO weeks).

    "Current streak" means the streak is still alive:
    - If completed in this ISO week: streak ends at this week.
    - Else if completed last ISO week: streak ends at last week (still alive).
    - Else: streak is broken => 0.

    Args:
        dates: Sorted list of unique completion dates.
        today: Reference date (injectable for deterministic tests).

    Returns:
        Current weekly streak length (in ISO weeks).
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

    streak = 0
    cur = end
    while cur in completed_weeks:
        streak += 1
        cur = _prev_iso_week(*cur)

    return streak


# ----------------------------------------------------------------------
# Public streak API
# ----------------------------------------------------------------------
def calculate_streak(habit: Habit) -> int:
    """
    Calculate the longest streak for a habit based on its periodicity.

    Args:
        habit: Habit object containing periodicity and completion timestamps.

    Returns:
        The longest streak length for the habit.
    """
    if not habit.completion_dates:
        return 0

    # Unique sorted dates (strip time).
    dates = sorted({dt.date() for dt in habit.completion_dates})

    if habit.periodicity.lower() == "weekly":
        return _longest_weekly_streak(dates)

    return _longest_daily_streak(dates)


def longest_streak_overall(habits: Iterable[Habit]) -> dict[str, Any]:
    """
    Return all habits that share the longest overall streak.

    Args:
        habits: An iterable of Habit objects.

    Returns:
        A dictionary:
            {
              "habits": list[Habit],  # all habits with the longest streak
              "streak": int           # the longest streak value
            }
    """
    longest = 0
    best: list[Habit] = []

    for habit in habits:
        streak = calculate_streak(habit)

        if streak > longest:
            longest = streak
            best = [habit]
        elif streak == longest and streak > 0:
            best.append(habit)

    return {"habits": best, "streak": longest}


def longest_streak_by_habit(habits: Iterable[Habit], habit_id: int) -> int:
    """
    Return the longest streak for a specific habit identified by habit_id.

    Args:
        habits: Iterable of Habit objects.
        habit_id: The habit identifier.

    Returns:
        The longest streak for the selected habit, or 0 if not found.
    """
    habit = next((h for h in habits if h.habit_id == habit_id), None)
    return calculate_streak(habit) if habit else 0


def calculate_current_streak(habit: Habit, *, today: Optional[date] = None) -> int:
    """
    Calculate the current (still-alive) streak for a habit.

    This differs from `calculate_streak` which returns the *maximum historical*
    streak. Current streak is computed relative to `today` and supports injection
    for deterministic tests.

    Args:
        habit: Habit object to evaluate.
        today: Reference date. Defaults to `date.today()` if not provided.

    Returns:
        Current streak length based on periodicity.
    """
    if not habit.completion_dates:
        return 0

    today = today or date.today()
    dates = sorted({dt.date() for dt in habit.completion_dates})

    if habit.periodicity.lower() == "weekly":
        return _current_weekly_streak(dates, today=today)

    return _current_daily_streak(dates, today=today)
