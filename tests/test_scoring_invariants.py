"""Counter-example tests enforcing the CIE v3 scoring INVARIANTS (audit-fix Request C, §七).

These tests exist to PROVE the invariants the audit required — they must fail loudly if any
invariant regresses:

  * `EvalScore.score` is a STRICT integer 1-5 (no 4.5, 0, 6, NaN, Infinity, bool, garbage string).
  * The LLM-as-judge cannot smuggle a fractional / missing score past `_judge` — a diagnostic
    `CIEScoringError` is raised instead of a silent default.
  * `total_score()` refuses a missing / duplicate / unknown dimension, a Stage-A/B mismatch, or
    malformed weights (keys != canonical six, or sum != 1.0).
  * `realization_quality` is a PLAN-LEVEL estimate: `evaluate_stage_b` UNCONDITIONALLY caps it at
    SCORE_MAX_PLAN (=4). NO `ctx` value — string, bool, container, or any 'empirical_evidence' claim —
    can lift the cap; there is no forgeable evidence switch. The 5-level is reserved for a FUTURE
    independent, structured, trusted empirical pipeline that does not yet exist.
  * `InnovationTrace` is structurally compatible with the canonical
    `CIE-Culinary-Bench/schema/cie_sample.schema.json` (extra forbidden, required fields, magnitude
    0-5, strength enum, non-empty arrays, non-blank strings).

Run offline (no network, no API key):

    PYTHONPATH=src python -m pytest tests/test_scoring_invariants.py -q
"""
from __future__ import annotations

import json
import math
from typing import Literal, get_args

import pytest
from pydantic import ValidationError

from creative_recipe.cie.dimensions import WEIGHTS, STAGE_A_KEYS, STAGE_B_KEYS
from creative_recipe.cie.framework import (
    CIEScoringError,
    evaluate_stage_a,
    evaluate_stage_b,
)
from creative_recipe.cie.scorer import total_score, weighted_total
from creative_recipe.llm.fake import FakeProvider
from creative_recipe.types import (
    EvalScore,
    ExistingCulinaryContext,
    Ingredient,
    IngredientAndTechniqueKnowledge,
    IngredientKnowledgeItem,
    InnovationDelta,
    InnovationTrace,
    MechanisticJustification,
    Recipe,
    RecipeConcept,
    RiskAndConstraint,
    SCORE_MAX,
    SCORE_MAX_PLAN,
    SCORE_MIN,
    Stage,
    TechniqueKnowledgeItem,
)


# ------------------------------------------------------------------------------------------
# Valid-object builders (mirror the shapes used by the rest of the suite)
# ------------------------------------------------------------------------------------------
def _trace():
    return InnovationTrace(
        existing_culinary_context=ExistingCulinaryContext(
            precedents=["coq au vin (wine-braised chicken)"],
            relationship="Inherits the braise template but swaps wine/stock for coffee's bitter-roast base.",
        ),
        ingredient_and_technique_knowledge=IngredientAndTechniqueKnowledge(
            ingredient_knowledge=[
                IngredientKnowledgeItem(
                    ingredient="chicken",
                    property="mild protein and collagen; collagen->gelatin when slow-cooked",
                )
            ],
            technique_knowledge=[
                TechniqueKnowledgeItem(
                    technique="braising",
                    principle="low moist heat dissolves collagen; keeps meat juicy, does NOT brown much",
                )
            ],
        ),
        innovation_delta=InnovationDelta(
            before="Chicken braised in wine/stock.",
            after="Chicken braised in reduced black coffee.",
            change_type=["ingredient substitution"],
            magnitude=3,
        ),
        mechanistic_justification=MechanisticJustification(
            flavor_mechanism="Coffee roast pyrazines echo toasted wine-reduction notes.",
            texture_mechanism="Collagen-to-gelatin braise keeps meat succulent.",
            chemical_or_culinary_basis="Maillard + pyrazine bitterness is a known savory enhancer.",
            strength="medium",
        ),
        creative_hypothesis="Replace wine/stock with coffee as the braise liquid, then cap with melted cheese.",
        risk_and_constraint=RiskAndConstraint(
            risk="Coffee turns acrid if reduced too hard.",
            tradeoff="Loses the bright acidity wine gives.",
            failure_condition="Braising liquid reduces to a burnt-bitter syrup.",
        ),
    )


