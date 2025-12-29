from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """
    Entity representing an authenticated user.

    This class is a simple, immutable data container holding authentication
    credentials. All password hashing, verification, and updates are handled
    by the AuthManager.

    Attributes:
        username: The user's login name.
        password_hash: Hex/base64 string of the hashed password.
        salt: Hex/base64 string of the random salt used during hashing.
    """

    username: str
    password_hash: str
    salt: str
