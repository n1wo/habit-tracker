from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence

from habit_tracker.storage import Storage

EXAMPLE_HABIT_DEFS: Sequence[Dict[str, str]] = [
    {"name": "Drink Water", "description": "Drink at least 2L of water", "periodicity": "daily"},
    {"name": "Read", "description": "Read 10 pages of a book", "periodicity": "daily"},
    {"name": "Exercise", "description": "Do at least 20 minutes of exercise", "periodicity": "daily"},
    {"name": "Weekly Review", "description": "Review goals and plan next week", "periodicity": "weekly"},
    {"name": "Clean Apartment", "description": "Do a quick cleaning session", "periodicity": "weekly"},
]


def _default_start_date() -> datetime:
    return datetime(2025, 1, 1, 8, 0, 0)


@dataclass
class ExampleDataFactory:
    """
    Perfect example dataset factory.

    • All daily habits: perfect 4-week completion (one per day).
    • All weekly habits: perfect 4-week completion (one per week).

    Subclasses can override `mutate()` to introduce imperfections.
    """

    start_date: datetime | None = None
    weeks: int = 4

    def _get_start_date(self) -> datetime:
        return self.start_date or _default_start_date()

    def build(self) -> List[Dict[str, Any]]:
        """
        Build the *perfect* example data as a list of dicts.
        Subclasses usually call `super().build()` and then modify the result.
        """
        start = self._get_start_date()
        total_days = self.weeks * 7
        habits: List[Dict[str, Any]] = []

        for meta in EXAMPLE_HABIT_DEFS:
            periodicity = meta["periodicity"]
            completion_dates: List[datetime] = []

            if periodicity == "daily":
                for offset in range(total_days):
                    completion_dates.append(start + timedelta(days=offset))
            elif periodicity == "weekly":
                for week in range(self.weeks):
                    completion_dates.append(start + timedelta(days=7 * week))
            else:
                raise ValueError(f"Unsupported periodicity: {periodicity!r}")

            habits.append(
                {
                    "name": meta["name"],
                    "description": meta.get("description") or "",
                    "periodicity": periodicity,
                    "created_date": start,
                    "completion_dates": completion_dates,
                }
            )

        # hook for subclasses to tweak the data
        return self.mutate(habits)

    def mutate(self, habits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Default implementation: no change.
        Subclasses override this to introduce imperfections.
        """
        return habits

    def load_into(self, storage: Storage) -> List[int]:
        """
        Build the dataset and persist it via a Storage backend.

        Returns a list of created habit_ids.
        """
        habits = self.build()
        ids: List[int] = []
        for h in habits:
            ids.append(storage.save_habit(h))
        return ids
