"""
Functional analytics for HabitForge.

This module contains analytical functions for habit and completion data.

The analytics layer deliberately remains independent of SQLite. It
receives Habit and Completion objects from the repository and performs
data transformations without modifying persistent application state.

Functional programming techniques used include:
- map
- filter
- reduce
- max
- min
- sorted
- lambda expressions
- comprehensions
"""

from datetime import date, datetime, timedelta
from functools import reduce
from typing import Dict, List, Optional, Tuple

from models import Completion, Habit, Periodicity


def _validate_periodicity(
    periodicity: Periodicity,
) -> None:
    """Ensure that a valid Periodicity value was supplied."""

    if not isinstance(
        periodicity,
        Periodicity,
    ):
        raise ValueError(
            "Periodicity must be "
            "Periodicity.DAILY or Periodicity.WEEKLY."
        )


def _validate_analysis_window(
    start: datetime,
    end: datetime,
) -> None:
    """Ensure that an analysis date range is valid."""

    if not isinstance(start, datetime):
        raise TypeError(
            "Analysis start must be a datetime object."
        )

    if not isinstance(end, datetime):
        raise TypeError(
            "Analysis end must be a datetime object."
        )

    if end < start:
        raise ValueError(
            "Analysis end time cannot be earlier "
            "than start time."
        )


# ----------------------------------------------------------------------
# Required habit-list analytics
# ----------------------------------------------------------------------

def get_all_habits(
    habits: List[Habit],
) -> List[Habit]:
    """
    Return all currently tracked habits.

    A new list is returned so that the original collection is not
    modified by the analytics layer.
    """

    return list(habits)


def get_habits_by_periodicity(
    habits: List[Habit],
    periodicity: Periodicity,
) -> List[Habit]:
    """
    Return only habits matching the selected periodicity.

    Functional filtering is deliberately used as part of the
    analytical implementation.
    """

    _validate_periodicity(
        periodicity
    )

    return list(
        filter(
            lambda habit:
                habit.periodicity
                == periodicity,
            habits,
        )
    )


# ----------------------------------------------------------------------
# Period helpers
# ----------------------------------------------------------------------

def _period_start(
    timestamp: datetime,
    periodicity: Periodicity,
) -> date:
    """
    Convert a timestamp into the corresponding habit period.

    Daily:
        Calendar date.

    Weekly:
        Monday of the corresponding ISO-style week.

    Representing weekly periods by their Monday date allows
    consecutive-week calculations to work naturally across calendar
    year boundaries.
    """

    _validate_periodicity(
        periodicity
    )

    completion_date = (
        timestamp.date()
    )

    if periodicity == Periodicity.DAILY:
        return completion_date

    return (
        completion_date
        - timedelta(
            days=completion_date.weekday()
        )
    )


def _period_step(
    periodicity: Periodicity,
) -> timedelta:
    """Return the interval between consecutive required periods."""

    _validate_periodicity(
        periodicity
    )

    if periodicity == Periodicity.DAILY:
        return timedelta(days=1)

    return timedelta(weeks=1)


def _unique_completed_periods(
    completions: List[Completion],
    periodicity: Periodicity,
) -> List[date]:
    """
    Convert completion timestamps into unique successful periods.

    Multiple check-offs within the same daily or weekly period count
    as only one successful period for analytical purposes.
    """

    periods = set(
        map(
            lambda completion:
                _period_start(
                    completion.completed_at,
                    periodicity,
                ),
            completions,
        )
    )

    return sorted(periods)


def _completions_for_habit(
    habit: Habit,
    completions: List[Completion],
) -> List[Completion]:
    """Return completion records belonging to one selected habit."""

    if habit.id is None:
        raise ValueError(
            "Habit must have a database ID "
            "before it can be analysed."
        )

    return list(
        filter(
            lambda completion:
                completion.habit_id
                == habit.id,
            completions,
        )
    )


def _effective_analysis_start(
    habit: Habit,
    requested_start: datetime,
) -> datetime:
    """
    Prevent analysis from counting periods before habit creation.
    """

    return max(
        requested_start,
        habit.created_at,
    )


def _completions_in_period_window(
    habit: Habit,
    completions: List[Completion],
    start: datetime,
    end: datetime,
) -> List[Completion]:
    """
    Return one habit's completions whose required periods fall inside
    an inclusive analytical period window.

    Period-based filtering is used rather than simple timestamp
    filtering so weekly analysis behaves consistently when a selected
    range begins or ends part-way through a week.
    """

    _validate_analysis_window(
        start,
        end,
    )

    habit_completions = (
        _completions_for_habit(
            habit,
            completions,
        )
    )

    start_period = _period_start(
        start,
        habit.periodicity,
    )

    end_period = _period_start(
        end,
        habit.periodicity,
    )

    return list(
        filter(
            lambda completion:
                start_period
                <= _period_start(
                    completion.completed_at,
                    habit.periodicity,
                )
                <= end_period,
            habit_completions,
        )
    )


