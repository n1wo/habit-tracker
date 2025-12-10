import pytest

from habit_tracker.services.auth_manager import AuthManager, AuthError
from helpers.in_memory_storage import InMemoryStorage  # or define InMemoryStorage in this file


# ---------------------------------------------------------------------------
# Basic lifecycle tests
# ---------------------------------------------------------------------------

def test_first_run_true_when_no_user():
    """
    When no user is stored yet, AuthManager.is_first_run() should return True.

    This ensures we can detect initial setup and trigger the password creation flow.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    assert auth.is_first_run() is True
    # get_current_user should also be None at this point
    assert auth.get_current_user() is None


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
    stored_user = storage.load_user()
    assert stored_user is not None
    assert stored_user.username == "default"

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


# ---------------------------------------------------------------------------
# Login + current user
# ---------------------------------------------------------------------------

def test_login_success_and_failure():
    """
    login() should:

    • Return True and set a current user on correct password.
    • Return False and NOT authenticate for a wrong password.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")

    # Before login, current user should be None.
    auth._current_user = None  # just to be explicit in this test
    assert auth.get_current_user() is None

    # Correct password → login succeeds and current user is set.
    assert auth.login("secret123") is True
    assert auth.get_current_user() is not None

    # Wrong password → login fails (and current user should remain set from before).
    assert auth.login("wrongpass") is False
    assert auth.get_current_user() is not None


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

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


def test_change_password_without_user_raises():
    """
    If no user exists yet, change_password should raise AuthError.

    This protects against misuse of the API.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    with pytest.raises(AuthError):
        auth.change_password("anything", "newpass")


# ---------------------------------------------------------------------------
# Hashing guarantees
# ---------------------------------------------------------------------------

def test_password_is_hashed_not_plain():
    """
    Ensure that AuthManager never stores the raw plain-text password.

    What we verify:
    • The stored password_hash must NOT equal the plain password.
    • A salt must be generated (ensuring hashing is salted).
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    plain_password = "mysecretpassword"

    user = auth.set_password(plain_password)

    # password_hash must NOT equal the plain password.
    assert user.password_hash != plain_password

    # Also verify the user actually has a salt.
    assert user.salt is not None and user.salt != ""


# ---------------------------------------------------------------------------
# Password strength checker
# ---------------------------------------------------------------------------

def test_check_password_strength_rejects_weak_and_common():
    """
    Very short or common passwords should fail the strength check
    and provide clear error messages.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    report_short = auth.check_password_strength("abc")
    assert report_short["ok"] is False
    assert any("at least 8 characters" in msg for msg in report_short["errors"])

    report_common = auth.check_password_strength("password")
    assert report_common["ok"] is False
    assert any("too common" in msg for msg in report_common["errors"])


def test_check_password_strength_medium_password_has_suggestions():
    """
    A password that passes the hard checks but is only just long enough
    should be OK but still come with suggestions (e.g. use 12+ chars).
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    # 8 chars, 3 categories → OK but not very long
    report = auth.check_password_strength("GoodPwd1")
    assert report["ok"] is True
    # At least one suggestion about improving length
    assert any("12 characters" in msg for msg in report["suggestions"])


def test_check_password_strength_accepts_strong_password():
    """
    A strong password with good length and multiple character classes
    should pass strength checks with no errors.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    strong = "Str0ng!Passw0rd123"
    report = auth.check_password_strength(strong)

    assert report["ok"] is True
    assert report["errors"] == []  # no hard failures
    # suggestions can be empty or not; we just care that there are no errors
