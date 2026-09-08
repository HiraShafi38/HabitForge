from datetime import datetime, timedelta

import pytest

from analytics import (
    calculate_consistency_rate,
    calculate_current_streak,
    calculate_current_streak_for_habit,
    calculate_longest_streak,
    calculate_longest_streak_for_habit,
    build_performance_report,
    count_missed_periods,
    find_longest_streak_across_habits,
    find_most_struggled_habit,
    get_all_habits,
    get_habits_by_periodicity,
)
from fixtures import (
    FIXTURE_START,
    seed_predefined_data,
)
from models import Completion, Habit, Periodicity
from repository import HabitRepository


@pytest.fixture
def fixture_repository():
    """Create an in-memory repository containing the four-week fixture."""

    repository = HabitRepository(":memory:")

    seed_predefined_data(repository)

    yield repository

    repository.close()


def _get_habit(repository, name):
    """Retrieve a fixture habit by name."""

    return next(
        habit
        for habit in repository.get_habits()
        if habit.name == name
    )


def test_get_all_habits(fixture_repository):
    habits = fixture_repository.get_habits()

    result = get_all_habits(habits)

    assert len(result) == 5


def test_filter_daily_habits(fixture_repository):
    habits = fixture_repository.get_habits()

    daily = get_habits_by_periodicity(
        habits,
        Periodicity.DAILY,
    )

    assert len(daily) == 4

    assert all(
        habit.periodicity == Periodicity.DAILY
        for habit in daily
    )


def test_filter_weekly_habits(fixture_repository):
    habits = fixture_repository.get_habits()

    weekly = get_habits_by_periodicity(
        habits,
        Periodicity.WEEKLY,
    )

    assert len(weekly) == 1
    assert weekly[0].name == "Weekly Planning"


def test_invalid_periodicity_is_rejected():
    with pytest.raises(ValueError):
        get_habits_by_periodicity(
            [],
            "daily",
        )


def test_no_completions_has_zero_longest_streak():
    assert (
        calculate_longest_streak(
            [],
            Periodicity.DAILY,
        )
        == 0
    )


def test_duplicate_daily_completions_count_once():
    completions = [
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 1, 8, 0),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 1, 20, 0),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 2, 8, 0),
        ),
    ]

    assert (
        calculate_longest_streak(
            completions,
            Periodicity.DAILY,
        )
        == 2
    )


def test_missing_day_breaks_daily_streak():
    completions = [
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 1),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 2),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 4),
        ),
    ]

    assert (
        calculate_longest_streak(
            completions,
            Periodicity.DAILY,
        )
        == 2
    )


def test_weekly_streak_handles_year_transition():
    completions = [
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 12, 28),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2027, 1, 4),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2027, 1, 11),
        ),
    ]

    assert (
        calculate_longest_streak(
            completions,
            Periodicity.WEEKLY,
        )
        == 3
    )


def test_drink_water_longest_streak(fixture_repository):
    habit = _get_habit(
        fixture_repository,
        "Drink Water",
    )

    completions = fixture_repository.get_completions()

    assert (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
        == 28
    )


def test_reading_longest_streak(fixture_repository):
    habit = _get_habit(
        fixture_repository,
        "Read 30 Minutes",
    )

    completions = fixture_repository.get_completions()

    assert (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
        == 6
    )


def test_workout_longest_streak(fixture_repository):
    habit = _get_habit(
        fixture_repository,
        "Morning Workout",
    )

    completions = fixture_repository.get_completions()

    assert (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
        == 3
    )


def test_meditation_longest_streak(fixture_repository):
    habit = _get_habit(
        fixture_repository,
        "Meditation",
    )

    completions = fixture_repository.get_completions()

    assert (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
        == 4
    )


def test_weekly_planning_longest_streak(
    fixture_repository,
):
    habit = _get_habit(
        fixture_repository,
        "Weekly Planning",
    )

    completions = fixture_repository.get_completions()

    assert (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
        == 2
    )


def test_longest_streak_across_all_habits(
    fixture_repository,
):
    habits = fixture_repository.get_habits()
    completions = fixture_repository.get_completions()

    habit, streak = (
        find_longest_streak_across_habits(
            habits,
            completions,
        )
    )

    assert habit.name == "Drink Water"
    assert streak == 28


def test_current_daily_streak():
    completions = [
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 4),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 5),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 6),
        ),
    ]

    result = calculate_current_streak(
        completions,
        Periodicity.DAILY,
        datetime(2026, 9, 6, 18, 0),
    )

    assert result == 3


def test_current_streak_zero_when_current_period_missing():
    completions = [
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 4),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(2026, 9, 5),
        ),
    ]

    result = calculate_current_streak(
        completions,
        Periodicity.DAILY,
        datetime(2026, 9, 6),
    )

    assert result == 0


