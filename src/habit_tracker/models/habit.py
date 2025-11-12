from datetime import datetime
class Habit:
    """Class representing a habit in the habit tracker application."""

    # Initialize a Habit instance
    def __init__(
        self,
        habit_id: int,
        name: str,
        periodicity: str,
        created_date: datetime,
        description: str = None,
        completion_dates: list[datetime] = None   
    ):
        self.habit_id = habit_id
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.completion_dates = completion_dates or []
        self.created_date = created_date

    def log_completion(self, date: datetime):
        """Log the completion of the habit for a specific date."""
        self.completion_dates.append(date)

    def __repr__(self):
        """Return a string representation of the Habit instance."""
        return f"Habit(id={self.habit_id}, name='{self.name}', periodicity='{self.periodicity}')"
