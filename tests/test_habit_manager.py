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
        result = self.mgr.list_habits()

        # Should reflect current state and be a list
        assert isinstance(result, list)
        assert len(result) == 3