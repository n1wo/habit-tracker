import sqlite3
from datetime import datetime
from typing import Optional
from pathlib import Path  # NEW

from habit_tracker.storage import Storage
from habit_tracker.models import User


class SQLStore(Storage):
    # Project root: .../src/habit_tracker/storage/sql_store.py -> go up 3 levels
    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    _DATA_DB_DIR = _PROJECT_ROOT / "data" / "db"
    _DATA_SAMPLE_DIR = _PROJECT_ROOT / "data" / "sample"

    # Default DB path in data/db
    _DEFAULT_DB_PATH = _DATA_DB_DIR / "habit_tracker.db"

    def __init__(self, db_path: Optional[str] = None):
        # allow overriding DB path (useful for tests)
        self._db_path = Path(db_path) if db_path is not None else self._DEFAULT_DB_PATH

        # Make sure directories exist (skip for in-memory DB)
        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        # also ensure sample data dir exists
        self._DATA_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

        self._initialize_db()

    def _initialize_db(self):
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
    def save_user(self, user: User):
        """Insert or update the single user row."""
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
        """Load the single stored user, or None if not set."""
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
    def save_habit(self, habit_data):
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

    def save_all(self, habits_list):
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

    def log_completion(self, habit_id: int, when: datetime):
        """Persist a single completion event for a habit."""
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

    def load_habits(self):
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

    def delete_habit(self, habit_id):
        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tracking WHERE habit_id = ?", (habit_id,))
            cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

            conn.commit()
            return True
