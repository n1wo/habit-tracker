from datetime import datetime
from habit_tracker.models import Habit

def test_habit_init_defaults():
    h = Habit(
        habit_id=1,
        name="Read",
        periodicity="daily",
        created_date=datetime(2025, 1, 1, 12, 0, 0),
    )

    assert h.habit_id == 1
    assert h.name == "Read"
    assert h.periodicity == "daily"
    assert h.description is None
    assert h.completion_dates == []
    assert h.created_date == datetime(2025, 1, 1, 12, 0, 0)

def test_log_completion_appends_given_datetime():
    h = Habit(1, "Read", "daily", created_date=datetime(2025, 1, 1, 12, 0, 0))
    when = datetime(2025, 1, 2, 8, 30, 0)

    h.log_completion(when)

    assert len(h.completion_dates) == 1
    assert h.completion_dates[0] == when