from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Optional

from habit_tracker.models import User          #
from habit_tracker.storage import Storage     


class AuthError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class AuthManager:
    """Handles password setup, login, and password changes.

    All hashing and salt handling happens here. The User entity
    only stores already-derived values (password_hash + salt).
    """

    _ALGORITHM = "sha256"
    _ITERATIONS = 100_000
    _KEY_LENGTH = 32  # bytes
    _USERNAME = "default"  # single-user app

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._current_user: Optional[User] = None


    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_salt(self) -> bytes:
        """Generate a random salt."""
        return os.urandom(16)

    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Derive a secure hash from password + salt using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            self._ALGORITHM,
            password.encode("utf-8"),
            salt,
            self._ITERATIONS,
            dklen=self._KEY_LENGTH,
        )

    def _verify_password(self, password: str, user: User) -> bool:
        """Check whether the password matches the stored hash for the user."""
        try:
            salt = self._decode(user.salt)
            stored_hash = self._decode(user.password_hash)
        except (ValueError, TypeError):
            # Corrupted or invalid encoding
            return False

        candidate_hash = self._hash_password(password, salt)
        # Use constant-time comparison to avoid timing attacks
        return hmac.compare_digest(candidate_hash, stored_hash)

    @staticmethod
    def _encode(raw: bytes) -> str:
        """Encode bytes as base64 string."""
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def _decode(encoded: str) -> bytes:
        """Decode base64 string back to bytes."""
        return base64.b64decode(encoded.encode("ascii"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_password_strength(self, password: str) -> dict[str, object]:
        """
        Check password strength using NIST-inspired rules.

        Returns:
            {
                "ok": bool,           # True if it passes hard requirements
                "errors": list[str],  # Things that MUST be fixed
                "suggestions": list[str],  # Optional improvements
            }
        """
        errors: list[str] = []
        suggestions: list[str] = []

        # 1) Hard minimum length (NIST: at least 8 chars)
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        # 2) Not all whitespace
        if password.strip() == "":
            errors.append("Password cannot consist of only spaces or whitespace.")

        # 3) Very small blacklist for obvious/common passwords
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

        # 4) Character category checks (NIST discourages *requiring* this,
        #    but we use it here as guidance with suggestions + a mild rule).
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        categories = sum((has_lower, has_upper, has_digit, has_symbol))

        # Require at least 3 of 4 categories for this project
        if categories < 3:
            if not has_lower:
                errors.append("Add at least one lowercase letter (a–z).")
            if not has_upper:
                errors.append("Add at least one uppercase letter (A–Z).")
            if not has_digit:
                errors.append("Add at least one number (0–9).")
            if not has_symbol:
                errors.append(
                    "Add at least one special character (e.g. ! ? # $ % &)."
                )

        # 5) Soft recommendation: longer is better
        if 8 <= len(password) < 12:
            suggestions.append(
                "Consider using at least 12 characters for stronger security."
            )

        # Overall result: ok if there are no hard errors.
        ok = len(errors) == 0

        return {
            "ok": ok,
            "errors": errors,
            "suggestions": suggestions,
        }

    def is_first_run(self) -> bool:
        """Return True if no user is stored yet."""
        user = self._storage.load_user()
        return user is None

    def set_password(self, password: str) -> User:
        """Initialize the user with a new password (first run only).

        Raises:
            AuthError: if a user already exists.
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
        """Check the given password against the stored user.

        Returns:
            True if login succeeds, False otherwise.
        """
        user = self._storage.load_user()
        if user is None:
            # No user configured yet
            return False

        if self._verify_password(password, user):
            self._current_user = user
            return True
        return False

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the stored password if old_password is correct.

        Returns:
            True on success, False if old_password was wrong.
        """
        user = self._storage.load_user()
        if user is None:
            raise AuthError("No user configured. Call set_password first.")

        if not self._verify_password(old_password, user):
            return False

        # Re-hash with a new salt
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
        """Return the currently logged-in user (or None)."""
        return self._current_user

