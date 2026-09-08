"""
Tests for HabitForge's predefined four-week fixture.
"""

from datetime import timedelta

from fixtures import (
    FIXTURE_DAYS,
    FIXTURE_SEED_KEY,
    FIXTURE_START,
    build_fixture_definition,
    seed_predefined_data,
)
from models import Habit, Periodicity
from repository import HabitRepository


def _get_definition(
    fixture,
    name,
):
    """Retrieve one fixture definition by habit name."""

    return next(
        item
        for item in fixture
        if item["name"] == name
    )


def test_fixture_contains_five_habits():
    fixture = build_fixture_definition()

    assert len(fixture) == 5


def test_fixture_contains_daily_and_weekly_habits():
    fixture = build_fixture_definition()

    periodicities = {
        definition["periodicity"]
        for definition in fixture
    }

    assert Periodicity.DAILY in periodicities
    assert Periodicity.WEEKLY in periodicities


def test_fixture_habit_names():
    fixture = build_fixture_definition()

    names = {
        definition["name"]
        for definition in fixture
    }

    assert names == {
        "Drink Water",
        "Read 30 Minutes",
        "Morning Workout",
        "Meditation",
        "Weekly Planning",
    }


def test_drink_water_has_28_completions():
    fixture = build_fixture_definition()

    drink_water = _get_definition(
        fixture,
        "Drink Water",
    )

    assert (
        len(drink_water["completions"])
        == 28
    )


def test_reading_has_24_completions():
    fixture = build_fixture_definition()

    reading = _get_definition(
        fixture,
        "Read 30 Minutes",
    )

    assert (
        len(reading["completions"])
        == 24
    )


def test_workout_has_16_completions():
    fixture = build_fixture_definition()

    workout = _get_definition(
        fixture,
        "Morning Workout",
    )

    assert (
        len(workout["completions"])
        == 16
    )


def test_meditation_has_22_completions():
    fixture = build_fixture_definition()

    meditation = _get_definition(
        fixture,
        "Meditation",
    )

    assert (
        len(meditation["completions"])
        == 22
    )


def test_weekly_planning_has_three_completions():
    fixture = build_fixture_definition()

    planning = _get_definition(
        fixture,
        "Weekly Planning",
    )

    assert (
        len(planning["completions"])
        == 3
    )


def test_fixture_covers_four_weeks():
    fixture = build_fixture_definition()

    assert FIXTURE_DAYS == 28

    all_dates = [
        completion
        for definition in fixture
        for completion
        in definition["completions"]
    ]

    assert min(all_dates) >= FIXTURE_START

    assert max(all_dates) < (
        FIXTURE_START
        + timedelta(
            days=FIXTURE_DAYS
        )
    )


def test_no_fixture_completion_occurs_before_habit_creation():
    fixture = build_fixture_definition()

    for definition in fixture:

        created_at = definition[
            "created_at"
        ]

        assert all(
            completion >= created_at
            for completion
            in definition["completions"]
        )


def test_seed_creates_five_habits():
    repository = HabitRepository(
        ":memory:"
    )

    habits = seed_predefined_data(
        repository
    )

    assert len(habits) == 5

    assert len(
        repository.get_habits()
    ) == 5

    repository.close()


def test_seed_stores_all_completion_records():
    repository = HabitRepository(
        ":memory:"
    )

    seed_predefined_data(
        repository
    )

    completions = (
        repository.get_completions()
    )

    # 28 + 24 + 16 + 22 + 3
    assert len(completions) == 93

    repository.close()


def test_fixture_metadata_is_recorded():
    repository = HabitRepository(
        ":memory:"
    )

    seed_predefined_data(
        repository
    )

    assert (
        repository.get_metadata(
            FIXTURE_SEED_KEY
        )
        == "true"
    )

    repository.close()


def test_seed_is_idempotent():
    """
    Calling the seed function repeatedly must not create duplicates.
    """

    repository = HabitRepository(
        ":memory:"
    )

    seed_predefined_data(
        repository
    )

    seed_predefined_data(
        repository
    )

    assert len(
        repository.get_habits()
    ) == 5

    assert len(
        repository.get_completions()
    ) == 93

    repository.close()


def test_deleted_predefined_habits_are_not_restored():
    """
    Deleting fixture habits must remain persistent.

    Once fixture initialization has occurred, an empty habits table
    must not cause the predefined habits to be recreated.
    """

    repository = HabitRepository(
        ":memory:"
    )

    seed_predefined_data(
        repository
    )

    habits = repository.get_habits()

    assert len(habits) == 5

    for habit in habits:
        repository.delete_habit(
            habit.id
        )

    assert (
        repository.get_habits()
        == []
    )

    assert (
        repository.get_completions()
        == []
    )

    # Simulate a later application startup.
    seed_predefined_data(
        repository
    )

    assert (
        repository.get_habits()
        == []
    )

    assert (
        repository.get_completions()
        == []
    )

    repository.close()


def test_existing_database_is_not_duplicated():
    """
    Existing databases without a fixture marker must not receive five
    additional predefined habits.
    """

    repository = HabitRepository(
        ":memory:"
    )

    repository.create_habit(
        Habit(
            name="Existing Habit",
            periodicity=Periodicity.DAILY,
        )
    )

    habits = seed_predefined_data(
        repository
    )

    assert len(habits) == 1

    assert (
        habits[0].name
        == "Existing Habit"
    )

    assert (
        repository.get_metadata(
            FIXTURE_SEED_KEY
        )
        == "true"
    )

    # Running initialization again must still
    # leave only the existing habit.
    seed_predefined_data(
        repository
    )

    assert len(
        repository.get_habits()
    ) == 1

    repository.close()


def test_fixture_daily_habit_patterns_are_deterministic():
    """
    Rebuilding the fixture must produce exactly the same timestamps.
    """

    first = build_fixture_definition()
    second = build_fixture_definition()

    assert first == second
    