from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Dict, Any, List


class FormatType(Enum):
    COMPLEX = "format1_complex"
    SIMPLE = "format2_simple"


@dataclass
class ComplexityMetrics:
    entity_count: int = 0
    transaction_count: int = 0
    relationship_count: int = 0
    document_count: int = 0
    note_count: int = 0
    custom_field_count: int = 0
    geographic_coordinates: int = 0
    intermediary_count: int = 0
    beneficial_owner_count: int = 0
    risk_factors_count: int = 0
    total_complexity_score: float = 0.0


class XSDFormatSelector:
    """Lightweight heuristic selector used by the format selector service.

    Heuristics are intentionally simple and deterministic to satisfy tests:
    - Count occurrences of key tokens to derive a complexity score
    - If score > threshold choose complex, otherwise simple
    """

    SIMPLE_THRESHOLD: float = 5.0

    def __init__(self) -> None:
        self._format_info: Dict[FormatType, Dict[str, Any]] = {
            FormatType.COMPLEX: {
                "name": "Complex Regulatory XML Format",
                "description": "Nested, comprehensive schema for detailed filings.",
                "characteristics": {
                    "nesting": "deep",
                    "supports_relationships": True,
                    "supports_documents": True,
                },
                "best_for": [
                    "Multi-entity cases",
                    "Multiple transactions",
                    "High-risk investigations",
                ],
                "data_requirements": [
                    "Primary and related entities",
                    "Intermediaries and beneficial owners",
                    "Risk factors and supporting documents",
                ],
            },
            FormatType.SIMPLE: {
                "name": "Simple Regulatory XML Format",
                "description": "Flat schema for basic, single-entity filings.",
                "characteristics": {
                    "nesting": "flat",
                    "supports_relationships": False,
                    "supports_documents": False,
                },
                "best_for": [
                    "Single entity",
                    "Single transaction",
                    "Low complexity reports",
                ],
                "data_requirements": [
                    "Entity name and type",
                    "One primary transaction",
                ],
            },
        }

    def get_format_recommendation(self, pipe_data: str) -> Tuple[FormatType, str, ComplexityMetrics]:
        tokens = self._tokenize(pipe_data)
        metrics = self._compute_metrics(tokens)
        reasoning = self._build_reasoning(metrics)
        format_type = FormatType.COMPLEX if metrics.total_complexity_score > self.SIMPLE_THRESHOLD else FormatType.SIMPLE
        return format_type, reasoning, metrics

    def validate_pipe_data(self, pipe_data: str) -> List[str]:
        issues: List[str] = []
        if not pipe_data or not pipe_data.strip():
            issues.append("Pipe data is empty")
            return issues

        lines = [ln.strip() for ln in pipe_data.splitlines() if ln.strip()]
        for idx, line in enumerate(lines, start=1):
            if "|" not in line:
                issues.append(f"Line {idx} has no field separator '|': {line}")
            else:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 2 or not parts[0] or not parts[1]:
                    issues.append(f"Line {idx} missing field name/value: {line}")
        return issues

    def get_format_info(self, format_type: FormatType) -> Dict[str, Any]:
        return self._format_info.get(format_type, {})

    def _tokenize(self, text: str) -> List[str]:
        # Split on pipes and non-alphanumeric boundaries, keep simple lowercase tokens
        raw = text.replace("|", " ").replace(":", " ").replace(",", " ")
        return [t.lower() for t in raw.split() if t]

    def _compute_metrics(self, tokens: List[str]) -> ComplexityMetrics:
        metrics = ComplexityMetrics()

        # Simple heuristics based on token presence/frequency
        metrics.entity_count = sum(tok.startswith("entity") for tok in tokens)
        metrics.transaction_count = sum(tok.startswith("transaction") or tok in {"txn", "tx"} for tok in tokens)
        metrics.relationship_count = tokens.count("relationship") + tokens.count("relatedentity")
        metrics.document_count = sum(tok.startswith("document") for tok in tokens)
        metrics.note_count = sum(tok.startswith("note") for tok in tokens)
        metrics.custom_field_count = tokens.count("type") + tokens.count("status") + tokens.count("amount")
        metrics.geographic_coordinates = tokens.count("lat") + tokens.count("lon") + tokens.count("geo")
        metrics.intermediary_count = tokens.count("intermediary")
        metrics.beneficial_owner_count = tokens.count("beneficial") + tokens.count("owner")
        metrics.risk_factors_count = tokens.count("risk") + tokens.count("severity") + tokens.count("confidence")

        # Weighted sum to produce an overall score
        score = 0.0
        score += 1.0 * metrics.entity_count
        score += 1.5 * metrics.transaction_count
        score += 1.5 * metrics.relationship_count
        score += 1.0 * metrics.document_count
        score += 0.5 * metrics.note_count
        score += 0.5 * metrics.custom_field_count
        score += 1.0 * metrics.geographic_coordinates
        score += 1.0 * metrics.intermediary_count
        score += 1.0 * metrics.beneficial_owner_count
        score += 1.0 * metrics.risk_factors_count

        # Additional bonus for lines > 4 (proxy for complexity)
        # We cannot easily count lines here, but increase score if many tokens present
        if len(tokens) > 30:
            score += 3.0
        elif len(tokens) > 15:
            score += 1.5

        metrics.total_complexity_score = score
        return metrics

    def _build_reasoning(self, metrics: ComplexityMetrics) -> str:
        parts = [
            f"entities={metrics.entity_count}",
            f"transactions={metrics.transaction_count}",
            f"relationships={metrics.relationship_count}",
            f"documents={metrics.document_count}",
            f"risk_factors={metrics.risk_factors_count}",
            f"score={metrics.total_complexity_score:.2f}",
        ]
        return "; ".join(parts)

