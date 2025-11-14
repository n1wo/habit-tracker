import questionary
from habit_tracker.services import HabitService

def add_habit(service: HabitService):
    """Add a new habit via CLI prompts."""
    name = questionary.text("Enter habit name:").ask()
    if not name:
        print("No name entered.")
        return

    periodicity = questionary.select(
        "Choose periodicity:",
        choices=["Daily", "Weekly"]
    ).ask()
    # Map UI -> backend format
    period_val = periodicity.lower()  # "daily" | "weekly"

    description = questionary.text("Enter description (optional):").ask()
    print(f"\n✅ Habit added: {name} ({periodicity}) - {description or 'No description'}\n")

    habit = service.add_habit(name=name, periodicity=period_val, description=description or None)
    print(f"\n✅ Habit added: (id={getattr(habit,'habit_id','?')}) {habit.name} [{period_val}]"
          f" - {habit.description or 'No description'}\n")
    
def remove_habit(service: HabitService):
    """Remove an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to remove.\n")
        return

    choices = [f"(id={getattr(h,'habit_id','?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to remove:",
        choices=choices
    ).ask()
    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(')')[0].strip('(id=')
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        print("Invalid habit ID.")
        return

    success = service.remove_habit(habit_id)
    if success:
        print(f"\n🗑️ Habit removed: {choice}\n")
    else:
        print("\n❌ Habit not found.\n")


def view_habits(service: HabitService):
    """View all existing habits."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits yet.\n")
        return

    print("\n📋 Your habits:")
    for h in habits:
        hid = getattr(h, "habit_id", "?")
        desc = getattr(h, "description", "") or "—"
        period = getattr(h, "periodicity", "?")
        created = getattr(h, "created_date", "")
        created_txt = getattr(created, "strftime", lambda *_: str(created))("%Y-%m-%d %H:%M") if created else ""
        print(f" • id:{hid} name:{h.name} period:{period} — description:{desc}  created:{created_txt}")
    print()

def log_completion(service: HabitService):
    """Remove an existing habit via CLI prompts."""
    habits = service.list_habits()
    if not habits:
        print("\n📋 No habits to log.\n")
        return

    choices = [f"(id={getattr(h,'habit_id','?')}) {h.name}" for h in habits]
    choice = questionary.select(
        "Select a habit to log:",
        choices=choices
    ).ask()
    if not choice:
        print("No habit selected.")
        return

    # Extract habit_id from the selected choice
    habit_id_str = choice.split(')')[0].strip('(id=')
    try:
        habit_id = int(habit_id_str)
    except ValueError:
        print("Invalid habit ID.")
        return

    success = service.log_completion(habit_id)
    if success:
        print(f"\n✅ Habit loged: {choice}\n")
    else:
        print("\n❌ Habit not found.\n")
