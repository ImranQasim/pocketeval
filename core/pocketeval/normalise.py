"""
Deterministic normalisation helpers for PocketEval graders.

Each function is a pure function with no side effects. These rules are
methodology: they are published alongside results and must not change
between evaluation runs without a version bump.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def collapse_whitespace(text: str) -> str:
    """Replace every run of whitespace (including newlines and tabs) with a
    single ASCII space, then strip leading and trailing whitespace.

    Does not alter any non-whitespace characters.
    """
    return re.sub(r"\s+", " ", text).strip()


def fold_case(text: str) -> str:
    """Return the Unicode casefold of *text*.

    Casefolding is stronger than lower-casing: it handles language-specific
    case pairs (e.g. German sharp-s) that str.lower() misses. ASCII input is
    unaffected beyond lower-casing.
    """
    return text.casefold()


def normalise_text(text: str) -> str:
    """Collapse whitespace then casefold.

    Convenience composition of collapse_whitespace and fold_case. Applied in
    that order so whitespace runs are reduced before casefolding, which
    guarantees idempotency.
    """
    return fold_case(collapse_whitespace(text))


def currency_to_decimal(value: str) -> Decimal:
    """Parse a currency string to a Decimal, raising ValueError on failure.

    Accepts optional leading currency symbols ($, EUR, GBP, etc.) and
    optional US-style thousands separators (commas before the decimal point,
    e.g. "1,234.56"). Never produces a float; callers must compare monetary
    values as Decimal.

    Does not support European-format numbers where the comma is the decimal
    separator (e.g. "1.234,56"). Such input is detected and raises ValueError
    rather than silently returning a wrong value.

    Does not apply rounding or precision coercion. The strings "10" and "10.00"
    produce Decimal values with different internal representations, but Python's
    == operator compares them as numerically equal. Callers that need to
    distinguish trailing zeros must use Decimal.compare() or compare the
    original strings directly.
    """
    stripped_val = value.strip()

    # Reject European-format numbers where a comma follows the last dot,
    # e.g. "1.234,56". The comma would otherwise be stripped silently,
    # producing Decimal("1.23456") instead of the correct 1234.56.
    last_comma = stripped_val.rfind(",")
    last_dot = stripped_val.rfind(".")
    if last_comma != -1 and last_dot != -1 and last_comma > last_dot:
        raise ValueError(
            f"Cannot parse currency string (European decimal-comma format is not supported): {value!r}"
        )

    cleaned = re.sub(r"[^\d.\-]", "", stripped_val)
    if not cleaned:
        raise ValueError(f"Cannot parse currency string: {value!r}")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Cannot parse currency string: {value!r}") from exc


def date_to_iso(value: str) -> str:
    """Parse common date string representations and return an ISO 8601 date
    (YYYY-MM-DD).

    Supported input formats (in order tried):
      YYYY-MM-DD    (already ISO; returned as-is after validation)
      MM/DD/YYYY
      DD/MM/YYYY    (tried only if MM/DD/YYYY produces an invalid date)
      Month DD, YYYY  (e.g. January 3, 2024 or Jan 3, 2024)

    Raises ValueError if no format matches or the resulting date is invalid.

    Does not accept two-digit years. Does not accept time components.
    """
    from datetime import date, datetime

    value = value.strip()

    # YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass

    # MM/DD/YYYY
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", value)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            # Try DD/MM/YYYY interpretation
            try:
                return date(year, day, month).isoformat()
            except ValueError:
                pass

    # Month DD, YYYY or Mon DD, YYYY
    m = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", value
    )
    if m:
        try:
            return datetime.strptime(
                f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y"
            ).date().isoformat()
        except ValueError:
            try:
                return datetime.strptime(
                    f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y"
                ).date().isoformat()
            except ValueError:
                pass

    raise ValueError(f"Cannot parse date string: {value!r}")


def strip_code_fences(text: str) -> str:
    """Remove a single wrapping Markdown code fence from *text* if present.

    A code fence is an opening line of three or more backticks (optionally
    with a language tag) followed by a matching closing line of three or more
    backticks. Only the outermost fence is removed; inner fences are left
    untouched.

    Leading and trailing whitespace outside the fence is stripped. Content
    inside the fence is returned with its own leading/trailing newlines
    stripped but otherwise intact.
    """
    stripped = text.strip()
    pattern = re.compile(
        r"^`{3,}[a-zA-Z0-9_\-]*\n(.*?)\n`{3,}$", re.DOTALL
    )
    m = pattern.match(stripped)
    if m:
        return m.group(1).strip()
    return stripped


