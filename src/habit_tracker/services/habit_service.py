from abc import ABC, abstractmethod

class HabitService(ABC):
    """Abstract base class defining the interface for habit-related operations."""

    @abstractmethod
    def add_habit(self, name: str, periodicity: str, description: str = None):
        """Add a new habit object."""
        raise NotImplementedError

    @abstractmethod
    def list_habits(self):
        """Return a list of all habits."""
        raise NotImplementedError