from datetime import datetime, timedelta
from habit_tracker.services import HabitManager
from habit_tracker.fixtures.predefined_habits import PREDEFINED_HABITS
from habit_tracker.fixtures.example_data import ExampleDataFactory, EXAMPLE_HABIT_DEFS

class TestHabitManager:
    """Unit tests for the HabitManager class."""

    def setup_method(self):
        """Setup a HabitManager instance before each test."""
        self.mgr = HabitManager()

        self.h1 = self.mgr.add_habit(name="Read", periodicity="daily", description="10 pages")
        self.h2 = self.mgr.add_habit(name="Workout", periodicity="weekly")
        self.h3 = self.mgr.add_habit(name="Meditate", periodicity="weekly", description="10 minutes")

    def test_add_habit_increments_id_and_stores(self):
        """Test that adding habits increments IDs and stores them correctly."""

        # IDs increment
        assert self.h1.habit_id == 1
        assert self.h2.habit_id == 2
        assert self.h3.habit_id == 3

        # Stored correctly
        habits = self.mgr.list_habits()
        assert len(habits) == 3
        assert habits[0].name == "Read"
        assert habits[1].periodicity == "weekly"
        assert habits[2].description == "10 minutes"
        assert isinstance(habits[0].created_date, datetime)

    def test_list_habits_returns_copy_like_list(self):
        """Test that listing habits returns a list reflecting current state."""

        result = self.mgr.list_habits()

        # Should reflect current state and be a list
        assert isinstance(result, list)
        assert len(result) == 3

    def test_remove_habit_by_id(self):
        """Test removing a habit by its ID."""

        # Remove existing habit
        success = self.mgr.remove_habit(habit_id=2)
        assert success is True

        habits = self.mgr.list_habits()
        assert len(habits) == 2
        assert all(h.habit_id != 2 for h in habits)

        # Attempt to remove non-existing habit
        success = self.mgr.remove_habit(habit_id=99)
        assert success is False

    def test_log_completion_delegates_to_habit(self):
        """HabitManager.log_completion should add a completion to the correct habit and return True."""

        when = datetime(2025, 1, 2, 8, 30, 0)

        result = self.mgr.log_completion(self.h1.habit_id, when=when)

        assert result is True
        assert len(self.h1.completion_dates) == 1
        assert self.h1.completion_dates[0] == when

    
    def test_log_completion_invalid_id_returns_false(self):
        """If the habit_id does not exist, log_completion should return False and not crash."""
        
        when = datetime(2025, 1, 2, 8, 30, 0)

        result = self.mgr.log_completion(999, when=when)

        assert result is False

    def test_daily_habit_cannot_be_completed_twice_same_day(self):
        """Daily habit: second completion on the same day should be rejected."""
        when_morning = datetime(2025, 1, 2, 8, 30, 0)
        when_evening = datetime(2025, 1, 2, 20, 0, 0)  # same calendar day

        result1 = self.mgr.log_completion(self.h1.habit_id, when=when_morning)
        result2 = self.mgr.log_completion(self.h1.habit_id, when=when_evening)

        assert result1 is True
        assert result2 is False

        # Only one completion stored
        assert len(self.h1.completion_dates) == 1
        assert self.h1.completion_dates[0] == when_morning

    def test_daily_habit_can_be_completed_on_multiple_days(self):
        """Daily habit: different days should both be allowed."""
        day1 = datetime(2025, 1, 2, 8, 30, 0)
        day2 = datetime(2025, 1, 3, 9, 0, 0)  # next calendar day

        result1 = self.mgr.log_completion(self.h1.habit_id, when=day1)
        result2 = self.mgr.log_completion(self.h1.habit_id, when=day2)

        assert result1 is True
        assert result2 is True

        assert len(self.h1.completion_dates) == 2
        assert self.h1.completion_dates[0] == day1
        assert self.h1.completion_dates[1] == day2

    def test_weekly_habit_cannot_be_completed_twice_same_week(self):
        """Weekly habit: multiple completions in the same ISO week should be rejected."""
        base = datetime(2025, 1, 6, 8, 0, 0)  # e.g. Monday
        same_week = base + timedelta(days=2)  # Wednesday of same ISO week

        result1 = self.mgr.log_completion(self.h2.habit_id, when=base)
        result2 = self.mgr.log_completion(self.h2.habit_id, when=same_week)

        assert result1 is True
        assert result2 is False

        assert len(self.h2.completion_dates) == 1
        assert self.h2.completion_dates[0] == base

    def test_weekly_habit_can_be_completed_in_different_weeks(self):
        """Weekly habit: completions in different ISO weeks should be allowed."""
        base = datetime(2025, 1, 6, 8, 0, 0)          # Monday, week X
        next_week = base + timedelta(days=7)          # Monday, week X+1

        result1 = self.mgr.log_completion(self.h2.habit_id, when=base)
        result2 = self.mgr.log_completion(self.h2.habit_id, when=next_week)

        assert result1 is True
        assert result2 is True

        assert len(self.h2.completion_dates) == 2
        assert self.h2.completion_dates[0] == base
        assert self.h2.completion_dates[1] == next_week

