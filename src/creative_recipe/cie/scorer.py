"""Weighted aggregation + ranking + diversity-aware Top-K selection.

The six CIE dimensions are weighted (see cie.dimensions.WEIGHTS, sum = 1.0) and combined into a
single canonical CIE v3 total. Candidates are then ranked; Top-K keeps the highest-scoring while
nudging diversity so we don't return near-duplicate ideas.

CANONICAL FINAL SCORE (CIE v3)
------------------------------
The final total is the DIRECT six-dimension weighted sum:

    total_score = sum(WEIGHTS[d] * score[d] for d in ALL_SIX_DIMENSIONS)

There is NO stage-level blend (the historical 0.75 / 0.25 Stage-A/Stage-B blend has been removed).
`weighted_total` is retained only as a DIAGNOSTIC normalized aggregate of a subset of dimensions
(e.g. the five Stage-A dimensions, or the single Stage-B dimension).

INTEGRITY CONTRACT (enforced by `total_score`)
------------------------------------------------
`total_score` validates its inputs BEFORE aggregating: exactly six scores; each canonical dimension
present exactly once (no missing / duplicate / unknown); Stage-A dimensions scored at stage A and
`realization_quality` at stage B; the supplied weights cover exactly the canonical six and sum to
1.0; and every score is an integer 1-5. A missing, duplicated or unknown dimension therefore cannot
yield a "normal" total.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Sequence, Set

from ..types import EvalScore, SCORE_MAX, SCORE_MIN, Stage
from .dimensions import STAGE_A_KEYS, STAGE_B_KEYS, WEIGHTS

# Kept as an alias of the canonical hub so external imports keep working.
DEFAULT_WEIGHTS: Dict[str, float] = WEIGHTS

# Canonical six-dimension set (Stage A's five + Stage B's one).
_CANONICAL_DIMENSIONS: Set[str] = set(STAGE_A_KEYS) | set(STAGE_B_KEYS)
_WEIGHT_SUM_TOL = 1e-9


def _validate_weights(weights: Dict[str, float]) -> None:
    """Validate a weight mapping against the canonical CIE v3 contract.

    Enforces:
      * `weights` is a mapping/dict,
      * its keys are EXACTLY the canonical six dimensions (no missing / ghost key),
      * every value is a number (int/float) but NOT a bool,
      * every value is finite,
      * every value is strictly greater than 0 (no zero / negative weight can silently
        zero-out a canonical dimension),
      * the values sum to 1.0 within a tight float tolerance.
    """
    if not isinstance(weights, Mapping):
        raise ValueError(f"weights must be a mapping/dict, got {type(weights).__name__}")
    if set(weights.keys()) != _CANONICAL_DIMENSIONS:
        missing = sorted(_CANONICAL_DIMENSIONS - set(weights.keys()))
        extra = sorted(set(weights.keys()) - _CANONICAL_DIMENSIONS)
        raise ValueError(
            f"weights must cover exactly the canonical six dimensions; "
            f"missing={missing} extra={extra}"
        )
    for key, val in weights.items():
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError(
                f"weight for {key!r} must be a number, got {type(val).__name__}: {val!r}"
            )
        if not math.isfinite(val):
            raise ValueError(f"weight for {key!r} must be finite, got {val!r}")
        if val <= 0:
            raise ValueError(f"weight for {key!r} must be strictly greater than 0, got {val!r}")
    if not math.isclose(sum(weights.values()), 1.0, rel_tol=_WEIGHT_SUM_TOL):
        raise ValueError(f"weights must sum to 1.0, got {sum(weights.values())!r}")


def _validate_score_set(scores: Sequence[EvalScore], weights: Dict[str, float]) -> None:
    if len(scores) != 6:
        raise ValueError(f"expected exactly 6 dimension scores, got {len(scores)}")
    dims = [s.dimension for s in scores]
    if len(set(dims)) != len(dims):
        dup = sorted({d for d in dims if dims.count(d) > 1})
        raise ValueError(f"duplicate dimensions not allowed: {dup}")
    if set(dims) != _CANONICAL_DIMENSIONS:
        missing = sorted(_CANONICAL_DIMENSIONS - set(dims))
        unknown = sorted(set(dims) - _CANONICAL_DIMENSIONS)
        raise ValueError(f"dimension set mismatch: missing={missing} unknown={unknown}")
    for s in scores:
        if s.dimension in STAGE_A_KEYS and s.stage is not Stage.A:
            raise ValueError(f"{s.dimension} is a Stage-A dimension but was scored at stage {s.stage}")
        if s.dimension == "realization_quality" and s.stage is not Stage.B:
            raise ValueError(f"realization_quality must be scored at Stage B, got {s.stage}")
        if not isinstance(s.score, int) or s.score < SCORE_MIN or s.score > SCORE_MAX:
            raise ValueError(
                f"{s.dimension} score must be an integer in [{SCORE_MIN}, {SCORE_MAX}], got {s.score!r}"
            )
    _validate_weights(weights)


def weighted_total(scores: Sequence[EvalScore], weights: Optional[Dict[str, float]] = None) -> float:
    """DIAGNOSTIC: weights-normalized average of the supplied dimension scores (1-5 scale).

    The result is the weights-NORMALIZED average of exactly the dimensions present in `scores`,
    so calling it on the five Stage-A scores yields the Stage-A diagnostic aggregate, and on the
    single Stage-B score yields the Stage-B diagnostic aggregate. It is NOT the final total.

    Unknown and duplicate dimensions are rejected — a diagnostic aggregate must not silently
    double-count or invent a weight.
    """
    w = WEIGHTS if weights is None else weights
    _validate_weights(w)
    seen: Set[str] = set()
    for s in scores:
        if s.dimension not in w:
            raise ValueError(f"unknown dimension {s.dimension!r}")
        if s.dimension in seen:
            raise ValueError(f"duplicate dimension {s.dimension!r}")
        seen.add(s.dimension)
    if not scores:
        return 0.0
    total_w = sum(w[s.dimension] for s in scores)
    if total_w <= 0:
        return 0.0
    return round(sum(s.score * w[s.dimension] for s in scores) / total_w, 3)


def stage_score(scores: Sequence[EvalScore], weights: Optional[Dict[str, float]] = None) -> float:
    """Alias for `weighted_total` — the normalized aggregate of a single stage's dimensions."""
    return weighted_total(scores, weights=weights)