# ----------------------------------------------------------------------
# Required streak analytics
# ----------------------------------------------------------------------

def calculate_longest_streak(
    completions: List[Completion],
    periodicity: Periodicity,
) -> int:
    """
    Calculate the longest sequence of consecutive completed periods.

    functools.reduce is used to transform the chronological sequence
    into accumulated streak state without mutating variables outside
    the reduction operation.

    Returns:
        Longest streak measured in required habit periods.
    """

    _validate_periodicity(
        periodicity
    )

    periods = (
        _unique_completed_periods(
            completions,
            periodicity,
        )
    )

    if not periods:
        return 0

    step = _period_step(
        periodicity
    )

    def accumulate_streak(
        state,
        current_period,
    ):
        """
        Produce the next immutable streak state.

        State:
            (
                longest streak so far,
                current streak,
                previous period
            )
        """

        (
            longest,
            current_streak,
            previous_period,
        ) = state

        next_streak = (
            current_streak + 1
            if (
                current_period
                - previous_period
                == step
            )
            else 1
        )

        return (
            max(
                longest,
                next_streak,
            ),
            next_streak,
            current_period,
        )

    longest, _, _ = reduce(
        accumulate_streak,
        periods[1:],
        (
            1,
            1,
            periods[0],
        ),
    )

    return longest


def calculate_longest_streak_for_habit(
    habit: Habit,
    completions: List[Completion],
) -> int:
    """Calculate the longest all-time streak for one selected habit."""

    habit_completions = (
        _completions_for_habit(
            habit,
            completions,
        )
    )

    return calculate_longest_streak(
        habit_completions,
        habit.periodicity,
    )


def find_longest_streak_across_habits(
    habits: List[Habit],
    completions: List[Completion],
) -> Tuple[Optional[Habit], int]:
    """
    Find the habit with the longest streak across all tracked habits.

    Returns:
        (Habit, streak)

        If no habits exist:
            (None, 0)
    """

    if not habits:
        return None, 0

    results = list(
        map(
            lambda habit: (
                habit,
                calculate_longest_streak_for_habit(
                    habit,
                    completions,
                ),
            ),
            habits,
        )
    )

    return max(
        results,
        key=lambda result:
            result[1],
    )


# ----------------------------------------------------------------------
# Current streak analytics
# ----------------------------------------------------------------------

def calculate_current_streak(
    completions: List[Completion],
    periodicity: Periodicity,
    reference_time: Optional[
        datetime
    ] = None,
) -> int:
    """
    Calculate a streak ending in the current/reference period.

    If the habit has not been completed during the reference period,
    its current streak is zero.
    """

    _validate_periodicity(
        periodicity
    )

    if reference_time is None:
        reference_time = datetime.now()

    periods = set(
        _unique_completed_periods(
            completions,
            periodicity,
        )
    )

    reference_period = (
        _period_start(
            reference_time,
            periodicity,
        )
    )

    if reference_period not in periods:
        return 0

    step = _period_step(
        periodicity
    )

    def count_backwards(
        period: date,
    ) -> int:
        """
        Recursively count consecutive periods backwards.

        The function is deliberately pure: it reads the completed-period
        set but does not modify it.
        """

        if period not in periods:
            return 0

        return (
            1
            + count_backwards(
                period - step
            )
        )

    return count_backwards(
        reference_period
    )


def calculate_current_streak_for_habit(
    habit: Habit,
    completions: List[Completion],
    reference_time: Optional[
        datetime
    ] = None,
) -> int:
    """Calculate the current streak for one selected habit."""

    habit_completions = (
        _completions_for_habit(
            habit,
            completions,
        )
    )

    return calculate_current_streak(
        habit_completions,
        habit.periodicity,
        reference_time,
    )


# ----------------------------------------------------------------------
# Expected and successful period calculations
# ----------------------------------------------------------------------

def _expected_period_count(
    periodicity: Periodicity,
    start: datetime,
    end: datetime,
) -> int:
    """
    Count expected required periods in an inclusive analysis window.
    """

    _validate_periodicity(
        periodicity
    )

    _validate_analysis_window(
        start,
        end,
    )

    start_period = _period_start(
        start,
        periodicity,
    )

    end_period = _period_start(
        end,
        periodicity,
    )

    if periodicity == Periodicity.DAILY:
        return (
            (
                end_period
                - start_period
            ).days
            + 1
        )

    return (
        (
            end_period
            - start_period
        ).days
        // 7
        + 1
    )


