"""
UI screen helpers for the Habit Tracker CLI.

This module contains simple, presentation-only functions such as banners
and static screens. No business logic should live here.
"""


def welcome_banner() -> None:
    """
    Display the application welcome banner.
    """
    print("\n=========================")
    print(" 🏆 Habit Tracker CLI 🏆 ")
    print("=========================\n")