def total_score(
    scores: Sequence[EvalScore],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Canonical CIE v3 final total: direct six-dimension weighted sum, sum(WEIGHTS[d] * score[d]).

    Validates the integrity of the six-dimension set and the weights BEFORE aggregating, so a
    missing / repeated / unknown dimension (or malformed weights) raises instead of producing a
    plausible-looking but wrong total. `scores` must contain all six dimensions (Stage-A's five +
    Stage-B's one); because the weights sum to 1.0, the result is already the score on the 1-5 scale.
    """
    w = WEIGHTS if weights is None else weights
    _validate_score_set(scores, w)
    return round(sum(s.score * w[s.dimension] for s in scores), 4)


def final_score(
    scores: Sequence[EvalScore],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Alias for `total_score` — the canonical direct six-dimension weighted sum (no stage blend)."""
    return total_score(scores, weights=weights)


def rank_reports(reports: List[EvalReport]) -> List[EvalReport]:
    """Sort reports by total_score (desc) and assign 1-based ranks in place."""
    ordered = sorted(reports, key=lambda r: r.total_score, reverse=True)
    for i, r in enumerate(ordered, 1):
        r.rank = i
    return ordered


def select_top_k(
    items: Sequence[EvalReport],
    k: int,
    diversity_key: Optional[str] = "concept_name",
) -> List[EvalReport]:
    """Return the top-k reports by total_score.

    Diversity guard: if two candidates share the same `diversity_key` (e.g. duplicate concept),
    only the higher-scoring one is kept, so Top-K never collapses to duplicates.
    """
    ranked = rank_reports(list(items))
    seen: Set[Any] = set()
    out: List[EvalReport] = []
    for r in ranked:
        key = getattr(r, diversity_key, None) if diversity_key else None
        if key is not None and key in seen:
            continue
        if key is not None:
            seen.add(key)
        out.append(r)
        if len(out) >= k:
            break
    return out
