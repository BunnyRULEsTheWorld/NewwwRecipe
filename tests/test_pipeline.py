"""Full pipeline test (P4/P5): ideation -> Stage-A CIE -> Top-K -> realization -> Stage-B CIE -> final ranking.

    PYTHONPATH=src python -m pytest tests/test_pipeline.py -q
"""
import re

from creative_recipe.llm.fake import FakeProvider
from creative_recipe.pipeline import run
from creative_recipe.types import Ingredient


class CieFakeProvider(FakeProvider):
    """Scripted fake: ideation -> concepts, realization -> recipe, CIE -> scores (canonical 1-5)."""

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
            return {
                "concepts": [
                    {
                        "concept_name": "Coffee-Braised Chicken",
                        "ingredients": ["chicken", "coffee", "cheese"],
                        "creative_angle": "coffee braise + cheese crust",
                        "core_idea": "braise in coffee, broil under cheese",
                        "trace": {
                            "existing_culinary_context": {
                                "precedents": ["coq au vin"],
                                "relationship": "inherits braise template, swaps coffee for wine",
                            },
                            "ingredient_and_technique_knowledge": {
                                "ingredient_knowledge": [
                                    {"ingredient": "chicken", "property": "mild protein"},
                                    {"ingredient": "coffee", "property": "bitter roasty"},
                                ],
                                "technique_knowledge": [
                                    {"technique": "braising", "principle": "low heat dissolves collagen"},
                                ],
                            },
                            "innovation_delta": {
                                "before": "wine braise", "after": "coffee braise",
                                "change_type": ["ingredient substitution"], "magnitude": 3,
                            },
                            "mechanistic_justification": {
                                "flavor_mechanism": "coffee roast pyrazines",
                                "texture_mechanism": "collagen to gelatin",
                                "chemical_or_culinary_basis": "Maillard", "strength": "medium",
                            },
                            "creative_hypothesis": "swap stock for coffee, cap with cheese",
                            "risk_and_constraint": {
                                "risk": "coffee burns", "tradeoff": "loses acidity",
                                "failure_condition": "syrup turns bitter",
                            },
                        },
                    }
                ]
            }
        if "Recipe Realization engine" in sys:
            return {
                "name": "Coffee-Braised Chicken with Melted Cheese Crust",
                "ingredients": [
                    {"name": "chicken", "quantity": "400g", "note": None},
                    {"name": "cheese", "quantity": "100g", "note": "grated"},
                ],
                "steps": ["sear", "braise 30 min", "broil under cheese"],
                "creative_explanation": "coffee replaces stock; cheese cuts bitterness",
            }
        if "Creative Innovation Evaluation" in sys:
            m = re.search(r"key=(\w+)", messages[1]["content"])
            key = m.group(1) if m else "innovation_delta_quality"
            return {"score": self.SCORES.get(key, 4.0), "reason": f"{key} judged"}
        return {"score": 4.0, "reason": "default"}


def test_full_pipeline_runs_end_to_end():
    fake = CieFakeProvider()
    ingredients = [Ingredient(name="chicken"), Ingredient(name="coffee"), Ingredient(name="cheese")]
    result = run(fake, ingredients, num_concepts=1, top_k_concepts=1, top_k_final=1)

    assert len(result.concepts) == 1
    assert len(result.recipes) == 1
    assert result.best_recipe is not None
    assert result.best_recipe.name == "Coffee-Braised Chicken with Melted Cheese Crust"
    # six-dimension report, total is the canonical direct weighted sum (4.25)
    assert result.best_report is not None
    assert result.best_report.total_score == 4.25
    assert result.best_report.rank == 1
    # recipe carries concept traceability
    assert result.recipes[0].concept_name == "Coffee-Braised Chicken"
