"""Tests for the Task A extraction grader.

Fixtures are synthetic inputs for testing grader code paths only.
They are NOT benchmark golden-set items and must not be used as evaluation data.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from pocketeval.graders.extraction import grade
from pocketeval.normalise import currency_to_decimal, date_to_iso

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "grader_fixtures.json"
_RAW = json.loads(FIXTURES_PATH.read_text())
EXPECTED = _RAW["extraction"]["expected_receipt"]
OUTPUTS = _RAW["extraction"]["outputs"]


# ---- Happy path ----

def test_correct_json_passes():
    result = grade(OUTPUTS["correct_json"], EXPECTED)
    assert not result.parse_error
    assert not result.schema_error
    assert result.correct_strict
    assert result.merchant_match
    assert result.date_match
    assert result.currency_match
    assert result.subtotal_match
    assert result.tax_match
    assert result.total_match
    assert result.line_items_results is not None
    assert all(r.all_match for r in result.line_items_results)


def test_fenced_json_passes():
    result = grade(OUTPUTS["fenced_json"], EXPECTED)
    assert not result.parse_error
    assert not result.schema_error
    assert result.correct_strict


# ---- Prose wrappers ----

def test_output_with_preamble_fails_parse():
    """Prose before JSON means the whole string is not valid JSON."""
    result = grade(OUTPUTS["with_preamble"], EXPECTED)
    assert result.parse_error
    assert not result.correct_strict


def test_output_with_trailing_prose_fails_parse():
    """Trailing prose after JSON produces invalid JSON."""
    result = grade(OUTPUTS["with_trailing_prose"], EXPECTED)
    assert result.parse_error
    assert not result.correct_strict


# ---- Empty / truncated ----

def test_empty_output():
    result = grade(OUTPUTS["empty_output"], EXPECTED)
    assert result.parse_error
    assert not result.correct_strict
    assert result.merchant_match is None


def test_truncated_json():
    result = grade(OUTPUTS["truncated_json"], EXPECTED)
    assert result.parse_error
    assert not result.correct_strict


# ---- Wrong types ----

def test_total_as_float_fails_schema():
    """total as a JSON number (float) must fail schema validation."""
    result = grade(OUTPUTS["total_as_string_wrong_type"], EXPECTED)
    assert not result.parse_error
    assert result.schema_error
    assert result.merchant_match is None


# ---- Decimal vs float money equality ----

def test_decimal_money_equality_not_float():
    """currency_to_decimal must return Decimal, not float."""
    d = currency_to_decimal("13.75")
    assert isinstance(d, Decimal)
    assert d == Decimal("13.75")


def test_european_format_raises():
    """European-format numbers (comma as decimal separator) must raise, not silently mangle."""
    with pytest.raises(ValueError, match="European decimal-comma"):
        currency_to_decimal("1.234,56")


# ---- Date normalisation ----

@pytest.mark.parametrize("value,expected_iso", [
    ("03/15/2024", "2024-03-15"),     # MM/DD/YYYY
    ("13/02/2024", "2024-02-13"),     # DD/MM/YYYY fallback: 13 is not a valid month
    ("January 3, 2024", "2024-01-03"),  # full month name with comma
    ("Jan 3 2024", "2024-01-03"),     # abbreviated month name without comma
])
def test_date_to_iso_non_iso_formats(value: str, expected_iso: str):
    assert date_to_iso(value) == expected_iso


def test_date_to_iso_invalid_raises():
    with pytest.raises(ValueError, match="Cannot parse date string"):
        date_to_iso("not-a-date")


def test_grader_rejects_float_imprecise_total():
    """A monetary value with float-arithmetic noise is scored as not matching."""
    wrong = json.loads(OUTPUTS["correct_json"])
    wrong["total"] = "13.750000000001"
    result = grade(json.dumps(wrong), EXPECTED)
    assert not result.total_match
    assert not result.correct_strict


# ---- Parse vs schema error distinguishable ----

def test_parse_error_flag_set_for_bad_json():
    result = grade("not json at all", EXPECTED)
    assert result.parse_error
    assert not result.schema_error


def test_schema_error_flag_set_for_wrong_structure():
    # Valid JSON but missing required fields
    result = grade('{"merchant": "X"}', EXPECTED)
    assert not result.parse_error
    assert result.schema_error


# ---- Per-field results ----

def test_per_field_results_returned():
    result = grade(OUTPUTS["correct_json"], EXPECTED)
    assert result.fields_matched == result.fields_total
    assert result.fields_matched == 6


def test_mismatched_merchant_flagged():
    wrong = json.loads(OUTPUTS["correct_json"])
    wrong["merchant"] = "Wrong Place"
    result = grade(json.dumps(wrong), EXPECTED)
    assert not result.parse_error
    assert not result.schema_error
    assert not result.merchant_match
    assert result.date_match
    assert not result.correct_strict


def test_line_item_count_mismatch_all_false():
    wrong = json.loads(OUTPUTS["correct_json"])
    wrong["line_items"] = []
    result = grade(json.dumps(wrong), EXPECTED)
    assert not result.parse_error
    assert not result.schema_error
    assert result.line_items_results is not None
    assert all(not r.all_match for r in result.line_items_results)
    assert not result.correct_strict


def test_line_item_unit_price_compared_as_decimal():
    correct = json.loads(OUTPUTS["correct_json"])
    # Use a different but numerically equal representation
    correct["line_items"][0]["unit_price"] = "3.500"
    result = grade(json.dumps(correct), EXPECTED)
    assert result.line_items_results[0].unit_price_match
