"""Creative Innovation Evaluation (CIE) framework — the core evaluation engine.

Two-stage, six-dimension, cognitive-process-mapping evaluation (CIE v3):

  Stage A (on RecipeConcept): culinary_knowledge_grounding, existing_culinary_precedent_analysis,
                              innovation_delta_quality, mechanistic_plausibility, innovation_value
  Stage B (on realized Recipe): realization_quality

The InnovationTrace is PRODUCED earlier in Creative Ideation; here it is consumed as review
evidence for Stage A. Each dimension is scored by an LLM-as-judge (Hy3) with a rubric; scoring
falls back to chat + JSON extraction if structured output fails.

The final total is the CANONICAL CIE v3 direct six-dimension weighted sum (see cie.scorer.total_score).
There is NO stage-level blend (the historical 0.75 / 0.25 blend has been removed).

SCORING INVARIANTS (enforced here)
-----------------------------------
* Every score is a strict integer in [SCORE_MIN, SCORE_MAX] = [1, 5]. Fractional values (4.5),
  out-of-range integers, NaN, Infinity, booleans and garbage strings are REJECTED — never silently
  defaulted, rounded or truncated.
* A missing `score` is rejected (the historical silent default of 3 is gone).
* The judge is given ONE correction retry (structured -> chat-fallback). If the score is still
  invalid afterwards, a diagnostic CIEScoringError is raised.
* `realization_quality` is a PLAN-LEVEL estimate and is UNCONDITIONALLY capped at SCORE_MAX_PLAN (4)
  by `evaluate_stage_b`. The current application has no trusted empirical-evidence channel, so it
  never produces a 5; the 5-level is reserved for a FUTURE independent, structured empirical pipeline.
* `reason` must be present, a string, and non-blank after stripping. A missing / `None` / numeric /
  blank reason is rejected by a single shared payload validator (structured and chat-fallback paths);
  if BOTH attempts are invalid, a diagnostic CIEScoringError is raised.
"""
from __future__ import annotations

import math
from typing import Any, List, Optional

from ..llm.base import LLMProvider
from ..recipe.ideation import _extract_json
from ..types import (
    ConceptEval,
    EvalReport,
    EvalScore,
    Recipe,
    RecipeConcept,
    RecipeEval,
    SCORE_MAX,
    SCORE_MAX_PLAN,
    SCORE_MIN,
    Stage,
)
from .dimensions import STAGE_A_SPECS, STAGE_B_SPECS, WEIGHTS
from .scorer import total_score, weighted_total


class CIEScoringError(Exception):
    """Raised when a dimension cannot be scored as a valid CIE v3 1-5 integer after retries."""


EVAL_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "eval",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "score": {"type": "integer", "minimum": SCORE_MIN, "maximum": SCORE_MAX},
                "reason": {"type": "string", "minLength": 1},
            },
            "required": ["score", "reason"],
        },
    },
}


def _extract_score(data: dict) -> float:
    """Pull `score` out of a judge payload, rejecting missing / non-numeric / non-finite values.

    Returns a finite number; the integer 1-5 contract itself is enforced by `EvalScore`.
    """
    if not isinstance(data, dict) or "score" not in data or data["score"] is None:
        raise CIEScoringError("judge response is missing the required 'score' field")
    raw = data["score"]
    if isinstance(raw, bool):
        raise CIEScoringError("judge 'score' must be an integer 1-5, not a bool")
    try:
        score = float(raw)
    except (TypeError, ValueError):
        raise CIEScoringError(f"judge 'score' is not numeric: {raw!r}")
    if math.isnan(score) or math.isinf(score):
        raise CIEScoringError(f"judge 'score' is not finite: {raw!r}")
    return score


def _validate_eval_payload(data: object) -> tuple[float, str]:
    """Validate a judge payload's `score` and `reason` with ONE shared rule for BOTH the structured
    and the chat-fallback paths.

    Rejects (raising CIEScoringError):
      * a non-dict payload,
      * a missing / non-numeric / non-finite `score` (handled by `_extract_score`),
      * a missing `reason`,
      * a non-string `reason` (no `str()` coercion of bogus values),
      * a blank `reason` (empty or whitespace-only after strip).

    Returns (score, reason) with `reason` already stripped.
    """
    if not isinstance(data, dict):
        raise CIEScoringError("judge payload is not an object")
    score = _extract_score(data)
    reason = data.get("reason")
    if reason is None:
        raise CIEScoringError("judge 'reason' is required")
    if not isinstance(reason, str):
        raise CIEScoringError(
            f"judge 'reason' must be a string, got {type(reason).__name__}: {reason!r}"
        )
    reason = reason.strip()
    if reason == "":
        raise CIEScoringError("judge 'reason' must not be blank")
    return score, reason


