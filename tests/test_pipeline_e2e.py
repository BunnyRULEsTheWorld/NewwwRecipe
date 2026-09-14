"""End-to-end pipeline integration test (P5), aligned to the canonical CIE v3 contract.

Goal: verify the complete closed loop from input ingredients to final innovation-recipe
evaluation, using an OFFLINE FakeProvider (no real Hy3 call, no network, no API key).

Run:
    PYTHONPATH=src python -m pytest tests/test_pipeline_e2e.py -q

The acceptance checks are encoded as individual test functions so a single failure is easy to localize.
"""
import re

from creative_recipe.llm.fake import FakeProvider
from creative_recipe.pipeline import run
from creative_recipe.types import Ingredient


# --------------------------------------------------------------------------------------
# Offline scripted provider (subclass of FakeProvider — never touches Hy3 / network)
# --------------------------------------------------------------------------------------
def _trace(before, after, hypothesis):
    return {
        "existing_culinary_context": {
            "precedents": ["coq au vin (wine-braised chicken)"],
            "relationship": "Inherits the braise template but swaps wine/stock for coffee's bitter-roast base.",
        },
        "ingredient_and_technique_knowledge": {
            "ingredient_knowledge": [
                {"ingredient": "chicken", "property": "mild protein and collagen; collagen->gelatin when slow-cooked"},
                {"ingredient": "coffee", "property": "bitter, roasty pyrazines; reduces to a glaze without curdling"},
            ],
            "technique_knowledge": [
                {"technique": "braising", "principle": "low moist heat dissolves collagen; keeps meat juicy"},
                {"technique": "broiling", "principle": "direct radiant heat browns the cheese crust; too long burns it"},
            ],
        },
        "innovation_delta": {
            "before": before,
            "after": after,
            "change_type": ["ingredient substitution"],
            "magnitude": 3,
        },
        "mechanistic_justification": {
            "flavor_mechanism": "Coffee roast pyrazines echo toasted wine-reduction notes; cheese glutamates fill the savory gap.",
            "texture_mechanism": "Collagen-to-gelatin braise keeps meat succulent; cheese adds a crisp bubbly lid.",
            "chemical_or_culinary_basis": "Maillard + pyrazine bitterness is a known savory enhancer; remains unproven vs stock on preference.",
            "strength": "medium",
        },
        "creative_hypothesis": hypothesis,
        "risk_and_constraint": {
            "risk": "Coffee turns acrid if reduced too hard.",
            "tradeoff": "Loses the bright acidity wine gives.",
            "failure_condition": "Braising liquid reduces to a burnt-bitter syrup, or cheese blackens before chicken is hot through.",
        },
    }


class E2EFakeProvider(FakeProvider):
    """Scripted FakeProvider that emulates the full Hy3 pipeline offline.

    Routes on the system prompt, exactly like the real provider would, so the pipeline code
    under test is identical to production. Scores are deterministic per dimension (1-5 scale).
    """

    SCORES = {
        "culinary_knowledge_grounding": 4.0,
        "existing_culinary_precedent_analysis": 4.0,
        "innovation_delta_quality": 5.0,
        "mechanistic_plausibility": 4.0,
        "innovation_value": 4.0,
        "realization_quality": 4.0,
    }

    CONCEPTS = [
        {
            "concept_name": "Coffee-Braised Chicken with Melted Cheese Crust",
            "ingredients": ["chicken", "coffee", "cheese"],
            "creative_angle": "Coffee as a savory braising liquid, finished with a bubbling cheese crust.",
            "core_idea": "Slow-braise chicken in strong black coffee, then broil under cheese.",
            "trace": _trace(
                "Chicken braised in wine/stock.",
                "Chicken braised in reduced black coffee.",
                "Replace stock with coffee as the braise liquid, then cap with melted cheese.",
            ),
        },
        {
            "concept_name": "Coffee-Rubbed Cheese-Stuffed Chicken",
            "ingredients": ["chicken", "coffee", "cheese"],
            "creative_angle": "Dry coffee rub plus a molten cheese core for a grill-friendly take.",
            "core_idea": "Cube chicken, stuff with cheese, coat in ground coffee rub, grill on skewers.",
            "trace": _trace(
                "Chicken grilled plain or with salt-pepper.",
                "Chicken cubes stuffed with cheese and coated in a coffee rub, grilled on skewers.",
                "Treat coffee like a spice rub rather than a liquid, pairing its crust with a cheese core.",
            ),
        },
    ]

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        sys = messages[0]["content"]
        if "Creative Ideation engine" in sys:
            return {"concepts": self.CONCEPTS}
        if "Recipe Realization engine" in sys:
            name = self._concept_name(messages[1]["content"]) or self.CONCEPTS[0]["concept_name"]
            concept = next((c for c in self.CONCEPTS if c["concept_name"] == name), self.CONCEPTS[0])
            return {
                "name": concept["concept_name"],
                "ingredients": [
                    {"name": i, "quantity": "200g" if i == "chicken" else "1 cup", "note": None}
                    for i in concept["ingredients"]
                ],
                "seasonings": [
                    {"name": "salt", "quantity": "to taste", "note": None},
                    {"name": "black pepper", "quantity": "to taste", "note": None},
                ],
                "steps": [
                    "Cut the chicken into 3 cm cubes and toss with salt, black pepper, and the finely ground coffee rub.",
                    "Tuck a small piece of cheese into the center of each cube, then thread the cubes onto skewers.",
                    "Preheat a grill or grill pan to medium (about 200 C / 400 F).",
                    "Grill the skewers 4-5 minutes per side, turning once, until browned and the thickest piece reaches 74 C / 165 F.",
                    "Rest 2 minutes off the heat, then serve.",
                ],
                "creative_explanation": f"{concept['creative_angle']} (faithful to InnovationTrace: {concept['trace']['creative_hypothesis']})",
            }
        if "Creative Innovation Evaluation" in sys:
            m = re.search(r"key=(\w+)", messages[1]["content"])
            key = m.group(1) if m else "innovation_delta_quality"
            return {"score": float(self.SCORES.get(key, 4.0)), "reason": f"{key} judged (offline)"}
        return {"score": 4.0, "reason": "default"}

    @staticmethod
    def _concept_name(user_text: str):
        m = re.search(r"Concept name\s*:\s*(.+)", user_text)
        return m.group(1).strip() if m else None


