from habit_tracker.models.user import User


def test_user_initializes_with_expected_fields():
    """
    Ensure that the User dataclass correctly stores all given fields.

    What we verify:
    • The username is stored exactly as provided.
    • The password_hash is stored verbatim (AuthManager handles hashing).
    • The salt is stored verbatim.
    """

    user = User(
        username="alice",
        password_hash="hashed_password_123",
        salt="random_salt_xyz",
    )

    assert user.username == "alice"
    assert user.password_hash == "hashed_password_123"
    assert user.salt == "random_salt_xyz"


def test_user_repr_contains_useful_info():
    """
    Dataclasses automatically provide a readable repr.
    We test that the repr at least contains the username,
    but *not* sensitive fields like passwords in real apps.
    Here it's acceptable because password_hash is already hashed.
    """

    user = User(
        username="bob",
        password_hash="hash",
        salt="salt",
    )

    repr_str = repr(user)

    assert "bob" in repr_str      # username included
    assert "password_hash" in repr_str
    assert "salt" in repr_str