def _judge(provider: LLMProvider, spec, target, ctx: Optional[dict] = None) -> EvalScore:
    """Score one dimension via LLM-as-judge with strict 1-5 integer enforcement.

    Strategy: try structured output; on any failure (missing score, non-integer, non-finite,
    schema rejection, parse error) fall back once to a plain chat call whose JSON we extract.
    If the score is still invalid after that single retry, raise a diagnostic CIEScoringError —
    we never silently substitute a default or truncate a fractional value.
    """
    messages = spec.build_messages(target, ctx)
    last_err: Optional[Exception] = None
    # attempt 0: structured output; attempt 1: one chat-fallback correction retry.
    # BOTH paths are validated by the SAME _validate_eval_payload (score + reason).
    for _attempt in range(2):
        try:
            if _attempt == 0:
                data = provider.structured(messages, schema=EVAL_SCHEMA)
            else:
                data = _extract_json(provider.chat(messages))
            score, reason = _validate_eval_payload(data)
            # EvalScore enforces the integer 1-5 contract (rejects 4.5, 0, 6, bool, NaN, inf).
            return EvalScore(dimension=spec.key, stage=spec.stage, score=score, reason=reason)
        except Exception as e:  # noqa: BLE001 - surface a single diagnostic error after the retry
            last_err = e
    raise CIEScoringError(
        f"dimension {spec.key}: could not obtain a valid integer 1-5 score with a non-blank reason after retry: {last_err}"
    )


def evaluate_stage_a(
    provider: LLMProvider, concepts: List[RecipeConcept], ctx: Optional[dict] = None
) -> List[ConceptEval]:
    """Run the five Stage-A dimensions over each concept; returns one ConceptEval per concept."""
    out: List[ConceptEval] = []
    for c in concepts:
        scores = [_judge(provider, spec, c, ctx) for spec in STAGE_A_SPECS]
        out.append(ConceptEval(concept_name=c.concept_name, scores=scores, trace=c.trace))
    return out


def evaluate_stage_b(
    provider: LLMProvider,
    recipes: List[Recipe],
    traces: Optional[List[Any]] = None,
    ctx: Optional[dict] = None,
) -> List[RecipeEval]:
    """Run the single Stage-B dimension (realization_quality) over each realized recipe.

    Stage-B consumes BOTH the Recipe AND its InnovationTrace: the trace (especially the
    `creative_hypothesis` and the `risk_and_constraint` failure condition) is fed in as evaluation
    context so the judge can check faithfulness and plan-level feasibility against the idea that was
    actually proposed. `traces[i]` must correspond to `recipes[i]`; pass None for any recipe that has
    no trace.

    PLAN-LEVEL CAP (UNCONDITIONAL): `realization_quality` is a PLAN-LEVEL estimate of the generated
    recipe and is ALWAYS capped at SCORE_MAX_PLAN (4). The current application has no trusted
    empirical-evidence channel, so it never awards the 5-level — the 5-level is reserved for a
    FUTURE independent, structured empirical evaluation pipeline. No `ctx` value (string, bool,
    container, or an "empirical_evidence" claim) can lift this cap.
    """
    out: List[RecipeEval] = []
    for idx, r in enumerate(recipes):
        trace = traces[idx] if traces else None
        rctx = {**(ctx or {}), "trace": trace} if trace is not None else (ctx or {})
        scores = [_judge(provider, spec, r, rctx) for spec in STAGE_B_SPECS]
        # Plan-level cap (UNCONDITIONAL): realization_quality is a plan-level estimate; the current
        # app has no trusted empirical channel, so it is always capped at SCORE_MAX_PLAN (4). No ctx
        # value can lift this cap. Level 5 is reserved for a future independent empirical pipeline.
        scores = [
            EvalScore(
                dimension=s.dimension,
                stage=s.stage,
                score=min(s.score, SCORE_MAX_PLAN),
                reason=s.reason + " [plan-level cap: realization_quality capped at 4; "
                "level 5 reserved for a future independent empirical pipeline]",
            )
            if s.dimension == "realization_quality" and s.score > SCORE_MAX_PLAN
            else s
            for s in scores
        ]
        out.append(RecipeEval(recipe_name=r.name, concept_name=r.concept_name, scores=scores))
    return out


def build_report(
    concept: RecipeConcept,
    concept_eval: ConceptEval,
    recipe: Recipe,
    recipe_eval: RecipeEval,
) -> EvalReport:
    """Combine Stage-A + Stage-B scores into a single six-dimension EvalReport.

    Stage-A aggregate = normalized weighted avg of the five Stage-A dimensions (DIAGNOSTIC only).
    Stage-B aggregate = normalized weighted avg of the single Stage-B dimension (DIAGNOSTIC only).
    Final total        = CANONICAL direct six-dimension weighted sum (sum(WEIGHTS[d] * score[d])),
                          equivalent to summing Stage A and Stage B contributions directly — there is
                          no 0.75 / 0.25 stage blend.
    """
    stage_a = weighted_total(concept_eval.scores, weights=WEIGHTS)
    stage_b = weighted_total(recipe_eval.scores, weights=WEIGHTS)
    all_scores = list(concept_eval.scores) + list(recipe_eval.scores)
    total = total_score(all_scores, weights=WEIGHTS)
    return EvalReport(
        concept_name=concept.concept_name,
        trace=concept.trace,
        stage_a=concept_eval.scores,
        stage_b=recipe_eval.scores,
        stage_a_score=stage_a,
        stage_b_score=stage_b,
        total_score=total,
        rank=0,
    )