def _concept(name="C1"):
    return RecipeConcept(
        concept_name=name,
        ingredients=["chicken", "coffee", "cheese"],
        creative_angle="coffee braise + cheese crust",
        core_idea="braise in coffee, broil under cheese",
        trace=_trace(),
    )


def _recipe(name="C1"):
    return Recipe(
        name=name,
        ingredients=[Ingredient(name="chicken")],
        steps=[
            "Pat the chicken dry and season with salt and pepper.",
            "Sear the chicken in a hot pan over medium-high heat for 2 minutes per side.",
            "Add the coffee and braise gently for 30 minutes until the centre reaches 74 C / 165 F.",
            "Sprinkle cheese over the chicken and broil 2 minutes until bubbling.",
            "Rest 3 minutes, then serve.",
        ],
        creative_explanation="coffee replaces stock",
        concept_name=name,
    )


def _six_dim_scores(scores: dict | None = None) -> list[EvalScore]:
    """A full, valid six-dimension score set (Stage A's five + Stage B's one).

    Default yields the canonical demo profile that sums to 4.25.
    """
    s = {
        "culinary_knowledge_grounding": 4,
        "existing_culinary_precedent_analysis": 4,
        "innovation_delta_quality": 5,
        "mechanistic_plausibility": 4,
        "innovation_value": 4,
        "realization_quality": 4,
    }
    if scores:
        s.update(scores)
    stage_of = {**{k: Stage.A for k in STAGE_A_KEYS}, **{k: Stage.B for k in STAGE_B_KEYS}}
    return [EvalScore(dimension=k, stage=stage_of[k], score=v, reason=f"{k} scored") for k, v in s.items()]


# ------------------------------------------------------------------------------------------
# §二 — strict integer 1-5 on EvalScore
# ------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bad",
    [
        4.5,            # fractional
        4.0 + 0.2,      # another fractional value
        0,              # below range
        6,              # above range
        -3,             # below range (negative)
        float("nan"),   # NaN
        float("inf"),   # Infinity
        float("-inf"),  # -Infinity
        True,           # bool is a subclass of int -> must be rejected
        False,          # bool -> rejected
        "4",            # numeric string -> not an int
        "high",         # garbage string
    ],
)
def test_evalscore_rejects_non_integer_1_5(bad):
    with pytest.raises(ValidationError):
        EvalScore(dimension="innovation_delta_quality", stage=Stage.A, score=bad, reason="x")


@pytest.mark.parametrize("ok", [1, 2, 3, 4, 5])
def test_evalscore_accepts_integer_1_5(ok):
    sc = EvalScore(dimension="innovation_delta_quality", stage=Stage.A, score=ok, reason="x")
    assert isinstance(sc.score, int)
    assert SCORE_MIN <= sc.score <= SCORE_MAX


def test_evalscore_accepts_whole_float_and_coerces_to_int():
    """A whole float (4.0) is tolerated and coerced to the int 4 — but ONLY whole floats."""
    sc = EvalScore(dimension="innovation_value", stage=Stage.A, score=4.0, reason="x")
    assert sc.score == 4
    assert isinstance(sc.score, int)


# ------------------------------------------------------------------------------------------
# §二 — the judge cannot smuggle a fractional / missing score past _judge
# ------------------------------------------------------------------------------------------
class _FractionalScoreProvider(FakeProvider):
    """Returns a fractional score from BOTH the structured path and the chat-fallback path."""

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        return {"score": 4.5, "reason": "fractional"}

    def chat(self, messages, **kwargs):
        return json.dumps({"score": 4.5, "reason": "fractional"})


class _MissingScoreProvider(FakeProvider):
    """Returns no 'score' field from either path."""

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        return {"reason": "no score key"}

    def chat(self, messages, **kwargs):
        return json.dumps({"reason": "no score key"})


