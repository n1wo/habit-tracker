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
    
    def remove_habit(self, habit_id: int) -> bool:
        """Remove a habit by its ID. Returns True if removed, False if not found."""
        for habit in self.habits:
            if habit.habit_id == habit_id:
                self.habits.remove(habit)
                return True
        return False

    def log_completion(self, habit_id: int, when: datetime = None) -> bool:
        """Check off habit completion by habit_id"""
        when = when or datetime.now()
        for habit in self.habits:
            if habit.habit_id == habit_id:
                habit.log_completion(when)
                return True
        return False


    def list_habits(self) -> list[Habit]:
        """Return all stored habits."""
        return self.habits
    