def _successful_period_count(
    habit: Habit,
    completions: List[Completion],
    start: datetime,
    end: datetime,
) -> int:
    """Count completed required periods inside an analysis window."""

    filtered = (
        _completions_in_period_window(
            habit,
            completions,
            start,
            end,
        )
    )

    return len(
        _unique_completed_periods(
            filtered,
            habit.periodicity,
        )
    )


# ----------------------------------------------------------------------
# Additional behavioural analytics
# ----------------------------------------------------------------------

def calculate_consistency_rate(
    habit: Habit,
    completions: List[Completion],
    start: datetime,
    end: datetime,
) -> float:
    """
    Calculate the percentage of required periods successfully completed.

    Formula:

        successful periods / expected periods * 100
    """

    _validate_analysis_window(
        start,
        end,
    )

    effective_start = (
        _effective_analysis_start(
            habit,
            start,
        )
    )

    if end < effective_start:
        return 0.0

    expected = (
        _expected_period_count(
            habit.periodicity,
            effective_start,
            end,
        )
    )

    successful = (
        _successful_period_count(
            habit,
            completions,
            effective_start,
            end,
        )
    )

    if expected == 0:
        return 0.0

    return (
        successful
        / expected
        * 100.0
    )


def count_missed_periods(
    habit: Habit,
    completions: List[Completion],
    start: datetime,
    end: datetime,
) -> int:
    """Calculate how many required periods were missed."""

    _validate_analysis_window(
        start,
        end,
    )

    effective_start = (
        _effective_analysis_start(
            habit,
            start,
        )
    )

    if end < effective_start:
        return 0

    expected = (
        _expected_period_count(
            habit.periodicity,
            effective_start,
            end,
        )
    )

    successful = (
        _successful_period_count(
            habit,
            completions,
            effective_start,
            end,
        )
    )

    return max(
        expected - successful,
        0,
    )


def find_most_struggled_habit(
    habits: List[Habit],
    completions: List[Completion],
    start: datetime,
    end: datetime,
) -> Tuple[Optional[Habit], float]:
    """
    Identify the habit with the lowest consistency rate.

    Returns:
        (
            habit requiring the most attention,
            consistency percentage
        )

        If no eligible habit exists:
            (None, 0.0)
    """

    _validate_analysis_window(
        start,
        end,
    )

    eligible_habits = list(
        filter(
            lambda habit:
                habit.created_at <= end,
            habits,
        )
    )

    if not eligible_habits:
        return None, 0.0

    results = list(
        map(
            lambda habit: (
                habit,
                calculate_consistency_rate(
                    habit,
                    completions,
                    start,
                    end,
                ),
            ),
            eligible_habits,
        )
    )

    return min(
        results,
        key=lambda result:
            result[1],
    )


# ----------------------------------------------------------------------
# Combined performance reporting
# ----------------------------------------------------------------------

def build_performance_report(
    habits: List[Habit],
    completions: List[Completion],
    start: datetime,
    end: datetime,
    reference_time: Optional[
        datetime
    ] = None,
) -> List[Dict]:
    """
    Build a behavioural performance report for all eligible habits.

    Every analytical measure in the report is calculated consistently
    within the selected analysis period.

    This means that "longest_streak" is the best streak inside the
    requested period rather than an unrelated all-time streak.

    Returns:
        A list of dictionaries containing:

        - habit
        - expected_periods
        - successful_periods
        - missed_periods
        - consistency_rate
        - longest_streak
        - current_streak
    """

    _validate_analysis_window(
        start,
        end,
    )

    if reference_time is None:
        reference_time = end

    eligible_habits = list(
        filter(
            lambda habit:
                habit.created_at <= end,
            habits,
        )
    )

    def build_report_item(
        habit: Habit,
    ) -> Dict:
        """Build one immutable analytical report entry."""

        effective_start = (
            _effective_analysis_start(
                habit,
                start,
            )
        )

        expected = (
            _expected_period_count(
                habit.periodicity,
                effective_start,
                end,
            )
        )

        window_completions = (
            _completions_in_period_window(
                habit,
                completions,
                effective_start,
                end,
            )
        )

        successful = len(
            _unique_completed_periods(
                window_completions,
                habit.periodicity,
            )
        )

        missed = max(
            expected - successful,
            0,
        )

        consistency = (
            successful
            / expected
            * 100.0
            if expected > 0
            else 0.0
        )

        longest_streak = (
            calculate_longest_streak(
                window_completions,
                habit.periodicity,
            )
        )

        current_streak = (
            calculate_current_streak(
                window_completions,
                habit.periodicity,
                reference_time,
            )
        )

        return {
            "habit": habit,
            "expected_periods": expected,
            "successful_periods": successful,
            "missed_periods": missed,
            "consistency_rate": consistency,
            "longest_streak": longest_streak,
            "current_streak": current_streak,
        }

    return list(
        map(
            build_report_item,
            eligible_habits,
        )
    )