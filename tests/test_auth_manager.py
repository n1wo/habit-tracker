import pytest

from habit_tracker.services.auth_manager import AuthManager, AuthError
from helpers.in_memory_storage import InMemoryStorage  # or define InMemoryStorage in this file


def test_first_run_true_when_no_user():
    """
    When no user is stored yet, AuthManager.is_first_run() should return True.

    This ensures we can detect initial setup and trigger the password creation flow.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    assert auth.is_first_run() is True


def test_set_password_creates_user_and_stores():
    """
    set_password() should:

    • Create a new User object with a default username.
    • Generate and store a non-empty password_hash and salt.
    • Persist the user via the storage backend.
    • Flip is_first_run() to False afterwards.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    user = auth.set_password("secret123")

    # Default username is used for the single-user system.
    assert user.username == "default"

    # Hash and salt must be non-empty (AuthManager is responsible for hashing).
    assert user.password_hash
    assert user.salt

    # The user must be persisted in storage.
    assert storage.load_user() is not None

    # After setup, this should no longer be treated as first run.
    assert auth.is_first_run() is False


def test_set_password_when_user_exists_raises():
    """
    Calling set_password() a second time when a user already exists
    should raise AuthError.

    This prevents accidentally overwriting an existing account.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")

    with pytest.raises(AuthError):
        auth.set_password("another")


def test_login_success_and_failure():
    """
    login() should:

    • Return True and set a current user on correct password.
    • Return False and NOT authenticate for a wrong password.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")

    # Correct password → login succeeds and current user is set.
    assert auth.login("secret123") is True
    assert auth.get_current_user() is not None

    # Wrong password → login fails.
    assert auth.login("wrongpass") is False


def test_change_password_happy_path():
    """
    change_password(old, new) with the correct old password should:

    • Return True.
    • Invalidate the old password.
    • Allow login with the new password.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")
    ok = auth.change_password("oldpass", "newpass")
    assert ok is True

    # Old password should stop working.
    assert auth.login("oldpass") is False

    # New password should work.
    assert auth.login("newpass") is True


def test_change_password_wrong_old():
    """
    change_password(old, new) with an incorrect old password should:

    • Return False.
    • Leave the existing password unchanged.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")
    ok = auth.change_password("wrongold", "newpass")
    assert ok is False

    # Existing password should still work.
    assert auth.login("oldpass") is True
