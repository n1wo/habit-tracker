# tests/test_sql_store.py

from datetime import datetime, timedelta

import sqlite3
import pytest

from habit_tracker.storage import SQLStore


@pytest.fixture
def sql_store(tmp_path):
    """
    Create a fresh SQLStore using a temporary SQLite DB per test.
    This avoids touching the real 'habit_tracker.db'.
    """
    db_file = tmp_path / "test_habits.db"
    store = SQLStore(str(db_file))
    return store

def test_save_habit_and_load_without_completions(sql_store):
    created = datetime(2025, 1, 1, 8, 0, 0)

    habit_data = {
        "name": "Read",
        "description": "10 pages",
        "periodicity": "daily",
        "created_date": created,
        "completion_dates": [],
    }

    habit_id = sql_store.save_habit(habit_data)

    # habit_id should be an int and start at 1
    assert isinstance(habit_id, int)
    assert habit_id == 1

    habits = sql_store.load_habits()
    assert len(habits) == 1

    h = habits[0]
    assert h["id"] == habit_id
    assert h["name"] == "Read"
    assert h["description"] == "10 pages"
    assert h["periodicity"] == "daily"
    assert h["created_date"] == created
    assert h["completion_dates"] == []


def test_save_habit_with_completions_and_load(sql_store):
    created = datetime(2025, 1, 1, 8, 0, 0)
    c1 = created + timedelta(days=1)
    c2 = created + timedelta(days=2)

    habit_data = {
        "name": "Workout",
        "description": "30 min run",
        "periodicity": "daily",
        "created_date": created,
        "completion_dates": [c1, c2],
    }

    habit_id = sql_store.save_habit(habit_data)
    assert habit_id == 1

    habits = sql_store.load_habits()
    assert len(habits) == 1
    h = habits[0]

    assert h["id"] == habit_id
    assert h["name"] == "Workout"
    assert h["periodicity"] == "daily"
    assert h["created_date"] == created

    # completions should be restored as datetime objects in correct order
    assert h["completion_dates"] == [c1, c2]


def test_save_all_replaces_existing_data(sql_store):
    created = datetime(2025, 1, 1, 8, 0, 0)

    # first habit via save_habit
    sql_store.save_habit(
        {
            "name": "Old Habit",
            "description": "",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [],
        }
    )

    habits_before = sql_store.load_habits()
    assert len(habits_before) == 1
    assert habits_before[0]["name"] == "Old Habit"

    # now we replace with save_all
    new_habits = [
        {
            "name": "Read",
            "description": "10 pages",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [],
        },
        {
            "name": "Meditate",
            "description": "10 minutes",
            "periodicity": "weekly",
            "created_date": created,
            "completion_dates": [],
        },
    ]

    result = sql_store.save_all(new_habits)
    assert result is True

    habits_after = sql_store.load_habits()
    assert len(habits_after) == 2

    names = {h["name"] for h in habits_after}
    assert names == {"Read", "Meditate"}

    # Make sure "Old Habit" is gone
    assert "Old Habit" not in names


def test_delete_habit_removes_habit_and_tracking(sql_store):
    created = datetime(2025, 1, 1, 8, 0, 0)
    c1 = created + timedelta(days=1)

    # habit 1 with completion
    h1_id = sql_store.save_habit(
        {
            "name": "Read",
            "description": "",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [c1],
        }
    )

    # habit 2 without completion
    h2_id = sql_store.save_habit(
        {
            "name": "Workout",
            "description": "",
            "periodicity": "weekly",
            "created_date": created,
            "completion_dates": [],
        }
    )

    # both should be there
    habits = sql_store.load_habits()
    assert len(habits) == 2

    # delete habit 1
    ok = sql_store.delete_habit(h1_id)
    assert ok is True

    habits_after = sql_store.load_habits()
    assert len(habits_after) == 1
    assert habits_after[0]["id"] == h2_id
    assert habits_after[0]["name"] == "Workout"

    # Optional: check directly that tracking rows for h1 are gone
    conn = sqlite3.connect(sql_store._db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tracking WHERE habit_id = ?", (h1_id,))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_log_completion_appends_new_completion(sql_store):
    created = datetime(2025, 1, 1, 8, 0, 0)
    habit_data = {
        "name": "Read",
        "description": "10 pages",
        "periodicity": "daily",
        "created_date": created,
        "completion_dates": [],
    }

    habit_id = sql_store.save_habit(habit_data)

    when = created + timedelta(days=3)

    # call the method under test
    sql_store.log_completion(habit_id, when)

    habits = sql_store.load_habits()
    assert len(habits) == 1
    h = habits[0]

    assert h["id"] == habit_id
    assert len(h["completion_dates"]) == 1
    assert h["completion_dates"][0] == when
