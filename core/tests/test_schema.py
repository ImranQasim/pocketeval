"""Tests for JSON schema validation of task_item and result schemas.

Uses jsonschema to validate synthetic examples against the published schemas.
These fixtures are grader logic test data, not benchmark golden-set items.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_DIR = Path(__file__).parent.parent.parent / "tasks" / "schema"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


TASK_ITEM_SCHEMA = load_schema("task_item.schema.json")
RESULT_SCHEMA = load_schema("result.schema.json")


def _validate(instance: dict, schema: dict) -> None:
    jsonschema.validate(instance, schema)


# ---- task_item: Task B (classification) ----

VALID_TASK_B = {
    "item_id": "test-b-001",
    "task": "B",
    "item_version": 1,
    "input": "I want to cancel my subscription.",
    "expected": {"label": "cancellation"},
    "source": "synthetic test fixture",
    "verified_by": "test",
    "verified_on": "2026-01-01",
}

VALID_TASK_A = {
    "item_id": "test-a-001",
    "task": "A",
    "item_version": 1,
    "input": "Extract the receipt.",
    "expected": {
        "merchant": "Corner Bakery",
        "date": "2024-03-15",
        "currency": "USD",
        "subtotal": "12.50",
        "tax": "1.25",
        "total": "13.75",
        "line_items": [
            {"description": "Croissant", "quantity": 2, "unit_price": "3.50"}
        ],
    },
    "source": "synthetic test fixture",
    "verified_by": "test",
    "verified_on": "2026-01-01",
}


def test_task_b_valid():
    _validate(VALID_TASK_B, TASK_ITEM_SCHEMA)


def test_task_a_valid():
    _validate(VALID_TASK_A, TASK_ITEM_SCHEMA)


@pytest.mark.parametrize("label", [
    "billing", "technical_support", "account_access",
    "cancellation", "product_query", "other",
])
def test_task_b_all_valid_labels(label: str):
    item = {**VALID_TASK_B, "expected": {"label": label}}
    _validate(item, TASK_ITEM_SCHEMA)


def test_task_b_invalid_label_rejected():
    item = {**VALID_TASK_B, "expected": {"label": "unknown_intent"}}
    with pytest.raises(jsonschema.ValidationError):
        _validate(item, TASK_ITEM_SCHEMA)


def test_task_item_missing_required_field():
    item = {k: v for k, v in VALID_TASK_B.items() if k != "verified_by"}
    with pytest.raises(jsonschema.ValidationError):
        _validate(item, TASK_ITEM_SCHEMA)


@pytest.mark.parametrize("task", ["C", "D", "Z", "a", ""])
def test_task_item_invalid_task_letter(task: str):
    item = {**VALID_TASK_B, "task": task}
    with pytest.raises(jsonschema.ValidationError):
        _validate(item, TASK_ITEM_SCHEMA)


# ---- result schema ----

VALID_RESULT = {
    "item_id": "test-b-001",
    "item_version": 1,
    "run_index": 0,
    "timestamp": "2026-01-01T00:00:00Z",
    "model_id": "test-model",
    "model_version": "1.0",
    "os_version": "18.0",
    "device_model": "iPhone17,1",
    "raw_output": "billing",
    "parsed_output": None,
    "schema_valid": True,
    "correct_strict": True,
    "correct_lenient": True,
    "time_to_first_token_ms": 120.5,
    "total_latency_ms": 850.0,
    "decode_tokens_per_sec": 12.3,
    "peak_memory_mb": 512.0,
    "thermal_state": "nominal",
    "battery_delta_pct": -0.5,
}


def test_result_valid():
    _validate(VALID_RESULT, RESULT_SCHEMA)


def test_result_nullable_fields_can_be_null():
    result = {
        **VALID_RESULT,
        "parsed_output": None,
        "time_to_first_token_ms": None,
        "total_latency_ms": None,
        "decode_tokens_per_sec": None,
        "peak_memory_mb": None,
        "thermal_state": None,
        "battery_delta_pct": None,
    }
    _validate(result, RESULT_SCHEMA)


def test_result_missing_raw_output_rejected():
    result = {k: v for k, v in VALID_RESULT.items() if k != "raw_output"}
    with pytest.raises(jsonschema.ValidationError):
        _validate(result, RESULT_SCHEMA)
