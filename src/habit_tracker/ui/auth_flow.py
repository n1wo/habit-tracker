"""
CLI authentication flows for the Habit Tracker app.

This module contains user interaction logic only (prompts + printing).
All authentication rules, hashing, and persistence are handled by AuthService.
"""

import questionary

from habit_tracker.services.auth_service import AuthService


def initial_password_setup(auth: AuthService) -> bool:
    """
    Guide the user through first-run password creation.

    Flow:
    - Ask for password twice (confirmation)
    - Validate non-empty input
    - Validate strength using AuthService.check_password_strength()
    - Persist credentials using AuthService.set_password()

    Returns:
        True if setup succeeds, False if the user cancels.
    """
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

        # Strength check
        report = auth.check_password_strength(pw1)

        if not report["ok"]:
            print("\n❌ Password is too weak:")
            for msg in report["errors"]:
                print(f"  • {msg}")

            if report["suggestions"]:
                print("\n💡 Suggestions:")
                for msg in report["suggestions"]:
                    print(f"  • {msg}")

            print()
            continue

        # Optional: show suggestions even if acceptable
        if report["suggestions"]:
            print("\n💡 Your password is acceptable, but you could improve it:")
            for msg in report["suggestions"]:
                print(f"  • {msg}")
            print()

        auth.set_password(pw1)
        print("\n✅ Password created successfully!\n")
        return True


def login_flow(auth: AuthService, attempts: int = 3) -> bool:
    """
    Prompt the user to log in with limited attempts.

    Args:
        auth: Authentication service.
        attempts: Maximum number of allowed password attempts.

    Returns:
        True if login succeeds, False if cancelled or attempts are exhausted.
    """
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
