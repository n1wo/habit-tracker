from datetime import datetime

from habit_tracker.models import Habit


class TestHabit:
    """Unit tests for the Habit model."""

    def setup_method(self) -> None:
        """Create a Habit instance before each test."""
        self.created = datetime(2025, 1, 1, 12, 0, 0)
        self.h = Habit(
            habit_id=1,
            name="Read",
            periodicity="daily",
            created_date=self.created,
        )

    def test_habit_init_defaults(self) -> None:
        """Test initializing a Habit with default values."""
        assert self.h.habit_id == 1
        assert self.h.name == "Read"
        assert self.h.periodicity == "daily"
        assert self.h.description is None
        assert self.h.completion_dates == []
        assert self.h.created_date == self.created

    def test_log_completion_appends_given_datetime(self) -> None:
        """Logging a completion should append the datetime to completion_dates."""
        d1 = datetime(2025, 1, 2, 8, 30, 0)
        d2 = datetime(2025, 1, 3, 10, 15, 0)

        self.h.log_completion(d1)
        self.h.log_completion(d2)

        assert self.h.completion_dates == [d1, d2]

    def test_repr_contains_key_fields(self) -> None:
        """__repr__ should include id, name, and periodicity for debugging."""
        rep = repr(self.h)
        assert "Habit(" in rep
        assert "id=1" in rep
        assert "Read" in rep
        assert "daily" in rep
