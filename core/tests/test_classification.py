"""Tests for the Task B classification grader.

Fixtures are synthetic inputs for testing grader code paths only.
They are NOT benchmark golden-set items and must not be used as evaluation data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pocketeval.graders.classification import grade
from pocketeval.schema import INTENT_LABELS

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "grader_fixtures.json"
_RAW = json.loads(FIXTURES_PATH.read_text())
OUTPUTS = _RAW["classification"]["outputs"]


# ---- Happy path ----

def test_exact_label_strict_and_lenient():
    result = grade(OUTPUTS["exact_label"], "billing")
    assert result.correct_strict
    assert result.correct_lenient


def test_label_in_sentence_lenient_only():
    """Label appears among words; strict fails because output is not the label alone."""
    result = grade(OUTPUTS["label_with_preamble"], "billing")
    assert not result.correct_strict
    assert result.correct_lenient


# ---- Fenced output ----

def test_fenced_label_strict_false_lenient_true():
    """The classification grader does not strip code fences.

    normalise_text collapses whitespace but preserves backticks, so the
    normalised output of "```\\nbilling\\n```" is "``` billing ```" (newlines
    become spaces), which does not equal "billing" and strict is False. The
    lenient path tokenises with \\w, which excludes backticks and spaces, so
    "billing" appears as a token and lenient is True.
    """
    result = grade(OUTPUTS["fenced_label"], "billing")
    assert not result.correct_strict
    assert result.correct_lenient


# ---- Two labels present ----

def test_two_labels_lenient_false():
    result = grade(OUTPUTS["two_labels_present"], "billing")
    assert not result.correct_strict
    assert not result.correct_lenient
    assert "billing" in result.labels_found
    assert "cancellation" in result.labels_found


# ---- No label present ----

def test_no_label_present():
    result = grade(OUTPUTS["no_label_present"], "billing")
    assert not result.correct_strict
    assert not result.correct_lenient
    assert result.labels_found == []


# ---- Empty output ----

def test_empty_output():
    result = grade(OUTPUTS["empty_output"], "billing")
    assert not result.correct_strict
    assert not result.correct_lenient
    assert result.labels_found == []


# ---- Trailing punctuation ----

def test_label_with_trailing_punctuation_strict_false_lenient_true():
    result = grade(OUTPUTS["label_with_trailing_punct"], "billing")
    # "billing." normalises to "billing." which != "billing"
    assert not result.correct_strict
    # But "billing" token is present (punctuation splits it from the dot)
    assert result.correct_lenient


def test_label_in_longer_sentence():
    """Label token appears alongside non-label words; no other label token present."""
    result = grade(OUTPUTS["label_in_sentence"], "billing")
    assert not result.correct_strict
    assert result.correct_lenient
    assert result.labels_found == ["billing"]


# ---- All valid labels ----

@pytest.mark.parametrize("label", sorted(INTENT_LABELS))
def test_exact_match_all_labels(label: str):
    result = grade(label, label)
    assert result.correct_strict
    assert result.correct_lenient


# ---- Invalid expected label raises ----

def test_invalid_expected_label_raises():
    with pytest.raises(ValueError, match="not a valid intent label"):
        grade("billing", "unknown_intent")


# ---- Result object contains diagnostics ----

def test_result_contains_labels_found():
    result = grade("This is about billing.", "billing")
    assert "billing" in result.labels_found


def test_result_contains_normalised_output():
    result = grade("  Billing  ", "billing")
    assert result.normalised_output == "billing"


def test_wrong_label_scores_false_on_both():
    """A response naming the wrong label must score False on both metrics."""
    result = grade("cancellation", "billing")
    assert not result.correct_strict
    assert not result.correct_lenient
