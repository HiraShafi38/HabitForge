from datetime import datetime

import pytest

from fixtures import FIXTURE_START, seed_predefined_data
from main import (
    analytics_consistency,
    analytics_longest_overall,
    analytics_struggle,
    complete_habit,
    create_habit,
    delete_habit,
    main_menu,
    prompt_date_range,
    prompt_periodicity,
    view_habits,
)
from models import Habit, Periodicity
from repository import HabitRepository


@pytest.fixture
def repository():
    """Create a clean in-memory repository for every CLI test."""

    repo = HabitRepository(":memory:")

    yield repo

    repo.close()


@pytest.fixture
def seeded_repository():
    """Create a repository containing the predefined fixture."""

    repo = HabitRepository(":memory:")
    seed_predefined_data(repo)

    yield repo

    repo.close()


def test_prompt_periodicity_daily(monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    result = prompt_periodicity()

    assert result == Periodicity.DAILY


def test_prompt_periodicity_weekly(monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "2",
    )

    result = prompt_periodicity()

    assert result == Periodicity.WEEKLY


def test_prompt_periodicity_retries_invalid_input(
    monkeypatch,
):
    inputs = iter(
        [
            "invalid",
            "9",
            "1",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = prompt_periodicity()

    assert result == Periodicity.DAILY


def test_prompt_date_range(monkeypatch):
    inputs = iter(
        [
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = prompt_date_range()

    assert result is not None

    start, end = result

    assert start == datetime(
        2026,
        8,
        3,
    )

    assert end == datetime(
        2026,
        8,
        30,
        23,
        59,
        59,
    )


def test_create_habit(
    repository,
    monkeypatch,
):
    inputs = iter(
        [
            "Study Python",
            "1",
            "Study Python for 30 minutes.",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    create_habit(repository)

    habits = repository.get_habits()

    assert len(habits) == 1
    assert habits[0].name == "Study Python"
    assert habits[0].periodicity == Periodicity.DAILY
    assert habits[0].description == (
        "Study Python for 30 minutes."
    )


def test_complete_habit(
    repository,
    monkeypatch,
):
    habit = repository.create_habit(
        Habit(
            name="Exercise",
            periodicity=Periodicity.DAILY,
        )
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(habit.id),
    )

    complete_habit(repository)

    completions = repository.get_completions(
        habit.id
    )

    assert len(completions) == 1
    assert completions[0].habit_id == habit.id


def test_delete_habit_confirmed(
    repository,
    monkeypatch,
):
    habit = repository.create_habit(
        Habit(
            name="Meditation",
            periodicity=Periodicity.DAILY,
        )
    )

    repository.record_completion(
        habit.id
    )

    inputs = iter(
        [
            str(habit.id),
            "y",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    delete_habit(repository)

    assert repository.get_habit(
        habit.id
    ) is None

    assert repository.get_completions(
        habit.id
    ) == []


def test_delete_habit_cancelled(
    repository,
    monkeypatch,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    inputs = iter(
        [
            str(habit.id),
            "n",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    delete_habit(repository)

    assert repository.get_habit(
        habit.id
    ) is not None


def test_view_habits(
    repository,
    capsys,
):
    repository.create_habit(
        Habit(
            name="Drink Water",
            periodicity=Periodicity.DAILY,
        )
    )

    view_habits(repository)

    output = capsys.readouterr().out

    assert "TRACKED HABITS" in output
    assert "Drink Water" in output
    assert "Daily" in output


def test_longest_streak_overall(
    seeded_repository,
    capsys,
):
    analytics_longest_overall(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Drink Water" in output
    assert "28 days" in output


def test_consistency_analysis(
    seeded_repository,
    monkeypatch,
    capsys,
):
    drink_water = next(
        habit
        for habit in seeded_repository.get_habits()
        if habit.name == "Drink Water"
    )

    inputs = iter(
        [
            str(drink_water.id),
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    analytics_consistency(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Drink Water" in output
    assert "100.0%" in output
    assert "Missed periods: 0" in output


def test_struggle_analysis(
    seeded_repository,
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    analytics_struggle(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Morning Workout" in output
    assert "57.1%" in output


def test_main_menu_exit(
    repository,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    main_menu(repository)

    output = capsys.readouterr().out

    assert "HABITFORGE" in output

    assert (
        "Thank you for using HabitForge."
        in output
    )
    