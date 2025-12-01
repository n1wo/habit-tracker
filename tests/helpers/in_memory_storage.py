from datetime import datetime
from typing import Optional

from habit_tracker.models import User
from habit_tracker.services.auth_manager import AuthManager, AuthError
from habit_tracker.storage import Storage


class InMemoryStorage(Storage):
    """Minimal in-memory implementation for testing AuthManager."""

    def __init__(self):
        self._user: Optional[User] = None

    # --- user methods used by AuthManager ---
    def load_user(self):
        return self._user

    def save_user(self, user: User):
        self._user = user

    # --- habit-related methods: not used in these tests ---
    def save_habit(self, habit_data):
        raise NotImplementedError

    def save_all(self, habits_list):
        raise NotImplementedError

    def load_habits(self):
        raise NotImplementedError

    def delete_habit(self, habit_id: int):
        raise NotImplementedError

    def log_completion(self, habit_id: int, when: datetime):
        raise NotImplementedError
