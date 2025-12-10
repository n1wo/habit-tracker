from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TypedDict

from habit_tracker.models import User


class PasswordStrengthReport(TypedDict):
    ok: bool
    errors: list[str]
    suggestions: list[str]


class AuthService(ABC):
    """Interface for authentication and password management."""

    @abstractmethod
    def is_first_run(self) -> bool:
        """Return True if no user is stored yet."""
        raise NotImplementedError

    @abstractmethod
    def set_password(self, password: str) -> User:
        """Initialize the user with a new password (first run only)."""
        raise NotImplementedError

    @abstractmethod
    def login(self, password: str) -> bool:
        """Check the given password against the stored user."""
        raise NotImplementedError

    @abstractmethod
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the stored password if old_password is correct."""
        raise NotImplementedError

    @abstractmethod
    def get_current_user(self) -> Optional[User]:
        """Return the currently logged-in user (or None)."""
        raise NotImplementedError

    @abstractmethod
    def check_password_strength(self, password: str) -> PasswordStrengthReport:
        """Return a NIST-style strength report for the given password."""
        raise NotImplementedError
