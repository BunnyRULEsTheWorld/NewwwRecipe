"""Tests for the Recipe Realization stage (P3), aligned to the canonical CIE v3 six-stage trace.

Run offline with the FakeProvider — no network, no API key required:

    PYTHONPATH=src python -m pytest tests/test_realization.py -q
"""
import json

from creative_recipe.llm.fake import FakeProvider
from creative_recipe.recipe.realization import (
    realize_concept,
    realize_concepts,
    validate_recipe_steps,
    StepValidationError,
)
from creative_recipe.types import (
    ExistingCulinaryContext,
    Ingredient,
    IngredientAndTechniqueKnowledge,
    IngredientKnowledgeItem,
    InnovationDelta,
    InnovationTrace,
    MechanisticJustification,
    RecipeConcept,
    RiskAndConstraint,
    TechniqueKnowledgeItem,
)

SAMPLE_RECIPE = {
    "name": "Coffee-Braised Chicken with Melted Cheese Crust",
    "ingredients": [
        {"name": "chicken", "quantity": "400g", "note": None},
        {"name": "coffee", "quantity": "1 cup brewed", "note": None},
        {"name": "cheese", "quantity": "100g", "note": "grated"},
    ],
    "seasonings": [
        {"name": "salt", "quantity": "to taste", "note": None},
        {"name": "black pepper", "quantity": "to taste", "note": "freshly ground"},
    ],
    "steps": [
        "Pat chicken dry and season with salt and pepper.",
        "Sear chicken in a hot pan until golden on both sides.",
        "Add brewed coffee, bring to a simmer, cover and braise 30 min.",
        "Uncover and reduce until the liquid becomes a glossy glaze.",
        "Top with grated cheese and broil 3-4 min until bubbling.",
        "Rest 2 min and serve.",
    ],
    "creative_explanation": "Coffee stands in for stock; its bitterness is cut by the cheese's fat. The InnovationTrace's risk_and_constraint (coffee burns if reduced too hard) is honored by a gentle braise-then-broil technique.",
}

_HYPOTHESIS = "Replace wine/stock with coffee as the braise liquid, then cap with melted cheese for a cafe-inspired comfort dish."


def _sample_concept():
    return RecipeConcept(
        concept_name="Coffee-Braised Chicken with Melted Cheese Crust",
        ingredients=["chicken", "coffee", "cheese"],
        creative_angle="Coffee as braising liquid + cheese crust.",
        core_idea="Braise chicken in coffee, finish under cheese.",
        trace=InnovationTrace(
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
            creative_hypothesis=_HYPOTHESIS,
            risk_and_constraint=RiskAndConstraint(
                risk="coffee burns", tradeoff="loses acidity", failure_condition="syrup turns bitter"
            ),
        ),
    )


def test_realize_concept_structured_path():
    fake = FakeProvider(fixed_structured=SAMPLE_RECIPE)
    recipe = realize_concept(fake, _sample_concept())
    assert fake.structured_calls == 1
    assert fake.chat_calls == 0
    assert isinstance(recipe, object)
    assert recipe.name == "Coffee-Braised Chicken with Melted Cheese Crust"
    assert recipe.concept_name == "Coffee-Braised Chicken with Melted Cheese Crust"
    assert len(recipe.ingredients) == 3
    assert recipe.ingredients[2].note == "grated"
    # P4-A: seasonings must be emitted separately from hero ingredients.
    assert len(recipe.seasonings) == 2
    assert recipe.seasonings[0].name == "salt"
    assert recipe.seasonings[1].note == "freshly ground"
    assert len(recipe.steps) == 6
    assert recipe.creative_explanation


def test_realize_concept_preserves_creative_hypothesis():
    fake = FakeProvider(fixed_structured=SAMPLE_RECIPE)
    recipe = realize_concept(fake, _sample_concept())
    # P4-A: the original creative hypothesis from the InnovationTrace (stage 5) is carried forward,
    # realization does NOT re-invent the idea.
    assert recipe.creative_hypothesis == _HYPOTHESIS
    assert recipe.concept_name == "Coffee-Braised Chicken with Melted Cheese Crust"


def test_realize_concept_fallback_to_chat():
    class BrokenStructured(FakeProvider):
        def structured(self, messages, schema=None, **kwargs):
            self.structured_calls += 1
            raise RuntimeError("schema rejected by provider")

    fake = BrokenStructured(fixed_text=json.dumps(SAMPLE_RECIPE))
    recipe = realize_concept(fake, _sample_concept())
    assert fake.structured_calls == 1
    assert fake.chat_calls == 1
    assert recipe.name == "Coffee-Braised Chicken with Melted Cheese Crust"
    assert len(recipe.steps) == 6


