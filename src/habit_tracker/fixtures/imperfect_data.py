from __future__ import annotations

from typing import Any, Dict, List

from habit_tracker.fixtures.example_data import ExampleDataFactory


class MissingDayDataFactory(ExampleDataFactory):
    """
    Imperfect example dataset:
    • Based on perfect data from ExampleDataFactory
    • For each daily habit, remove one completion to break the streak.
    """

    def mutate(self, habits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for h in habits:
            if h["periodicity"] == "daily":
                dates = h["completion_dates"]
                if len(dates) > 10:
                    # remove the 11th date to create a gap
                    del dates[10]
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
