# HabitForge

HabitForge is a command-line habit tracking and behaviour analytics application developed in Python.

The application allows users to create and manage daily and weekly habits, record completion events, persist habit data between sessions, and analyse behavioural patterns such as streaks, consistency rates, missed periods, and habits requiring additional attention.

The project demonstrates the use of both object-oriented and functional programming concepts in Python.

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
- Automatic removal of associated completion history
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
- Automated unit testing with pytest

---

## Predefined Habits

When HabitForge is started with a new database, five predefined habits and four weeks of example tracking data are automatically created.

| Habit | Periodicity | Example Behaviour |
|---|---|---|
| Drink Water | Daily | Highly consistent |
| Read 30 Minutes | Daily | Occasional missed days |
| Morning Workout | Daily | Irregular completion pattern |
| Meditation | Daily | Moderately consistent |
| Weekly Planning | Weekly | One missed week |

The fixture is deterministic rather than randomly generated. This makes the expected analytical results reproducible and testable.

---

## Application Architecture

HabitForge is divided into several focused modules.

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
