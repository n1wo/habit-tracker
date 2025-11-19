from abc import ABC, abstractmethod
from datetime import datetime

class Storage(ABC):
    @abstractmethod
    def save_habit(self, habit_data):
        pass

    @abstractmethod
    def save_all(self, habits_list):
        pass

    @abstractmethod
    def load_habits(self):
        pass

    @abstractmethod
    def delete_habit(self, habit_id: int):
        pass

    @abstractmethod
    def log_completion(self, habit_id: int, when: datetime):
        """Append a completion timestamp for an existing habit."""
        pass