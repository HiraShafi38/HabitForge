# HabitForge

HabitForge is a command-line habit tracking and behaviour analytics application developed in Python.

The application allows users to create and manage daily and weekly habits, record completion events, persist habit data between sessions, and analyse behavioural patterns such as streaks, consistency rates, missed periods, and habits requiring additional attention.

The project demonstrates the use of both **object-oriented programming (OOP)** and **functional programming (FP)** concepts in Python.

---

## Features

HabitForge supports:

- Creation of daily and weekly habits
- Optional habit descriptions
- Automatic habit creation timestamps
- Habit completion tracking with date and time
- Persistent SQLite storage
- Viewing all currently tracked habits
- Deleting habits with confirmation
- Automatic deletion of associated completion history
- Five predefined habits
- Four weeks of deterministic example tracking data
- Habit filtering by periodicity
- Longest streak calculation across all habits
- Longest streak calculation for an individual habit
- Current streak calculation
- Consistency-rate analysis
- Missed-period analysis
- Identification of the most struggled-with habit
- Multi-habit performance reports
- Input validation
- Automated testing using pytest
- Test coverage using pytest-cov
- Automated verification using GitHub Actions

---

## Predefined Habits

When HabitForge is initialized with a new database, five predefined habits are created together with four weeks of deterministic tracking data.

| Habit | Periodicity | Behaviour Pattern |
|---|---|---|
| Drink Water | Daily | Highly consistent |
| Read 30 Minutes | Daily | Occasional missed days |
| Morning Workout | Daily | Irregular completion pattern |
| Meditation | Daily | Moderately consistent |
| Weekly Planning | Weekly | One missed week |

The fixture is deterministic rather than randomly generated.

This allows analytical results to be reproduced and verified against known expected values.

---

## Application Architecture

HabitForge separates the application into focused components.

```text
User
 │
 ▼
Command-Line Interface
 │
 ├──────────────► Functional Analytics
 │
 ▼
HabitRepository
 │
 ▼
SQLite Database
```

The analytics layer does not directly access the database.

Instead:

```text
SQLite Database
      │
      ▼
HabitRepository
      │
      ▼
Habit / Completion objects
      │
      ▼
Functional Analytics
      │
      ▼
CLI Results
```

This separation reduces coupling and makes the application easier to test and maintain.

---

## Project Structure

```text
HabitForge/
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── tests/
│   ├── test_models.py
│   ├── test_repository.py
│   ├── test_fixtures.py
│   ├── test_analytics.py
│   └── test_main.py
│
├── main.py
├── models.py
├── repository.py
├── analytics.py
├── fixtures.py
├── requirements.txt
├── README.md
└── .gitignore
```

The SQLite runtime database file:

```text
habitforge.db
```

is generated automatically when the application is first executed.

It is intentionally excluded from Git using `.gitignore`.

---

# Core Components

## `models.py`

Contains the object-oriented domain model of HabitForge.

### `Periodicity`

An enumeration defining the supported habit frequencies:

```text
DAILY
WEEKLY
```

Using an enumeration prevents inconsistent raw string values from being used throughout the application.

### `Habit`

Represents one habit being tracked.

A Habit contains:

```text
id
name
description
periodicity
created_at
```

New habits initially have no database ID. SQLite assigns the identifier when the habit is persisted.

### `Completion`

Represents one recorded habit completion.

A Completion contains:

```text
id
habit_id
completed_at
```

Completion events are stored separately from Habit objects so that the complete tracking history can be retained.

---

## `repository.py`

Contains the `HabitRepository` class, which provides the persistence layer.

It is responsible for:

- creating the SQLite schema
- creating habits
- retrieving habits
- deleting habits
- recording completions
- retrieving completion history
- storing internal application metadata

HabitForge uses three SQLite tables:

```text
habits
completions
app_metadata
```

### Habits Table

Stores:

```text
id
name
description
periodicity
created_at
```

### Completions Table

Stores:

```text
id
habit_id
completed_at
```

Each completion is linked to its habit through:

```text
habit_id
```

The relationship is:

```text
Habit 1 ───────── 0..* Completion
```

SQLite foreign-key cascading is enabled so that deleting a habit automatically removes its associated completion records.

### Application Metadata

The metadata table is used to remember whether the predefined fixture has already been initialized.

This prevents deleted predefined habits from unexpectedly reappearing when HabitForge is restarted.

---

## `fixtures.py`

Contains the deterministic four-week example dataset required by the project.

The fixture period begins on:

```text
2026-08-03
```

and covers:

```text
28 days
```

The predefined habits have intentionally different behavioural patterns so that analytics can be tested against known expected values.

A total of:

```text
93 completion records
```

are generated across the five predefined habits.

Fixture initialization is performed only once.

---

## `analytics.py`

Contains the functional analytics layer.

The module receives Habit and Completion objects and performs analytical transformations without directly accessing or modifying the SQLite database.

Functional programming techniques used include:

- `map()`
- `filter()`
- `reduce()`
- `max()`
- `min()`
- `sorted()`
- lambda expressions
- comprehensions
- immutable-style state transformations

