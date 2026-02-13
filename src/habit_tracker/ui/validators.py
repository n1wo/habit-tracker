from __future__ import annotations

import re
from typing import Callable


def required_text(
    *,
    field_name: str = "Value",
    min_len: int = 1,
    max_len: int = 60,
    pattern: str | None = None,
) -> Callable[[str], bool | str]:
    """
    questionary validator for required text inputs.

    Returns:
        True if valid, otherwise an error message string.
    """
    compiled = re.compile(pattern) if pattern else None

    def _validate(value: str) -> bool | str:

        v = (value or "").strip()

        if len(v) < min_len:
            return f"{field_name} is required."
        if max_len and len(v) > max_len:
            return f"{field_name} must be at most {max_len} characters."
        if compiled and not compiled.fullmatch(v):
            return f"{field_name} contains invalid characters."
        return True

    return _validate


def optional_text(*, max_len: int = 200, pattern: str | None = None) -> Callable[[str], bool | str]:
    compiled = re.compile(pattern) if pattern else None

    def _validate(value: str) -> bool | str:
        v = (value or "").strip()
        if len(v) > max_len:
            return f"Must be at most {max_len} characters."
        if compiled and v and not compiled.fullmatch(v):
            return "Contains invalid characters."
        return True

    return _validate
