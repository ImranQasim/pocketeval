"""Shared data classes for grader inputs and outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


INTENT_LABELS: frozenset[str] = frozenset({
    "billing",
    "technical_support",
    "account_access",
    "cancellation",
    "product_query",
    "other",
})


@dataclass(frozen=True)
class LineItemResult:
    description_match: bool
    quantity_match: bool
    unit_price_match: bool

    @property
    def all_match(self) -> bool:
        return self.description_match and self.quantity_match and self.unit_price_match


@dataclass(frozen=True)
class ExtractionResult:
    """Result of grading one Task A (receipt extraction) response."""

    # Top-level parse / schema outcomes
    parse_error: bool
    schema_error: bool

    # Per-field match results (None when parse or schema failed)
    merchant_match: Optional[bool]
    date_match: Optional[bool]
    currency_match: Optional[bool]
    subtotal_match: Optional[bool]
    tax_match: Optional[bool]
    total_match: Optional[bool]
    line_items_results: Optional[list[LineItemResult]]

    @property
    def correct_strict(self) -> bool:
        """All fields present and all match exactly after normalisation."""
        if self.parse_error or self.schema_error:
            return False
        scalar_matches = [
            self.merchant_match,
            self.date_match,
            self.currency_match,
            self.subtotal_match,
            self.tax_match,
            self.total_match,
        ]
        if not all(scalar_matches):
            return False
        if self.line_items_results is None:
            return False
        return all(r.all_match for r in self.line_items_results)

    @property
    def correct_lenient(self) -> bool:
        """Lenient matching is not separately defined for Task A.

        Structured extraction either matches all required fields or it does not.
        A partial-match threshold has not been specified, so this returns the same
        value as correct_strict. Do not treat the two as distinct measurements
        in Task A result records.
        """
        return self.correct_strict

    @property
    def fields_matched(self) -> int:
        """Count of scalar fields that matched (0 when parse/schema failed)."""
        if self.parse_error or self.schema_error:
            return 0
        return sum([
            bool(self.merchant_match),
            bool(self.date_match),
            bool(self.currency_match),
            bool(self.subtotal_match),
            bool(self.tax_match),
            bool(self.total_match),
        ])

    @property
    def fields_total(self) -> int:
        return 6


@dataclass(frozen=True)
class ClassificationResult:
    """Result of grading one Task B (intent classification) response."""

    raw_output: str
    expected_label: str

    correct_strict: bool
    correct_lenient: bool

    # Diagnostics
    normalised_output: str
    labels_found: list[str]
