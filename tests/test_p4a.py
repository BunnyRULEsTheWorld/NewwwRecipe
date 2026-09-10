"""P4-A integration test (DemoProvider): chicken + coffee + cheese.

Exercises the full Recipe Realization -> Stage-B CIE -> Final Ranking path offline and asserts the
contract: realization emits seasonings + preserves the creative hypothesis, Stage-B evaluates only
realization_quality with the InnovationTrace in context, and the Final CIE report is the canonical
direct six-dimension weighted sum (no 0.75/0.25 blend).

    PYTHONPATH=src python -m pytest tests/test_p4a.py -q
"""
from creative_recipe.llm.fake import DemoProvider
from creative_recipe.recipe.ideation import generate_concepts
from creative_recipe.recipe.realization import realize_concept
from creative_recipe.cie.framework import evaluate_stage_a, evaluate_stage_b, build_report
from creative_recipe.types import Ingredient


def test_chicken_coffee_cheese_realization_stage_b_final():
    provider = DemoProvider()
    ingredients = [
        Ingredient(name="chicken"),
        Ingredient(name="coffee"),
        Ingredient(name="cheese"),
    ]

    concepts = generate_concepts(provider, ingredients, num_concepts=3)
    assert concepts, "ideation should produce concepts"
    concept = concepts[0]

    # --- Recipe Realization (P4-A.1) ---
    recipe = realize_concept(provider, concept)
    assert recipe.name
    assert recipe.ingredients, "realization must emit hero ingredients"
    assert recipe.seasonings, "realization must emit 调料 (seasonings) separately"
    assert recipe.steps
    # original creative hypothesis carried forward, not re-invented
    assert recipe.creative_hypothesis == concept.trace.creative_hypothesis

    # --- Stage-B CIE (P4-A.2/3): Recipe + InnovationTrace ---
    ce = evaluate_stage_a(provider, [concept])[0]
    re = evaluate_stage_b(provider, [recipe], traces=[concept.trace])[0]
    assert len(re.scores) == 1  # realization_quality only
    dims = {s.dimension for s in re.scores}
    assert dims == {"realization_quality"}

    # --- Final Ranking (P4-A.4): canonical direct six-dimension weighted sum ---
    report = build_report(concept, ce, recipe, re)
    assert len(report.stage_a) == 5
    assert len(report.stage_b) == 1
    # DemoProvider scoring -> direct six-dimension weighted sum = 4.25 (no 0.75/0.25 blend).
    assert report.total_score == 4.25
    assert report.stage_a_score > 0 and report.stage_b_score > 0
