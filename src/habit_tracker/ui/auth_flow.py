# src/habit_tracker/ui/auth_flow.py

from __future__ import annotations
import questionary
import sys

from habit_tracker.services.auth_manager import AuthManager, AuthError


def initial_password_setup(auth: AuthManager) -> bool:
    """Guide user through first-run password creation."""
    print("\n🔐 First-time setup — create your master password.\n")

    while True:
        pw1 = questionary.password("Choose a password:").ask()
        if pw1 is None:
            print("\nSetup cancelled.\n")
            return False

        pw2 = questionary.password("Confirm password:").ask()
        if pw2 is None:
            print("\nSetup cancelled.\n")
            return False

        if pw1.strip() == "":
            print("⚠️ Password cannot be empty.\n")
            continue

        if pw1 != pw2:
            print("⚠️ Passwords do not match.\n")
            continue

        auth.set_password(pw1)
        print("\n✅ Password created successfully!\n")
        return True


def login_flow(auth: AuthManager, attempts: int = 3) -> bool:
    """Prompt user to log in."""
    print("\n🔐 Please log in.\n")

    for attempt in range(1, attempts + 1):
        pw = questionary.password("Password:").ask()
        if pw is None:
            print("\nLogin cancelled.\n")
            return False

        if auth.login(pw):
            print("\n✅ Login successful!\n")
            return True

        remaining = attempts - attempt
        if remaining > 0:
            print(f"❌ Wrong password. Attempts left: {remaining}\n")
        else:
            print("❌ Too many failed attempts.\n")

    return False