---

# Habit Analytics

## List All Habits

Returns all currently tracked habits.

---

## Filter by Periodicity

Habits can be filtered by:

```text
Daily
Weekly
```

---

## Longest Streak

HabitForge calculates the longest sequence of consecutive successful habit periods.

For a daily habit:

```text
Monday      Completed
Tuesday     Completed
Wednesday   Completed
Thursday    Missed
Friday      Completed
```

the longest streak is:

```text
3 days
```

For a weekly habit, consecutive weeks are evaluated instead.

---

## Duplicate Completion Handling

Multiple completion events within the same required period count as only one successful period for streak calculations.

For example:

```text
Monday 08:00    Completed
Monday 19:00    Completed
Tuesday 08:00   Completed
```

produces:

```text
2-day streak
```

rather than three.

The actual completion timestamps are still retained in the database.

---

## Weekly Streak Calculation

Weekly periods are represented using the Monday of their corresponding week.

This allows weekly streak calculations to work correctly even when consecutive weeks cross calendar-year boundaries.

For example:

```text
2026-12-28
2027-01-04
2027-01-11
```

correctly forms:

```text
3 consecutive weeks
```

---

# Additional Behaviour Analytics

HabitForge includes several analytical features beyond the basic required functionality.

## Current Streak

Calculates the number of consecutive successful periods ending in the selected/current reference period.

If the current required period has not been completed, the current streak is zero.

---

## Consistency Rate

Consistency is calculated as:

```text
successful required periods
----------------------------- × 100
total expected periods
```

For example:

```text
24 completed days out of 28
```

produces:

```text
85.7%
```

---

## Missed Periods

HabitForge calculates the number of expected daily or weekly periods that were not successfully completed within a selected analysis range.

---

## Struggle Analysis

HabitForge identifies the habit with the lowest consistency rate during a selected analysis period.

This helps identify which habit may require the most attention.

---

## Performance Report

HabitForge can generate a combined performance report containing:

```text
Completed periods
Missed periods
Consistency rate
Longest streak
Current streak
```

The report's streak calculations are restricted to the selected analysis period, ensuring that results remain internally consistent.

---

# Example Fixture Results

For the predefined analysis period:

```text
2026-08-03 to 2026-08-30
```

the expected results are:

| Habit | Completed | Expected | Consistency |
|---|---:|---:|---:|
| Drink Water | 28 | 28 | 100.0% |
| Read 30 Minutes | 24 | 28 | 85.7% |
| Morning Workout | 16 | 28 | 57.1% |
| Meditation | 22 | 28 | 78.6% |
| Weekly Planning | 3 | 4 | 75.0% |

Known longest streaks are:

| Habit | Longest Streak |
|---|---:|
| Drink Water | 28 days |
| Read 30 Minutes | 6 days |
| Morning Workout | 3 days |
| Meditation | 4 days |
| Weekly Planning | 2 weeks |

The longest streak across all predefined habits is therefore:

```text
Drink Water — 28 days
```

The predefined habit with the lowest four-week consistency is:

```text
Morning Workout — approximately 57.1%
```

---

# Requirements

HabitForge requires:

```text
Python 3.7 or later
```

The submitted version was developed and tested using:

```text
Python 3.14
```

The application uses Python's standard library for its core functionality, including:

- `sqlite3`
- `datetime`
- `dataclasses`
- `enum`
- `functools`
- `typing`

Development/testing dependencies are:

```text
pytest==9.1.1
pytest-cov==7.1.0
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/HiraShafi38/HabitForge.git
```

Move into the project directory:

```bash
cd HabitForge
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

# Running HabitForge

Start the application with:

```bash
python main.py
```

The main menu appears:

```text
================================================================
                           HABITFORGE
================================================================

1. View Habits
2. Create Habit
3. Complete Habit
4. Delete Habit
5. Analyse Habits
0. Exit
```

On the first launch with a new database, the predefined four-week fixture is automatically initialized.

---

# Using the Application

## View Habits

Select:

```text
1. View Habits
```

The application displays:

- habit ID
- name
- periodicity
- creation date
- description

---

## Create a Habit

Select:

```text
2. Create Habit
```

The user provides:

```text
Habit name
Periodicity
Optional description
```

The application automatically records the creation timestamp.

---

## Complete a Habit

Select:

```text
3. Complete Habit
```

Choose a habit using its ID.

HabitForge stores a Completion record containing the current date and time.

---

## Delete a Habit

Select:

```text
4. Delete Habit
```

The application displays the selected habit and asks for confirmation.

Deletion also removes its related completion history through SQLite cascade deletion.

---

## Analyse Habits

Select:

```text
5. Analyse Habits
```

The analytics menu provides:

```text
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
```

---

# Persistence

HabitForge uses SQLite for persistent local storage.

This means that habits and completion records remain available after the application is closed and restarted.

Persistence is also verified automatically by a test that:

```text
opens database
      ↓
creates habit and completion
      ↓
closes repository
      ↓
