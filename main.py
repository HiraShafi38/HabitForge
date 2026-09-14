"""
Command-line interface for HabitForge.

This module provides the user-facing application menu and connects
the HabitForge domain model, repository, predefined fixture data,
and functional analytics.
"""

from datetime import datetime
from typing import Optional, Tuple

from analytics import (
    build_performance_report,
    calculate_consistency_rate,
    calculate_current_streak_for_habit,
    calculate_longest_streak_for_habit,
    count_missed_periods,
    find_longest_streak_across_habits,
    find_most_struggled_habit,
    get_all_habits,
    get_habits_by_periodicity,
)
from fixtures import seed_predefined_data
from models import Habit, Periodicity
from repository import HabitRepository


DATABASE_PATH = "habitforge.db"


# ---------------------------------------------------------------------------
# General display helpers
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    """Print a consistent section heading."""

    width = 64

    print()
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def pause() -> None:
    """Wait for the user before returning to a menu."""

    input("\nPress Enter to continue...")


def periodicity_label(periodicity: Periodicity) -> str:
    """Return a user-friendly periodicity label."""

    return periodicity.value.capitalize()


def streak_label(
    habit: Habit,
    streak: int,
) -> str:
    """Return a readable streak value with the correct unit."""

    if habit.periodicity == Periodicity.DAILY:
        unit = "day" if streak == 1 else "days"
    else:
        unit = "week" if streak == 1 else "weeks"

    return f"{streak} {unit}"


# ---------------------------------------------------------------------------
# Habit selection / input helpers
# ---------------------------------------------------------------------------

def display_habit_list(
    habits,
    show_description: bool = False,
) -> None:
    """Display habits in a clean tabular format."""

    if not habits:
        print("\nNo habits are currently being tracked.")
        return

    print()
    print(
        f"{'ID':<5}"
        f"{'Habit':<25}"
        f"{'Periodicity':<15}"
        f"{'Created':<12}"
    )

    print("-" * 57)

    for habit in habits:
        print(
            f"{habit.id:<5}"
            f"{habit.name[:23]:<25}"
            f"{periodicity_label(habit.periodicity):<15}"
            f"{habit.created_at:%Y-%m-%d}"
        )

        if show_description and habit.description:
            print(
                f"     Description: {habit.description}"
            )


def select_habit(
    repository: HabitRepository,
    prompt: str = "Enter habit ID",
) -> Optional[Habit]:
    """
    Ask the user to select an existing habit.

    Returns:
        Selected Habit or None when cancelled.
    """

    habits = repository.get_habits()

    if not habits:
        print("\nNo habits are currently available.")
        return None

    display_habit_list(habits)

    while True:
        value = input(
            f"\n{prompt} (0 to cancel): "
        ).strip()

        if value == "0":
            return None

        try:
            habit_id = int(value)
        except ValueError:
            print(
                "Invalid input. Please enter a numeric habit ID."
            )
            continue

        habit = repository.get_habit(habit_id)

        if habit is None:
            print(
                f"No habit exists with ID {habit_id}."
            )
            continue

        return habit


def prompt_periodicity() -> Optional[Periodicity]:
    """Ask the user to choose daily or weekly periodicity."""

    print("\nChoose periodicity:")
    print("1. Daily")
    print("2. Weekly")
    print("0. Cancel")

    while True:
        choice = input("\nSelection: ").strip()

        if choice == "1":
            return Periodicity.DAILY

        if choice == "2":
            return Periodicity.WEEKLY

        if choice == "0":
            return None

        print(
            "Invalid selection. Please enter 1, 2, or 0."
        )


def prompt_date_range() -> Optional[Tuple[datetime, datetime]]:
    """
    Ask the user for an inclusive analysis date range.

    Expected format:
        YYYY-MM-DD
    """

    print(
        "\nEnter the analysis period using YYYY-MM-DD."
    )
    print("Enter 0 at any point to cancel.")

    while True:
        start_text = input(
            "\nStart date: "
        ).strip()

        if start_text == "0":
            return None

        end_text = input(
            "End date: "
        ).strip()

        if end_text == "0":
            return None

        try:
            start = datetime.strptime(
                start_text,
                "%Y-%m-%d",
            )

            end = datetime.strptime(
                end_text,
                "%Y-%m-%d",
            ).replace(
                hour=23,
                minute=59,
                second=59,
            )

        except ValueError:
            print(
                "Invalid date. Please use YYYY-MM-DD."
            )
            continue

        if end < start:
            print(
                "End date cannot be earlier than start date."
            )
            continue

        return start, end


# ---------------------------------------------------------------------------
# Habit-management actions
# ---------------------------------------------------------------------------

def view_habits(
    repository: HabitRepository,
) -> None:
    """Display all currently tracked habits."""

    print_header("TRACKED HABITS")

    habits = repository.get_habits()

    display_habit_list(
        habits,
        show_description=False,
    )


