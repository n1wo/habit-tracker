from datetime import datetime
from typing import List, Optional


class Habit:
    """
    Domain entity representing a habit in the habit tracker application.

    A Habit defines:
    - What task is being tracked (name, description)
    - How often it must be completed (periodicity)
    - When it was created
    - When it has been completed over time

    The Habit class is a pure data model and does not handle persistence
    or analytics logic directly.
    """

    def __init__(
        self,
        habit_id: int,
        name: str,
        periodicity: str,
        created_date: datetime,
        description: Optional[str] = None,
        completion_dates: Optional[List[datetime]] = None,
    ):
        """
        Initialize a Habit instance.

        Args:
            habit_id: Unique identifier for the habit.
            name: Short name describing the habit.
            periodicity: Habit frequency (e.g. "daily", "weekly").
            created_date: Datetime when the habit was created.
            description: Optional longer description of the habit.
            completion_dates: Optional list of datetimes when the habit
                was completed.
        """
        self.habit_id = habit_id
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.created_date = created_date
        self.completion_dates = completion_dates or []

    def log_completion(self, when: datetime) -> None:
        """
        Record a completion event for the habit.

        Args:
            when: Datetime when the habit was completed.
        """
        self.completion_dates.append(when)

    def __repr__(self) -> str:
        """
        Return a concise string representation of the Habit instance.

        Useful for debugging and logging.
        """
        return (
            f"Habit("
            f"id={self.habit_id}, "
            f"name='{self.name}', "
            f"periodicity='{self.periodicity}'"
            f")"
        )
