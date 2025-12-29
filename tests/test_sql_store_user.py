from habit_tracker.storage import SQLStore
from habit_tracker.models import User


def test_load_user_initially_none(tmp_path) -> None:
    """SQLStore.load_user() should return None when no user row exists."""
    db_path = tmp_path / "test_user_initially_none.db"
    store = SQLStore(str(db_path))

    assert store.load_user() is None


def test_save_and_load_user_roundtrip(tmp_path) -> None:
    """Saving a user and loading it back should preserve all fields."""
    db_path = tmp_path / "test_user_roundtrip.db"
    store = SQLStore(str(db_path))

    original = User(
        username="default",
        password_hash="somehashvalue",
        salt="somesaltvalue",
    )

    store.save_user(original)
    loaded = store.load_user()

    assert loaded is not None
    assert isinstance(loaded, User)
    assert loaded.username == original.username
    assert loaded.password_hash == original.password_hash
    assert loaded.salt == original.salt


def test_user_persists_across_store_instances(tmp_path) -> None:
    """User data should persist on disk across separate SQLStore instances."""
    db_path = tmp_path / "test_user_persistence.db"

    store1 = SQLStore(str(db_path))
    store1.save_user(
        User(username="default", password_hash="hash123", salt="salt123")
    )

    store2 = SQLStore(str(db_path))
    loaded = store2.load_user()

    assert loaded is not None
    assert loaded.username == "default"
    assert loaded.password_hash == "hash123"
    assert loaded.salt == "salt123"