def test_fixture_drink_water_consistency(
    fixture_repository,
):
    habit = _get_habit(
        fixture_repository,
        "Drink Water",
    )

    completions = fixture_repository.get_completions()

    end = FIXTURE_START + timedelta(
        days=27,
        hours=23,
    )

    rate = calculate_consistency_rate(
        habit,
        completions,
        FIXTURE_START,
        end,
    )

    assert rate == pytest.approx(100.0)


def test_reading_consistency(
    fixture_repository,
):
    habit = _get_habit(
        fixture_repository,
        "Read 30 Minutes",
    )

    completions = fixture_repository.get_completions()

    end = FIXTURE_START + timedelta(
        days=27,
        hours=23,
    )

    rate = calculate_consistency_rate(
        habit,
        completions,
        FIXTURE_START,
        end,
    )

    assert rate == pytest.approx(
        24 / 28 * 100
    )


def test_workout_is_most_struggled_habit(
    fixture_repository,
):
    habits = fixture_repository.get_habits()
    completions = fixture_repository.get_completions()

    end = FIXTURE_START + timedelta(
        days=27,
        hours=23,
    )

    habit, rate = find_most_struggled_habit(
        habits,
        completions,
        FIXTURE_START,
        end,
    )

    assert habit.name == "Morning Workout"

    assert rate == pytest.approx(
        16 / 28 * 100
    )


def test_reading_has_four_missed_periods(
    fixture_repository,
):
    habit = _get_habit(
        fixture_repository,
        "Read 30 Minutes",
    )

    completions = fixture_repository.get_completions()

    end = FIXTURE_START + timedelta(
        days=27,
        hours=23,
    )

    missed = count_missed_periods(
        habit,
        completions,
        FIXTURE_START,
        end,
    )

    assert missed == 4


def test_weekly_planning_has_one_missed_period(
    fixture_repository,
):
    habit = _get_habit(
        fixture_repository,
        "Weekly Planning",
    )

    completions = fixture_repository.get_completions()

    end = FIXTURE_START + timedelta(
        days=27,
        hours=23,
    )

    missed = count_missed_periods(
        habit,
        completions,
        FIXTURE_START,
        end,
    )

    assert missed == 1

    def test_performance_report_longest_streak_respects_date_range():

        """ The report's longest streak must only use completions belonging to
    the requested analysis period.
    """

habit = Habit(
        id=1,
        name="Test Habit",
        periodicity=Periodicity.DAILY,
        created_at=datetime(
            2026,
            7,
            1,
        ),
    )

completions = [
        # Five-day streak outside requested range.
        Completion(
            habit_id=1,
            completed_at=datetime(
                2026,
                7,
                day,
            ),
        )
        for day in range(
            1,
            6,
        )
    ]

completions += [
        # Two-day streak inside requested range.
        Completion(
            habit_id=1,
            completed_at=datetime(
                2026,
                8,
                10,
            ),
        ),
        Completion(
            habit_id=1,
            completed_at=datetime(
                2026,
                8,
                11,
            ),
        ),
    ]

report = build_performance_report(
        [habit],
        completions,
        datetime(
            2026,
            8,
            1,
        ),
        datetime(
            2026,
            8,
            31,
            23,
            59,
        ),
        reference_time=datetime(
            2026,
            8,
            11,
        ),
    )

assert len(report) == 1

assert (
        report[0]["longest_streak"]
        == 2
    )


def test_performance_report_fixture_results(
    fixture_repository,
):
    """
    Verify the complete four-week fixture report against known results.
    """

    habits = (
        fixture_repository.get_habits()
    )

    completions = (
        fixture_repository.get_completions()
    )

    end = (
        FIXTURE_START
        + timedelta(
            days=27,
            hours=23,
        )
    )

    report = build_performance_report(
        habits,
        completions,
        FIXTURE_START,
        end,
        reference_time=end,
    )

    results = {
        item["habit"].name: item
        for item in report
    }

    assert (
        results["Drink Water"][
            "successful_periods"
        ]
        == 28
    )

    assert (
        results["Drink Water"][
            "longest_streak"
        ]
        == 28
    )

    assert (
        results["Read 30 Minutes"][
            "successful_periods"
        ]
        == 24
    )

    assert (
        results["Read 30 Minutes"][
            "longest_streak"
        ]
        == 6
    )

    assert (
        results["Morning Workout"][
            "successful_periods"
        ]
        == 16
    )

    assert (
        results["Morning Workout"][
            "longest_streak"
        ]
        == 3
    )

    assert (
        results["Meditation"][
            "successful_periods"
        ]
        == 22
    )

    assert (
        results["Meditation"][
            "longest_streak"
        ]
        == 4
    )

    assert (
        results["Weekly Planning"][
            "successful_periods"
        ]
        == 3
    )

    assert (
        results["Weekly Planning"][
            "longest_streak"
        ]
        == 2
    )
    