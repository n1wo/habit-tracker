from datetime import datetime, timedelta, date

from habit_tracker.models import Habit
from habit_tracker.fixtures.example_data import ExampleDataFactory
from habit_tracker.fixtures.imperfect_data import MissingDayDataFactory
from habit_tracker.analytics import (
    list_all_habits,
    list_habits_by_periodicity,
    calculate_streak,
    longest_streak_overall,
    longest_streak_by_habit,
    calculate_current_streak,
)


class TestAnalytics:
    """Unit tests for the pure functional analytics module."""

    def setup_method(self) -> None:
        """Set up common base datetimes for deterministic tests."""
        self.created = datetime(2025, 1, 1, 8, 0, 0)
        self.base = datetime(2025, 1, 1, 8, 0, 0)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _make_habit(
        self,
        habit_id: int,
        name: str,
        periodicity: str,
        completion_dates: list[datetime] | None = None,
    ) -> Habit:
        """
        Helper to build Habit instances for analytics tests.

        Args:
            habit_id: Unique habit identifier.
            name: Habit name.
            periodicity: "daily" or "weekly".
            completion_dates: Optional list of completion datetimes.

        Returns:
            A Habit instance suitable for analytics.
        """
        return Habit(
            habit_id=habit_id,
            name=name,
            periodicity=periodicity,
            created_date=self.created,
            description=None,
            completion_dates=completion_dates or [],
        )

    # ------------------------------------------------------------------
    # list_all_habits / list_habits_by_periodicity
    # ------------------------------------------------------------------
    def test_list_all_habits_returns_copy(self) -> None:
        h1 = self._make_habit(1, "Read", "daily")
        h2 = self._make_habit(2, "Workout", "weekly")

        habits = [h1, h2]
        result = list_all_habits(habits)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] is h1
        assert result[1] is h2
        # defensive copy, not the same list object
        assert result is not habits

    def test_list_habits_by_periodicity_filters_case_insensitively(self) -> None:
        h1 = self._make_habit(1, "Read", "daily")
        h2 = self._make_habit(2, "Workout", "weekly")
        h3 = self._make_habit(3, "Meditate", "DAILY")

        habits = [h1, h2, h3]

        daily = list_habits_by_periodicity(habits, "daily")
        weekly = list_habits_by_periodicity(habits, "weekly")

        assert {h.habit_id for h in daily} == {1, 3}
        assert {h.habit_id for h in weekly} == {2}

    # ------------------------------------------------------------------
    # calculate_streak – daily habits
    # ------------------------------------------------------------------
    def test_calculate_streak_daily_no_completions_is_zero(self) -> None:
        h = self._make_habit(1, "Read", "daily", completion_dates=[])
        assert calculate_streak(h) == 0

    def test_calculate_streak_daily_consecutive_days(self) -> None:
        base = self.base
        completions = [
            base,
            base + timedelta(days=1),
            base + timedelta(days=2),
            base + timedelta(days=3),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_streak(h) == 4  # 4 consecutive days

    def test_calculate_streak_daily_with_gaps_takes_longest_run(self) -> None:
        base = self.base
        completions = [
            base,                           # day 1
            base + timedelta(days=2),       # day 3 (gap)
            base + timedelta(days=3),       # day 4
            base + timedelta(days=4),       # day 5
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        # longest run is days 3–5 → length 3
        assert calculate_streak(h) == 3

    def test_calculate_streak_daily_multiple_completions_same_day_collapsed(self) -> None:
        base = self.base
        completions = [
            base,
            base.replace(hour=12),
            base.replace(hour=20),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        # still only 1 day of completion
        assert calculate_streak(h) == 1

    # ------------------------------------------------------------------
    # calculate_streak – weekly habits
    # ------------------------------------------------------------------
    def test_calculate_streak_weekly_no_completions_is_zero(self) -> None:
        h = self._make_habit(1, "Workout", "weekly", completion_dates=[])
        assert calculate_streak(h) == 0

    def test_calculate_streak_weekly_consecutive_weeks(self) -> None:
        # Use Mondays to keep ISO weeks simple
        week1 = datetime(2025, 1, 6, 8, 0, 0)           # ISO week 2
        week2 = week1 + timedelta(days=7)               # ISO week 3
        week3 = week2 + timedelta(days=7)               # ISO week 4

        completions = [week1, week2, week3]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        assert calculate_streak(h) == 3  # 3 consecutive ISO weeks

    def test_calculate_streak_weekly_with_gap_takes_longest_run(self) -> None:
        week1 = datetime(2025, 1, 6, 8, 0, 0)           # week 2
        week2 = week1 + timedelta(days=7)               # week 3
        week3 = week2 + timedelta(days=14)              # skip one → week 5

        completions = [week1, week2, week3]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        # longest run is weeks 2–3 → length 2
        assert calculate_streak(h) == 2

    def test_calculate_streak_weekly_multiple_completions_same_week_collapsed(self) -> None:
        week1_mon = datetime(2025, 1, 6, 8, 0, 0)       # Monday
        week1_wed = week1_mon + timedelta(days=2)       # Wednesday same ISO week

        completions = [week1_mon, week1_wed]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        # still only 1 week of completion
        assert calculate_streak(h) == 1

    # ------------------------------------------------------------------
    # longest_streak_overall / longest_streak_by_habit
    # ------------------------------------------------------------------
    def test_longest_streak_overall_returns_all_habits_with_same_max_streak(self) -> None:
        """
        Use ExampleDataFactory to create a perfect dataset.

        All daily habits (with a 28-day streak) should tie for longest streak.
        """
        factory = ExampleDataFactory(start_date=self.base, weeks=4)
        habit_dicts = factory.build()

        habits: list[Habit] = []
        for i, d in enumerate(habit_dicts, start=1):
            habits.append(
                Habit(
                    habit_id=i,
                    name=d["name"],
                    periodicity=d["periodicity"],
                    created_date=d["created_date"],
                    description=d["description"],
                    completion_dates=d["completion_dates"],
                )
            )

        result = longest_streak_overall(habits)

        expected_streak = factory.weeks * 7  # 4 weeks * 7 days = 28
        assert result["streak"] == expected_streak

        best_habits = result["habits"]
        assert len(best_habits) > 1
        assert all(h.periodicity == "daily" for h in best_habits)

        expected_daily_names = {
            d["name"] for d in habit_dicts if d["periodicity"] == "daily"
        }
        assert {h.name for h in best_habits} == expected_daily_names

    def test_longest_streak_overall_with_no_habits_returns_zero_and_empty_list(self) -> None:
        result = longest_streak_overall([])
        assert result["streak"] == 0
        assert result["habits"] == []

    def test_longest_streak_by_habit_returns_zero_for_unknown_id(self) -> None:
        base = self.base
        h1 = self._make_habit(
            1,
            "Read",
            "daily",
            completion_dates=[base, base + timedelta(days=1)],
        )

        streak = longest_streak_by_habit([h1], habit_id=999)
        assert streak == 0

    def test_longest_streak_by_habit_matches_calculate_streak(self) -> None:
        base = self.base
        completions = [
            base,
            base + timedelta(days=1),
            base + timedelta(days=2),
        ]
        h1 = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert longest_streak_by_habit([h1], habit_id=1) == calculate_streak(h1)

    def test_missing_day_factory_results_in_single_max_streak_winner(self) -> None:
        """
        Using MissingDayDataFactory, some daily habits are broken, but one
        daily habit should still have the maximum streak (28 days).
        """
        factory = MissingDayDataFactory(start_date=self.base, weeks=4)
        habit_dicts = factory.build()

        habits: list[Habit] = []
        for i, d in enumerate(habit_dicts, start=1):
            habits.append(
                Habit(
                    habit_id=i,
                    name=d["name"],
                    periodicity=d["periodicity"],
                    created_date=d["created_date"],
                    description=d["description"],
                    completion_dates=d["completion_dates"],
                )
            )

        result = longest_streak_overall(habits)

        expected_streak = factory.weeks * 7  # 28 for daily
        assert result["streak"] == expected_streak

        best_habits = result["habits"]
        assert len(best_habits) == 1  # unique winner

        winner = best_habits[0]
        assert winner.periodicity == "daily"

        daily_habits = [h for h in habits if h.periodicity == "daily"]
        assert len(daily_habits) >= 2

        assert any(
            calculate_streak(h) < expected_streak
            for h in daily_habits
            if h is not winner
        )

    # ------------------------------------------------------------------
    # calculate_current_streak – daily habits
    # ------------------------------------------------------------------
    def test_current_streak_daily_no_completions_is_zero(self) -> None:
        h = self._make_habit(1, "Read", "daily", completion_dates=[])
        today = date(2025, 1, 10)

        assert calculate_current_streak(h, today=today) == 0

    def test_current_streak_daily_counts_back_from_today_if_completed_today(self) -> None:
        completions = [
            datetime(2025, 1, 8, 8, 0, 0),
            datetime(2025, 1, 9, 8, 0, 0),
            datetime(2025, 1, 10, 8, 0, 0),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 10)) == 3

    def test_current_streak_daily_counts_back_from_yesterday_if_not_done_today(self) -> None:
        completions = [
            datetime(2025, 1, 7, 8, 0, 0),
            datetime(2025, 1, 8, 8, 0, 0),
            datetime(2025, 1, 9, 8, 0, 0),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 10)) == 3

    def test_current_streak_daily_is_zero_if_missed_yesterday_and_today(self) -> None:
        completions = [
            datetime(2025, 1, 7, 8, 0, 0),
            datetime(2025, 1, 8, 8, 0, 0),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 10)) == 0

    def test_current_streak_daily_multiple_completions_same_day_collapsed(self) -> None:
        completions = [
            datetime(2025, 1, 10, 8, 0, 0),
            datetime(2025, 1, 10, 12, 0, 0),
            datetime(2025, 1, 10, 20, 0, 0),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 10)) == 1

    def test_current_streak_daily_ignores_old_longest_if_current_is_broken(self) -> None:
        completions = [
            datetime(2025, 1, 1, 8, 0, 0),
            datetime(2025, 1, 2, 8, 0, 0),
            datetime(2025, 1, 3, 8, 0, 0),
        ]
        h = self._make_habit(1, "Read", "daily", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 10)) == 0

    # ------------------------------------------------------------------
    # calculate_current_streak – weekly habits (ISO weeks)
    # ------------------------------------------------------------------
    def test_current_streak_weekly_no_completions_is_zero(self) -> None:
        h = self._make_habit(1, "Workout", "weekly", completion_dates=[])
        today = date(2025, 1, 15)

        assert calculate_current_streak(h, today=today) == 0

    def test_current_streak_weekly_counts_if_completed_this_week(self) -> None:
        completions = [
            datetime(2025, 1, 6, 8, 0, 0),   # week 2
            datetime(2025, 1, 13, 8, 0, 0),  # week 3
        ]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 15)) == 2

    def test_current_streak_weekly_counts_back_from_last_week_if_not_done_this_week(self) -> None:
        completions = [
            datetime(2025, 1, 6, 8, 0, 0),   # week 2
            datetime(2025, 1, 13, 8, 0, 0),  # week 3
        ]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 22)) == 2

    def test_current_streak_weekly_is_zero_if_missed_last_week_and_this_week(self) -> None:
        completions = [
            datetime(2025, 1, 6, 8, 0, 0),  # week 2
        ]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 22)) == 0

    def test_current_streak_weekly_multiple_completions_same_week_collapsed(self) -> None:
        completions = [
            datetime(2025, 1, 13, 8, 0, 0),   # Monday (week 3)
            datetime(2025, 1, 15, 8, 0, 0),   # Wednesday (week 3)
        ]
        h = self._make_habit(1, "Workout", "weekly", completion_dates=completions)

        assert calculate_current_streak(h, today=date(2025, 1, 15)) == 1
