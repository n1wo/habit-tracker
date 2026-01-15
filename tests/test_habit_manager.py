"""
Unit tests for the HabitManager service layer.

These tests validate HabitManager behavior in two modes:
1) Pure in-memory mode (storage=None)
2) Persistence-backed mode using a lightweight in-memory Storage stub

Focus:
- ID assignment rules (in-memory counter vs DB-returned ids)
- Removal and write-through persistence calls
- Periodicity enforcement (daily vs weekly)
- Loading habits from storage on startup
- Seeding predefined habits (non-forced vs forced)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

from habit_tracker.services.habit_manager import HabitManager
from habit_tracker.models import Habit


@dataclass
class SpyStorage:
    """
    Minimal in-memory Storage double used for HabitManager unit tests.

    - Stores habits as list[dict] in the same shape SQLStore uses.
    - Tracks calls to save_habit/delete_habit/log_completion/save_all.
    - Implements user methods only to satisfy the Storage interface.
    """

    # persisted habit dicts (as Storage would return them)
    habits: List[Dict[str, Any]] = field(default_factory=list)

    # call tracking
    save_habit_calls: List[Dict[str, Any]] = field(default_factory=list)
    delete_habit_calls: List[int] = field(default_factory=list)
    log_completion_calls: List[tuple[int, datetime]] = field(default_factory=list)
    save_all_calls: List[List[Dict[str, Any]]] = field(default_factory=list)

    # simple auto-increment behavior
    _next_id: int = 1

    # --- Storage: habits -------------------------------------------------
    def save_habit(self, habit_data: Dict[str, Any]) -> int:
        self.save_habit_calls.append(habit_data)

        habit_id = self._next_id
        self._next_id += 1

        # persist in "DB format"
        self.habits.append(
            {
                "id": habit_id,
                "name": habit_data["name"],
                "description": habit_data.get("description", ""),
                "periodicity": habit_data["periodicity"],
                "created_date": habit_data["created_date"],
                "completion_dates": list(habit_data.get("completion_dates", [])),
            }
        )
        return habit_id

    def save_all(self, habits_list: List[Dict[str, Any]]) -> bool:
        self.save_all_calls.append(habits_list)

        # mimic "full rewrite" behavior
        self.habits = []
        self._next_id = 1
        for h in habits_list:
            # In a real DB you'd keep ids; for tests this method isn't critical.
            # We store the dict as-is to keep it simple.
            self.habits.append(dict(h))
            # keep _next_id beyond max existing if present
            if "id" in h and isinstance(h["id"], int):
                self._next_id = max(self._next_id, h["id"] + 1)
        return True

    def load_habits(self) -> List[Dict[str, Any]]:
        # return deep-ish copies so caller can't mutate our storage silently
        return [dict(h, completion_dates=list(h.get("completion_dates", []))) for h in self.habits]

    def delete_habit(self, habit_id: int) -> bool:
        self.delete_habit_calls.append(habit_id)
        before = len(self.habits)
        self.habits = [h for h in self.habits if h.get("id") != habit_id]
        return len(self.habits) != before

    def log_completion(self, habit_id: int, when: datetime) -> None:
        self.log_completion_calls.append((habit_id, when))
        for h in self.habits:
            if h.get("id") == habit_id:
                h.setdefault("completion_dates", []).append(when)
                break


@pytest.fixture
def fixed_now(monkeypatch) -> datetime:
    """
    Freeze datetime.now() inside habit_tracker.services.habit_manager
    so tests are deterministic.
    """
    frozen = datetime(2025, 1, 1, 8, 0, 0)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: D401
            return frozen

    # Patch the datetime class used inside the HabitManager module
    import habit_tracker.services.habit_manager as hm_mod
    monkeypatch.setattr(hm_mod, "datetime", _FixedDateTime)
    return frozen


# ---------------------------------------------------------------------
# In-memory mode tests (storage=None)
# ---------------------------------------------------------------------
def test_add_habit_in_memory_assigns_incrementing_ids(fixed_now) -> None:
    """
    In-memory mode should assign incrementing IDs starting at 1.
    created_date should be deterministic thanks to fixed_now.
    """
    mgr = HabitManager(storage=None)

    h1 = mgr.add_habit("Read", "daily")
    h2 = mgr.add_habit("Workout", "weekly")

    assert h1.habit_id == 1
    assert h2.habit_id == 2
    assert h1.created_date == fixed_now
    assert h2.created_date == fixed_now
    assert mgr.list_habits() == [h1, h2]


def test_remove_habit_in_memory_success_and_failure(fixed_now) -> None:
    """remove_habit returns True when removed and False when id is unknown."""
    mgr = HabitManager(storage=None)
    h1 = mgr.add_habit("Read", "daily")

    assert mgr.remove_habit(h1.habit_id) is True
    assert mgr.list_habits() == []

    # removing again should fail
    assert mgr.remove_habit(h1.habit_id) is False


def test_log_completion_returns_false_for_unknown_habit(fixed_now) -> None:
    """log_completion should return False when habit id does not exist."""
    mgr = HabitManager(storage=None)
    assert mgr.log_completion(habit_id=999) is False


def test_log_completion_daily_prevents_duplicate_same_day(fixed_now) -> None:
    """
    Daily habits allow only one completion per calendar day.
    Second completion on same day should be rejected.
    """
    mgr = HabitManager(storage=None)
    h = mgr.add_habit("Read", "daily")

    t1 = datetime(2025, 1, 2, 9, 0, 0)
    t2 = datetime(2025, 1, 2, 20, 0, 0)  # same calendar day

    assert mgr.log_completion(h.habit_id, when=t1) is True
    assert mgr.log_completion(h.habit_id, when=t2) is False
    assert h.completion_dates == [t1]


def test_log_completion_daily_allows_next_day(fixed_now) -> None:
    """Daily habits should allow a completion on a different day."""
    mgr = HabitManager(storage=None)
    h = mgr.add_habit("Read", "daily")

    t1 = datetime(2025, 1, 2, 9, 0, 0)
    t2 = datetime(2025, 1, 3, 9, 0, 0)

    assert mgr.log_completion(h.habit_id, when=t1) is True
    assert mgr.log_completion(h.habit_id, when=t2) is True
    assert h.completion_dates == [t1, t2]


def test_log_completion_weekly_prevents_duplicate_same_iso_week(fixed_now) -> None:
    """
    Weekly habits allow only one completion per ISO week.
    A second completion in the same ISO week should be rejected.
    """
    mgr = HabitManager(storage=None)
    h = mgr.add_habit("Workout", "weekly")

    # Week 2 of 2025: Jan 6 (Mon) and Jan 8 (Wed)
    t1 = datetime(2025, 1, 6, 9, 0, 0)
    t2 = datetime(2025, 1, 8, 9, 0, 0)

    assert mgr.log_completion(h.habit_id, when=t1) is True
    assert mgr.log_completion(h.habit_id, when=t2) is False
    assert h.completion_dates == [t1]


def test_log_completion_weekly_allows_next_week(fixed_now) -> None:
    """Weekly habits should allow a completion in the next ISO week."""
    mgr = HabitManager(storage=None)
    h = mgr.add_habit("Workout", "weekly")

    t1 = datetime(2025, 1, 6, 9, 0, 0)   # week 2
    t2 = datetime(2025, 1, 13, 9, 0, 0)  # week 3

    assert mgr.log_completion(h.habit_id, when=t1) is True
    assert mgr.log_completion(h.habit_id, when=t2) is True
    assert h.completion_dates == [t1, t2]


# ---------------------------------------------------------------------
# Storage-backed mode tests
# ---------------------------------------------------------------------
def test_manager_loads_habits_from_storage_on_startup(fixed_now) -> None:
    """
    When a Storage backend is provided, HabitManager should load habits on init
    and build both the ordered list and the id index.
    """
    store = SpyStorage()
    created = datetime(2025, 1, 1, 8, 0, 0)

    # Seed storage with two habits (as SQLStore.load_habits would return)
    store.habits = [
        {
            "id": 5,
            "name": "Drink Water",
            "description": "",
            "periodicity": "daily",
            "created_date": created,
            "completion_dates": [created + timedelta(days=1)],
        },
        {
            "id": 9,
            "name": "Weekly Review",
            "description": "Plan next week",
            "periodicity": "weekly",
            "created_date": created,
            "completion_dates": [],
        },
    ]
    store._next_id = 10  # next auto-increment

    mgr = HabitManager(storage=store)

    habits = mgr.list_habits()
    assert len(habits) == 2
    assert {h.habit_id for h in habits} == {5, 9}
    assert mgr.habit_id_counter == 9  # max existing id


def test_add_habit_with_storage_uses_db_assigned_id_and_calls_save_habit(fixed_now) -> None:
    """
    With a Storage backend, add_habit should call storage.save_habit()
    and use the returned id.
    """
    store = SpyStorage()
    mgr = HabitManager(storage=store)

    h = mgr.add_habit("Read", "daily", description="10 pages")

    assert h.habit_id == 1
    assert len(store.save_habit_calls) == 1
    assert store.save_habit_calls[0]["name"] == "Read"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
    assert store.save_habit_calls[0]["periodicity"] == "daily"
    assert store.save_habit_calls[0]["description"] == "10 pages"
    assert mgr.habit_id_counter == 1


def test_remove_habit_with_storage_calls_delete_habit(fixed_now) -> None:
    """With storage, remove_habit should call storage.delete_habit."""
    store = SpyStorage()
    mgr = HabitManager(storage=store)
    h = mgr.add_habit("Read", "daily")

    assert mgr.remove_habit(h.habit_id) is True
    assert store.delete_habit_calls == [h.habit_id]


def test_log_completion_with_storage_calls_storage_log_completion(fixed_now) -> None:
    """
    With storage, log_completion should write-through to storage.log_completion
    when a completion is accepted.
    """
    store = SpyStorage()
    mgr = HabitManager(storage=store)
    h = mgr.add_habit("Read", "daily")

    when = datetime(2025, 1, 2, 9, 0, 0)

    assert mgr.log_completion(h.habit_id, when=when) is True
    assert store.log_completion_calls == [(h.habit_id, when)]

    # second completion same day should not call storage again
    when2 = datetime(2025, 1, 2, 20, 0, 0)
    assert mgr.log_completion(h.habit_id, when=when2) is False
    assert store.log_completion_calls == [(h.habit_id, when)]


# ---------------------------------------------------------------------
# Seeding predefined habits
# ---------------------------------------------------------------------
def test_seed_predefined_habits_skips_when_habits_exist(fixed_now) -> None:
    """
    By default, seed_predefined_habits should do nothing if habits already exist.
    """
    mgr = HabitManager(storage=None)
    mgr.add_habit("Existing", "daily")

    created = mgr.seed_predefined_habits(force=False)
    assert created == 0


def test_seed_predefined_habits_creates_when_empty(monkeypatch, fixed_now) -> None:
    """
    When empty, seed_predefined_habits should create all predefined habits.
    We monkeypatch the fixtures module so the test is deterministic.
    """
    fake_defs = [
        {"name": "Drink Water", "periodicity": "daily", "description": "2L"},
        {"name": "Weekly Review", "periodicity": "weekly", "description": "Plan"},
    ]

    import habit_tracker.fixtures.predefined_habits as defs_mod
    monkeypatch.setattr(defs_mod, "PREDEFINED_HABITS", fake_defs, raising=True)

    mgr = HabitManager(storage=None)
    created = mgr.seed_predefined_habits(force=False)

    assert created == 2
    assert [h.name for h in mgr.list_habits()] == ["Drink Water", "Weekly Review"]


def test_seed_predefined_habits_force_adds_even_if_existing(monkeypatch, fixed_now) -> None:
    """
    If force=True, seeding should run even if habits already exist.
    """
    fake_defs = [
        {"name": "Drink Water", "periodicity": "daily", "description": "2L"},
    ]

    import habit_tracker.fixtures.predefined_habits as defs_mod
    monkeypatch.setattr(defs_mod, "PREDEFINED_HABITS", fake_defs, raising=True)

    mgr = HabitManager(storage=None)
    mgr.add_habit("Existing", "daily")

    created = mgr.seed_predefined_habits(force=True)

    assert created == 1
    assert [h.name for h in mgr.list_habits()] == ["Existing", "Drink Water"]