# --------------------------------------------------------------------------------------
# Shared fixtures
# --------------------------------------------------------------------------------------
INGREDIENTS = [Ingredient(name="chicken"), Ingredient(name="coffee"), Ingredient(name="cheese")]


def _run():
    fake = E2EFakeProvider()
    result = run(fake, INGREDIENTS, num_concepts=2, top_k_concepts=2, top_k_final=1)
    return fake, result


# --------------------------------------------------------------------------------------
# Acceptance checks
# --------------------------------------------------------------------------------------

def test_1_ideation_produces_multiple_concepts():
    """Creative Ideation must yield more than one RecipeConcept."""
    _, result = _run()
    assert len(result.concepts) >= 2, "expected multiple RecipeConcepts"
    assert all(c.concept_name for c in result.concepts)


def test_2_each_concept_has_full_six_stage_innovation_trace():
    """Each concept carries a complete six-stage InnovationTrace."""
    _, result = _run()
    for c in result.concepts:
        t = c.trace
        assert t.existing_culinary_context.precedents
        assert t.existing_culinary_context.relationship
        assert t.ingredient_and_technique_knowledge.ingredient_knowledge
        assert t.ingredient_and_technique_knowledge.technique_knowledge
        assert t.innovation_delta.before and t.innovation_delta.after
        assert t.innovation_delta.change_type
        assert 0 <= t.innovation_delta.magnitude <= 5
        assert t.mechanistic_justification.flavor_mechanism
        assert t.creative_hypothesis
        assert t.risk_and_constraint.risk


def test_3_stage_a_returns_five_dimensions_with_reasons():
    """Stage-A CIE must return the five Stage-A dimensions, each with a score and reason."""
    _, result = _run()
    report = result.best_report
    stage_a_keys = {s.dimension for s in report.stage_a}
    expected = {
        "culinary_knowledge_grounding",
        "existing_culinary_precedent_analysis",
        "innovation_delta_quality",
        "mechanistic_plausibility",
        "innovation_value",
    }
    assert stage_a_keys == expected, f"Stage-A dims mismatch: {stage_a_keys}"
    for s in report.stage_a:
        assert 1.0 <= s.score <= 5.0, f"score out of 1-5 range: {s.dimension}={s.score}"
        assert s.reason, f"missing reason for {s.dimension}"


def test_4_recipe_realization_produces_recipe():
    """Recipe Realization must turn a concept into a full Recipe (no new innovation invented)."""
    _, result = _run()
    assert len(result.recipes) >= 1
    r = result.best_recipe
    assert r is not None
    assert r.name
    assert len(r.ingredients) >= 1
    assert len(r.seasonings) >= 1            # seasonings is a real field, not a string list
    assert len(r.steps) >= 1
    assert r.creative_explanation
    # traceability: recipe must reference its source concept (not invent a new one)
    assert r.concept_name in {c.concept_name for c in result.concepts}


def test_5_stage_b_returns_single_dimension_with_reason():
    """Stage-B CIE must return only realization_quality, with a score and reason."""
    _, result = _run()
    report = result.best_report
    stage_b_keys = {s.dimension for s in report.stage_b}
    expected = {"realization_quality"}
    assert stage_b_keys == expected, f"Stage-B dims mismatch: {stage_b_keys}"
    for s in report.stage_b:
        assert 1.0 <= s.score <= 5.0
        assert s.reason


def test_6_final_ranking_is_direct_six_dimension_weighted_sum():
    """Final Ranking must emit an EvalReport whose total_score = Σ(weight_d × score_d)."""
    from creative_recipe.cie.dimensions import WEIGHTS
    from creative_recipe.cie.scorer import total_score

    _, result = _run()
    report = result.best_report
    assert report is not None
    assert report.rank >= 1

    # Recompute the canonical direct six-dimension weighted sum and compare to total_score.
    expected_total = total_score(list(report.stage_a) + list(report.stage_b), weights=WEIGHTS)
    assert report.total_score == expected_total, (
        f"Final total mismatch: got {report.total_score}, expected {expected_total}"
    )
    # The historical 0.75 / 0.25 Stage-A/Stage-B blend is no longer used.
    assert report.total_score != round(0.75 * report.stage_a_score + 0.25 * report.stage_b_score, 4)
    # With the scripted scores, the direct weighted sum equals 4.25.
    assert report.total_score == 4.25
