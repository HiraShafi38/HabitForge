from datetime import datetime

import pytest

from models import Completion, Habit, Periodicity


def test_daily_periodicity_value():
    assert Periodicity.DAILY.value == "daily"


def test_weekly_periodicity_value():
    assert Periodicity.WEEKLY.value == "weekly"


def test_create_daily_habit():
    habit = Habit(
        name="Drink Water",
        periodicity=Periodicity.DAILY,
        description="Drink at least two litres of water.",
    )

    assert habit.name == "Drink Water"
    assert habit.periodicity == Periodicity.DAILY
    assert habit.description == "Drink at least two litres of water."
    assert habit.id is None
    assert isinstance(habit.created_at, datetime)


def test_create_weekly_habit():
    habit = Habit(
        name="Weekly Planning",
        periodicity=Periodicity.WEEKLY,
    )

    assert habit.name == "Weekly Planning"
    assert habit.periodicity == Periodicity.WEEKLY
    assert habit.description == ""


def test_habit_name_whitespace_is_removed():
    habit = Habit(
        name="   Meditation   ",
        periodicity=Periodicity.DAILY,
    )

    assert habit.name == "Meditation"


def test_empty_habit_name_is_rejected():
    with pytest.raises(ValueError):
        Habit(
            name="",
            periodicity=Periodicity.DAILY,
        )


def test_whitespace_only_habit_name_is_rejected():
    with pytest.raises(ValueError):
        Habit(
            name="     ",
            periodicity=Periodicity.DAILY,
        )


def test_invalid_periodicity_is_rejected():
    with pytest.raises(ValueError):
        Habit(
            name="Reading",
            periodicity="daily",
        )


def test_habit_with_existing_id():
    habit = Habit(
        id=5,
        name="Exercise",
        periodicity=Periodicity.DAILY,
    )

    assert habit.id == 5


def test_invalid_habit_id_is_rejected():
    with pytest.raises(ValueError):
        Habit(
            id=0,
            name="Exercise",
            periodicity=Periodicity.DAILY,
        )


def test_create_completion():
    completion = Completion(habit_id=1)

    assert completion.habit_id == 1
    assert completion.id is None
    assert isinstance(completion.completed_at, datetime)


def test_completion_with_existing_id():
    completion = Completion(
        id=10,
        habit_id=3,
    )

    assert completion.id == 10
    assert completion.habit_id == 3


def test_invalid_completion_habit_id_is_rejected():
    with pytest.raises(ValueError):
        Completion(habit_id=0)


def test_completion_requires_integer_habit_id():
    with pytest.raises(TypeError):
        Completion(habit_id="1")


def test_custom_habit_creation_timestamp():
    creation_time = datetime(2026, 9, 1, 8, 30)

    habit = Habit(
        name="Morning Workout",
        periodicity=Periodicity.DAILY,
        created_at=creation_time,
    )

    assert habit.created_at == creation_time


def test_custom_completion_timestamp():
    completion_time = datetime(2026, 9, 2, 19, 45)

    completion = Completion(
        habit_id=1,
        completed_at=completion_time,
    )

    assert completion.completed_at == completion_time


def test_habit_string_representation():
    habit = Habit(
        name="Read 30 Minutes",
        periodicity=Periodicity.DAILY,
    )

    assert str(habit) == "Read 30 Minutes (Daily)"

def test_habit_name_must_be_string():
    with pytest.raises(TypeError):
        Habit(
            name=123,
            periodicity=Periodicity.DAILY,
        )


def test_habit_description_must_be_string():
    with pytest.raises(TypeError):
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
            description=123,
        )


def test_habit_id_must_be_integer_when_present():
    with pytest.raises(TypeError):
        Habit(
            id="1",
            name="Reading",
            periodicity=Periodicity.DAILY,
        )


def test_habit_creation_time_must_be_datetime():
    with pytest.raises(TypeError):
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
            created_at="2026-08-03",
        )


def test_completion_id_must_be_integer_when_present():
    with pytest.raises(TypeError):
        Completion(
            id="1",
            habit_id=1,
        )


def test_completion_id_must_be_positive():
    with pytest.raises(ValueError):
        Completion(
            id=0,
            habit_id=1,
        )


def test_completion_time_must_be_datetime():
    with pytest.raises(TypeError):
        Completion(
            habit_id=1,
            completed_at="2026-08-03",
        )


def test_completion_string_representation():
    completion = Completion(
        id=1,
        habit_id=3,
        completed_at=datetime(
            2026,
            8,
            3,
            12,
            30,
        ),
    )

    result = str(completion)

    assert "Habit 3" in result
    assert "2026-08-03 12:30:00" in result    

