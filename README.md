🧠 Habit Tracker App

A Command-Line Interface (CLI) application built in Python 3.14, designed to help users create, track, and analyze habits using a modular and testable architecture.
Developed as part of the IU course DLBDSOOFPP01 – Object Oriented and Functional Programming with Python.

📘 Overview

The Habit Tracker helps users build good habits and maintain streaks by tracking daily and weekly tasks.
It uses Object-Oriented Programming (OOP) for core logic and Functional Programming (FP) for analytics.

🧩 Features

✅ Create, delete, and list habits

🔁 Support for daily and weekly habits

🗓️ Track completions and streaks

📊 Functional analytics:

List all habits

Filter by periodicity

View longest streak overall

View longest streak for a specific habit

💾 Persistent data storage (SQLite or JSON)

🔐 Password-based login with SHA-256 hashing

🧪 Unit-tested using pytest

🏗️ Architecture
Layer	Description	Example Components
Boundary (UI)	Handles user input/output	CLI (questionary)
Control (Service)	Core business logic	HabitManager, AuthManager
Entity (Data)	Data models	Habit, User
Persistence (Storage)	Data saving/loading	Storage, SqliteStorage, JsonStorage
Analytics (Functional)	Pure FP functions	Analytics module

Design principles:

Clear separation of concerns

Swappable storage and front-end

Analytics module is side-effect-free

⚙️ Installation
1. Clone the repository
git clone https://github.com/<your-username>/habit-tracker.git
cd habit-tracker

2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # on macOS/Linux
venv\Scripts\activate     # on Windows

3. Install dependencies
pip install -r requirements.txt

🚀 Usage

Start the app:

python habit_tracker.py


You’ll be guided through:

First-time password setup (hashed and stored securely)

Main menu for creating, checking off, and analyzing habits

Example flow:

> Add new habit
> Check off habit
> Show longest streak

🧪 Testing

Run all unit tests:

pytest


Tests cover:

Habit creation and deletion

Completion and streak logic

Analytics functions

Authentication and password handling

📊 Example Data

Includes 5 predefined habits (daily and weekly)
with 4 weeks of sample completions for testing and analysis.

🧾 Requirements Summary

Python ≥ 3.7

No external habit tracker reuse

README + docstrings required

SQLite or JSON persistence

Functional analytics implementation

Unit testing via pytest
