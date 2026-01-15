# 🧠 Habit Tracker App

A **Command-Line Interface (CLI)** application built with **Python 3.14**, designed to help users **create, track, and analyze habits** using a modular, testable architecture.

Developed as part of the **IU course DLBDSOOFPP01 – Object-Oriented and Functional Programming with Python**.

---

## 📘 Overview

The Habit Tracker helps users build consistent daily and weekly routines by tracking habits, marking completions, and analyzing streaks.  
It applies **Object-Oriented Programming (OOP)** for business logic and **Functional Programming (FP)** for analytics — providing a clean, maintainable structure.

---

## 🧩 Features

✅ Create, view, and delete habits  
🔁 Supports **daily** and **weekly** habits  
🗓️ Mark habits as **completed**  
📊 Analyze progress and streaks  
💾 Persistent data storage via **SQLite** or **JSON**  
🔐 Secure login with **SHA-256 password hashing**  
🧪 Tested with **pytest**  
💬 User-friendly CLI built with **questionary**

---

## 🏗️ Architecture Overview

| Layer | Description | Example Components |
|-------|--------------|--------------------|
| **Boundary (UI)** | Handles user interaction and display | `CLI (questionary)` |
| **Control (Service)** | Core application logic | `HabitManager`, `AuthManager` |
| **Entity (Data)** | Data models (independent of storage) | `Habit`, `User` |
| **Persistence (Storage)** | Saves and loads data | `Storage`, `SqliteStorage`, `JsonStorage` |
| **Analytics (Functional)** | Pure functions (no side effects) | `analytics.py` |

### Design Principles
- Clear **separation of concerns**
- **Swappable** UI and storage backends
- Analytics layer is **pure and side-effect free**
- Testable modular design (OOP + FP blend)

---

## ⚙️ Installation (Step-by-Step)

### 1️⃣ Clone the repository
```bash
git clone https://github.com/n1wo/habit-tracker.git
cd habit-tracker
```

### 2️⃣ Create and activate a virtual environment
**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install the project (runtime dependencies)
Install the project in editable mode so Python automatically finds the src/ layout:
```bash
pip install -e .
```

(Optional) Install development & test dependencies
```bash
pip install -r requirements-dev.txt
```

---

## 🚀 Usage

### Run the app
From the project root:
```bash
python -m habit_tracker
```

### The CLI will guide you through:
- 🔐 First-time password setup (stored securely)
- 📋 Main menu for creating, viewing, and analyzing habits
- ✅ Marking habits as completed
- 🏆 Viewing streak analytics

Example flow:
```
> Add new habit
> Mark habit as completed
> View all habits
> Analyze longest streak
```

---

## 🧪 Running Tests

Run all unit tests with:
```bash
pytest
```

### Test coverage includes:
- Habit creation and deletion
- Completion tracking and streak logic
- Analytics (pure functions)
- Authentication and password handling

---

## 📁 Example Data

The example dataset includes:
- 5 sample habits (daily and weekly)
- 4 weeks of completions  
Use it to test analytics and habit streak features.

---

## 📋 Requirements Summary

- **Python ≥ 3.10**  
- No external habit-tracking libraries  
- Project must include:
  - README with setup and usage instructions  
  - Docstrings and comments  
  - Persistent storage (JSON or SQLite)  
  - Functional analytics  
  - Unit tests (`pytest`)

---

## 💡 Notes for Developers

- Use `HabitService` (abstract base class) to define the logic interface.  
- `HabitManager` implements this interface and is injected into the CLI.  
- Run the app with:
  ```bash
  python -m habit_tracker
  ```
- If you use the `src/` layout, either:
  - Run via `pip install -e .`, or  
  - Temporarily set the path:
    ```powershell
    $env:PYTHONPATH = (Resolve-Path "src").Path
    ```