opens a new repository session
      ↓
retrieves the same habit and completion
```

This verifies persistence between independent application sessions.

---

# Testing

HabitForge uses pytest for automated testing.

Run the complete test suite with:

```bash
python -m pytest -v
```

The current project test suite contains:

```text
91 automated tests
```

covering areas including:

- Habit model creation
- Completion model creation
- Periodicity validation
- Invalid habit names
- Invalid identifiers
- Habit timestamps
- Completion timestamps
- SQLite habit persistence
- Completion persistence
- Cross-session persistence
- Cascade deletion
- Application metadata
- Fixture creation
- Fixture reproducibility
- Fixture duplication prevention
- Deleted-fixture behaviour
- Daily streak calculations
- Weekly streak calculations
- Duplicate-period completion handling
- Missed-period calculations
- Current streak calculations
- Consistency calculations
- Struggle analysis
- Performance report calculations
- Analysis-window behaviour
- Calendar-year week transitions
- CLI input handling
- Habit creation through the CLI
- Completion through the CLI
- Habit deletion through the CLI
- Analytics output

---

# Test Coverage

Run test coverage using:

```bash
python -m pytest --cov=models --cov=repository --cov=fixtures --cov=analytics --cov=main --cov-report=term-missing
```

For an HTML coverage report:

```bash
python -m pytest --cov=models --cov=repository --cov=fixtures --cov=analytics --cov=main --cov-report=html
```

Then open:

```text
htmlcov/index.html
```

---

# GitHub Actions

HabitForge includes an automated GitHub Actions workflow:

```text
.github/workflows/tests.yml
```

Whenever code is pushed to the repository or a pull request is created, GitHub automatically:

```text
checks out the repository
        ↓
sets up Python
        ↓
installs dependencies
        ↓
runs the complete pytest suite
        ↓
runs coverage analysis
```

This provides automated verification in a clean environment independent of the developer's local computer.

---

# Design Decisions

## Command-Line Interface

A command-line interface was deliberately selected instead of a graphical or web interface.

The project's primary focus is:

- object-oriented programming
- functional programming
- persistent storage
- analytics
- validation
- testing
- documentation

A CLI keeps the implementation focused on these core programming requirements.

---

## SQLite Persistence

SQLite was selected because it provides:

- persistent structured storage
- relational integrity
- foreign-key support
- cascade deletion
- efficient retrieval
- no external database server requirement

This provides a stronger persistence model than temporary in-memory data structures.

---

## Separate Habit and Completion Models

Completion events are stored separately from habits.

This allows one habit to have multiple historical completion timestamps:

```text
Habit
 │
 ├── Completion
 ├── Completion
 ├── Completion
 └── ...
```

This structure allows historical streak and consistency analysis without modifying the Habit object itself.

---

## Repository Layer

Database operations are isolated inside `HabitRepository`.

This prevents the command-line interface and analytics layer from being tightly coupled to SQLite.

---

## Functional Analytics

Analytics are separated from persistence and implemented as data-processing functions.

The module makes explicit use of functional programming constructs including:

```text
map
filter
reduce
max
min
sorted
lambda expressions
comprehensions
```

The streak reducer transforms chronological periods into accumulated analytical state without modifying the source data.

---

## Deterministic Fixture

The predefined four-week fixture is deliberately deterministic rather than random.

This means analytical outputs can be verified using exact expected values.

For example:

```text
Drink Water
28 successful periods
Longest streak = 28
Consistency = 100%
```

will produce the same result every time.

---

## In-Memory Testing

Repository tests use temporary or in-memory SQLite databases where appropriate:

```python
HabitRepository(":memory:")
```

This isolates tests from the real runtime database.

Tests that specifically verify persistence use temporary SQLite files and reopen them in independent repository sessions.

---

# Error Handling and Validation

HabitForge validates several invalid states, including:

- empty habit names
- whitespace-only habit names
- unsupported periodicity values
- invalid habit IDs
- invalid completion IDs
- nonexistent habits
- invalid date ranges
- incorrect CLI selections

This prevents inconsistent data from entering the application.

---

# Scope

HabitForge currently supports:

```text
Daily habits
Weekly habits
Single-user local operation
SQLite persistence
Command-line interaction
Behaviour analytics
```

The project intentionally does not include:

- authentication
- multi-user accounts
- cloud synchronization
- web interface
- graphical desktop interface
- notification services

These features were kept outside the current scope so development could focus on correctness, architecture, testing, and analytical functionality.

---

# Possible Future Improvements

Future versions of HabitForge could include:

- monthly habits
- user-defined periodicities
- habit editing
- habit archiving
- data export
- graphical progress visualisations
- configurable reminders
- desktop interface
- web interface
- cloud synchronization
- multi-user support

---

# Repository

Public GitHub repository:

```text
https://github.com/HiraShafi38/HabitForge
```

---

# Author

**Hira Shafi**

IU International University of Applied Sciences

Course:

**Object Oriented and Functional Programming with Python**

Course ID:

**DLBDSOOFPP01**