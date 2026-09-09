"""
Tests for the HabitForge command-line interface.

The CLI tests use monkeypatch to simulate user input and capsys to
inspect displayed output without requiring manual interaction.
"""

from datetime import datetime

import pytest

import main as app
from fixtures import seed_predefined_data
from models import Habit, Periodicity
from repository import HabitRepository


@pytest.fixture
def repository():
    """Provide a clean in-memory repository."""

    repo = HabitRepository(":memory:")

    yield repo

    repo.close()


@pytest.fixture
def seeded_repository():
    """Provide a repository containing predefined HabitForge data."""

    repo = HabitRepository(":memory:")

    seed_predefined_data(repo)

    yield repo

    repo.close()


# ----------------------------------------------------------------------
# Display helpers
# ----------------------------------------------------------------------

def test_print_header(capsys):
    app.print_header("TEST")

    output = capsys.readouterr().out

    assert "TEST" in output
    assert "=" in output


def test_periodicity_label_daily():
    assert (
        app.periodicity_label(
            Periodicity.DAILY
        )
        == "Daily"
    )


def test_periodicity_label_weekly():
    assert (
        app.periodicity_label(
            Periodicity.WEEKLY
        )
        == "Weekly"
    )


def test_daily_streak_label_singular():
    habit = Habit(
        name="Test",
        periodicity=Periodicity.DAILY,
    )

    assert (
        app.streak_label(
            habit,
            1,
        )
        == "1 day"
    )


def test_daily_streak_label_plural():
    habit = Habit(
        name="Test",
        periodicity=Periodicity.DAILY,
    )

    assert (
        app.streak_label(
            habit,
            4,
        )
        == "4 days"
    )


def test_weekly_streak_label_singular():
    habit = Habit(
        name="Test",
        periodicity=Periodicity.WEEKLY,
    )

    assert (
        app.streak_label(
            habit,
            1,
        )
        == "1 week"
    )


def test_weekly_streak_label_plural():
    habit = Habit(
        name="Test",
        periodicity=Periodicity.WEEKLY,
    )

    assert (
        app.streak_label(
            habit,
            3,
        )
        == "3 weeks"
    )


def test_display_empty_habit_list(
    capsys,
):
    app.display_habit_list([])

    output = capsys.readouterr().out

    assert (
        "No habits are currently being tracked."
        in output
    )


def test_display_habit_with_description(
    repository,
    capsys,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
            description="Read for 30 minutes.",
        )
    )

    app.display_habit_list(
        [habit],
        show_description=True,
    )

    output = capsys.readouterr().out

    assert "Reading" in output
    assert "Daily" in output
    assert "Read for 30 minutes." in output


# ----------------------------------------------------------------------
# Habit selection
# ----------------------------------------------------------------------

def test_select_habit_when_repository_empty(
    repository,
    capsys,
):
    result = app.select_habit(
        repository
    )

    assert result is None

    output = capsys.readouterr().out

    assert (
        "No habits are currently available."
        in output
    )


def test_select_habit_can_be_cancelled(
    repository,
    monkeypatch,
):
    repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    assert (
        app.select_habit(repository)
        is None
    )


