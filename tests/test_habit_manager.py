from datetime import datetime
from habit_tracker.services import HabitManager

def test_add_habit_increments_id_and_stores():
    mgr = HabitManager()

    h1 = mgr.add_habit(name="Read", periodicity="daily", description="10 pages")
    h2 = mgr.add_habit(name="Workout", periodicity="weekly")

    # IDs increment
    assert h1.habit_id == 1
    assert h2.habit_id == 2

    # Stored correctly
    habits = mgr.list_habits()
    assert len(habits) == 2
    assert habits[0].name == "Read"
    assert habits[1].periodicity == "weekly"
    assert isinstance(habits[0].created_date, datetime)


def test_list_habits_returns_copy_like_list():
    mgr = HabitManager()
    mgr.add_habit("Meditate", "daily")
    result = mgr.list_habits()

    # Should reflect current state and be a list
    assert isinstance(result, list)
    assert len(result) == 1