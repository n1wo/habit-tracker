from abc import ABC, abstractmethod
from typing import List, Optional

from habit_tracker.models import Habit


class HabitService(ABC):
    """
    Abstract service interface for habit-related operations.

    Defines the contract for managing habits independently of the
    concrete implementation (e.g. in-memory or database-backed).
    """

    @abstractmethod
    def add_habit(
        self,
        name: str,
        periodicity: str,
        description: Optional[str] = None,
    ) -> Habit:
        """
        Create and register a new habit.

        Args:
            name: Short name of the habit.
            periodicity: Habit frequency (e.g. "daily", "weekly").
            description: Optional longer description.

        Returns:
            The newly created Habit instance.
        """
        raise NotImplementedError

    @abstractmethod
    def list_habits(self) -> List[Habit]:
        """
        Return all registered habits.

        Returns:
            A list of Habit objects.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_habit(self, habit_id: int) -> bool:
        """
        Remove a habit by its identifier.

        Args:
            habit_id: Unique habit identifier.

        Returns:
            True if the habit was removed, False if not found.
        """
        raise NotImplementedError
