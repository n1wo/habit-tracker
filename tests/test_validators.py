"""
Unit tests for the CLI prompt validators.

These tests verify that the Questionary-style validators in habit_tracker.ui.validators:
- Enforce required input (non-empty after stripping)
- Enforce min/max length constraints
- Optionally enforce allowed characters via regex patterns
- Allow optional input while still enforcing max length and (optionally) regex rules

Validators follow the Questionary contract:
- Return True for valid input
- Return a string error message for invalid input
"""

import pytest

from habit_tracker.ui.validators import required_text, optional_text


# Keep these aligned with what actions.py
NAME_PATTERN = r"[A-Za-z0-9 _-]+"
DESC_PATTERN = r"[A-Za-z0-9 _\-\.,!?()']*"


@pytest.fixture
def name_validator():
    """
    Provide a required_text() validator configured for habit names.
    """
    return required_text(
        field_name="Habit name",
        min_len=2,
        max_len=40,
        pattern=NAME_PATTERN,
    )


@pytest.fixture
def desc_validator():
    """
    Provide an optional_text() validator configured for habit descriptions.
    """
    return optional_text(
        max_len=120,
        pattern=DESC_PATTERN,
    )


def test_required_text_rejects_empty_and_whitespace(name_validator) -> None:
    """
    required_text() should reject empty and whitespace-only values.
    """
    result_empty = name_validator("")
    result_ws = name_validator("   ")

    assert result_empty is not True
    assert isinstance(result_empty, str)

    assert result_ws is not True
    assert isinstance(result_ws, str)


def test_required_text_rejects_too_short(name_validator) -> None:
    """
    required_text() should reject values shorter than min_len.
    """
    result = name_validator("A")

    assert result is not True
    assert isinstance(result, str)


def test_required_text_rejects_too_long() -> None:
    """
    required_text() should reject values longer than max_len.
    """
    validate = required_text(
        field_name="Habit name",
        min_len=2,
        max_len=5,
        pattern=NAME_PATTERN,
    )

    result = validate("abcdef")

    assert result is not True
    assert isinstance(result, str)


def test_required_text_rejects_invalid_characters(name_validator) -> None:
    """
    required_text() should reject values that do not match the regex pattern.
    """
    result_semicolon = name_validator("Drop table;")
    result_slash = name_validator("Hello/World")

    assert result_semicolon is not True
    assert isinstance(result_semicolon, str)

    assert result_slash is not True
    assert isinstance(result_slash, str)


def test_required_text_accepts_valid_input(name_validator) -> None:
    """
    required_text() should accept valid values that meet length + pattern rules.
    """
    assert name_validator("Read") is True
    assert name_validator("Gym - Day 1") is True
    assert name_validator("Read_Books_2026") is True
    assert name_validator("A1") is True


def test_optional_text_allows_empty_values(desc_validator) -> None:
    """
    optional_text() should allow empty input (including whitespace-only).
    """
    assert desc_validator("") is True
    assert desc_validator("   ") is True


def test_optional_text_enforces_max_length() -> None:
    """
    optional_text() should reject values longer than max_len.
    """
    validate = optional_text(max_len=5, pattern=DESC_PATTERN)

    result = validate("toolong")

    assert result is not True
    assert isinstance(result, str)


def test_optional_text_rejects_invalid_characters_when_nonempty(desc_validator) -> None:
    """
    optional_text() should reject invalid characters when pattern is provided
    and the user entered a non-empty value.
    """
    assert desc_validator("Nice, simple description.") is True

    # Slash is not allowed by DESC_PATTERN
    result = desc_validator("Bad/Char")

    assert result is not True
    assert isinstance(result, str)
