from datetime import datetime
from habit_tracker.models import Habit
from .habit_service import HabitService

class HabitManager(HabitService):
    """Class to manage multiple habits in the habit tracker application."""

    def __init__(self):
        self.habits: list[Habit] = []
        self.habit_id_counter = 0

    def add_habit(self, name: str, periodicity: str, description: str = None) -> Habit:
        """Add a new habit to the manager."""

        # Generate a unique habit ID
        self.habit_id_counter += 1
        habit_id = self.habit_id_counter

        # Create a new Habit instance
        new_habit = Habit(
            habit_id=habit_id,
            name=name,
            periodicity=periodicity,
            created_date=datetime.now(),
            description=description
        )

        self.habits.append(new_habit)

        return new_habit

    def list_habits(self) -> list[Habit]:
        """Return all stored habits."""
        return self.habits