def test_judge_rejects_fractional_score():
    with pytest.raises(CIEScoringError):
        evaluate_stage_a(_FractionalScoreProvider(), [_concept()])


def test_judge_rejects_missing_score():
    with pytest.raises(CIEScoringError):
        evaluate_stage_a(_MissingScoreProvider(), [_concept()])


class _FixedPayloadProvider(FakeProvider):
    """Returns the SAME payload from BOTH the structured path and the chat-fallback path."""

    def __init__(self, payload: dict):
        super().__init__()
        self._payload = payload

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        return dict(self._payload)

    def chat(self, messages, **kwargs):
        return json.dumps(self._payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"score": 4},                 # reason missing entirely
        {"score": 4, "reason": None},  # reason is None
        {"score": 4, "reason": 123},   # reason is a number (no str() coercion)
        {"score": 4, "reason": ""},    # reason empty
        {"score": 4, "reason": "   "},  # reason whitespace-only
    ],
)
def test_judge_rejects_bad_reason(payload):
    """The shared payload validator must reject a missing / None / numeric / blank reason from BOTH
    the structured and chat-fallback paths; a single CIEScoringError is raised after the retry."""
    with pytest.raises(CIEScoringError):
        evaluate_stage_a(_FixedPayloadProvider(payload), [_concept()])


def test_judge_accepts_valid_non_blank_reason():
    """A present, string, non-blank reason (after stripping) is accepted."""
    provider = _FixedPayloadProvider({"score": 4, "reason": "  solid mechanistic basis  "})
    evals = evaluate_stage_a(provider, [_concept()])
    assert evals[0].scores[0].reason == "solid mechanistic basis"


# ------------------------------------------------------------------------------------------
# §三 — total_score() integrity: exactly the canonical six, once each, correct stage, valid weights
# ------------------------------------------------------------------------------------------
def test_total_score_full_valid_six_dimensions_is_4_25():
    scores = _six_dim_scores()  # [4,4,5,4,4,4] -> 4*0.75 + 5*0.25 = 4.25
    assert total_score(scores) == 4.25
    # Every score object carries a true int 1-5.
    for s in scores:
        assert isinstance(s.score, int)
        assert SCORE_MIN <= s.score <= SCORE_MAX


def test_total_score_missing_one_dimension_fails():
    scores = _six_dim_scores()
    scores = [s for s in scores if s.dimension != "realization_quality"]  # only five
    assert len(scores) == 5
    with pytest.raises(ValueError):
        total_score(scores)


def test_total_score_duplicate_dimension_fails():
    scores = _six_dim_scores()
    dup = EvalScore(dimension="realization_quality", stage=Stage.B, score=4, reason="dup")
    with pytest.raises(ValueError):
        total_score(scores + [dup])


def test_total_score_unknown_dimension_fails():
    scores = _six_dim_scores()
    scores = [
        s if s.dimension != "realization_quality"
        else EvalScore(dimension="bogus_dimension", stage=Stage.B, score=4, reason="x")
        for s in scores
    ]
    with pytest.raises(ValueError):
        total_score(scores)


def test_total_score_stage_mismatch_fails():
    """realization_quality must be scored at Stage B; scoring it at Stage A is rejected."""
    scores = _six_dim_scores()
    scores = [
        s if s.dimension != "realization_quality"
        else EvalScore(dimension="realization_quality", stage=Stage.A, score=4, reason="wrong stage")
        for s in scores
    ]
    with pytest.raises(ValueError):
        total_score(scores)


def test_total_score_malformed_weights_missing_key_fails():
    bad_weights = {k: v for k, v in WEIGHTS.items() if k != "realization_quality"}
    with pytest.raises(ValueError):
        total_score(_six_dim_scores(), weights=bad_weights)


def test_total_score_malformed_weights_wrong_sum_fails():
    # Six valid keys but the weights do not sum to 1.0.
    bad_weights = {k: 0.17 for k in WEIGHTS}
    with pytest.raises(ValueError):
        total_score(_six_dim_scores(), weights=bad_weights)


