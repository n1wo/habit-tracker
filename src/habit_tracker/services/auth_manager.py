"""
Authentication service implementation for the Habit Tracker app.

AuthManager handles:
- First-run password setup
- Login verification
- Password changes

Security notes:
- Passwords are hashed using PBKDF2-HMAC (SHA-256) with per-user random salt.
- Stored values are base64-encoded strings (hash + salt).
- Verification uses constant-time comparison to reduce timing attack risk.

The storage layer persists a single User record (single-user app design).
"""

import base64
import hashlib
import hmac
import os
from typing import Optional, TypedDict

from habit_tracker.models import User
from habit_tracker.storage import Storage
from habit_tracker.services.auth_service import AuthService, PasswordStrengthReport


class AuthError(Exception):
    """Raised for authentication configuration or flow errors."""


class PasswordStrengthResult(TypedDict):
    """Structured result for password strength checks."""
    ok: bool
    errors: list[str]
    suggestions: list[str]


class AuthManager(AuthService):
    """
    Authentication manager for password setup, login, and password changes.

    This class owns all hashing and salt handling. The User entity only stores
    derived values (password_hash + salt), while AuthManager performs all
    password validation and verification.
    """

    _ALGORITHM = "sha256"
    _ITERATIONS = 100_000
    _KEY_LENGTH = 32  # bytes
    _USERNAME = "default"  # single-user app

    def __init__(self, storage: Storage) -> None:
        """
        Create a new AuthManager.

        Args:
            storage: Persistence backend used to store and load the single User record.
        """
        self._storage = storage
        self._current_user: Optional[User] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_salt(self) -> bytes:
        """Return a new cryptographically-secure random salt."""
        return os.urandom(16)

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """
        Derive a password hash using PBKDF2-HMAC.

        Args:
            password: Plain text password.
            salt: Random salt bytes.

        Returns:
            Derived key bytes.
        """
        return hashlib.pbkdf2_hmac(
            self._ALGORITHM,
            password.encode("utf-8"),
            salt,
            self._ITERATIONS,
            dklen=self._KEY_LENGTH,
        )

    def _verify_password(self, password: str, user: User) -> bool:
        """
        Verify a password against the stored user credentials.

        Args:
            password: Password attempt.
            user: Stored user record containing base64-encoded hash and salt.

        Returns:
            True if the password matches, otherwise False.
        """
        try:
            salt = self._decode(user.salt)
            stored_hash = self._decode(user.password_hash)
        except (ValueError, TypeError):
            # Invalid encoding (corrupt storage)
            return False

        candidate_hash = self._hash_password(password, salt)
        return hmac.compare_digest(candidate_hash, stored_hash)

    @staticmethod
    def _encode(raw: bytes) -> str:
        """Encode bytes as a base64 ASCII string for storage."""
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _decode(encoded: str) -> bytes:
        """Decode a base64 ASCII string back to bytes."""
        return base64.b64decode(encoded.encode("ascii"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def check_password_strength(self, password: str) -> PasswordStrengthReport:
        """
        Check password strength using simple NIST-inspired rules.

        Rules (project-level):
        - Minimum length of 8 characters (hard requirement)
        - Not only whitespace (hard requirement)
        - Reject a small blacklist of very common passwords (hard requirement)
        - Require at least 3 of 4 categories (lower/upper/digit/symbol)

        Args:
            password: Password to evaluate.

        Returns:
            Dictionary with:
            - ok: True if it passes hard requirements
            - errors: list of issues that must be fixed
            - suggestions: optional improvements
        """
        errors: list[str] = []
        suggestions: list[str] = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password.strip() == "":
            errors.append("Password cannot consist of only spaces or whitespace.")

        lowered = password.lower()
        common_passwords = {
            "password",
            "12345678",
            "123456789",
            "qwerty",
            "iloveyou",
            "admin",
            "welcome",
        }
        if lowered in common_passwords:
            errors.append("Password is too common and easy to guess.")

        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        categories = sum((has_lower, has_upper, has_digit, has_symbol))

        if categories < 3:
            if not has_lower:
                errors.append("Add at least one lowercase letter (a–z).")
            if not has_upper:
                errors.append("Add at least one uppercase letter (A–Z).")
            if not has_digit:
                errors.append("Add at least one number (0–9).")
            if not has_symbol:
                errors.append("Add at least one special character (e.g. ! ? # $ % &).")

        if 8 <= len(password) < 12:
            suggestions.append("Consider using at least 12 characters for stronger security.")

        return {"ok": len(errors) == 0, "errors": errors, "suggestions": suggestions}

    def is_first_run(self) -> bool:
        """
        Return True if no user is stored yet.

        The app is single-user, so this checks whether the user record exists.
        """
        return self._storage.load_user() is None

    def set_password(self, password: str) -> User:
        """
        Initialize the user with a new password (first run only).

        Args:
            password: New password to store.

        Returns:
            The created User record.

        Raises:
            AuthError: If a user already exists.
        """
        if not self.is_first_run():
            raise AuthError("User already exists. Use change_password instead.")

        salt_bytes = self._generate_salt()
        hash_bytes = self._hash_password(password, salt_bytes)

        user = User(
            username=self._USERNAME,
            password_hash=self._encode(hash_bytes),
            salt=self._encode(salt_bytes),
        )
        self._storage.save_user(user)
        self._current_user = user
        return user

    def login(self, password: str) -> bool:
        """
        Check the given password against the stored user.

        Args:
            password: Password attempt.

        Returns:
            True if login succeeds, otherwise False.
        """
        user = self._storage.load_user()
        if user is None:
            return False

        if self._verify_password(password, user):
            self._current_user = user
            return True

        return False

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change the stored password if old_password is correct.

        Args:
            old_password: Current password.
            new_password: New password to set.

        Returns:
            True on success, False if old_password was wrong.

        Raises:
            AuthError: If no user is configured yet.
        """
        user = self._storage.load_user()
        if user is None:
            raise AuthError("No user configured. Call set_password first.")

        if not self._verify_password(old_password, user):
            return False

        new_salt = self._generate_salt()
        new_hash = self._hash_password(new_password, new_salt)

        updated_user = User(
            username=user.username,
            password_hash=self._encode(new_hash),
            salt=self._encode(new_salt),
        )

        self._storage.save_user(updated_user)
        self._current_user = updated_user
        return True

    def get_current_user(self) -> Optional[User]:
        """Return the currently logged-in user (or None if not logged in)."""
        return self._current_user
