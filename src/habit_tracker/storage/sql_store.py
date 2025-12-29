import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path

from habit_tracker.storage import Storage
from habit_tracker.models import User


class SQLStore(Storage):
    """
    SQLite-backed persistence layer for the Habit Tracker app.

    Implements the `Storage` interface for habit persistence using a local SQLite
    database. It supports:
    - Saving a single habit and its completion history (`save_habit`)
    - Replacing all habits in one operation (`save_all`)
    - Loading all habits with completion timestamps (`load_habits`)
    - Deleting a habit and its tracked completions (`delete_habit`)
    - Appending a completion event (`log_completion`)

    Additionally, this storage class includes helper methods for the app's optional
    authentication feature (single-user design): `save_user` and `load_user`.

    Notes:
    - Default database path: `data/db/habit_tracker.db` relative to the project root.
    - A custom database path can be provided (useful for tests), including the SQLite in-memory path `:memory:`.
    - Datetimes are stored as ISO 8601 strings and parsed back to `datetime` on load.
    """

    # Project root: .../src/habit_tracker/storage/sql_store.py -> go up 3 levels
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    _DATA_DB_DIR = _PROJECT_ROOT / "data" / "db"
    _DATA_SAMPLE_DIR = _PROJECT_ROOT / "data" / "example"

    # Default DB path in data/db
    _DEFAULT_DB_PATH = _DATA_DB_DIR / "habit_tracker.db"

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite storage backend.

        Args:
            db_path: Optional path to the SQLite database file. If None, the
                default project DB path is used. Use `:memory:` for an in-memory
                database during tests.

        Side effects:
            - Ensures required directories exist (unless using `:memory:`).
            - Creates database tables if they do not already exist.
        """

        # allow overriding DB path (useful for tests)
        self._db_path = Path(db_path) if db_path is not None else self._DEFAULT_DB_PATH

        # Make sure directories exist (skip for in-memory DB)
        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        # also ensure sample data dir exists
        self._DATA_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

        self._initialize_db()

    def _initialize_db(self):
        """
        Create required database tables if they do not exist.

        Tables:
            - habits: Stores habit definitions (name, description, periodicity, created_date)
            - tracking: Stores completion events for habits (habit_id, completion_date)
            - user: Stores a single user record (id fixed to 1) with password hash and salt
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            # Habits table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    periodicity TEXT NOT NULL,
                    created_date TEXT NOT NULL
                )
                """
            )

            # Tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER NOT NULL,
                    completion_date TEXT,
                    FOREIGN KEY (habit_id) REFERENCES habits (id)
                )
                """
            )

            # User table (single-user app; id is always 1)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                )
                """
            )

            conn.commit()

    # ------------------------------------------------------------------
    # User methods
    # ------------------------------------------------------------------
    def save_user(self, user: User) -> None:
        """
        Persist the single user record (insert or update).

        The application is designed as a single-user workflow, therefore the row
        always uses `id = 1`.

        Args:
            user: User instance containing username, password_hash, and salt.
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO user (id, username, password_hash, salt)
                VALUES (1, ?, ?, ?)
                """,
                (user.username, user.password_hash, user.salt),
            )
            conn.commit()

    def load_user(self) -> Optional[User]:
        """
        Load the stored user record.

        Returns:
            A `User` instance if a user is stored, otherwise None.
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password_hash, salt FROM user WHERE id = 1"
            )
            row = cursor.fetchone()

            if row is None:
                return None

            username, password_hash, salt = row
            return User(username=username, password_hash=password_hash, salt=salt)

    # ------------------------------------------------------------------
    # Habit methods
    # ------------------------------------------------------------------
    def save_habit(self, habit_data) -> int:
        """
        Insert a new habit and its completion history.

        Expects a dict-like structure containing the habit fields. Completion
        timestamps (if provided) are inserted into the tracking table.

        Args:
            habit_data: Dictionary containing:
                - name (str)
                - description (str, optional)
                - periodicity (str)
                - created_date (datetime)
                - completion_dates (list[datetime], optional)

        Returns:
            The newly created habit id (int).
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO habits (name, description, periodicity, created_date)
                VALUES (?, ?, ?, ?)
                """,
                (
                    habit_data["name"],
                    habit_data.get("description", ""),
                    habit_data.get("periodicity"),
                    habit_data.get("created_date").isoformat(),
                ),
            )

            habit_id = cursor.lastrowid

            for dt in habit_data.get("completion_dates", []):
                cursor.execute(
                    """
                    INSERT INTO tracking (habit_id, completion_date)
                    VALUES (?, ?)
                    """,
                    (habit_id, dt.isoformat()),
                )

            conn.commit()
            return habit_id

    def save_all(self, habits_list) -> bool:
        """
        Replace all stored habits with the provided list (full rewrite).

        This method clears existing data in both `habits` and `tracking` tables
        and re-inserts each habit and its completion events.

        Intended use:
            - Bulk persistence from in-memory state
            - Resetting the DB to match an authoritative source (e.g., fixtures)

        Args:
            habits_list: List of habit dictionaries (same shape as `save_habit`).

        Returns:
            True if the operation completed successfully.
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tracking")
            cursor.execute("DELETE FROM habits")

            for habit_data in habits_list:
                cursor.execute(
                    """
                    INSERT INTO habits (name, description, periodicity, created_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        habit_data["name"],
                        habit_data.get("description", ""),
                        habit_data["periodicity"],
                        habit_data["created_date"].isoformat(),
                    ),
                )

                habit_id = cursor.lastrowid

                for dt in habit_data.get("completion_dates", []):
                    cursor.execute(
                        """
                        INSERT INTO tracking (habit_id, completion_date)
                        VALUES (?, ?)
                        """,
                        (habit_id, dt.isoformat()),
                    )

            conn.commit()
            return True

    def log_completion(self, habit_id: int, when: datetime) -> None:
        """
        Persist a single completion event for a habit.

        Args:
            habit_id: Database id of the habit being completed.
            when: Datetime of completion (stored as ISO 8601 string).
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tracking (habit_id, completion_date)
                VALUES (?, ?)
                """,
                (habit_id, when.isoformat()),
            )
            conn.commit()

    def load_habits(self) -> list[dict]:
        """
        Load all habits and their completion history from the database.

        Returns:
            A list of habit dictionaries. Each dictionary contains:
                - id (int)
                - name (str)
                - description (str)
                - periodicity (str)
                - created_date (datetime)
                - completion_dates (list[datetime])
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM habits")
            rows = cursor.fetchall()

            habits = []
            for row in rows:
                habit_id = row[0]

                cursor.execute(
                    """
                    SELECT completion_date FROM tracking
                    WHERE habit_id = ?
                    ORDER BY completion_date ASC
                    """,
                    (habit_id,),
                )

                completions = [
                    datetime.fromisoformat(r[0]) for r in cursor.fetchall()
                ]

                habit = {
                    "id": habit_id,
                    "name": row[1],
                    "description": row[2],
                    "periodicity": row[3],
                    "created_date": datetime.fromisoformat(row[4]),
                    "completion_dates": completions,
                }
                habits.append(habit)

            return habits

    def delete_habit(self, habit_id: int) -> bool:
        """
        Delete a habit and all associated completion events.

        Args:
            habit_id: Database id of the habit to delete.

        Returns:
            True if the deletion was executed.
        """

        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tracking WHERE habit_id = ?", (habit_id,))
            cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

            conn.commit()
            return True