def test_total_score_uses_default_weights_when_none():
    # Default weights cover exactly the canonical six and sum to 1.0 -> 4.25.
    assert math.isclose(sum(WEIGHTS.values()), 1.0, rel_tol=1e-9)
    assert total_score(_six_dim_scores()) == 4.25


def test_weighted_total_rejects_unknown_and_duplicate():
    """The DIAGNOSTIC aggregate must not silently double-count or invent a weight."""
    scores = _six_dim_scores()
    with pytest.raises(ValueError):
        weighted_total(scores + [EvalScore(dimension="realization_quality", stage=Stage.B, score=4, reason="dup")])
    bad = [EvalScore(dimension="ghost", stage=Stage.A, score=4, reason="x")]
    with pytest.raises(ValueError):
        weighted_total(bad)


# ------------------------------------------------------------------------------------------
# §三 — weight validation bypasses closed (custom weights must pass _validate_weights)
# ------------------------------------------------------------------------------------------
def test_validate_weights_empty_dict_rejected():
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights={})


def test_validate_weights_ghost_key_rejected():
    # A ghost key must NOT legitimize a ghost dimension.
    with pytest.raises(ValueError):
        weighted_total(
            [EvalScore(dimension="ghost", stage=Stage.A, score=4, reason="x")],
            weights={"ghost": 1.0},
        )


def test_validate_weights_missing_key_rejected():
    bad = {k: v for k, v in WEIGHTS.items() if k != "realization_quality"}
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_negative_but_sum_1_rejected():
    # Six canonical keys, sum exactly 1.0, but one weight is negative -> rejected.
    bad = dict(WEIGHTS)
    bad["innovation_value"] = bad["innovation_value"] - 0.3
    bad["mechanistic_plausibility"] = bad["mechanistic_plausibility"] + 0.3
    assert math.isclose(sum(bad.values()), 1.0, rel_tol=1e-9)
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_nan_rejected():
    bad = dict(WEIGHTS)
    bad["innovation_value"] = float("nan")
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_inf_rejected():
    bad = dict(WEIGHTS)
    bad["innovation_value"] = float("inf")
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_bool_rejected():
    # A bool is a subclass of int; it must NOT count as a numeric weight.
    bad = dict(WEIGHTS)
    bad["innovation_value"] = True
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_non_numeric_string_rejected():
    bad = dict(WEIGHTS)
    bad["innovation_value"] = "0.15"  # a numeric-looking string is not a number
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights=bad)


def test_validate_weights_canonical_passes():
    # The shipped canonical weights are valid: mapping, six keys, positive finite, sum 1.0.
    _validate_weights_via_total()  # smoke: total_score accepts default weights (== WEIGHTS)
    assert total_score(_six_dim_scores()) == 4.25


def _validate_weights_via_total():
    total_score(_six_dim_scores())


def test_weighted_total_stage_a_subset_aggregation_ok():
    """A diagnostic Stage-A subset aggregate still works under canonical weights (normalized avg)."""
    # Override innovation_delta_quality to 4 so all five Stage-A scores are 4 -> avg is 4.0.
    stage_a_scores = [
        s for s in _six_dim_scores({"innovation_delta_quality": 4}) if s.stage is Stage.A
    ]
    assert len(stage_a_scores) == 5
    agg = weighted_total(stage_a_scores, weights=WEIGHTS)
    assert agg == 4.0


def test_weighted_total_empty_weights_no_silent_fallback():
    """An explicitly empty weight dict must raise, never silently fall back to WEIGHTS."""
    with pytest.raises(ValueError):
        weighted_total(_six_dim_scores(), weights={})


def test_weighted_total_ghost_dimension_with_ghost_weight_rejected():
    """`{"ghost": 1.0}` must not make a ghost dimension valid — _validate_weights rejects the key."""
    with pytest.raises(ValueError):
        weighted_total(
            [EvalScore(dimension="ghost", stage=Stage.A, score=4, reason="x")],
            weights={"ghost": 1.0},
        )


