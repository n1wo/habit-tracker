from dataclasses import dataclass

@dataclass
class User:
    """Entity representing an authenticated user.

    This class is a simple data container.
    All password hashing and verification is handled by AuthManager.
    """

    username: str
    password_hash: str  # hex/base64 string of the hashed password
    salt: str           # hex/base64 string of the random salt