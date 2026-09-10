"""Tests for the CIE framework + scorer (P4), aligned to the canonical CIE v3 contract.

Run offline with a scripted fake provider — no network, no API key:

    PYTHONPATH=src python -m pytest tests/test_cie.py -q
"""
from creative_recipe.cie.dimensions import (
    REGISTRY,
    WEIGHTS,
    STAGE_A_SPECS,
    STAGE_B_SPECS,
)
from creative_recipe.cie.framework import (
    evaluate_stage_a,
    evaluate_stage_b,
    build_report,
)
from creative_recipe.cie.scorer import (
    weighted_total,
    total_score,
    rank_reports,
    select_top_k,
)
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
    Stage,
    TechniqueKnowledgeItem,
)


def _trace():
    return InnovationTrace(
        existing_culinary_context=ExistingCulinaryContext(
            precedents=["coq au vin (wine-braised chicken)"],
            relationship="Inherits the braise template but swaps wine/stock for coffee's bitter-roast base.",
        ),
        ingredient_and_technique_knowledge=IngredientAndTechniqueKnowledge(
            ingredient_knowledge=[IngredientKnowledgeItem(ingredient="chicken", property="mild protein and collagen; collagen->gelatin when slow-cooked")],
            technique_knowledge=[TechniqueKnowledgeItem(technique="braising", principle="low moist heat dissolves collagen; keeps meat juicy, does NOT brown much")],
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
        steps=["sear", "braise", "broil"],
        creative_explanation="coffee replaces stock",
        concept_name=name,
    )


def test_dimension_registry_complete():
    assert set(REGISTRY) == set(WEIGHTS)
    assert sum(WEIGHTS.values()) == 1.0
    # Stage A = five concept-level dimensions; Stage B = one recipe-level dimension.
    assert len(STAGE_A_SPECS) == 5
    assert len(STAGE_B_SPECS) == 1
    # Weights per the canonical CIE v3 design.
    assert WEIGHTS == {
        "culinary_knowledge_grounding": 0.15,
        "existing_culinary_precedent_analysis": 0.15,
        "innovation_delta_quality": 0.25,
        "mechanistic_plausibility": 0.20,
        "innovation_value": 0.15,
        "realization_quality": 0.10,
    }


def test_weighted_total_matches_expected():
    scores = [
        EvalScore(dimension="culinary_knowledge_grounding", stage=Stage.A, score=4.0, reason=""),
        EvalScore(dimension="existing_culinary_precedent_analysis", stage=Stage.A, score=4.0, reason=""),
        EvalScore(dimension="innovation_delta_quality", stage=Stage.A, score=5.0, reason=""),
        EvalScore(dimension="mechanistic_plausibility", stage=Stage.A, score=4.0, reason=""),
        EvalScore(dimension="innovation_value", stage=Stage.A, score=4.0, reason=""),
        EvalScore(dimension="realization_quality", stage=Stage.B, score=4.0, reason=""),
    ]
    # Diagnostic normalized average over all six (weights sum to 1.0) -> 4.25.
    expected = round(sum(WEIGHTS[s.dimension] * s.score for s in scores), 4)
    assert weighted_total(scores) == expected
    assert weighted_total(scores) == 4.25


def test_rank_and_select_top_k():
    reports = [
        type("R", (), {"concept_name": "A", "total_score": 5.0, "rank": 0})(),
        type("R", (), {"concept_name": "B", "total_score": 9.0, "rank": 0})(),
        type("R", (), {"concept_name": "C", "total_score": 7.0, "rank": 0})(),
    ]
    ranked = rank_reports(reports)
    assert [r.concept_name for r in ranked] == ["B", "C", "A"]
    assert [r.rank for r in ranked] == [1, 2, 3]
    top = select_top_k(ranked, k=2)
    assert [r.concept_name for r in top] == ["B", "C"]


class CieFakeProvider(FakeProvider):
    """Returns concepts / recipe / eval JSON depending on the system prompt (canonical 1-5 scores)."""

    SCORES = {
        "culinary_knowledge_grounding": 4.0,
        "existing_culinary_precedent_analysis": 4.0,
        "innovation_delta_quality": 5.0,
        "mechanistic_plausibility": 4.0,
        "innovation_value": 4.0,
        "realization_quality": 4.0,
    }

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        sys = messages[0]["content"]
        if "Creative Ideation engine" in sys:
            return {"concepts": [_concept().model_dump()]}
        if "Recipe Realization engine" in sys:
            return _recipe().model_dump()
        if "Creative Innovation Evaluation" in sys:
            import re

            m = re.search(r"key=(\w+)", messages[1]["content"])
            key = m.group(1) if m else "innovation_delta_quality"
            return {"score": self.SCORES.get(key, 4.0), "reason": f"{key} judged"}
        return {"score": 4.0, "reason": "default"}


def test_evaluate_stage_a_returns_five_scores():
    fake = CieFakeProvider()
    evals = evaluate_stage_a(fake, [_concept()])
    assert len(evals) == 1
    assert len(evals[0].scores) == 5
    dims = {s.dimension for s in evals[0].scores}
    assert dims == {s.key for s in STAGE_A_SPECS}


def test_evaluate_stage_b_returns_one_score():
    fake = CieFakeProvider()
    evals = evaluate_stage_b(fake, [_recipe()])
    assert len(evals[0].scores) == 1
    dims = {s.dimension for s in evals[0].scores}
    assert dims == {s.key for s in STAGE_B_SPECS}
    assert dims == {"realization_quality"}


def test_build_report_combines_six_dimensions():
    fake = CieFakeProvider()
    ce = evaluate_stage_a(fake, [_concept()])[0]
    re = evaluate_stage_b(fake, [_recipe()])[0]
    report = build_report(_concept(), ce, _recipe(), re)
    assert len(report.stage_a) == 5
    assert len(report.stage_b) == 1
    # Canonical CIE v3 direct six-dimension weighted sum (no 0.75/0.25 blend): 4.25.
    assert report.total_score == 4.25
    all_scores = list(report.stage_a) + list(report.stage_b)
    assert total_score(all_scores) == report.total_score


def test_final_total_is_direct_six_dimension_weighted_sum():
    """The final total must equal sum(weight_d * score_d); it must NOT be a 0.75/0.25 blend."""
    ce = evaluate_stage_a(CieFakeProvider(), [_concept()])[0]
    re = evaluate_stage_b(CieFakeProvider(), [_recipe()])[0]
    report = build_report(_concept(), ce, _recipe(), re)

    # Direct six-dimension weighted sum.
    direct = round(
        sum(WEIGHTS[s.dimension] * s.score for s in list(ce.scores) + list(re.scores)),
        4,
    )
    assert report.total_score == direct

    # Sanity: the historical 0.75/0.25 Stage-A/Stage-B blend would NOT reproduce this total
    # (Stage-A diagnostic aggregate != the final total), so the new contract is genuinely in force.
    assert report.total_score != round(0.75 * report.stage_a_score + 0.25 * report.stage_b_score, 4)


def test_stage_b_receives_innovation_trace():
    """Stage-B evaluation must be fed the Recipe's InnovationTrace as context."""

    class TraceCapturingFake(FakeProvider):
        captured_user: list = []

        def structured(self, messages, schema=None, **kwargs):
            self.structured_calls += 1
            sys = messages[0]["content"]
            if "Recipe Realization engine" in sys:
                return _recipe().model_dump()
            if "Creative Innovation Evaluation" in sys:
                TraceCapturingFake.captured_user.append(messages[1]["content"])
                return {"score": 4.0, "reason": "captured"}
            return {"score": 4.0, "reason": "x"}

    fake = TraceCapturingFake()
    concept = _concept()
    recipe = _recipe()
    evaluate_stage_b(fake, [recipe], traces=[concept.trace])
    # every Stage-B judge message must contain the InnovationTrace (and the creative hypothesis).
    assert TraceCapturingFake.captured_user, "no Stage-B messages were produced"
    for msg in TraceCapturingFake.captured_user:
        assert "InnovationTrace" in msg
        assert concept.trace.creative_hypothesis in msg