# ------------------------------------------------------------------------------------------
# §四 — realization_quality plan-level evidence cap
# ------------------------------------------------------------------------------------------
class _FiveRealizationProvider(FakeProvider):
    """Always returns 5 for the realization_quality dimension."""

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        sys = messages[0]["content"]
        if "Creative Innovation Evaluation" in sys:
            return {"score": 5, "reason": "judge says 5"}
        return {"score": 4, "reason": "default"}

    def chat(self, messages, **kwargs):
        return json.dumps({"score": 5, "reason": "judge says 5"})


def test_realization_quality_capped_at_4_without_evidence():
    """Default flow supplies no empirical evidence -> a 5 is capped to SCORE_MAX_PLAN (4)."""
    revals = evaluate_stage_b(_FiveRealizationProvider(), [_recipe()])  # no ctx
    sc = revals[0].scores[0]
    assert sc.dimension == "realization_quality"
    assert sc.score == SCORE_MAX_PLAN
    assert sc.score < SCORE_MAX
    assert "plan-level cap" in sc.reason


@pytest.mark.parametrize(
    "ctx",
    [
        {"empirical_evidence": None},        # explicit None
        {"empirical_evidence": ""},          # empty string
        {"empirical_evidence": "yes"},       # truthy string
        {"empirical_evidence": True},        # bool (forgeable)
        {"empirical_evidence": ["cooked"]},  # container
        {"claim": "tested"},                 # dict WITHOUT an empirical_evidence key
        {"empirical_evidence": "blind tasting"},  # plausible-looking string claim
    ],
)
def test_realization_quality_cap_not_lifted_by_any_ctx(ctx):
    """No `ctx` value — string, bool, container, or any 'empirical_evidence' claim — can lift the
    UNCONDITIONAL plan-level cap. The current application has no trusted empirical channel, so it
    never produces a 5 regardless of what a caller puts in `ctx`."""
    revals = evaluate_stage_b(_FiveRealizationProvider(), [_recipe()], ctx=ctx)
    sc = revals[0].scores[0]
    assert sc.dimension == "realization_quality"
    assert sc.score == SCORE_MAX_PLAN
    assert sc.score < SCORE_MAX
    assert "cap" in sc.reason


# ------------------------------------------------------------------------------------------
# §五 — InnovationTrace runtime constraints aligned to the canonical sample schema
# ------------------------------------------------------------------------------------------
def test_illegal_strength_rejected():
    with pytest.raises(ValidationError):
        MechanisticJustification(
            flavor_mechanism="x",
            texture_mechanism="y",
            chemical_or_culinary_basis="z",
            strength="bogus",  # not in {weak, medium, strong}
        )


def test_empty_required_trace_arrays_rejected():
    with pytest.raises(ValidationError):
        ExistingCulinaryContext(precedents=[], relationship="x")  # min_length=1
    with pytest.raises(ValidationError):
        IngredientAndTechniqueKnowledge(
            ingredient_knowledge=[],
            technique_knowledge=[TechniqueKnowledgeItem(technique="t", principle="p")],
        )


def test_blank_required_strings_rejected():
    with pytest.raises(ValidationError):
        ExistingCulinaryContext(precedents=["x"], relationship="   ")  # whitespace-only -> blank
    with pytest.raises(ValidationError):
        InnovationDelta(
            before="",
            after="y",
            change_type=["ingredient substitution"],
            magnitude=2,
        )


def test_blank_change_type_items_rejected():
    with pytest.raises(ValidationError):
        InnovationDelta(
            before="a",
            after="b",
            change_type=["ingredient substitution", ""],  # blank item
            magnitude=2,
        )


def test_precedents_whitespace_only_item_rejected():
    """A whitespace-only precedent item is NOT a valid non-blank string."""
    with pytest.raises(ValidationError):
        ExistingCulinaryContext(precedents=["   "], relationship="x")


def test_change_type_whitespace_only_item_rejected():
    with pytest.raises(ValidationError):
        InnovationDelta(before="a", after="b", change_type=["   "], magnitude=2)


