from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from habit_tracker.models.user import User


class Storage(ABC):
    """
    Abstract persistence interface for habit data.

    Concrete implementations (e.g. SQLStore) are responsible for storing and
    retrieving habit data and completion events. The storage layer does not
    contain business logic or analytics.
    """

    @abstractmethod
    def save_habit(self, habit_data: Dict[str, Any]) -> int:
        """
        Persist a single habit and its completion history.

        Args:
            habit_data: Dictionary containing:
                - name (str)
                - description (str)
                - periodicity (str)
                - created_date (datetime)
                - completion_dates (list[datetime])

        Returns:
            The unique identifier assigned to the habit.
        """
        raise NotImplementedError

    @abstractmethod
    def save_all(self, habits_list: List[Dict[str, Any]]) -> bool:
        """
        Persist all habits in bulk (full rewrite).

        Args:
            habits_list: List of habit dictionaries in the same format
                accepted by `save_habit`.

        Returns:
            True if the operation completed successfully.
        """
        raise NotImplementedError

    @abstractmethod
    def load_habits(self) -> List[Dict[str, Any]]:
        """
        Load all stored habits and their completion history.

        Returns:
            A list of habit dictionaries, each containing:
                - id (int)
                - name (str)
                - description (str)
                - periodicity (str)
                - created_date (datetime)
                - completion_dates (list[datetime])
        """
        raise NotImplementedError

    @abstractmethod
    def delete_habit(self, habit_id: int) -> bool:
        """
        Delete a habit and all associated completion events.

        Args:
            habit_id: Unique identifier of the habit.

        Returns:
            True if the habit was deleted, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def log_completion(self, habit_id: int, when: datetime) -> None:
        """
        Append a completion timestamp for an existing habit.

        Args:
            habit_id: Unique identifier of the habit.
            when: Datetime when the habit was completed.
        """
        raise NotImplementedError
    
    @abstractmethod
    def save_user(self, user: User) -> None:
        """
        Save user information to the storage.

        Args:
            user: 
                User object containing user details:
                    - username (str)
                    - password_hash (str)
                    - salt (str)    
        """
        raise NotImplementedError
    
    @abstractmethod
    def load_user(self) -> Optional[User]:
        """
        Load user information from the storage.

        Returns:
            The stored User, or None if no user exists yet.
        """
        raise NotImplementedError
