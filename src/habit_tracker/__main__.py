"""
Application entry point for the Habit Tracker CLI.

This module provides a minimal `main()` function that delegates all
startup logic to the UI layer via `run_app()`.
"""

from habit_tracker.app_entry import run_app


def main() -> None:
    """Thin entry point that delegates to the UI layer."""
    run_app()


if __name__ == "__main__":
    main()