def test_select_habit_retries_invalid_text(
    repository,
    monkeypatch,
    capsys,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    inputs = iter(
        [
            "abc",
            str(habit.id),
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = app.select_habit(
        repository
    )

    assert result.id == habit.id

    output = capsys.readouterr().out

    assert (
        "Invalid input"
        in output
    )


def test_select_habit_retries_unknown_id(
    repository,
    monkeypatch,
    capsys,
):
    habit = repository.create_habit(
        Habit(
            name="Reading",
            periodicity=Periodicity.DAILY,
        )
    )

    inputs = iter(
        [
            "999",
            str(habit.id),
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = app.select_habit(
        repository
    )

    assert result.id == habit.id

    output = capsys.readouterr().out

    assert "No habit exists with ID 999" in output


# ----------------------------------------------------------------------
# Periodicity input
# ----------------------------------------------------------------------

def test_prompt_periodicity_daily(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    assert (
        app.prompt_periodicity()
        == Periodicity.DAILY
    )


def test_prompt_periodicity_weekly(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "2",
    )

    assert (
        app.prompt_periodicity()
        == Periodicity.WEEKLY
    )


def test_prompt_periodicity_cancel(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    assert (
        app.prompt_periodicity()
        is None
    )


def test_prompt_periodicity_retries_invalid(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "9",
            "1",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = app.prompt_periodicity()

    assert result == Periodicity.DAILY

    output = capsys.readouterr().out

    assert "Invalid selection" in output


# ----------------------------------------------------------------------
# Date range input
# ----------------------------------------------------------------------

def test_prompt_valid_date_range(
    monkeypatch,
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

    result = app.prompt_date_range()

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


def test_prompt_date_range_cancel_at_start(
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    assert (
        app.prompt_date_range()
        is None
    )


def test_prompt_date_range_cancel_at_end(
    monkeypatch,
):
    inputs = iter(
        [
            "2026-08-03",
            "0",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    assert (
        app.prompt_date_range()
        is None
    )


def test_prompt_date_range_retries_invalid_date(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "wrong",
            "2026-08-30",
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = app.prompt_date_range()

    assert result is not None

    output = capsys.readouterr().out

    assert "Invalid date" in output


def test_prompt_date_range_retries_reversed_range(
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "2026-08-30",
            "2026-08-03",
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    result = app.prompt_date_range()

    assert result is not None

    output = capsys.readouterr().out

    assert (
        "End date cannot be earlier"
        in output
    )


# ----------------------------------------------------------------------
# Habit-management operations
# ----------------------------------------------------------------------

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

    app.view_habits(
        repository
    )

    output = capsys.readouterr().out

    assert "TRACKED HABITS" in output
    assert "Drink Water" in output


def test_create_daily_habit(
    repository,
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "Study Python",
            "1",
            "Practice Python daily.",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.create_habit(
        repository
    )

    habits = repository.get_habits()

    assert len(habits) == 1
    assert habits[0].name == "Study Python"

    output = capsys.readouterr().out

    assert "Habit created successfully" in output


def test_create_habit_cancelled_at_name(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    app.create_habit(
        repository
    )

    assert repository.get_habits() == []


def test_create_habit_cancelled_at_periodicity(
    repository,
    monkeypatch,
):
    inputs = iter(
        [
            "Reading",
            "0",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.create_habit(
        repository
    )

    assert repository.get_habits() == []


def test_create_habit_rejects_blank_name(
    repository,
    monkeypatch,
    capsys,
):
    inputs = iter(
        [
            "   ",
            "1",
            "",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.create_habit(
        repository
    )

    assert repository.get_habits() == []

    output = capsys.readouterr().out

    assert (
        "Habit could not be created"
        in output
    )


def test_complete_habit(
    repository,
    monkeypatch,
    capsys,
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

    app.complete_habit(
        repository
    )

    assert len(
        repository.get_completions(
            habit.id
        )
    ) == 1

    output = capsys.readouterr().out

    assert (
        "Completion recorded successfully"
        in output
    )


def test_complete_habit_when_none_exist(
    repository,
    capsys,
):
    app.complete_habit(
        repository
    )

    assert (
        repository.get_completions()
        == []
    )

    output = capsys.readouterr().out

    assert (
        "No habits are currently available."
        in output
    )


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

    app.delete_habit(
        repository
    )

    assert (
        repository.get_habit(
            habit.id
        )
        is None
    )

    assert (
        repository.get_completions(
            habit.id
        )
        == []
    )


def test_delete_habit_cancelled(
    repository,
    monkeypatch,
    capsys,
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

    app.delete_habit(
        repository
    )

    assert (
        repository.get_habit(
            habit.id
        )
        is not None
    )

    output = capsys.readouterr().out

    assert "Deletion cancelled" in output


def test_delete_habit_when_none_exist(
    repository,
):
    app.delete_habit(
        repository
    )

    assert repository.get_habits() == []


# ----------------------------------------------------------------------
# Analytics actions
# ----------------------------------------------------------------------

def test_analytics_all_habits(
    seeded_repository,
    capsys,
):
    app.analytics_all_habits(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "ALL TRACKED HABITS" in output
    assert "Drink Water" in output


def test_analytics_by_daily_periodicity(
    seeded_repository,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "1",
    )

    app.analytics_by_periodicity(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "DAILY HABITS" in output
    assert "Drink Water" in output


def test_analytics_by_periodicity_cancel(
    seeded_repository,
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    app.analytics_by_periodicity(
        seeded_repository
    )


def test_longest_streak_overall(
    seeded_repository,
    capsys,
):
    app.analytics_longest_overall(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Drink Water" in output
    assert "28 days" in output


def test_longest_streak_overall_no_habits(
    repository,
    capsys,
):
    app.analytics_longest_overall(
        repository
    )

    output = capsys.readouterr().out

    assert "No habits are available" in output


def test_longest_streak_for_selected_habit(
    seeded_repository,
    monkeypatch,
    capsys,
):
    habit = next(
        habit
        for habit
        in seeded_repository.get_habits()
        if habit.name == "Weekly Planning"
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: str(habit.id),
    )

    app.analytics_longest_for_habit(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Weekly Planning" in output
    assert "2 weeks" in output


def test_current_streaks_no_habits(
    repository,
    capsys,
):
    app.analytics_current_streaks(
        repository
    )

    output = capsys.readouterr().out

    assert "No habits are available" in output


def test_current_streaks_with_habits(
    seeded_repository,
    capsys,
):
    app.analytics_current_streaks(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "CURRENT STREAKS" in output
    assert "Drink Water" in output


def test_consistency_analysis(
    seeded_repository,
    monkeypatch,
    capsys,
):
    habit = next(
        habit
        for habit
        in seeded_repository.get_habits()
        if habit.name == "Drink Water"
    )

    inputs = iter(
        [
            str(habit.id),
            "2026-08-03",
            "2026-08-30",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.analytics_consistency(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "100.0%" in output
    assert "Missed periods: 0" in output


def test_consistency_cancel_habit_selection(
    seeded_repository,
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    app.analytics_consistency(
        seeded_repository
    )


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

    app.analytics_struggle(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "Morning Workout" in output
    assert "57.1%" in output


def test_struggle_analysis_no_habits(
    repository,
    capsys,
):
    app.analytics_struggle(
        repository
    )

    output = capsys.readouterr().out

    assert "No habits are available" in output


def test_performance_report(
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

    app.analytics_performance_report(
        seeded_repository
    )

    output = capsys.readouterr().out

    assert "HABIT PERFORMANCE REPORT" in output
    assert "Drink Water" in output
    assert "100.0%" in output


def test_performance_report_cancelled(
    seeded_repository,
    monkeypatch,
):
    monkeypatch.setattr(
        "builtins.input",
        lambda _: "0",
    )

    app.analytics_performance_report(
        seeded_repository
    )


# ----------------------------------------------------------------------
# Menu routing
# ----------------------------------------------------------------------

def test_analytics_menu_routes_all_options(
    repository,
    monkeypatch,
    capsys,
):
    calls = []

    monkeypatch.setattr(
        app,
        "analytics_all_habits",
        lambda repo: calls.append("1"),
    )

    monkeypatch.setattr(
        app,
        "analytics_by_periodicity",
        lambda repo: calls.append("2"),
    )

    monkeypatch.setattr(
        app,
        "analytics_longest_overall",
        lambda repo: calls.append("3"),
    )

    monkeypatch.setattr(
        app,
        "analytics_longest_for_habit",
        lambda repo: calls.append("4"),
    )

    monkeypatch.setattr(
        app,
        "analytics_current_streaks",
        lambda repo: calls.append("5"),
    )

    monkeypatch.setattr(
        app,
        "analytics_consistency",
        lambda repo: calls.append("6"),
    )

    monkeypatch.setattr(
        app,
        "analytics_struggle",
        lambda repo: calls.append("7"),
    )

    monkeypatch.setattr(
        app,
        "analytics_performance_report",
        lambda repo: calls.append("8"),
    )

    monkeypatch.setattr(
        app,
        "pause",
        lambda: None,
    )

    inputs = iter(
        [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "invalid",
            "0",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.analytics_menu(
        repository
    )

    assert calls == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
    ]

    output = capsys.readouterr().out

    assert "Invalid selection" in output


def test_main_menu_routes_all_options(
    repository,
    monkeypatch,
    capsys,
):
    calls = []

    monkeypatch.setattr(
        app,
        "view_habits",
        lambda repo: calls.append("1"),
    )

    monkeypatch.setattr(
        app,
        "create_habit",
        lambda repo: calls.append("2"),
    )

    monkeypatch.setattr(
        app,
        "complete_habit",
        lambda repo: calls.append("3"),
    )

    monkeypatch.setattr(
        app,
        "delete_habit",
        lambda repo: calls.append("4"),
    )

    monkeypatch.setattr(
        app,
        "analytics_menu",
        lambda repo: calls.append("5"),
    )

    monkeypatch.setattr(
        app,
        "pause",
        lambda: None,
    )

    inputs = iter(
        [
            "1",
            "2",
            "3",
            "4",
            "5",
            "invalid",
            "0",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(inputs),
    )

    app.main_menu(
        repository
    )

    assert calls == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    output = capsys.readouterr().out

    assert "Invalid selection" in output

    assert (
        "Thank you for using HabitForge."
        in output
    )


# ----------------------------------------------------------------------
# Main application lifecycle
# ----------------------------------------------------------------------

def test_main_initializes_and_closes_repository(
    monkeypatch,
):
    class FakeRepository:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake_repository = FakeRepository()

    monkeypatch.setattr(
        app,
        "HabitRepository",
        lambda path: fake_repository,
    )

    monkeypatch.setattr(
        app,
        "seed_predefined_data",
        lambda repo: None,
    )

    monkeypatch.setattr(
        app,
        "main_menu",
        lambda repo: None,
    )

    app.main()

    assert fake_repository.closed is True


def test_main_handles_keyboard_interrupt(
    monkeypatch,
    capsys,
):
    class FakeRepository:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake_repository = FakeRepository()

    monkeypatch.setattr(
        app,
        "HabitRepository",
        lambda path: fake_repository,
    )

    monkeypatch.setattr(
        app,
        "seed_predefined_data",
        lambda repo: None,
    )

    def interrupt(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        app,
        "main_menu",
        interrupt,
    )

    app.main()

    assert fake_repository.closed is True

    output = capsys.readouterr().out

    assert "interrupted by the user" in output