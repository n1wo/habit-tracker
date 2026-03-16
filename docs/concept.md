# Habit Tracker App – Written Concept
## Overview
The Habit Tracker App is a **command-line-based application** written in **Python 3.14**, designed to help users build and maintain positive habits through structured daily and weekly tracking.  
It uses a **modular backend** architecture that separates logic, persistence, and user interaction, making it possible to swap the CLI for a future web or desktop interface, and to change the storage backend (e.g., JSON ↔ SQLite) without altering the business logic. It also implements cybersecurity measures through user authentication.

The system follows an **object-oriented architecture** for core entities and a **functional approach** for analytics, ensuring clear separation of concerns and maintainability.  
Unit tests are implemented using **pytest**.

The concept includes five predefined habits (e.g., ‘Drink Water Daily’, ‘Exercise Weekly’) with four weeks of tracking data, used as test fixtures for analytics validation.
## System Overview
- **Entities:** `Habit`, `User` – core data classes, persistence-agnostic.  
- **Control:** `HabitManager`, `AuthManager` – implement `HabitService` / `AuthService` via abstract base classes. Manage logic and persistence.  
- **Persistence:** `Storage` interface with `SqliteStorage` / `JsonStorage` backends.  
- **Boundary:** CLI (via `questionary`) – input/output only, calls service interfaces.  
- **Analytics:** Pure functions (no side effects) for streaks, filtering, and summaries.
### Communication Rules
Boundary → Interface → Control → Entity / Persistence / Analytics

Entities are unaware of persistence; Persistence never calls Control; Analytics is read-only.
### Core Components
- **HabitManager:** Adds, deletes, and tracks habits; delegates storage; invokes analytics.
- **AuthManager:** Handles password setup and login (SHA-256 hashing).
- **HabitService:** Interface that defines the business logic for habit management, ensuring the CLI interacts through a consistent abstraction.
- **AuthService:** Interface that defines the business logic for user authentication and authorization.
- **Storage:** Interface that abstracts data persistence, enabling interchangeable storage backends (e.g., SQLite or JSON) without affecting business logic.
- **Analytics:** Functional module containing pure functions that compute and summarize habit statistics.
- **CLI:** Provides menus for creating, checking off, deleting habits, viewing analytics, and exiting the program.

<div style="page-break-before: always;"></div>

### Typical Flow
1. The user starts the app (`python habit-tracker.py`)
2. On first start, the user creates a password
3. On later runs, the user logs in
4. The main menu is displayed with options:
    - Create a new habit
    - Show list of habits to check off
    - Show analytics
	    - List all habits with statistics
	    - List all habits with statistics by periodicity
	    - Show longest streak overall
	    - Show longest streak per habit
    - Delete a habit
    - Edit a habit
    - Exit the program

Each action triggers a call to the corresponding service interface (`AuthService` or `HabitService`), which delegates logic to the manager and persistence to the storage backend.
### Dependencies
`questionary`, `pytest`, `sqlite3 / json`, `hashlib`
## Summary
The Habit Tracker App is a modular, CLI-based Python application designed using **object-oriented principles** combined with **functional analytics**.  
It ensures data persistence via a swappable storage layer and enforces security through user authentication, and its architecture allows testing, simple extensibility, and a clear separation between user interface, business logic, and data persistence.
