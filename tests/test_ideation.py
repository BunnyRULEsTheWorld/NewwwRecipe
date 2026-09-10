"""Tests for the Creative Ideation stage (P2), aligned to the canonical CIE v3 six-stage trace.

Run offline with the FakeProvider — no network, no API key required:

    PYTHONPATH=src python -m pytest tests/test_ideation.py -q
"""
import json

from creative_recipe.llm.fake import FakeProvider
from creative_recipe.recipe.ideation import generate_concepts
from creative_recipe.types import Ingredient, InnovationTrace, RecipeConcept

# A realistic chicken / coffee / cheese concept used by the tests and the demo, with a six-stage trace.
SAMPLE_CONCEPTS = {
    "concepts": [
        {
            "concept_name": "Coffee-Braised Chicken with Melted Cheese Crust",
            "ingredients": ["chicken", "coffee", "cheese"],
            "creative_angle": "Uses coffee as a savory braising liquid and finishes with a bubbling cheese crust to soften coffee's bitterness.",
            "core_idea": "Slow-braise chicken in strong black coffee until it reduces to a glossy glaze, then broil under cheese for a umami crust.",
            "trace": {
                "existing_culinary_context": {
                    "precedents": ["coq au vin", "coffee-rubbed brisket"],
                    "relationship": "Inherits the wine-braised-chicken template, swaps the braise liquid for coffee's bitter-roast base.",
                },
                "ingredient_and_technique_knowledge": {
                    "ingredient_knowledge": [
                        {"ingredient": "chicken", "property": "mild protein and collagen; collagen->gelatin when slow-cooked"},
                        {"ingredient": "coffee", "property": "bitter, roasty pyrazines; reduces to a glaze without curdling"},
                        {"ingredient": "cheese", "property": "fat + glutamates for umami; melts and browns under direct heat"},
                    ],
                    "technique_knowledge": [
                        {"technique": "braising", "principle": "low moist heat dissolves collagen; keeps meat juicy, does NOT brown much"},
                        {"technique": "broiling", "principle": "direct radiant heat browns the cheese crust; too long burns milk solids"},
                    ],
                },
                "innovation_delta": {
                    "before": "Chicken braised in wine/stock, finished plainly.",
                    "after": "Chicken braised in reduced black coffee, finished under a melted-cheese crust.",
                    "change_type": ["ingredient substitution", "flavor architecture"],
                    "magnitude": 3,
                },
                "mechanistic_justification": {
                    "flavor_mechanism": "Coffee roast pyrazines echo toasted wine-reduction notes; cheese glutamates fill the savory gap.",
                    "texture_mechanism": "Collagen-to-gelatin braise keeps meat succulent; cheese adds a crisp bubbly lid.",
                    "chemical_or_culinary_basis": "Maillard + pyrazine bitterness is a known savory enhancer; unproven vs stock on preference.",
                    "strength": "medium",
                },
                "creative_hypothesis": "Replace wine/stock with coffee as the braise liquid, then cap with melted cheese for a cafe-inspired comfort dish.",
                "risk_and_constraint": {
                    "risk": "Coffee turns acrid if reduced too hard; cheese scorches under the broiler.",
                    "tradeoff": "Loses the bright acidity wine gives; trades it for roasty depth.",
                    "failure_condition": "Braising liquid reduces to a burnt-bitter syrup, or cheese blackens before chicken is hot through.",
                },
            },
        },
        {
            "concept_name": "Coffee-Rubbed Cheese Chicken Skewers",
            "ingredients": ["chicken", "coffee", "cheese"],
            "creative_angle": "Dry coffee rub + cheese-stuffed chicken skewers for a grill-friendly, contrasting-texture take.",
            "core_idea": "Cube chicken, stuff with cheese, coat in ground coffee rub, grill on skewers.",
            "trace": {
                "existing_culinary_context": {
                    "precedents": ["coffee-rubbed steak", "cheese-stuffed chicken breast"],
                    "relationship": "Combines the coffee-rub technique with the cheese-stuffed poultry idea, formatted on a skewer.",
                },
                "ingredient_and_technique_knowledge": {
                    "ingredient_knowledge": [
                        {"ingredient": "ground coffee", "property": "acts as a dry rub: bitter + aromatic; burns above medium heat"},
                        {"ingredient": "cheese", "property": "inside keeps chicken juicy; melts at ~55C; seals the core"},
                    ],
                    "technique_knowledge": [
                        {"technique": "dry rubbing", "principle": "surface spice forms a crust via Maillard; no liquid added, burns if too hot"},
                        {"technique": "skewer grilling", "principle": "even surface exposure; fast cook; core must reach safe temperature without burning the rub"},
                    ],
                },
                "innovation_delta": {
                    "before": "Chicken grilled plain or with salt-pepper.",
                    "after": "Chicken cubes stuffed with cheese and coated in a coffee rub, grilled on skewers.",
                    "change_type": ["technique transfer", "ingredient stacking"],
                    "magnitude": 2,
                },
                "mechanistic_justification": {
                    "flavor_mechanism": "Coffee crust adds bitter-roast aromatics that contrast the molten cheese's fat-savory core.",
                    "texture_mechanism": "Cheese core stays molten and moist; rub gives a thin crisp shell.",
                    "chemical_or_culinary_basis": "Dry spice crusting is a standard barbecue mechanism; cheese melt point well established.",
                    "strength": "medium",
                },
                "creative_hypothesis": "Treat coffee like a spice rub rather than a liquid, pairing its crust with a cheese core.",
                "risk_and_constraint": {
                    "risk": "Coffee rub burns on the grill before the chicken core is cooked.",
                    "tradeoff": "Small cubes dry out faster than a braise; less saucy comfort.",
                    "failure_condition": "Rub is black-bittered while chicken interior is under 74C.",
                },
            },
        },
    ]
}


