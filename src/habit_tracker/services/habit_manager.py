from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from habit_tracker.models import Habit
from habit_tracker.storage import Storage
from .habit_service import HabitService


class HabitManager(HabitService):
    """
    Service layer for managing habits in memory with optional persistence.

    Responsibilities:
    - Create and delete habits
    - Log completions (check-offs) while enforcing periodicity rules
    - Load/save habit state via a Storage backend (e.g. SQLStore)

    Design notes:
    - The manager keeps an in-memory list for ordering and display.
    - A dict index (_habit_by_id) provides O(1) lookup by habit_id.
    - If a Storage backend is provided, habits are loaded on startup and
      completion events are written through immediately.
    """

    def __init__(self, storage: Optional[Storage] = None) -> None:
        """
        Initialize the manager.

        Args:
            storage: Optional persistence backend. If None, the manager works
                purely in memory (useful for unit tests).
        """
        self._storage = storage
        self.habits: list[Habit] = []
        self._habit_by_id: Dict[int, Habit] = {}
        self.habit_id_counter = 0

        if self._storage is not None:
            self._load_from_storage()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_from_storage(self) -> None:
        """
        Load habits from the storage backend into memory.

        Expects the storage layer to return a list of dictionaries with:
            id, name, description, periodicity, created_date, completion_dates
        """
        if self._storage is None:
            return

        raw_habits = self._storage.load_habits()

        self.habits.clear()
        self._habit_by_id.clear()

        for data in raw_habits:
            habit = Habit(
                habit_id=data["id"],
                name=data["name"],
                periodicity=data["periodicity"],
                created_date=data["created_date"],
                description=data.get("description"),
                completion_dates=data.get("completion_dates", []),
            )
            self.habits.append(habit)
            self._habit_by_id[habit.habit_id] = habit

        # Keep the counter in sync with existing ids.
        if self.habits:
            self.habit_id_counter = max(h.habit_id for h in self.habits)

    def _serialize_habit(self, habit: Habit) -> Dict:
        """
        Convert a Habit object into the dict format expected by Storage.

        Args:
            habit: Habit instance to serialize.

        Returns:
            Dictionary representing the habit and its completion history.
        """
        return {
            "id": habit.habit_id,
            "name": habit.name,
            "description": habit.description or "",
            "periodicity": habit.periodicity,
            "created_date": habit.created_date,
            "completion_dates": list(habit.completion_dates),
        }

    def _save_all_to_storage(self) -> None:
        """
        Persist the full in-memory habit list.

        This is useful as a "bulk rewrite" when needed, but most operations use
        write-through persistence on each action (save_habit, log_completion, delete).
        """
        if self._storage is None:
            return

        habits_data = [self._serialize_habit(h) for h in self.habits]
        self._storage.save_all(habits_data)

    @staticmethod
    def _already_completed_for_period(habit: Habit, when: datetime) -> bool:
        """
        Return True if the habit already has a completion in the target period.

        Period rules:
        - weekly: only one completion per ISO week
        - daily: only one completion per calendar day
        """
        per = habit.periodicity.lower()

        if per == "weekly":
            year, week, _ = when.isocalendar()
            for dt in habit.completion_dates:
                y, w, _ = dt.isocalendar()
                if (y, w) == (year, week):
                    return True
            return False

        # Default: daily
        target_date = when.date()
        return any(dt.date() == target_date for dt in habit.completion_dates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_habit(self, name: str, periodicity: str, description: Optional[str] = None) -> Habit:
        """
        Add a new habit.

        If a storage backend is provided, the database assigns the habit id.
        Otherwise, the manager assigns an incrementing in-memory id.

        Args:
            name: Habit name.
            periodicity: "daily" or "weekly" (string-based).
            description: Optional longer description.

        Returns:
            The created Habit instance.
        """
        created = datetime.now()

        if self._storage is not None:
            habit_data = {
                "name": name,
                "description": description or "",
                "periodicity": periodicity,
                "created_date": created,
                "completion_dates": [],
            }
            habit_id = self._storage.save_habit(habit_data)
            # Keep counter aligned with DB ids (important if you later add in-memory habits).
            self.habit_id_counter = max(self.habit_id_counter, habit_id)
        else:
            self.habit_id_counter += 1
            habit_id = self.habit_id_counter

        new_habit = Habit(
            habit_id=habit_id,
            name=name,
            periodicity=periodicity,
            created_date=created,
            description=description,
            completion_dates=[],
        )

        self.habits.append(new_habit)
        self._habit_by_id[habit_id] = new_habit
        return new_habit

    def remove_habit(self, habit_id: int) -> bool:
        """
        Remove a habit by id.

        Args:
            habit_id: The id of the habit to remove.

        Returns:
            True if the habit existed and was removed, otherwise False.
        """
        habit = self._habit_by_id.pop(habit_id, None)
        if habit is None:
            return False

        if habit in self.habits:
            self.habits.remove(habit)

        if self._storage is not None:
            self._storage.delete_habit(habit_id)

        return True

    def log_completion(self, habit_id: int, when: Optional[datetime] = None) -> bool:
        """
        Log a completion (check-off) for the given habit id.

        Enforces one completion per period (day/week).

        Args:
            habit_id: Habit identifier.
            when: Completion timestamp. Defaults to `datetime.now()`.

        Returns:
            True if the completion was recorded, False if the habit was not found
            or already completed in the same period.
        """
        when = when or datetime.now()

        habit = self._habit_by_id.get(habit_id)
        if habit is None:
            return False

        if self._already_completed_for_period(habit, when):
            return False

        habit.log_completion(when)

        if self._storage is not None:
            self._storage.log_completion(habit_id, when)

        return True

    def list_habits(self) -> list[Habit]:
        """
        Return all habits currently loaded in memory.

        Returns:
            A list of Habit objects.
        """
        return self.habits

    def seed_predefined_habits(self, force: bool = False) -> int:
        """
        Seed the application with predefined habits.

        Behavior:
        - By default, seeds only if there are no existing habits.
        - If `force=True`, seeds even if habits already exist.

        Args:
            force: If True, always seed.

        Returns:
            The number of habits created.
        """
        from habit_tracker.fixtures.predefined_habits import PREDEFINED_HABITS

        if not force and self.habits:
            return 0

        count = 0
        for h in PREDEFINED_HABITS:
            self.add_habit(
                name=h["name"],
                periodicity=h["periodicity"],
                description=h.get("description", ""),
            )
            count += 1

        return count
