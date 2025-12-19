import questionary

def choose_mode() -> str | None:
    return questionary.select(
        "How would you like to use the Habit Tracker today?",
        choices=[
            "🔐 Log into my habit tracker (real data)",
            "🧪 Try demo with example data (resets every time)",
            "🚪 Exit application",
        ],
    ).ask()
