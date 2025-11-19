import sqlite3
from habit_tracker.storage import Storage
from datetime import datetime

class SQLStore(Storage):
    _DB_NAME = 'habit_tracker.db'

    def __init__(self):
        self._initialize_db()

    def _initialize_db(self):
            with sqlite3.connect(self._DB_NAME) as conn:
                cursor = conn.cursor() # Creates a cursor, which is an object used to run SQL commands.

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS habits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        periodicity TEXT NOT NULL,
                        created_date TEXT NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        habit_id INTEGER NOT NULL,
                        completion_date TEXT,
                        FOREIGN KEY (habit_id) REFERENCES habits (id)
                    )
                ''')

                conn.commit() # Saves the table creation to the database

    # Storage interface methods

    # Save a single habit
    def save_habit(self, habit_data):
        with sqlite3.connect(self._DB_NAME) as conn:
            cursor = conn.cursor() 

            # Insert habit
            cursor.execute("""
                INSERT INTO habits (name, description, periodicity, created_date)
                VALUES (?, ?, ?, ?)
            """, (
                habit_data["name"],
                habit_data.get("description", ""),
                habit_data.get("periodicity"),
                habit_data.get("created_date").isoformat()
            ))

            habit_id = cursor.lastrowid
            
            # Insert completions
            for dt in habit_data.get("completion_dates", []):
                cursor.execute("""
                    INSERT INTO tracking (habit_id, completion_date)
                    VALUES (?, ?)
                """, (habit_id, dt.isoformat()))

            conn.commit()

            return habit_id

    # Save all habits
    def save_all(self, habits_list):
        with sqlite3.connect(self._DB_NAME) as conn:
            cursor = conn.cursor()

            # Clear old data
            cursor.execute("DELETE FROM tracking")
            cursor.execute("DELETE FROM habits")

            for habit_data in habits_list:
                cursor.execute("""
                    INSERT INTO habits (name, description, periodicity, created_date)
                    VALUES (?, ?, ?, ?)
                """, (
                    habit_data["name"],
                    habit_data.get("description", ""),
                    habit_data["periodicity"],
                    habit_data["created_date"].isoformat()
                ))

                habit_id = cursor.lastrowid

                for dt in habit_data.get("completion_dates", []):
                    cursor.execute("""
                        INSERT INTO tracking (habit_id, completion_date)
                        VALUES (?, ?)
                    """, (habit_id, dt.isoformat()))

            conn.commit()
            return True
        
    def log_completion(self, habit_id: int, when: datetime):
        """Persist a single completion event for a habit."""
        with sqlite3.connect(self._DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tracking (habit_id, completion_date)
                VALUES (?, ?)
            """, (habit_id, when.isoformat()))
            conn.commit()

    # Load all habits
    def load_habits(self):
        with sqlite3.connect(self._DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM habits")
            rows = cursor.fetchall()

            habits = []
            for row in rows:
                habit_id = row[0]

                cursor.execute("""
                    SELECT completion_date FROM tracking
                    WHERE habit_id = ?
                    ORDER BY completion_date ASC
                """, (habit_id,))

                completions = [datetime.fromisoformat(r[0]) for r in cursor.fetchall()]

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
        with sqlite3.connect(self._DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM tracking WHERE habit_id = ?", (habit_id,))
            cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

            conn.commit()

            return True
        




