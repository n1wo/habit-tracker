from datetime import datetime, timedelta

from habit_tracker.fixtures.example_data import ExampleDataFactory, EXAMPLE_HABIT_DEFS
from habit_tracker.fixtures.imperfect_data import MissingDayDataFactory


def test_example_factory_builds_perfect_daily_and_weekly_data() -> None:
    """
    ExampleDataFactory.build() should create a perfect, deterministic dataset.

    Verifies:
    - Number of generated habits matches EXAMPLE_HABIT_DEFS.
    - created_date equals the fixed start date for all habits.
    - completion_dates are datetime objects.
    - Daily habits: 28 completions (4 weeks × 7 days), perfectly consecutive.
    - Weekly habits: 4 completions (one per week), spaced 7 days apart.
    """
    factory = ExampleDataFactory(weeks=4)
    habits = factory.build()

    assert len(habits) == len(EXAMPLE_HABIT_DEFS)

    expected_start = datetime(2025, 1, 1, 8, 0, 0)

    for h in habits:
        assert h["created_date"] == expected_start

        dates = h["completion_dates"]
        assert all(isinstance(d, datetime) for d in dates)

        if h["periodicity"] == "daily":
            assert len(dates) == 28
            for i, d in enumerate(dates):
                assert d == expected_start + timedelta(days=i)

        elif h["periodicity"] == "weekly":
            assert len(dates) == 4
            for i, d in enumerate(dates):
                assert d == expected_start + timedelta(days=7 * i)

        else:
            raise AssertionError(f"Unexpected periodicity: {h['periodicity']}")


def test_example_factory_load_into_calls_storage_save_habit() -> None:
    """
    ExampleDataFactory.load_into(storage) should call storage.save_habit()
    once per generated habit and return the list of ids from the storage backend.
    """

    class DummyStorage:
        """Fake storage that records save_habit calls and returns auto-increment ids."""

        def __init__(self) -> None:
            self.saved: list[dict] = []

        def save_habit(self, habit_data: dict) -> int:
            self.saved.append(habit_data)
            return len(self.saved)  # simulate DB auto-increment

    store = DummyStorage()
    factory = ExampleDataFactory(weeks=4)

    ids = factory.load_into(store)

    assert len(store.saved) == len(EXAMPLE_HABIT_DEFS)
    assert len(ids) == len(EXAMPLE_HABIT_DEFS)
    assert ids == list(range(1, len(EXAMPLE_HABIT_DEFS) + 1))


def test_missing_day_factory_introduces_gaps_for_some_daily_habits_but_not_all() -> None:
    """
    MissingDayDataFactory should introduce imperfections for some daily habits
    while leaving at least one daily habit perfect and keeping weekly habits unchanged.

    Verifies:
    - Same number of habits as the perfect dataset.
    - Some daily habits have exactly one fewer completion.
    - At least one daily habit remains perfect.
    - For broken daily habits, a gap >= 2 days exists after sorting dates.
    - Weekly habits are unchanged.
    """
    perfect = ExampleDataFactory(weeks=4).build()
    imperfect = MissingDayDataFactory(weeks=4).build()

    assert len(perfect) == len(imperfect)

    daily_reduced = 0
    daily_unchanged = 0

    for h_perfect, h_imperfect in zip(perfect, imperfect):
        assert h_perfect["name"] == h_imperfect["name"]
        assert h_perfect["periodicity"] == h_imperfect["periodicity"]

        if h_perfect["periodicity"] == "daily":
            perfect_dates = h_perfect["completion_dates"]
            imperfect_dates = h_imperfect["completion_dates"]

            if len(imperfect_dates) == len(perfect_dates) - 1:
                daily_reduced += 1

                dates = sorted(imperfect_dates)
                gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                assert any(g >= 2 for g in gaps)  # confirms broken streak

            elif len(imperfect_dates) == len(perfect_dates):
                daily_unchanged += 1
                assert imperfect_dates == perfect_dates

            else:
                raise AssertionError("Daily habit has unexpected completion count.")

        else:
            # Weekly habits should be identical between perfect and imperfect sets.
            assert h_imperfect["completion_dates"] == h_perfect["completion_dates"]

    assert daily_reduced >= 1
    assert daily_unchanged >= 1
