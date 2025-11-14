from datetime import datetime
from habit_tracker.services import HabitManager

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