def create_habit(
    repository: HabitRepository,
) -> None:
    """Create and persist a new habit."""

    print_header("CREATE HABIT")

    name = input(
        "\nHabit name (0 to cancel): "
    ).strip()

    if name == "0":
        return

    periodicity = prompt_periodicity()

    if periodicity is None:
        return

    description = input(
        "\nDescription (optional): "
    ).strip()

    try:
        habit = Habit(
            name=name,
            periodicity=periodicity,
            description=description,
        )

        repository.create_habit(habit)

    except (ValueError, TypeError) as error:
        print(
            f"\nHabit could not be created: {error}"
        )
        return

    print(
        "\nHabit created successfully."
    )

    print(
        f"ID: {habit.id}\n"
        f"Name: {habit.name}\n"
        f"Periodicity: "
        f"{periodicity_label(habit.periodicity)}\n"
        f"Description: "
        f"{habit.description if habit.description else 'None'}"     
    )


def complete_habit(
    repository: HabitRepository,
) -> None:
    """Record a completion for a selected habit."""

    print_header("COMPLETE HABIT")

    habit = select_habit(
        repository,
        "Enter the ID of the completed habit",
    )

    if habit is None:
        return

    completion = repository.record_completion(
        habit.id
    )

    print(
        "\nCompletion recorded successfully."
    )

    print(
        f"{habit.name} was completed at "
        f"{completion.completed_at:%Y-%m-%d %H:%M:%S}."
    )


def delete_habit(
    repository: HabitRepository,
) -> None:
    """Delete a selected habit after explicit confirmation."""

    print_header("DELETE HABIT")

    habit = select_habit(
        repository,
        "Enter the ID of the habit to delete",
    )

    if habit is None:
        return

    completion_count = len(
        repository.get_completions(
            habit.id
        )
    )

    print(
        f"\nYou are about to delete:"
        f"\n  {habit.name}"
    )

    print(
        f"\nThis will also remove "
        f"{completion_count} completion record(s)."
    )

    confirmation = input(
        "\nConfirm deletion? (y/n): "
    ).strip().lower()

    if confirmation not in {
        "y",
        "yes",
    }:
        print("\nDeletion cancelled.")
        return

    deleted = repository.delete_habit(
        habit.id
    )

    if deleted:
        print(
            f"\n'{habit.name}' was deleted successfully."
        )
    else:
        print(
            "\nThe habit could not be deleted."
        )


# ---------------------------------------------------------------------------
# Analytics actions
# ---------------------------------------------------------------------------

def analytics_all_habits(
    repository: HabitRepository,
) -> None:
    """Show all habits through the analytics module."""

    habits = get_all_habits(
        repository.get_habits()
    )

    print_header("ALL TRACKED HABITS")

    display_habit_list(habits)


def analytics_by_periodicity(
    repository: HabitRepository,
) -> None:
    """Display habits matching a selected periodicity."""

    periodicity = prompt_periodicity()

    if periodicity is None:
        return

    habits = get_habits_by_periodicity(
        repository.get_habits(),
        periodicity,
    )

    print_header(
        f"{periodicity.value.upper()} HABITS"
    )

    display_habit_list(habits)


def analytics_longest_overall(
    repository: HabitRepository,
) -> None:
    """Display the longest streak across all habits."""

    habits = repository.get_habits()
    completions = repository.get_completions()

    habit, streak = (
        find_longest_streak_across_habits(
            habits,
            completions,
        )
    )

    print_header("LONGEST STREAK OVERALL")

    if habit is None:
        print("\nNo habits are available.")
        return

    print(
        f"\nHabit: {habit.name}"
    )

    print(
        f"Longest streak: "
        f"{streak_label(habit, streak)}"
    )


def analytics_longest_for_habit(
    repository: HabitRepository,
) -> None:
    """Display the longest streak for one selected habit."""

    habit = select_habit(
        repository,
        "Select habit",
    )

    if habit is None:
        return

    completions = repository.get_completions()

    streak = (
        calculate_longest_streak_for_habit(
            habit,
            completions,
        )
    )

    print_header("HABIT LONGEST STREAK")

    print(
        f"\nHabit: {habit.name}"
    )

    print(
        f"Longest streak: "
        f"{streak_label(habit, streak)}"
    )


def analytics_current_streaks(
    repository: HabitRepository,
) -> None:
    """Display current streaks for all habits."""

    habits = repository.get_habits()
    completions = repository.get_completions()

    print_header("CURRENT STREAKS")

    if not habits:
        print("\nNo habits are available.")
        return

    print()

    for habit in habits:

        streak = (
            calculate_current_streak_for_habit(
                habit,
                completions,
            )
        )

        print(
            f"{habit.name:<28}"
            f"{streak_label(habit, streak)}"
        )


def analytics_consistency(
    repository: HabitRepository,
) -> None:
    """Calculate consistency for one selected habit."""

    habit = select_habit(
        repository,
        "Select habit",
    )

    if habit is None:
        return

    date_range = prompt_date_range()

    if date_range is None:
        return

    start, end = date_range

    completions = repository.get_completions()

    rate = calculate_consistency_rate(
        habit,
        completions,
        start,
        end,
    )

    missed = count_missed_periods(
        habit,
        completions,
        start,
        end,
    )

    print_header("CONSISTENCY ANALYSIS")

    print(
        f"\nHabit: {habit.name}"
    )

    print(
        f"Analysis period: "
        f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
    )

    print(
        f"Consistency rate: {rate:.1f}%"
    )

    print(
        f"Missed periods: {missed}"
    )


