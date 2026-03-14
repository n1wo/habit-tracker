"""
UI screen helpers for the Habit Tracker CLI.

This module contains simple, presentation-only functions such as banners
and static screens. No business logic should live here.
"""


def _safe_print(preferred: str, fallback: str) -> None:
    """Print Unicode text when supported, otherwise use an ASCII fallback."""
    try:
        print(preferred)
    except UnicodeEncodeError:
        print(fallback)


def welcome_banner() -> None:
    """
    Display the application welcome banner.
    """
    print("\n=========================")
    _safe_print(" \U0001F3C6 Habit Tracker CLI \U0001F3C6 ", " Habit Tracker CLI ")
    print("=========================\n")