def test_realize_concepts_preserves_order():
    fake = FakeProvider(fixed_structured=SAMPLE_RECIPE)
    concepts = [_sample_concept(), _sample_concept()]
    recipes = realize_concepts(fake, concepts)
    assert len(recipes) == 2
    assert recipes[0].concept_name == recipes[1].concept_name


# --- Step-quality validation (programmatic backstop) -----------------------------------------

def test_validate_recipe_steps_valid_4_to_7():
    assert validate_recipe_steps(SAMPLE_RECIPE["steps"]) == []


def test_validate_recipe_steps_placeholder():
    bad = ["placeholder", "Sear the chicken over medium heat for 5 minutes.",
           "Simmer for 10 minutes until done.", "Serve hot."]
    errs = validate_recipe_steps(bad)
    assert any("placeholder" in e.lower() for e in errs)


def test_validate_recipe_steps_empty_step():
    bad = ["", "Sear the chicken over medium heat for 5 minutes.",
           "Simmer for 10 minutes until done.", "Serve hot."]
    errs = validate_recipe_steps(bad)
    assert any("empty" in e.lower() for e in errs)


def test_validate_recipe_steps_too_few():
    bad = ["Sear the chicken over medium heat for 5 minutes.",
           "Simmer for 10 minutes until done.", "Serve hot."]
    errs = validate_recipe_steps(bad)
    assert any("too few" in e.lower() for e in errs)


def test_validate_recipe_steps_too_many():
    bad = [
        "Pat the chicken dry and season with salt and pepper.",
        "Sear over medium-high heat for 2 minutes per side.",
        "Add coffee and simmer for 10 minutes.",
        "Uncover and cook until the centre reaches 74 C / 165 F.",
        "Sprinkle cheese and broil 2 minutes until bubbling.",
        "Rest 3 minutes.",
        "Slice and plate.",
        "Serve with chili oil.",
    ]
    errs = validate_recipe_steps(bad)
    assert any("too many" in e.lower() for e in errs)


def test_validate_recipe_steps_vague_cook_until_done():
    bad = ["Prep the given ingredients.", "Cook until done.",
           "Season as needed.", "Serve and enjoy."]
    errs = validate_recipe_steps(bad)
    assert errs  # rejected
    assert any("placeholder" in e.lower() for e in errs)


def test_validate_recipe_steps_no_actionable_info():
    bad = ["Prepare the ingredients.", "Combine the ingredients in a bowl.",
           "Mix gently.", "Plate and serve."]
    errs = validate_recipe_steps(bad)
    assert any("actionable information" in e.lower() for e in errs)


# --- Realization retry behaviour ------------------------------------------------------------

class _SeqProvider(FakeProvider):
    """Returns a different fixed structured payload on each call (for retry tests)."""
    def __init__(self, sequence):
        super().__init__()
        self._seq = list(sequence)
        self._i = 0

    def structured(self, messages, schema=None, **kwargs):
        self.structured_calls += 1
        idx = min(self._i, len(self._seq) - 1)
        self._i += 1
        return dict(self._seq[idx])


_VALID_RECIPE = dict(SAMPLE_RECIPE, steps=list(SAMPLE_RECIPE["steps"]))
_INVALID_PLACEHOLDER = dict(
    SAMPLE_RECIPE,
    steps=["placeholder",
           "Sear the chicken over medium heat for 5 minutes until golden.",
           "Simmer for 10 minutes until the centre is set.",
           "Serve hot with chili oil."],
)
_INVALID_TOO_FEW = dict(
    SAMPLE_RECIPE,
    steps=["Sear the chicken over medium heat for 5 minutes until golden.",
           "Simmer for 10 minutes until done.", "Serve hot with chili oil."],
)


def test_realize_retry_first_invalid_then_valid():
    provider = _SeqProvider([_INVALID_PLACEHOLDER, _VALID_RECIPE])
    recipe = realize_concept(provider, _sample_concept())
    assert provider.structured_calls == 2
    assert len(recipe.steps) == 6  # valid recipe surfaced after directed retry


def test_realize_both_invalid_raises():
    provider = _SeqProvider([_INVALID_PLACEHOLDER, _INVALID_TOO_FEW])
    try:
        realize_concept(provider, _sample_concept())
        assert False, "expected StepValidationError"
    except StepValidationError as e:
        assert provider.structured_calls == 2
        assert "validation" in str(e).lower()
