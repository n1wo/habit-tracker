import pytest

from habit_tracker.services.auth_manager import AuthManager, AuthError
from helpers.in_memory_storage import InMemoryStorage  # or define InMemoryStorage in this file


def test_first_run_true_when_no_user():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    assert auth.is_first_run() is True


def test_set_password_creates_user_and_stores():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    user = auth.set_password("secret123")

    assert user.username == "default"
    assert user.password_hash  # not empty
    assert user.salt           # not empty
    assert storage.load_user() is not None
    assert auth.is_first_run() is False


def test_set_password_when_user_exists_raises():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")
    with pytest.raises(AuthError):
        auth.set_password("another")


def test_login_success_and_failure():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("secret123")

    assert auth.login("secret123") is True
    assert auth.get_current_user() is not None

    assert auth.login("wrongpass") is False


def test_change_password_happy_path():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")
    ok = auth.change_password("oldpass", "newpass")
    assert ok is True

    # Old should fail
    assert auth.login("oldpass") is False
    # New should work
    assert auth.login("newpass") is True


def test_change_password_wrong_old():
    storage = InMemoryStorage()
    auth = AuthManager(storage)

    auth.set_password("oldpass")
    ok = auth.change_password("wrongold", "newpass")
    assert ok is False
