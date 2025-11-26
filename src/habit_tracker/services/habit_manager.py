from datetime import datetime
from typing import Optional

from habit_tracker.models import Habit
from habit_tracker.storage import Storage 
from .habit_service import HabitService


class HabitManager(HabitService):
    """Class to manage multiple habits in the habit tracker application."""

    def __init__(self, storage: Optional[Storage] = None):
        """
        :param storage: Optional persistence backend (e.g. SQLStore).
                        If None, the manager works purely in memory (for tests).
        """
        self._storage = storage
        self.habits: list[Habit] = []
        self._habit_by_id: dict[int, Habit] = {} # habit_id -> Habit mapping for quick lookup
        self.habit_id_counter = 0

        # Load existing habits from storage on startup
        if self._storage is not None:
            self._load_from_storage()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_from_storage(self) -> None:
        """Load habits from the storage backend into memory."""
        raw_habits = self._storage.load_habits()  # list[dict] from SQLStore

        for data in raw_habits:
            habit = Habit(
                habit_id=data["id"],
                name=data["name"],
                periodicity=data["periodicity"],
                created_date=data["created_date"],
                description=data.get("description"),
            )
            # restore completion dates
            # assuming Habit has an attribute `completion_dates: list[datetime]`
            habit.completion_dates = data.get("completion_dates", [])

            self.habits.append(habit)
            self._habit_by_id[habit.habit_id] = habit

        if self.habits:
            self.habit_id_counter = max(h.habit_id for h in self.habits)

    def _serialize_habit(self, habit: Habit) -> dict:
        """Convert a Habit object to the dict format expected by Storage."""
        return {
            "id": habit.habit_id,
            "name": habit.name,
            "description": habit.description or "",
            "periodicity": habit.periodicity,
            "created_date": habit.created_date,
            "completion_dates": list(getattr(habit, "completion_dates", [])),
        } 

    def _save_all_to_storage(self) -> None:
        """Write-through persistence of all habits (fallback for complex updates)."""
        if self._storage is None:
            return
        habits_data = [self._serialize_habit(h) for h in self.habits]
        self._storage.save_all(habits_data)   

    @staticmethod
    def _already_completed_for_period(habit, when: datetime) -> bool:
        """Return True if the habit already has a completion in this period."""
        per = getattr(habit, "periodicity", "").lower()


        # WEEKLY
        if per == "weekly":
            year, week, _ = when.isocalendar() # get year and week number
            for dt in habit.completion_dates: 
                y, w, _ = dt.isocalendar()
                if (y, w) == (year, week): # 
                    return True
            return False

        # DAILY (default)
        target_date = when.date()
        return any(dt.date() == target_date for dt in habit.completion_dates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_habit(self, name: str, periodicity: str, description: str = None) -> Habit:
        """Add a new habit to the manager."""

        created = datetime.now()

        # Generate a unique habit ID
        # If we have a storage backend, let the DB generate the ID
        if self._storage is not None:
            habit_data = {
                "name": name,
                "description": description or "",
                "periodicity": periodicity,
                "created_date": created,
                "completion_dates": [],
            }
            habit_id = self._storage.save_habit(habit_data)
        else:
            # pure in-memory fallback
            self.habit_id_counter += 1
            habit_id = self.habit_id_counter

        # Create a new Habit instance
        new_habit = Habit(
            habit_id=habit_id,
            name=name,
            periodicity=periodicity,
            created_date=created,
            description=description
        )

        # habits start with no completions
        if not hasattr(new_habit, "completion_dates"):
            new_habit.completion_dates = []
        self.habits.append(new_habit)
        self._habit_by_id[habit_id] = new_habit

        return new_habit
    
    def remove_habit(self, habit_id: int) -> bool:
        """Remove a habit by its ID. Returns True if removed, False if not found."""
        habit = self._habit_by_id.pop(habit_id, None)
        if habit is None:
            return False
        
        # remove from list
        if habit in self.habits:
            self.habits.remove(habit)

        # also delete from storage if available
        if self._storage is not None:
            self._storage.delete_habit(habit_id)

        return True

    def log_completion(self, habit_id: int, when: datetime = None) -> bool:
        """Check off habit completion by habit_id"""
        when = when or datetime.now()

        habit = self._habit_by_id.get(habit_id)
        if habit is None:
            return False
        
        if self._already_completed_for_period(habit, when):
            # already logged for this day/week
            return False
        
        habit.log_completion(when)

        # persist if storage available
        if self._storage is not None:
            self._storage.log_completion(habit_id, when)

        return True

    def list_habits(self) -> list[Habit]:
        """Return all stored habits."""
        return self.habits
    
