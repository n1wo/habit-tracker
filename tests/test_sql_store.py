"""
Unit tests for the SQLStore persistence layer.

These tests verify that the SQLite-backed Storage implementation:
- Correctly persists and loads habits
- Handles completion events
- Replaces data when requested
- Cleans up related tracking rows on deletion

All tests use a temporary SQLite database to avoid touching real user data.
"""

from datetime import datetime, timedelta
import sqlite3

import pytest

from habit_tracker.storage import SQLStore


@pytest.fixture
def sql_store(tmp_path) -> SQLStore:
    """
    Provide a fresh SQLStore instance backed by a temporary SQLite database.

    Using tmp_path ensures:
    - Each test runs with an isolated database
    - No real application data is modified
    """
    db_file = tmp_path / "test_habits.db"
    return SQLStore(str(db_file))


def test_save_habit_and_load_without_completions(sql_store: SQLStore) -> None:
    """
    Saving a habit without completion dates should persist the habit correctly
    and load it back with an empty completion list.
    """
    created = datetime(2025, 1, 1, 8, 0, 0)

    habit_data = {
        "name": "Read",
        "description": "10 pages",
        "periodicity": "daily",
        "created_date": created,
        "completion_dates": [],
    }

    habit_id = sql_store.save_habit(habit_data)

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


def test_save_habit_with_completions_and_load(sql_store: SQLStore) -> None:
    """
    Saving a habit with completion dates should restore those completions
    as datetime objects in ascending order.
    """
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
    assert h["completion_dates"] == [c1, c2]


def test_save_all_replaces_existing_data(sql_store: SQLStore) -> None:
    """
    save_all() should remove all existing habits and tracking data
    and replace them with the provided dataset.
    """
    created = datetime(2025, 1, 1, 8, 0, 0)

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

    assert sql_store.save_all(new_habits) is True

    habits_after = sql_store.load_habits()
    assert len(habits_after) == 2

    names = {h["name"] for h in habits_after}
    assert names == {"Read", "Meditate"}
    assert "Old Habit" not in names


def test_delete_habit_removes_habit_and_tracking(sql_store: SQLStore) -> None:
    """
    Deleting a habit should:
    - Remove the habit from the habits table
    - Remove all associated tracking rows
    """
    created = datetime(2025, 1, 1, 8, 0, 0)
    c1 = created + timedelta(days=1)

    h1_id = sql_store.save_habit(
        {
            "name": "Read",
            "description": "",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [c1],
        }
    )

    h2_id = sql_store.save_habit(
        {
            "name": "Workout",
            "description": "",
            "periodicity": "weekly",
            "created_date": created,
            "completion_dates": [],
        }
    )

    assert len(sql_store.load_habits()) == 2

    assert sql_store.delete_habit(h1_id) is True

    habits_after = sql_store.load_habits()
    assert len(habits_after) == 1
    assert habits_after[0]["id"] == h2_id
    assert habits_after[0]["name"] == "Workout"

    # Direct DB check: tracking rows must be gone
    with sqlite3.connect(str(sql_store._db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracking WHERE habit_id = ?", (h1_id,))
        count = cursor.fetchone()[0]

    assert count == 0


def test_log_completion_appends_new_completion(sql_store: SQLStore) -> None:
    """
    log_completion() should append a new completion event
    to an existing habit without overwriting previous data.
    """
    created = datetime(2025, 1, 1, 8, 0, 0)

    habit_id = sql_store.save_habit(
        {
            "name": "Read",
            "description": "10 pages",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [],
        }
    )

    when = created + timedelta(days=3)

    sql_store.log_completion(habit_id, when)

    habits = sql_store.load_habits()
    assert len(habits) == 1
    assert habits[0]["completion_dates"] == [when]
