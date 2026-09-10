"""Tests for output formatting / export (P5), aligned to the canonical CIE v3 contract.

    PYTHONPATH=src python -m pytest tests/test_output.py -q
"""
import json
import os
import tempfile

from creative_recipe.output.formatter import format_result, format_console
from creative_recipe.output.exporter import export, to_json
from creative_recipe.types import (
    EvalReport,
    EvalScore,
    ExistingCulinaryContext,
    Ingredient,
    IngredientAndTechniqueKnowledge,
    IngredientKnowledgeItem,
    InnovationDelta,
    InnovationTrace,
    MechanisticJustification,
    PipelineResult,
    Recipe,
    RecipeConcept,
    RiskAndConstraint,
    Stage,
    TechniqueKnowledgeItem,
)


def _trace():
    return InnovationTrace(
        existing_culinary_context=ExistingCulinaryContext(
            precedents=["coq au vin"], relationship="inherits braise template, swaps coffee for wine"
        ),
        ingredient_and_technique_knowledge=IngredientAndTechniqueKnowledge(
            ingredient_knowledge=[IngredientKnowledgeItem(ingredient="chicken", property="mild protein")],
            technique_knowledge=[TechniqueKnowledgeItem(technique="braising", principle="low heat dissolves collagen")],
        ),
        innovation_delta=InnovationDelta(
            before="wine braise", after="coffee braise", change_type=["ingredient substitution"], magnitude=3
        ),
        mechanistic_justification=MechanisticJustification(
            flavor_mechanism="coffee roast pyrazines", texture_mechanism="collagen to gelatin",
            chemical_or_culinary_basis="Maillard", strength="medium",
        ),
        creative_hypothesis="swap stock for coffee, cap with cheese",
        risk_and_constraint=RiskAndConstraint(risk="coffee burns", tradeoff="loses acidity", failure_condition="syrup turns bitter"),
    )


def _result():
    concept = RecipeConcept(
        concept_name="Coffee-Braised Chicken",
        ingredients=["chicken", "coffee", "cheese"],
        creative_angle="coffee braise + cheese crust",
        core_idea="braise in coffee, broil under cheese",
        trace=_trace(),
    )
    recipe = Recipe(
        name="Coffee-Braised Chicken with Melted Cheese Crust",
        ingredients=[Ingredient(name="chicken", quantity="400g"), Ingredient(name="cheese", quantity="100g")],
        steps=["sear", "braise 30 min", "broil under cheese"],
        creative_explanation="coffee replaces stock; cheese cuts bitterness",
        concept_name="Coffee-Braised Chicken",
    )
    report = EvalReport(
        concept_name="Coffee-Braised Chicken",
        trace=concept.trace,
        stage_a=[
            EvalScore(dimension="culinary_knowledge_grounding", stage=Stage.A, score=4.0, reason="ok"),
            EvalScore(dimension="existing_culinary_precedent_analysis", stage=Stage.A, score=4.0, reason="ok"),
            EvalScore(dimension="innovation_delta_quality", stage=Stage.A, score=5.0, reason="ok"),
            EvalScore(dimension="mechanistic_plausibility", stage=Stage.A, score=4.0, reason="ok"),
            EvalScore(dimension="innovation_value", stage=Stage.A, score=4.0, reason="ok"),
        ],
        stage_b=[EvalScore(dimension="realization_quality", stage=Stage.B, score=4.0, reason="ok")],
        total_score=4.25,
        rank=1,
    )
    return PipelineResult(
        inputs=[Ingredient(name="chicken"), Ingredient(name="coffee"), Ingredient(name="cheese")],
        concepts=[concept],
        recipes=[recipe],
        reports=[report],
        best_recipe=recipe,
        best_report=report,
    )


def test_format_result_contains_best_recipe():
    md = format_result(_result())
    assert "Coffee-Braised Chicken with Melted Cheese Crust" in md
    assert "Final CIE score" in md
    assert "Stage-A aggregate" in md
    assert "Stage-B aggregate" in md
    # Six-stage trace is rendered (stage labels, not the old flat field names).
    assert "InnovationTrace (six-stage)" in md
    assert "Stage 5 Creative Hypothesis" in md
    # The two removed top-level trace fields must not appear; `ingredient_knowledge` is allowed
    # only as a sub-field of `ingredient_and_technique_knowledge` (canonical schema).
    assert "concept_bridge" not in md
    assert "preliminary_feasibility_reasoning" not in md


def test_format_console_compact():
    txt = format_console(_result())
    assert "== Coffee-Braised Chicken" in txt
    assert "Steps:" in txt


def test_export_writes_json():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.json")
        export(_result(), path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["best_recipe"]["name"].startswith("Coffee-Braised")
        assert data["best_report"]["total_score"] == 4.25


def test_to_json_string():
    s = to_json(_result())
    assert "best_recipe" in s