class TestHabitManagerWithExampleData:
    """
    Tests for HabitManager that use the perfect example dataset.

    The goal here is NOT to test the ExampleDataFactory itself (that has its
    own tests), but to verify that HabitManager can:
      • Ingest the generated example data correctly.
      • Preserve all completion dates for each habit.
      • Expose the same structure via list_habits() as the factory produces.
    """

    def setup_method(self):
        """
        Set up an in-memory HabitManager and populate it with the PERFECT
        example dataset from ExampleDataFactory.

        Steps:
        1. Create HabitManager with no storage backend (pure in-memory).
        2. Build the example habit dictionaries via ExampleDataFactory.
        3. For each habit dict:
           - Create a Habit inside the manager using add_habit()
             (letting HabitManager decide created_date itself).
           - Replay all completion_dates via log_completion().
        """
        # In-memory manager: we don't care about persistence in this test.
        self.mgr = HabitManager(storage=None)

        # Build the perfect 4-week dataset (already covered by its own tests).
        self.factory = ExampleDataFactory(weeks=4)
        self.example_dicts = self.factory.build()

        # Load the example data into HabitManager.
        for habit_dict in self.example_dicts:
            # Note: HabitManager.add_habit does NOT accept created_date,
            # so we only pass the supported arguments here.
            habit = self.mgr.add_habit(
                name=habit_dict["name"],
                periodicity=habit_dict["periodicity"],
                description=habit_dict["description"],
            )

            # Replay all completion timestamps onto the Habit instance.
            for dt in habit_dict["completion_dates"]:
                self.mgr.log_completion(habit.habit_id, when=dt)

    def test_manager_contains_all_example_habits(self):
        """
        Test that HabitManager ends up with exactly the same number of habits
        as defined by the example dataset.

        What we verify:
        • list_habits() returns one Habit per example habit.
        • Names from HabitManager and factory output are consistent.
        """
        habits = self.mgr.list_habits()

        # The manager should contain exactly all example habits.
        assert len(habits) == len(self.example_dicts)
        assert len(habits) == len(EXAMPLE_HABIT_DEFS)

        # Compare names to ensure the mapping is as expected.
        names_from_manager = sorted(h.name for h in habits)
        names_from_example = sorted(h["name"] for h in self.example_dicts)
        assert names_from_manager == names_from_example

    def test_completion_dates_match_example_dataset(self):
        """
        Test that completion_dates stored in HabitManager match the dates
        from the ExampleDataFactory exactly.

        What we verify:
        • For each habit name, the set of completion_dates in the manager
          equals the set produced by the factory.
        • No dates are lost, duplicated, or altered when passing through
          HabitManager's add_habit + log_completion logic.
        """
        habits = self.mgr.list_habits()

        # Build a helper mapping from habit name -> example dict.
        example_by_name = {h["name"]: h for h in self.example_dicts}

        for habit in habits:
            example = example_by_name[habit.name]

            # Convert both lists to sorted lists of datetime for comparison.
            manager_dates = sorted(habit.completion_dates)
            example_dates = sorted(example["completion_dates"])

            # All dates must be datetime instances.
            assert all(isinstance(d, datetime) for d in manager_dates)
            assert all(isinstance(d, datetime) for d in example_dates)

            # The manager must preserve exactly the same timestamps.
            assert manager_dates == example_dates

class TestHabitManagerPredefinedHabits:
    """
    Unit tests for seeding predefined habits into HabitManager.

    These tests verify that:
    • The predefined habit fixtures can be loaded into HabitManager.
    • Seeding uses the standard add_habit() API (no special cases).
    • Seeding is idempotent by default (no duplicate habits on re-run).
    • Optional forced seeding behaves as expected.

    Persistence is intentionally NOT tested here; all tests use an
    in-memory HabitManager (storage=None).
    """

    def setup_method(self):
        """
        Create a fresh in-memory HabitManager before each test.

        Using storage=None ensures that:
        • No database or filesystem is involved.
        • Tests remain fast and deterministic.
        • We only validate HabitManager behavior, not persistence.
        """
        self.mgr = HabitManager(storage=None)

    def test_seed_predefined_habits_creates_expected_habits(self):
        """
        Test that seeding predefined habits creates the expected number
        of Habit instances with correct attributes.

        Verifies:
        • seed_predefined_habits() returns the number of created habits.
        • list_habits() contains exactly one Habit per predefined fixture.
        • Habit attributes (name, periodicity, description) match the fixture data.
        """
        created = self.mgr.seed_predefined_habits()

        # Correct number of habits created
        assert created == len(PREDEFINED_HABITS)

        habits = self.mgr.list_habits()
        assert len(habits) == len(PREDEFINED_HABITS)

        # Compare habits by name to avoid ID ordering assumptions
        manager_by_name = {h.name: h for h in habits}

        for hdef in PREDEFINED_HABITS:
            assert hdef["name"] in manager_by_name

            habit = manager_by_name[hdef["name"]]
            assert habit.periodicity == hdef["periodicity"]

            # Description may be optional or empty
            expected_desc = hdef.get("description", "") or ""
            actual_desc = habit.description or ""
            assert actual_desc == expected_desc

    def test_seed_predefined_habits_is_idempotent(self):
        """
        Test that seeding predefined habits is idempotent by default.

        Running seed_predefined_habits() multiple times without force=True
        should:
        • Only create habits on the first call.
        • Return 0 on subsequent calls.
        • Leave the total habit count unchanged.
        """
        first = self.mgr.seed_predefined_habits()
        second = self.mgr.seed_predefined_habits()

        assert first == len(PREDEFINED_HABITS)
        assert second == 0
        assert len(self.mgr.list_habits()) == len(PREDEFINED_HABITS)

    def test_seed_predefined_habits_force_reseeds(self):
        """
        Test that force=True allows predefined habits to be re-seeded.

        This behavior is useful for:
        • Demo resets
        • Development/testing scenarios

        When force=True:
        • Predefined habits are added again even if they already exist.
        • The total number of habits increases accordingly.
        """
        self.mgr.seed_predefined_habits()

        created = self.mgr.seed_predefined_habits(force=True)

        assert created == len(PREDEFINED_HABITS)
        assert len(self.mgr.list_habits()) == 2 * len(PREDEFINED_HABITS)