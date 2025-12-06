from __future__ import annotations

from typing import Any, Dict, List

from habit_tracker.fixtures.example_data import ExampleDataFactory



class MissingDayDataFactory(ExampleDataFactory):
    """
    Imperfect example dataset:

    • Based on perfect data from ExampleDataFactory.
    • For some daily habits, remove one completion in the middle
      to break their streak.
    • At least one daily habit keeps a perfect 28-day streak and
      therefore has the longest streak.
    """

    MAX_BROKEN_DAILY = 4

    def mutate(self, habits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Find all indices of daily habits
        daily_indices = [i for i, h in enumerate(habits) if h["periodicity"] == "daily"]

        # If there are 0 or 1 daily habits, nothing to break
        if len(daily_indices) <= 1:
            return habits

        # We want to break at most MAX_BROKEN_DAILY, but always leave
        # at least ONE daily habit untouched (the last one in daily_indices).
        to_break = min(self.MAX_BROKEN_DAILY, len(daily_indices) - 1)

        for idx in daily_indices[:to_break]:
            dates = habits[idx]["completion_dates"]
            if len(dates) >= 3:
                # Remove one day roughly in the middle to create a gap
                gap_index = len(dates) // 2
                del dates[gap_index]

        return habits


class ShuffledDataFactory(ExampleDataFactory):
    """
    Imperfect example dataset:
    • Uses perfect data, then shuffles completion_dates
      for the first daily habit to test sorting logic.
    """

    def mutate(self, habits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        import random

        for h in habits:
            if h["periodicity"] == "daily":
                random.shuffle(h["completion_dates"])
                break
        return habits