def _sample_ingredients():
    return [
        Ingredient(name="chicken", quantity="400g"),
        Ingredient(name="coffee", quantity="1 cup brewed"),
        Ingredient(name="cheese", quantity="100g"),
    ]


def test_generate_concepts_structured_path():
    """FakeProvider returns a valid concepts dict via structured(); chat must NOT be used."""
    fake = FakeProvider(fixed_structured=SAMPLE_CONCEPTS)
    concepts = generate_concepts(fake, _sample_ingredients(), num_concepts=2)
    assert fake.structured_calls == 1
    assert fake.chat_calls == 0
    assert len(concepts) == 2
    assert all(isinstance(c, RecipeConcept) for c in concepts)
    assert concepts[0].concept_name == "Coffee-Braised Chicken with Melted Cheese Crust"
    assert set(concepts[0].ingredients) == {"chicken", "coffee", "cheese"}


def test_generate_concepts_produces_six_stage_innovation_trace():
    """Every concept must carry a complete six-stage InnovationTrace."""
    fake = FakeProvider(fixed_structured=SAMPLE_CONCEPTS)
    concepts = generate_concepts(fake, _sample_ingredients(), num_concepts=2)
    for c in concepts:
        assert isinstance(c.trace, InnovationTrace)
        assert c.trace.existing_culinary_context.precedents
        assert c.trace.ingredient_and_technique_knowledge.ingredient_knowledge
        assert c.trace.innovation_delta.before and c.trace.innovation_delta.after
        assert c.trace.mechanistic_justification.flavor_mechanism
        assert c.trace.creative_hypothesis
        assert c.trace.risk_and_constraint.risk


def test_generate_concepts_fallback_to_chat():
    """When structured() fails, chat() is used and its JSON text is parsed."""

    class BrokenStructured(FakeProvider):
        def structured(self, messages, schema=None, **kwargs):
            self.structured_calls += 1
            raise RuntimeError("schema rejected by provider")

    chat_json = json.dumps(SAMPLE_CONCEPTS)
    fake = BrokenStructured(fixed_text=chat_json)
    concepts = generate_concepts(fake, _sample_ingredients(), num_concepts=2)
    assert fake.structured_calls == 1
    assert fake.chat_calls == 1
    assert len(concepts) == 2
    assert concepts[0].concept_name == "Coffee-Braised Chicken with Melted Cheese Crust"


def test_generate_concepts_empty_input():
    assert generate_concepts(FakeProvider(), []) == []
