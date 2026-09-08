"""
Domain models for the HabitForge application.

This module contains the core objects used throughout the application:
- Periodicity: allowed habit frequencies
- Habit: represents a habit tracked by the user
- Completion: represents a recorded habit completion
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Periodicity(Enum):
    """
    Represents the supported habit periods.

    HabitForge currently supports daily and weekly habits.
    """

    DAILY = "daily"
    WEEKLY = "weekly"

    def __str__(self) -> str:
        """Return a user-friendly representation of the periodicity."""
        return self.value


@dataclass
class Habit:
    """
    Represents a habit that is tracked by the application.

    Attributes:
        name:
            Short name or task specification of the habit.
        periodicity:
            Frequency at which the habit must be completed.
        description:
            Optional additional information about the habit.
        id:
            Database identifier. It remains None until the habit is stored.
        created_at:
            Date and time at which the habit was created.
    """

    name: str
    periodicity: Periodicity
    description: str = ""
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """
        Validate and normalize habit data after initialization.

        Raises:
            ValueError:
                If the habit name is empty or the periodicity is invalid.
            TypeError:
                If supplied values have unexpected types.
        """

        if not isinstance(self.name, str):
            raise TypeError("Habit name must be a string.")

        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Habit name cannot be empty.")

        if not isinstance(self.periodicity, Periodicity):
            raise ValueError(
                "Periodicity must be Periodicity.DAILY or "
                "Periodicity.WEEKLY."
            )

        if not isinstance(self.description, str):
            raise TypeError("Habit description must be a string.")

        self.description = self.description.strip()

        if self.id is not None:
            if not isinstance(self.id, int):
                raise TypeError("Habit ID must be an integer or None.")

            if self.id <= 0:
                raise ValueError("Habit ID must be greater than zero.")

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime object.")

    def __str__(self) -> str:
        """Return a readable representation of the habit."""

        return (
            f"{self.name} "
            f"({self.periodicity.value.capitalize()})"
        )


@dataclass
class Completion:
    """
    Represents one recorded completion of a habit.

    A habit may have multiple completion records. The analytics layer
    later groups these timestamps into daily or weekly periods when
    calculating streaks.

    Attributes:
        habit_id:
            Database identifier of the habit being completed.
        completed_at:
            Date and time at which the completion was recorded.
        id:
            Database identifier of this completion record.
    """

    habit_id: int
    completed_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def __post_init__(self) -> None:
        """
        Validate completion data after initialization.

        Raises:
            TypeError:
                If the habit ID, completion ID, or timestamp has an
                unexpected type.
            ValueError:
                If an identifier is not positive.
        """

        if not isinstance(self.habit_id, int):
            raise TypeError("habit_id must be an integer.")

        if self.habit_id <= 0:
            raise ValueError("habit_id must be greater than zero.")

        if self.id is not None:
            if not isinstance(self.id, int):
                raise TypeError(
                    "Completion ID must be an integer or None."
                )

            if self.id <= 0:
                raise ValueError(
                    "Completion ID must be greater than zero."
                )

        if not isinstance(self.completed_at, datetime):
            raise TypeError(
                "completed_at must be a datetime object."
            )

    def __str__(self) -> str:
        """Return a readable representation of the completion."""

        return (
            f"Habit {self.habit_id} completed at "
            f"{self.completed_at:%Y-%m-%d %H:%M:%S}"
        )
    