def test_precedents_non_string_item_rejected():
    """A non-string item must NOT be coerced via str() — it must be rejected."""
    with pytest.raises(ValidationError):
        ExistingCulinaryContext(precedents=[123], relationship="x")
    with pytest.raises(ValidationError):
        ExistingCulinaryContext(precedents=[None], relationship="x")


def test_change_type_non_string_item_rejected():
    with pytest.raises(ValidationError):
        InnovationDelta(before="a", after="b", change_type=[7], magnitude=2)
    with pytest.raises(ValidationError):
        InnovationDelta(before="a", after="b", change_type=[{"k": "v"}], magnitude=2)


def test_precedents_items_stripped_on_save():
    """A valid but padded string is preserved (stripped) as a non-blank item."""
    ecc = ExistingCulinaryContext(precedents=["  coq au vin  "], relationship="x")
    assert ecc.precedents == ["coq au vin"]


def test_extra_fields_rejected_on_trace():
    with pytest.raises(ValidationError):
        InnovationTrace(
            **_trace().model_dump(),
            extra_field_not_in_contract="should be forbidden",
        )


def test_magnitude_out_of_0_5_rejected():
    with pytest.raises(ValidationError):
        InnovationDelta(before="a", after="b", change_type=["x"], magnitude=7)
    with pytest.raises(ValidationError):
        InnovationDelta(before="a", after="b", change_type=["x"], magnitude=-1)


def _required_fields(model_cls) -> set:
    return {n for n, f in model_cls.model_fields.items() if f.is_required()}


def test_innovation_trace_matches_canonical_sample():
    """Prove the InnovationTrace model is structurally compatible with the frozen benchmark schema
    across ALL six stages — not just the top-level required fields.

    For each stage we mirror the canonical schema's nested objects: nested field names, the required
    set, the magnitude range (0-5 for innovation_delta), and the strength enum (weak/medium/strong for
    mechanistic_justification). If any nested field, required set, magnitude range, or strength enum
    drifts, this fails. This is what justifies the docstring's 'mirrors' (not 'field-for-field
    matches') claim, and it does NOT add a heavyweight jsonschema dependency to do so.
    """
    import os

    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "CIE-Culinary-Bench", "schema", "cie_sample.schema.json"
    )
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)

    trace_schema = schema["properties"]["innovation_trace"]
    assert schema.get("additionalProperties") is False  # whole sample forbids extra top-level keys
    assert InnovationTrace.model_config.get("extra") == "forbid"

    # Required fields of the canonical innovation_trace == required fields of the model.
    schema_required = set(trace_schema["required"])
    model_required = _required_fields(InnovationTrace)
    assert model_required == schema_required, f"field mismatch: {model_required ^ schema_required}"

    # Map each canonical stage property to the model class that implements it, and check the
    # NESTED field names + required sets (not just the top-level required list).
    STAGE_MODELS = {
        "existing_culinary_context": ExistingCulinaryContext,
        "ingredient_and_technique_knowledge": IngredientAndTechniqueKnowledge,
        "innovation_delta": InnovationDelta,
        "mechanistic_justification": MechanisticJustification,
        "risk_and_constraint": RiskAndConstraint,
    }
    for stage_prop, model_cls in STAGE_MODELS.items():
        sub = trace_schema["properties"][stage_prop]
        sub_required = set(sub.get("required", []))
        model_fields = set(model_cls.model_fields.keys())
        # The canonical schema enumerates `properties` only for `innovation_delta`; the other stages
        # declare just a `required` set. Where properties are enumerated we check field names exactly;
        # otherwise the model's fields must equal the schema's required set (no extra / missing field).
        if "properties" in sub:
            assert model_fields == set(sub["properties"].keys()), (
                f"{stage_prop}: nested field-name mismatch "
                f"{model_fields ^ set(sub['properties'].keys())}"
            )
        else:
            assert model_fields == sub_required, (
                f"{stage_prop}: model fields must equal schema required set "
                f"{model_fields ^ sub_required}"
            )
        assert _required_fields(model_cls) == sub_required, (
            f"{stage_prop}: nested required-set mismatch "
            f"{_required_fields(model_cls) ^ sub_required}"
        )
        assert model_cls.model_config.get("extra") == "forbid"

    # creative_hypothesis is a plain string in both the schema and the model.
    assert trace_schema["properties"]["creative_hypothesis"].get("type") == "string"
    assert InnovationTrace.model_fields["creative_hypothesis"].annotation is str

    # magnitude is integer 0-5 (matches schema minimum/maximum).
    mag_schema = trace_schema["properties"]["innovation_delta"]["properties"]["magnitude"]
    assert mag_schema.get("type") == "integer"
    assert mag_schema.get("minimum") == 0 and mag_schema.get("maximum") == 5
    mag = InnovationDelta.model_fields["magnitude"]
    assert any(getattr(m, "ge", None) == 0 for m in mag.metadata)
    assert any(getattr(m, "le", None) == 5 for m in mag.metadata)

    # strength is a closed enum {weak, medium, strong} on the MODEL. The canonical schema declares
    # `strength` only as a required string (it does not enumerate the enum), so this project-level
    # invariant is asserted on the model to guarantee the canonical vocabulary is enforced.
    strength_ann = MechanisticJustification.model_fields["strength"].annotation
    assert get_args(strength_ann) == ("weak", "medium", "strong")

    # Non-empty array constraints on the key trace arrays.
    ecc = ExistingCulinaryContext.model_fields["precedents"]
    ik = IngredientAndTechniqueKnowledge.model_fields["ingredient_knowledge"]
    tk = IngredientAndTechniqueKnowledge.model_fields["technique_knowledge"]
    ct = InnovationDelta.model_fields["change_type"]
    assert any(getattr(m, "min_length", None) and getattr(m, "min_length", 0) >= 1 for m in ecc.metadata)
    assert any(getattr(m, "min_length", None) and getattr(m, "min_length", 0) >= 1 for m in ik.metadata)
    assert any(getattr(m, "min_length", None) and getattr(m, "min_length", 0) >= 1 for m in tk.metadata)
    assert any(getattr(m, "min_length", None) and getattr(m, "min_length", 0) >= 1 for m in ct.metadata)

    # A fully valid trace round-trips through the canonical shape.
    dumped = _trace().model_dump()
    InnovationTrace.model_validate(dumped)  # must not raise


