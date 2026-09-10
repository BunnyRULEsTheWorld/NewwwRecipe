"""Recipe Realization stage.

Responsibility:
    Take a RecipeConcept (which already carries an explicit six-stage InnovationTrace) and turn it
    into a fully cookable Recipe (name, ingredients, ordered steps, human-readable creative explanation).

    The concept's InnovationTrace — especially `creative_hypothesis` (stage 5) and the
    `risk_and_constraint` (stage 6) — is fed back into the realization prompt so the model's concrete
    steps stay faithful to the idea it proposed during ideation. The trace is an auditable artifact,
    NOT a claim about the model's true thinking.

    This stage does NOT evaluate recipes — that is Stage-B CIE (realization_quality, plan-level only).

Outputs: Recipe
"""
from __future__ import annotations

import json
from typing import List, Optional

from ..llm.base import LLMProvider
from ..types import Ingredient, Recipe, RecipeConcept
from .ideation import _extract_json


# --------------------------------------------------------------------------------------
# Prompt (versioned, testable)
# --------------------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Recipe Realization engine of a recipe AI system.

You are given a RecipeConcept and its six-stage InnovationTrace (produced earlier during Creative Ideation).
Your job is to turn that concept into ONE fully cookable recipe.

Rules:
- PRESERVE the concept's creative_hypothesis (stage 5). You are realizing an already-decided idea, NOT inventing a new one.
  Make the steps concrete and feasible, faithful to the proposed change and mindful of the stated risk_and_constraint (stage 6):
  design the steps so they avoid the stated failure_condition where possible.
- Use the concept's listed ingredients as the HERO ingredients. You MAY add minimal pantry staples
  (salt, pepper, oil, water) and assign reasonable quantities; do NOT introduce major new hero ingredients.
- Output TWO separate ingredient lists:
    "ingredients" : the hero ingredients from the concept (with quantities/notes)
    "seasonings"  : the seasonings / condiments / spices used (e.g. salt, pepper, spices, sauces)
- Steps must be ordered, specific, and actionable (technique + time where useful).
- creative_explanation must explain the creativity in plain language, reference the InnovationTrace, and
  must NOT contradict the original creative_hypothesis.

Return STRICT JSON of the form:
{
  "name": "string",
  "ingredients": [ {"name": "string", "quantity": "string or null", "note": "string or null"} ],
  "seasonings": [ {"name": "string", "quantity": "string or null", "note": "string or null"} ],
  "steps": ["string", "..."],
  "creative_explanation": "string"
}
"""


def build_realization_messages(
    concept: RecipeConcept,
    constraints: Optional[str] = None,
) -> List[dict]:
    constraint_block = f"\nConstraints: {constraints}\n" if constraints else "\n"
    t = concept.trace
    concept_block = (
        f"Concept name : {concept.concept_name}\n"
        f"Ingredients  : {', '.join(concept.ingredients)}\n"
        f"Creative angle: {concept.creative_angle}\n"
        f"Core idea    : {concept.core_idea}\n"
        f"InnovationTrace:\n"
        f"  Stage 1 Existing Culinary Context:\n"
        f"    precedents : {t.existing_culinary_context.precedents}\n"
        f"    relationship: {t.existing_culinary_context.relationship}\n"
        f"  Stage 3 Innovation Delta: before={t.innovation_delta.before} | after={t.innovation_delta.after} | change_type={t.innovation_delta.change_type} | magnitude={t.innovation_delta.magnitude}\n"
        f"  Stage 5 Creative Hypothesis: {t.creative_hypothesis}\n"
        f"  Stage 6 Risk & Constraint: risk={t.risk_and_constraint.risk} | tradeoff={t.risk_and_constraint.tradeoff} | failure_condition={t.risk_and_constraint.failure_condition}\n"
        f"\nIMPORTANT: preserve this creative_hypothesis when writing the recipe; do not re-invent it.\n"
    )
    user = (
        f"Realize the following concept into a complete recipe:{constraint_block}"
        f"{concept_block}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


# --------------------------------------------------------------------------------------
# JSON schema for strict structured output
# --------------------------------------------------------------------------------------

RECIPE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "recipe",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": ["string", "null"]},
                            "note": {"type": ["string", "null"]},
                        },
                        "required": ["name", "quantity", "note"],
                    },
                },
                "seasonings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": ["string", "null"]},
                            "note": {"type": ["string", "null"]},
                        },
                        "required": ["name", "quantity", "note"],
                    },
                },
                "steps": {"type": "array", "items": {"type": "string"}},
                "creative_explanation": {"type": "string"},
            },
            "required": ["name", "ingredients", "seasonings", "steps", "creative_explanation"],
        },
    },
}


# --------------------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------------------

def _parse_recipe(data: dict, concept: RecipeConcept) -> Recipe:
    if not isinstance(data, dict):
        raise ValueError("LLM output was not a JSON object")
    name = data.get("name")
    if not name:
        name = concept.concept_name
    raw_ings = data.get("ingredients") or []
    ingredients = [
        Ingredient(
            name=i.get("name", ""),
            quantity=i.get("quantity"),
            note=i.get("note"),
        )
        for i in raw_ings
        if isinstance(i, dict) and i.get("name")
    ]
    raw_seas = data.get("seasonings") or []
    seasonings = [
        Ingredient(
            name=s.get("name", ""),
            quantity=s.get("quantity"),
            note=s.get("note"),
        )
        for s in raw_seas
        if isinstance(s, dict) and s.get("name")
    ]
    steps = [s for s in (data.get("steps") or []) if isinstance(s, str) and s.strip()]
    explanation = data.get("creative_explanation") or concept.core_idea
    # Preserve the ORIGINAL creative hypothesis from the concept's InnovationTrace (stage 5).
    return Recipe(
        name=name,
        ingredients=ingredients,
        seasonings=seasonings,
        steps=steps,
        creative_explanation=explanation,
        creative_hypothesis=concept.trace.creative_hypothesis,
        concept_name=concept.concept_name,
    )


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def realize_concept(
    provider: LLMProvider,
    concept: RecipeConcept,
    constraints: Optional[str] = None,
) -> Recipe:
    """Realize a single RecipeConcept into a full Recipe (structured output + chat fallback)."""
    messages = build_realization_messages(concept, constraints=constraints)
    try:
        data = provider.structured(messages, schema=RECIPE_SCHEMA)
        return _parse_recipe(data, concept)
    except Exception:
        raw = provider.chat(messages)
        data = _extract_json(raw)
        return _parse_recipe(data, concept)


def realize_concepts(
    provider: LLMProvider,
    concepts: List[RecipeConcept],
    constraints: Optional[str] = None,
) -> List[Recipe]:
    """Realize several concepts (order preserved)."""
    return [realize_concept(provider, c, constraints=constraints) for c in concepts]
