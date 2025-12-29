import pytest

from habit_tracker.services.auth_manager import AuthManager, AuthError
from helpers.in_memory_storage import InMemoryStorage


# ---------------------------------------------------------------------------
# Basic lifecycle tests
# ---------------------------------------------------------------------------

def test_first_run_true_when_no_user() -> None:
    """
    When no user is stored yet, AuthManager.is_first_run() should return True.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    assert auth.is_first_run() is True
    assert auth.get_current_user() is None


def test_set_password_creates_user_and_stores() -> None:
    """
    set_password() should create and persist a new user with a hashed password.
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    user = auth.set_password("secret123")

    assert user.username == "default"
    assert user.password_hash  # non-empty
    assert user.salt          # non-empty

    stored_user = storage.load_user()
    assert stored_user is not None
    assert stored_user.username == "default"

    assert auth.is_first_run() is False


def test_set_password_when_user_exists_raises() -> None:
    """Calling set_password() when a user already exists should raise AuthError."""
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")

    with pytest.raises(AuthError):
        auth.set_password("another")


# ---------------------------------------------------------------------------
# Login + current user
# ---------------------------------------------------------------------------

def test_login_success_and_failure() -> None:
    """
    login() should:
    - return True and set current user on correct password
    - return False on wrong password
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")
    assert auth.get_current_user() is not None  # set_password stores & sets current user

    # Optional: simulate "logged out" by constructing a fresh manager instance.
    auth = AuthManager(storage)
    assert auth.get_current_user() is None

    assert auth.login("secret123") is True
    assert auth.get_current_user() is not None

    # Wrong password should fail. By current implementation, it does not clear
    # the existing authenticated user.
    assert auth.login("wrongpass") is False
    assert auth.get_current_user() is not None


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

def test_change_password_happy_path() -> None:
    """
    change_password(old, new) with the correct old password should:
    - return True
    - invalidate the old password
    - allow login with the new password
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")

    ok = auth.change_password("oldpass", "newpass")
    assert ok is True

    assert auth.login("oldpass") is False
    assert auth.login("newpass") is True


def test_change_password_wrong_old() -> None:
    """
    change_password(old, new) with an incorrect old password should:
    - return False
    - keep the existing password unchanged
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")

    ok = auth.change_password("wrongold", "newpass")
    assert ok is False

    assert auth.login("oldpass") is True


def test_change_password_without_user_raises() -> None:
    """If no user exists, change_password should raise AuthError."""
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    with pytest.raises(AuthError):
        auth.change_password("anything", "newpass")


# ---------------------------------------------------------------------------
# Hashing guarantees
# ---------------------------------------------------------------------------

def test_password_is_hashed_not_plain() -> None:
    """
    Ensure AuthManager never stores the raw password:
    - password_hash != plain password
    - a salt is generated
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    plain_password = "mysecretpassword"
    user = auth.set_password(plain_password)

    assert user.password_hash != plain_password
    assert user.salt is not None and user.salt != ""


# ---------------------------------------------------------------------------
# Password strength checker
# ---------------------------------------------------------------------------

def test_check_password_strength_rejects_weak_and_common() -> None:
    """Short or common passwords should fail the strength check."""
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    report_short = auth.check_password_strength("abc")
    assert report_short["ok"] is False
    assert any("at least 8 characters" in msg for msg in report_short["errors"])

    report_common = auth.check_password_strength("password")
    assert report_common["ok"] is False
    assert any("too common" in msg for msg in report_common["errors"])


def test_check_password_strength_medium_password_has_suggestions() -> None:
    """
    A password that passes hard checks but is only 8–11 chars should be ok,
    but include suggestions (e.g., "12+ characters").
    """
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    report = auth.check_password_strength("GoodPwd1")  # 8 chars, 3 categories
    assert report["ok"] is True
    assert any("12 characters" in msg for msg in report["suggestions"])


def test_check_password_strength_accepts_strong_password() -> None:
    """A strong password should pass with no hard errors."""
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    strong = "Str0ng!Passw0rd123"
    report = auth.check_password_strength(strong)

    assert report["ok"] is True
    assert report["errors"] == []
