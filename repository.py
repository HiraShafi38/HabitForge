"""
SQLite persistence layer for HabitForge.

The HabitRepository is responsible for:
- creating the database schema
- storing and retrieving habits
- recording and retrieving habit completions
- deleting habits and related completion history
- storing small pieces of application metadata
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from models import Completion, Habit, Periodicity


class HabitRepository:
    """Manage HabitForge data using SQLite."""

    def __init__(self, db_path: str = "habitforge.db") -> None:
        """
        Open the SQLite database and create the required tables.

        Args:
            db_path:
                Path to the SQLite database file.
                ':memory:' can be used for temporary test databases.
        """

        self.db_path = db_path

        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row

        # SQLite foreign keys must be explicitly enabled.
        self.connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        self._create_tables()

    def _create_tables(self) -> None:
        """Create all required tables if they do not already exist."""

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                periodicity TEXT NOT NULL
                    CHECK (periodicity IN ('daily', 'weekly')),
                created_at TEXT NOT NULL
            )
            """
        )

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_at TEXT NOT NULL,

                FOREIGN KEY (habit_id)
                    REFERENCES habits(id)
                    ON DELETE CASCADE
            )
            """
        )

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        self.connection.commit()

    # ------------------------------------------------------------------
    # Habit operations
    # ------------------------------------------------------------------

    def create_habit(
        self,
        habit: Habit,
    ) -> Habit:
        """
        Store a new habit.

        Args:
            habit:
                Habit object to persist.

        Returns:
            The same Habit object with its generated database ID.

        Raises:
            TypeError:
                If habit is not a Habit instance.
            ValueError:
                If the habit already has an ID.
        """

        if not isinstance(habit, Habit):
            raise TypeError(
                "habit must be a Habit object."
            )

        if habit.id is not None:
            raise ValueError(
                "Habit already has an ID and may already be stored."
            )

        cursor = self.connection.execute(
            """
            INSERT INTO habits (
                name,
                description,
                periodicity,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                habit.name,
                habit.description,
                habit.periodicity.value,
                habit.created_at.isoformat(),
            ),
        )

        self.connection.commit()

        habit.id = cursor.lastrowid

        return habit

    def get_habit(
        self,
        habit_id: int,
    ) -> Optional[Habit]:
        """
        Retrieve one habit by database ID.

        Returns:
            Habit if found, otherwise None.
        """

        cursor = self.connection.execute(
            """
            SELECT
                id,
                name,
                description,
                periodicity,
                created_at
            FROM habits
            WHERE id = ?
            """,
            (habit_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_habit(row)

    def get_habits(self) -> List[Habit]:
        """
        Return all stored habits ordered by database ID.
        """

        cursor = self.connection.execute(
            """
            SELECT
                id,
                name,
                description,
                periodicity,
                created_at
            FROM habits
            ORDER BY id ASC
            """
        )

        return [
            self._row_to_habit(row)
            for row in cursor.fetchall()
        ]

    def delete_habit(
        self,
        habit_id: int,
    ) -> bool:
        """
        Delete a habit.

        Related Completion records are automatically removed through
        the SQLite ON DELETE CASCADE foreign-key relationship.

        Returns:
            True if a habit was deleted, otherwise False.
        """

        cursor = self.connection.execute(
            """
            DELETE FROM habits
            WHERE id = ?
            """,
            (habit_id,),
        )

        self.connection.commit()

        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Completion operations
    # ------------------------------------------------------------------

    def record_completion(
        self,
        habit_id: int,
        completed_at: Optional[datetime] = None,
    ) -> Completion:
        """
        Record a completion for an existing habit.

        Args:
            habit_id:
                Database ID of the habit.
            completed_at:
                Optional completion timestamp. If omitted, the current
                time is used.

        Returns:
            Persisted Completion object.

        Raises:
            ValueError:
                If the requested habit does not exist.
        """

        habit = self.get_habit(habit_id)

        if habit is None:
            raise ValueError(
                f"Cannot record completion: "
                f"habit {habit_id} does not exist."
            )

        completion = Completion(
            habit_id=habit_id,
            completed_at=(
                completed_at
                if completed_at is not None
                else datetime.now()
            ),
        )

        cursor = self.connection.execute(
            """
            INSERT INTO completions (
                habit_id,
                completed_at
            )
            VALUES (?, ?)
            """,
            (
                completion.habit_id,
                completion.completed_at.isoformat(),
            ),
        )

        self.connection.commit()

        completion.id = cursor.lastrowid

        return completion

    def get_completions(
        self,
        habit_id: Optional[int] = None,
    ) -> List[Completion]:
        """
        Retrieve completion history.

        Args:
            habit_id:
                When supplied, only completions for that habit are
                returned. If omitted, all completions are returned.
        """

        if habit_id is None:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    habit_id,
                    completed_at
                FROM completions
                ORDER BY completed_at ASC
                """
            )

        else:
            cursor = self.connection.execute(
                """
                SELECT
                    id,
                    habit_id,
                    completed_at
                FROM completions
                WHERE habit_id = ?
                ORDER BY completed_at ASC
                """,
                (habit_id,),
            )

        return [
            self._row_to_completion(row)
            for row in cursor.fetchall()
        ]

    # ------------------------------------------------------------------
    # Application metadata
    # ------------------------------------------------------------------

    def get_metadata(
        self,
        key: str,
    ) -> Optional[str]:
        """
        Retrieve an application metadata value.

        Metadata is used for internal state such as remembering whether
        the predefined fixture has previously been initialized.
        """

        cursor = self.connection.execute(
            """
            SELECT value
            FROM app_metadata
            WHERE key = ?
            """,
            (key,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["value"]

    def set_metadata(
        self,
        key: str,
        value: str,
    ) -> None:
        """
        Store or replace an application metadata value.
        """

        self.connection.execute(
            """
            INSERT OR REPLACE INTO app_metadata (
                key,
                value
            )
            VALUES (?, ?)
            """,
            (
                key,
                value,
            ),
        )

        self.connection.commit()

    # ------------------------------------------------------------------
    # Row conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_habit(
        row: sqlite3.Row,
    ) -> Habit:
        """Convert an SQLite row into a Habit object."""

        return Habit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            periodicity=Periodicity(
                row["periodicity"]
            ),
            created_at=datetime.fromisoformat(
                row["created_at"]
            ),
        )

    @staticmethod
    def _row_to_completion(
        row: sqlite3.Row,
    ) -> Completion:
        """Convert an SQLite row into a Completion object."""

        return Completion(
            id=row["id"],
            habit_id=row["habit_id"],
            completed_at=datetime.fromisoformat(
                row["completed_at"]
            ),
        )

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the SQLite database connection."""

        self.connection.close()

    def __enter__(self):
        """Allow HabitRepository to be used with a with statement."""

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        """Close the database when leaving a context manager."""

        self.close()
        