# ------------------------------------------------------------------------------------------
# Main pipeline offline end-to-end must still pass (regression anchor for the whole contract)
# ------------------------------------------------------------------------------------------
def test_offline_pipeline_e2e_still_passes():
    """The full offline pipeline still produces a valid six-dimension report totalling 4.25."""
    import re

    from creative_recipe.pipeline import run

    class _E2E(FakeProvider):
        SCORES = {
            "culinary_knowledge_grounding": 4,
            "existing_culinary_precedent_analysis": 4,
            "innovation_delta_quality": 5,
            "mechanistic_plausibility": 4,
            "innovation_value": 4,
            "realization_quality": 4,
        }

        def structured(self, messages, schema=None, **kwargs):
            self.structured_calls += 1
            sys = messages[0]["content"]
            if "Creative Ideation engine" in sys:
                return {"concepts": [_concept().model_dump()]}
            if "Recipe Realization engine" in sys:
                return _recipe().model_dump()
            if "Creative Innovation Evaluation" in sys:
                m = re.search(r"key=(\w+)", messages[1]["content"])
                key = m.group(1) if m else "innovation_delta_quality"
                return {"score": self.SCORES.get(key, 4), "reason": f"{key} judged"}
            return {"score": 4, "reason": "default"}

    ingredients = [Ingredient(name="chicken"), Ingredient(name="coffee"), Ingredient(name="cheese")]
    result = run(_E2E(), ingredients, num_concepts=1, top_k_concepts=1, top_k_final=1)
    assert result.best_report is not None
    report = result.best_report
    all_dims = {s.dimension for s in report.stage_a} | {s.dimension for s in report.stage_b}
    assert all_dims == set(WEIGHTS)
    # Direct six-dimension weighted sum, no stage blend; equals 4.25 with the scripted scores.
    assert report.total_score == 4.25
