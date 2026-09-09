"""
Tests for HabitForge's SQLite repository.
"""

from datetime import datetime

import pytest

from models import Habit, Periodicity
from repository import HabitRepository


@pytest.fixture
def repository():
    """Provide a fresh in-memory database for every test."""

    repo = HabitRepository(":memory:")

    yield repo

    repo.close()


def test_repository_starts_empty(
    repository,
):
    assert repository.get_habits() == []


def test_create_habit(
    repository,
):
    habit = Habit(
        name="Drink Water",
        periodicity=Periodicity.DAILY,
    )

    stored = repository.create_habit(
        habit
    )

    assert stored.id is not None
    assert stored.name == "Drink Water"


def test_get_habit(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Meditation",
            periodicity=Periodicity.DAILY,
        )
    )

    retrieved = repository.get_habit(
        habit.id
    )

    assert retrieved is not None
    assert retrieved.id == habit.id
    assert retrieved.name == "Meditation"
    assert (
        retrieved.periodicity
        == Periodicity.DAILY
    )


def test_get_nonexistent_habit_returns_none(
    repository,
):
    assert (
        repository.get_habit(999)
        is None
    )


def test_get_multiple_habits(
    repository,
):
    repository.create_habit(
        Habit(
            name="Drink Water",
            periodicity=Periodicity.DAILY,
        )
    )

    repository.create_habit(
        Habit(
            name="Weekly Planning",
            periodicity=Periodicity.WEEKLY,
        )
    )

    habits = repository.get_habits()

    assert len(habits) == 2
    assert habits[0].name == "Drink Water"
    assert habits[1].name == "Weekly Planning"


def test_description_is_persisted(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
            description=(
                "Read for at least 30 minutes."
            ),
        )
    )

    retrieved = repository.get_habit(
        habit.id
    )

    assert retrieved.description == (
        "Read for at least 30 minutes."
    )


def test_creation_timestamp_is_persisted(
    repository,
):
    created_at = datetime(
        2026,
        9,
        1,
        8,
        30,
    )

    habit = repository.create_habit(
        Habit(
            name="Morning Workout",
            periodicity=Periodicity.DAILY,
            created_at=created_at,
        )
    )

    retrieved = repository.get_habit(
        habit.id
    )

    assert retrieved.created_at == created_at


def test_rejects_already_stored_habit(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    with pytest.raises(ValueError):
        repository.create_habit(
            habit
        )


def test_create_habit_requires_habit_object(
    repository,
):
    with pytest.raises(TypeError):
        repository.create_habit(
            "not a habit"
        )


def test_record_completion(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Exercise",
            periodicity=Periodicity.DAILY,
        )
    )

    completion = repository.record_completion(
        habit.id
    )

    assert completion.id is not None
    assert completion.habit_id == habit.id


def test_custom_completion_timestamp(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Exercise",
            periodicity=Periodicity.DAILY,
        )
    )

    completion_time = datetime(
        2026,
        9,
        2,
        18,
        30,
    )

    repository.record_completion(
        habit.id,
        completion_time,
    )

    completions = repository.get_completions(
        habit.id
    )

    assert len(completions) == 1

    assert (
        completions[0].completed_at
        == completion_time
    )


def test_multiple_completions_are_stored(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Drink Water",
            periodicity=Periodicity.DAILY,
        )
    )

    repository.record_completion(
        habit.id,
        datetime(
            2026,
            9,
            1,
            8,
            0,
        ),
    )

    repository.record_completion(
        habit.id,
        datetime(
            2026,
            9,
            1,
            18,
            0,
        ),
    )

    completions = repository.get_completions(
        habit.id
    )

    assert len(completions) == 2


def test_completion_for_unknown_habit_is_rejected(
    repository,
):
    with pytest.raises(ValueError):
        repository.record_completion(
            999
        )


def test_delete_habit(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Meditation",
            periodicity=Periodicity.DAILY,
        )
    )

    deleted = repository.delete_habit(
        habit.id
    )

    assert deleted is True

    assert (
        repository.get_habit(
            habit.id
        )
        is None
    )


def test_delete_nonexistent_habit(
    repository,
):
    assert (
        repository.delete_habit(999)
        is False
    )


def test_deleting_habit_removes_completions(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Morning Workout",
            periodicity=Periodicity.DAILY,
        )
    )

    repository.record_completion(
        habit.id
    )

    assert len(
        repository.get_completions(
            habit.id
        )
    ) == 1

    repository.delete_habit(
        habit.id
    )

    assert (
        repository.get_completions(
            habit.id
        )
        == []
    )


def test_get_all_completions(
    repository,
):
    first_habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    second_habit = repository.create_habit(
        Habit(
            name="Weekly Planning",
            periodicity=Periodicity.WEEKLY,
        )
    )

    repository.record_completion(
        first_habit.id
    )

    repository.record_completion(
        second_habit.id
    )

    completions = repository.get_completions()

    assert len(completions) == 2


def test_habit_periodicity_survives_database_round_trip(
    repository,
):
    habit = repository.create_habit(
        Habit(
            name="Weekly Planning",
            periodicity=Periodicity.WEEKLY,
        )
    )

    retrieved = repository.get_habit(
        habit.id
    )

    assert (
        retrieved.periodicity
        == Periodicity.WEEKLY
    )


# ----------------------------------------------------------------------
# Metadata tests
# ----------------------------------------------------------------------

def test_metadata_can_be_stored_and_retrieved(
    repository,
):
    repository.set_metadata(
        "example_key",
        "example_value",
    )

    assert (
        repository.get_metadata(
            "example_key"
        )
        == "example_value"
    )


def test_unknown_metadata_returns_none(
    repository,
):
    assert (
        repository.get_metadata(
            "missing_key"
        )
        is None
    )


def test_metadata_value_can_be_updated(
    repository,
):
    repository.set_metadata(
        "status",
        "first",
    )

    repository.set_metadata(
        "status",
        "second",
    )

    assert (
        repository.get_metadata(
            "status"
        )
        == "second"
    )


# ----------------------------------------------------------------------
# Real persistence test
# ----------------------------------------------------------------------

def test_data_survives_repository_restart(
    tmp_path,
):
    """
    Prove that habits and completions persist between database sessions.
    """

    database_path = (
        tmp_path
        / "persistence_test.db"
    )

    completion_time = datetime(
        2026,
        9,
        7,
        12,
        30,
    )

    # First application/database session.
    first_repository = HabitRepository(
        str(database_path)
    )

    habit = first_repository.create_habit(
        Habit(
            name="Persistent Habit",
            periodicity=Periodicity.WEEKLY,
            description=(
                "Used to test cross-session persistence."
            ),
        )
    )

    habit_id = habit.id

    first_repository.record_completion(
        habit_id,
        completion_time,
    )

    first_repository.close()

    # Simulate restarting HabitForge by creating a completely
    # separate repository connected to the same SQLite file.
    second_repository = HabitRepository(
        str(database_path)
    )

    retrieved = second_repository.get_habit(
        habit_id
    )

    completions = (
        second_repository.get_completions(
            habit_id
        )
    )

    assert retrieved is not None
    assert retrieved.name == "Persistent Habit"
    assert (
        retrieved.periodicity
        == Periodicity.WEEKLY
    )

    assert len(completions) == 1

    assert (
        completions[0].completed_at
        == completion_time
    )

    second_repository.close()

def test_repository_context_manager():
    with HabitRepository(
        ":memory:"
    ) as repository:

        habit = repository.create_habit(
            Habit(
                name="Context Manager Habit",
                periodicity=Periodicity.DAILY,
            )
        )

        assert habit.id is not None    