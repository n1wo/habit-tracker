from datetime import datetime
from habit_tracker.models import Habit

class TestHabit:
    """Unit tests for the Habit class."""

    def setup_method(self):
        """Setup a Habit instance before each test."""
        self.h = Habit(
            habit_id=1,
            name="Read",
            periodicity="daily",
            created_date=datetime(2025, 1, 1, 12, 0, 0),
        )


    def test_habit_init_defaults(self):
        """"Test initializing a Habit with default values."""

        assert self.h.habit_id == 1
        assert self.h.name == "Read"
        assert self.h.periodicity == "daily"
        assert self.h.description is None
        assert self.h.completion_dates == []
        assert self.h.created_date == datetime(2025, 1, 1, 12, 0, 0)

    def test_log_completion_appends_given_datetime(self):
        """Test that logging a completion appends the given datetime to completion_dates."""

        d1 = datetime(2025, 1, 2, 8, 30, 0)
        d2 = datetime(2025, 1, 3, 10, 15, 0)

        self.h.log_completion(d1)
        self.h.log_completion(d2)

        assert len(self.h.completion_dates) == 2
        assert self.h.completion_dates[0] == d1
        assert self.h.completion_dates[1] == d2