def analytics_struggle(
    repository: HabitRepository,
) -> None:
    """Identify the habit with the lowest consistency rate."""

    habits = repository.get_habits()

    if not habits:
        print("\nNo habits are available.")
        return

    date_range = prompt_date_range()

    if date_range is None:
        return

    start, end = date_range

    completions = repository.get_completions()

    habit, rate = find_most_struggled_habit(
        habits,
        completions,
        start,
        end,
    )

    print_header("STRUGGLE ANALYSIS")

    if habit is None:
        print(
            "\nNo habits were active during this period."
        )
        return

    print(
        f"\nHabit requiring the most attention:"
        f"\n{habit.name}"
    )

    print(
        f"\nConsistency rate: {rate:.1f}%"
    )


def analytics_performance_report(
    repository: HabitRepository,
) -> None:
    """Display a performance report for all habits."""

    date_range = prompt_date_range()

    if date_range is None:
        return

    start, end = date_range

    habits = repository.get_habits()
    completions = repository.get_completions()

    report = build_performance_report(
        habits,
        completions,
        start,
        end,
        reference_time=end,
    )

    print_header("HABIT PERFORMANCE REPORT")

    if not report:
        print(
            "\nNo habit data is available for this period."
        )
        return

    print(
        f"\nPeriod: "
        f"{start:%Y-%m-%d} to {end:%Y-%m-%d}\n"
    )

    print(
        f"{'Habit':<22}"
        f"{'Done':<8}"
        f"{'Missed':<9}"
        f"{'Rate':<9}"
        f"{'Best':<9}"
        f"{'Current':<9}"
    )

    print("-" * 66)

    for item in report:

        habit = item["habit"]

        rate_text = (
            f"{item['consistency_rate']:.1f}%"
        )

        print(
            f"{habit.name[:20]:<22}"
            f"{item['successful_periods']:<8}"
            f"{item['missed_periods']:<9}"
            f"{rate_text:<9}"
            f"{item['longest_streak']:<9}"
            f"{item['current_streak']:<9}"
        )


# ---------------------------------------------------------------------------
# Analytics menu
# ---------------------------------------------------------------------------

def analytics_menu(
    repository: HabitRepository,
) -> None:
    """Display and handle the HabitForge analytics menu."""

    while True:

        print_header("HABIT ANALYTICS")

        print(
            """
1. Show all tracked habits
2. Show habits by periodicity
3. Show longest streak overall
4. Show longest streak for a habit

Advanced Analytics
------------------
5. Show current streaks
6. Show consistency and missed periods
7. Show most struggled-with habit
8. Show performance report

0. Back to main menu
"""
        )

        choice = input(
            "Choose an option: "
        ).strip()

        if choice == "1":
            analytics_all_habits(
                repository
            )

        elif choice == "2":
            analytics_by_periodicity(
                repository
            )

        elif choice == "3":
            analytics_longest_overall(
                repository
            )

        elif choice == "4":
            analytics_longest_for_habit(
                repository
            )

        elif choice == "5":
            analytics_current_streaks(
                repository
            )

        elif choice == "6":
            analytics_consistency(
                repository
            )

        elif choice == "7":
            analytics_struggle(
                repository
            )

        elif choice == "8":
            analytics_performance_report(
                repository
            )

        elif choice == "0":
            return

        else:
            print(
                "\nInvalid selection. "
                "Please choose an available option."
            )

        if choice in {
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
        }:
            pause()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main_menu(
    repository: HabitRepository,
) -> None:
    """Display and handle the main HabitForge menu."""

    while True:

        print_header("HABITFORGE")

        print(
            """
1. View Habits
2. Create Habit
3. Complete Habit
4. Delete Habit
5. Analyse Habits
0. Exit
"""
        )

        choice = input(
            "Choose an option: "
        ).strip()

        if choice == "1":
            view_habits(repository)
            pause()

        elif choice == "2":
            create_habit(repository)
            pause()

        elif choice == "3":
            complete_habit(repository)
            pause()

        elif choice == "4":
            delete_habit(repository)
            pause()

        elif choice == "5":
            analytics_menu(repository)

        elif choice == "0":
            print(
                "\nThank you for using HabitForge."
            )
            return

        else:
            print(
                "\nInvalid selection. "
                "Please choose an available option."
            )


def main() -> None:
    """
    Initialize and run HabitForge.

    The predefined fixture is inserted only when the database contains
    no habits, so restarting the application does not create duplicates.
    """

    repository = HabitRepository(
        DATABASE_PATH
    )

    try:
        seed_predefined_data(
            repository
        )

        main_menu(
            repository
        )

    except KeyboardInterrupt:
        print(
            "\n\nHabitForge was interrupted by the user."
        )

    finally:
        repository.close()


if __name__ == "__main__":
    main()
    