"""
Predefined deterministic fixture data for HabitForge.

Provides deterministic tracking data for five predefined habits
across a four-week period. The fixture deliberately contains different behavioural
patterns so analytics can be tested against known results.
"""

from datetime import datetime, timedelta
from typing import Dict, List

from models import Habit, Periodicity
from repository import HabitRepository


# Monday, beginning of the four-week fixture period.
FIXTURE_START = datetime(
    2026,
    8,
    3,
    0,
    0,
    0,
)

# Four complete weeks.
FIXTURE_DAYS = 28

# Metadata key used to ensure fixture data is initialized only once.
FIXTURE_SEED_KEY = "predefined_fixture_seeded"


def _daily_dates(
    completed_days: List[int],
    hour: int = 8,
) -> List[datetime]:
    """
    Convert zero-based day offsets into completion timestamps.
    """

    return [
        (
            FIXTURE_START
            + timedelta(days=day)
        ).replace(
            hour=hour,
            minute=0,
            second=0,
            microsecond=0,
        )
        for day in completed_days
    ]


def _weekly_dates(
    completed_weeks: List[int],
    weekday_offset: int = 0,
    hour: int = 18,
) -> List[datetime]:
    """
    Convert zero-based week offsets into completion timestamps.
    """

    return [
        (
            FIXTURE_START
            + timedelta(
                weeks=week,
                days=weekday_offset,
            )
        ).replace(
            hour=hour,
            minute=0,
            second=0,
            microsecond=0,
        )
        for week in completed_weeks
    ]


def build_fixture_definition() -> List[Dict]:
    """
    Return definitions for the five predefined HabitForge habits.

    Each habit has a deliberately different completion pattern so
    streak, consistency, and struggle analytics have predictable
    expected results.
    """

    return [
        {
            "name": "Drink Water",
            "description": (
                "Drink at least two litres of water during the day."
            ),
            "periodicity": Periodicity.DAILY,
            "created_at": FIXTURE_START,
            # 28/28 successful days.
            # Longest streak: 28 days.
            "completions": _daily_dates(
                list(range(28)),
                hour=8,
            ),
        },
        {
            "name": "Read 30 Minutes",
            "description": (
                "Read a book or other meaningful material "
                "for at least 30 minutes."
            ),
            "periodicity": Periodicity.DAILY,
            "created_at": FIXTURE_START,
            # Misses days 6, 13, 20 and 27.
            # 24/28 successful days.
            # Longest streak: 6 days.
            "completions": _daily_dates(
                [
                    day
                    for day in range(28)
                    if day not in {
                        6,
                        13,
                        20,
                        27,
                    }
                ],
                hour=20,
            ),
        },
        {
            "name": "Morning Workout",
            "description": (
                "Complete a morning exercise or workout session."
            ),
            "periodicity": Periodicity.DAILY,
            "created_at": FIXTURE_START,
            # Irregular pattern.
            # 16/28 successful days.
            # Longest streak: 3 days.
            "completions": _daily_dates(
                [
                    0,
                    1,
                    2,
                    4,
                    7,
                    8,
                    10,
                    11,
                    12,
                    16,
                    17,
                    19,
                    21,
                    24,
                    25,
                    26,
                ],
                hour=7,
            ),
        },
        {
            "name": "Meditation",
            "description": (
                "Complete a daily meditation session."
            ),
            "periodicity": Periodicity.DAILY,
            "created_at": FIXTURE_START,
            # 22/28 successful days.
            # Longest streak: 4 days.
            "completions": _daily_dates(
                [
                    day
                    for day in range(28)
                    if day not in {
                        4,
                        9,
                        14,
                        19,
                        24,
                        27,
                    }
                ],
                hour=21,
            ),
        },
        {
            "name": "Weekly Planning",
            "description": (
                "Review the previous week and prepare priorities "
                "for the coming week."
            ),
            "periodicity": Periodicity.WEEKLY,
            "created_at": FIXTURE_START,
            # Weeks 1, 2 and 4 are completed.
            # Week 3 is missed.
            # Longest streak: 2 weeks.
            "completions": _weekly_dates(
                [
                    0,
                    1,
                    3,
                ],
                weekday_offset=0,
                hour=18,
            ),
        },
    ]


def seed_predefined_data(
    repository: HabitRepository,
) -> List[Habit]:
    """
    Initialize the predefined fixture exactly once.

    A metadata marker remembers that fixture initialization has already
    occurred. Therefore, if the user later deletes the predefined
    habits, those habits will not automatically reappear after restart.

    Existing databases created before this metadata mechanism are also
    handled safely. If habits already exist, HabitForge marks the fixture
    as initialized without inserting duplicates.

    Returns:
        Currently stored Habit objects.
    """

    already_seeded = (
        repository.get_metadata(
            FIXTURE_SEED_KEY
        )
        == "true"
    )

    if already_seeded:
        return repository.get_habits()

    existing_habits = repository.get_habits()

    # Handle databases that already contain data but were created
    # before the fixture metadata mechanism was introduced.
    if existing_habits:
        repository.set_metadata(
            FIXTURE_SEED_KEY,
            "true",
        )

        return existing_habits

    created_habits: List[Habit] = []

    for definition in build_fixture_definition():

        habit = Habit(
            name=definition["name"],
            description=definition[
                "description"
            ],
            periodicity=definition[
                "periodicity"
            ],
            created_at=definition[
                "created_at"
            ],
        )

        repository.create_habit(
            habit
        )

        for completion_time in definition[
            "completions"
        ]:
            repository.record_completion(
                habit.id,
                completion_time,
            )

        created_habits.append(
            habit
        )

    repository.set_metadata(
        FIXTURE_SEED_KEY,
        "true",
    )

    return created_habits
