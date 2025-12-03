from datetime import datetime, timedelta

from habit_tracker.fixtures.example_data import ExampleDataFactory, EXAMPLE_HABIT_DEFS
from habit_tracker.fixtures.imperfect_data import MissingDayDataFactory


def test_example_factory_builds_perfect_daily_and_weekly_data():
    """
    Test that ExampleDataFactory.build() creates a PERFECT example dataset.

    What we verify:

    • The number of generated habits matches the predefined definitions.
    • All created_date values match the expected fixed start date.
    • All completion_dates are valid datetime objects.
    • Daily habits have 28 completions (4 weeks × 7 days), perfectly consecutive.
    • Weekly habits have 4 completions (1 per week), perfectly spaced 7 days apart.

    This ensures the perfect sample dataset acts as a stable baseline for analytics.
    """

    factory = ExampleDataFactory(weeks=4)
    habits = factory.build()

    # The number of returned habits must match the predefined example habit definitions.
    assert len(habits) == len(EXAMPLE_HABIT_DEFS)

    expected_start = datetime(2025, 1, 1, 8, 0, 0)

    for h in habits:
        # All habits must use the same deterministic anchor date.
        assert h["created_date"] == expected_start

        dates = h["completion_dates"]

        # All completion timestamps must be datetime objects.
        assert all(isinstance(d, datetime) for d in dates)

        if h["periodicity"] == "daily":
            # Daily habits must have a perfect 28-day streak.
            assert len(dates) == 28

            # Every entry must be exactly one day apart from the previous.
            for i, d in enumerate(dates):
                assert d == expected_start + timedelta(days=i)

        elif h["periodicity"] == "weekly":
            # Weekly habits must have a perfect 4-week streak.
            assert len(dates) == 4

            # Each completion must be exactly 7 days apart.
            for i, d in enumerate(dates):
                assert d == expected_start + timedelta(days=7 * i)

        else:
            # No other periodicities should exist in test data.
            raise AssertionError(f"Unexpected periodicity in test: {h['periodicity']}")


def test_example_factory_load_into_calls_storage_save_habit():
    """
    Test that ExampleDataFactory.load_into(storage) correctly forwards all
    generated habit dicts into the storage backend.

    We simulate a storage backend using a DummyStorage object that simply records
    every call to save_habit.

    What we verify:

    • save_habit is called once per generated habit.
    • load_into returns incrementing IDs (1..N), matching DB-like behavior.
    """

    class DummyStorage:
        """A fake storage class that records calls to save_habit."""
        def __init__(self):
            self.saved = []

        def save_habit(self, habit_data):
            self.saved.append(habit_data)
            # Simulate a DB auto-increment ID
            return len(self.saved)

    store = DummyStorage()
    factory = ExampleDataFactory(weeks=4)

    # load_into() internally calls .build() and then save_habit() for each habit.
    ids = factory.load_into(store)

    # Ensure save_habit was called exactly once per defined habit.
    assert len(store.saved) == len(EXAMPLE_HABIT_DEFS)
    assert len(ids) == len(EXAMPLE_HABIT_DEFS)

    # The IDs returned must match the auto-increment behavior 1..N.
    assert ids == list(range(1, len(EXAMPLE_HABIT_DEFS) + 1))


def test_missing_day_factory_removes_one_day_from_each_daily_habit():
    """
    Test that MissingDayDataFactory correctly introduces an imperfection
    (a missing daily completion) while keeping weekly habits unchanged.

    What we verify:

    • The imperfect dataset has the same number of habits as the perfect dataset.
    • Daily habits have exactly ONE fewer completion than the perfect version.
    • The removed date produces a gap > 1 day (a broken streak).
    • Weekly habits remain untouched.

    This test ensures that imperfect datasets reliably simulate streak breaks.
    """

    # Build a baseline perfect dataset.
    base_factory = ExampleDataFactory(weeks=4)
    perfect = base_factory.build()

    # Build the imperfect dataset that should have one removed day.
    imperfect_factory = MissingDayDataFactory(weeks=4)
    imperfect = imperfect_factory.build()

    # Number of habits must remain identical.
    assert len(perfect) == len(imperfect)

    for h_perfect, h_imperfect in zip(perfect, imperfect):

        # Names and periodicity must not change.
        assert h_perfect["name"] == h_imperfect["name"]
        assert h_perfect["periodicity"] == h_imperfect["periodicity"]

        if h_perfect["periodicity"] == "daily":
            # Imperfect daily habits must have one missing completion date.
            assert len(h_imperfect["completion_dates"]) == len(h_perfect["completion_dates"]) - 1

            # Sort dates and detect the gap introduced by deletion.
            dates = sorted(h_imperfect["completion_dates"])
            gaps = [
                (dates[i + 1] - dates[i]).days
                for i in range(len(dates) - 1)
            ]

            # At least one gap must be >= 2 days → confirms a break in streak.
            assert max(gaps) >= 2

        else:
            # Weekly habits should remain identical between perfect and imperfect sets.
            assert h_imperfect["completion_dates"] == h_perfect["completion_dates"]
