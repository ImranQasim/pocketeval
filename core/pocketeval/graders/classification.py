"""Task B grader: intent classification.

Scoring rules:

  correct_strict: raw output, after whitespace collapse and casefolding,
                  equals the expected label exactly.

  correct_lenient: the expected label appears as a whole token in the output
                   AND no other valid class label appears. If two or more
                   class labels are present, lenient is False. Ambiguous
                   output is scored False, not guessed.
"""

from __future__ import annotations

import re

from pocketeval.normalise import normalise_text
from pocketeval.schema import INTENT_LABELS, ClassificationResult


def _tokenise(text: str) -> list[str]:
    """Split on non-word characters, returning lower-cased tokens."""
    return re.findall(r"[\w]+", text.casefold())


def _labels_in_tokens(tokens: list[str]) -> list[str]:
    """Return which intent labels appear in *tokens* (as whole token matches).

    Multi-word labels (e.g. technical_support) are matched as a single token
    because the underscore is a word character and re.findall keeps it intact.
    Result is sorted alphabetically for deterministic output across Python versions.
    """
    return sorted(label for label in INTENT_LABELS if label in tokens)


def grade(raw_output: str, expected_label: str) -> ClassificationResult:
    """Grade a raw model output against an expected intent label.

    Args:
        raw_output: Verbatim text from the model.
        expected_label: One of the six valid intent labels.

    Returns:
        ClassificationResult with strict and lenient scores plus diagnostics.

    Raises:
        ValueError: If expected_label is not a recognised intent label.
    """
    if expected_label not in INTENT_LABELS:
        raise ValueError(
            f"expected_label {expected_label!r} is not a valid intent label. "
            f"Valid labels: {sorted(INTENT_LABELS)}"
        )

    normalised = normalise_text(raw_output)

    # Strict: entire normalised output equals the label
    correct_strict = normalised == expected_label

    # Lenient: label appears as a token, and no other label does
    tokens = _tokenise(raw_output)
    labels_found = _labels_in_tokens(tokens)

    if len(labels_found) == 1 and labels_found[0] == expected_label:
        correct_lenient = True
    else:
        correct_lenient = False

    return ClassificationResult(
        raw_output=raw_output,
        expected_label=expected_label,
        correct_strict=correct_strict,
        correct_lenient=correct_lenient,
        normalised_output=normalised,
        labels_found=labels_found,
    )
