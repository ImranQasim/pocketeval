"""Task A grader: receipt field extraction.

Grade order:
  1. Strip code fences and attempt JSON parse  -> parse_error if this fails
  2. Validate against the receipt schema        -> schema_error if this fails
  3. Field-by-field comparison after normalise  -> per-field match flags

A parse failure and a schema failure are distinct: parse_error=True means the
output was not valid JSON at all; schema_error=True means the JSON parsed but
did not conform to the expected receipt structure (wrong types, missing fields,
etc.). Both flags can be inspected independently in ExtractionResult.
"""

from __future__ import annotations

import json
from typing import Any

import jsonschema

from pocketeval.normalise import (
    collapse_whitespace,
    currency_to_decimal,
    date_to_iso,
    fold_case,
    strip_code_fences,
)
from pocketeval.schema import ExtractionResult, LineItemResult


_RECEIPT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["merchant", "date", "currency", "subtotal", "tax", "total", "line_items"],
    "additionalProperties": False,
    "properties": {
        "merchant": {"type": "string"},
        "date": {"type": "string"},
        "currency": {"type": "string"},
        "subtotal": {"type": "string"},
        "tax": {"type": "string"},
        "total": {"type": "string"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "quantity", "unit_price"],
                "additionalProperties": False,
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "string"},
                },
            },
        },
    },
}

_VALIDATOR = jsonschema.Draft202012Validator(_RECEIPT_SCHEMA)


def _money_eq(a: str, b: str) -> bool:
    """Compare two monetary strings as Decimal. Returns False if either is unparseable."""
    try:
        return currency_to_decimal(a) == currency_to_decimal(b)
    except ValueError:
        return False


def _normalise_str(s: str) -> str:
    return fold_case(collapse_whitespace(s))


def grade(raw_output: str, expected: dict[str, Any]) -> ExtractionResult:
    """Grade a raw model output against an expected receipt dict.

    Args:
        raw_output: Verbatim text from the model.
        expected: The ground-truth receipt dict (already validated; callers
            should load this from a verified task item).

    Returns:
        ExtractionResult with per-field match flags and aggregate outcomes.
    """
    # Step 1: strip fences and parse JSON
    cleaned = strip_code_fences(raw_output)
    try:
        parsed: dict[str, Any] = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return ExtractionResult(
            parse_error=True,
            schema_error=False,
            merchant_match=None,
            date_match=None,
            currency_match=None,
            subtotal_match=None,
            tax_match=None,
            total_match=None,
            line_items_results=None,
        )

    # Step 2: validate schema
    errors = list(_VALIDATOR.iter_errors(parsed))
    if errors:
        return ExtractionResult(
            parse_error=False,
            schema_error=True,
            merchant_match=None,
            date_match=None,
            currency_match=None,
            subtotal_match=None,
            tax_match=None,
            total_match=None,
            line_items_results=None,
        )

    # Step 3: field-by-field comparison
    merchant_match = _normalise_str(parsed["merchant"]) == _normalise_str(expected["merchant"])
    currency_match = parsed["currency"].strip().upper() == expected["currency"].strip().upper()
    subtotal_match = _money_eq(parsed["subtotal"], expected["subtotal"])
    tax_match = _money_eq(parsed["tax"], expected["tax"])
    total_match = _money_eq(parsed["total"], expected["total"])

    try:
        date_match = date_to_iso(parsed["date"]) == date_to_iso(expected["date"])
    except ValueError:
        date_match = False

    # Line items: compare element-wise; length mismatch means no items match
    expected_items: list[dict[str, Any]] = expected.get("line_items", [])
    parsed_items: list[dict[str, Any]] = parsed.get("line_items", [])

    if len(parsed_items) != len(expected_items):
        line_items_results = [
            LineItemResult(
                description_match=False,
                quantity_match=False,
                unit_price_match=False,
            )
            for _ in expected_items
        ]
    else:
        line_items_results = [
            LineItemResult(
                description_match=(
                    _normalise_str(p["description"]) == _normalise_str(e["description"])
                ),
                quantity_match=(p["quantity"] == e["quantity"]),
                unit_price_match=_money_eq(p["unit_price"], e["unit_price"]),
            )
            for p, e in zip(parsed_items, expected_items)
        ]

    return ExtractionResult(
        parse_error=False,
        schema_error=False,
        merchant_match=merchant_match,
        date_match=date_match,
        currency_match=currency_match,
        subtotal_match=subtotal_match,
        tax_match=tax_match,
        total_match=total_match,
        line_items_results=line_items_results,
    )
