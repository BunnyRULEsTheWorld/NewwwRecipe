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
import re
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
- Steps must be ordered, specific, and ACTIONABLE. Write 4-7 steps. Each step must contain at least
  two of: an explicit action/technique, a named ingredient or tool, a time (e.g. "8-10 minutes"), a
  temperature or heat level (e.g. "medium-high", "200 C / 400 F"), a doneness check, or a food-safety
  standard.
- For proteins, include an explicit safety doneness check (e.g. "cook until the thickest part reaches
  74 C / 165 F" for poultry). Choose the safety standard that fits the actual main ingredient — do not
  hard-code a single protein's rule onto every recipe.
- FORBIDDEN placeholder steps (never use these alone as a step): "Prep the given ingredients.",
  "Cook until done.", "Cook until done; rest and serve.", "Season as needed.", "Serve and enjoy.",
  "Follow normal cooking procedure.", "Add the ingredients and cook.", "Finish and serve.", "placeholder",
  "N/A", "None", "Steps", "Instructions".
- Example of a BAD steps array (NEVER return this): ["Prep the given ingredients.", "Cook until done."]
- Example of a GOOD steps array for a chicken-coffee idea:
  ["Pat 450g ground chicken and 2 tbsp finely ground espresso dry; season with 1/2 tsp salt and 1/4 tsp white pepper.",
   "Mix with 1 beaten egg white and 1 tsp cornstarch until a sticky paste forms.",
   "Line a small heatproof dish with parchment and pack the paste 2 cm thick.",
   "Steam over gently boiling water, covered, for 18-20 minutes until the center is set and reaches 74 C / 165 F.",
   "Let rest 3 minutes, then slice and serve with a drizzle of soy sauce and chili oil."]
- Before outputting JSON, self-check: (1) steps has between 4 and 7 items, (2) no item is a placeholder
  or single vague verb, (3) every protein recipe has a doneness/safety check, (4) step 1 is a real
  prep action and step N is a finishing/resting/serving action.
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


# --------------------------------------------------------------------------------------
# Programmatic step-quality validation (defense-in-depth, not a prompt-only rule)
# --------------------------------------------------------------------------------------

# Steps that are placeholders on their own — never acceptable as a realization step.
PLACEHOLDER_STEPS = {
    "prepare the ingredients",
    "prep the given ingredients",
    "cook until done",
    "cook until done; rest and serve",
    "season as needed",
    "serve and enjoy",
    "follow normal cooking procedure",
    "add the ingredients and cook",
    "finish and serve",
    "placeholder",
    "n/a",
    "none",
    "steps",
    "instructions",
}

MIN_STEPS = 4
MAX_STEPS = 7

# Explicit cooking action verbs, used for the "overall explicit action" check.
ACTION_VERBS = (
    "pat", "season", "sear", "brown", "fry", "saute", "sauté", "stir", "simmer",
    "boil", "bake", "roast", "grill", "steam", "broil", "poach", "blanch", "braise",
    "knead", "whisk", "beat", "mix", "combine", "fold", "toss", "marinate", "cook",
    "heat", "warm", "chill", "rest", "reduce", "glaze", "caramelize", "char", "grind",
    "mince", "chop", "slice", "dice", "grate", "rub", "coat", "stuff", "thread",
    "skewer", "steep", "strain", "plate", "serve", "add", "pour", "place", "remove",
    "arrange", "garnish", "drizzle", "sprinkle", "transfer", "turn", "flip", "press",
    "roll", "shape", "freeze", "cool", "score", "zest", "juice", "peel", "core",
    "bring", "cook", "spread", "brush", "line", "pack", "cover", "uncover", "wrap",
)
_ACTION_RE = re.compile(r"\b(" + "|".join(ACTION_VERBS) + r")\b", re.I)
_TIME_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(min|mins|minute|minutes|sec|secs|second|seconds|s|hr|hrs|hour|hours|小时|分钟|秒)\b",
    re.I,
)
_TEMP_RE = re.compile(r"\b\d+\s*(°|deg|degrees?|c|f|度|摄氏度|华氏度)\b", re.I)
_HEAT_RE = re.compile(
    r"\b(low|medium|medium-low|medium-high|high|gentle|low heat|medium heat|high heat|boiling|gentle boil|barely simmering)\b",
    re.I,
)
_DONENESS_RE = re.compile(
    r"until .{0,40}(reaches|set|golden|tender|opaque|cooked|done|firm|springy|bubbling|melted|caramelized)|"
    r"doneness|internal temperature|thickest part|centre|center|\b74\s*[cf]\b|\b165\s*[cf]\b",
    re.I,
)


def validate_recipe_steps(steps) -> List[str]:
    """Return a list of human-readable validation errors (empty list == valid).

    Rules (the programmatic backstop for the realization prompt):
      - `steps` must be a list of 4-7 non-empty strings
      - no step may be the literal "placeholder"
      - no step may be a standalone placeholder sentence
        ("Prepare the ingredients", "Cook until done", "Season as needed", "Serve and enjoy", ...)
      - overall the steps must contain at least one explicit cooking action AND at least one piece
        of actionable information (time, temperature, heat level, or a doneness check)
    """
    errors: List[str] = []
    if not isinstance(steps, list):
        return ["steps must be a list of 4-7 strings"]
    n = len(steps)
    if n < MIN_STEPS:
        errors.append(f"too few steps: {n} (need {MIN_STEPS}-{MAX_STEPS})")
    if n > MAX_STEPS:
        errors.append(f"too many steps: {n} (need {MIN_STEPS}-{MAX_STEPS})")
    for i, s in enumerate(steps, 1):
        if not isinstance(s, str) or not s.strip():
            errors.append(f"step {i} is empty or not a string")
            continue
        norm = s.strip().lower().rstrip(".").strip()
        if norm in PLACEHOLDER_STEPS:
            errors.append(f"step {i} is a placeholder sentence: {s.strip()!r}")
    combined = " ".join(str(s) for s in steps).lower()
    if not _ACTION_RE.search(combined):
        errors.append("steps contain no explicit cooking action (e.g. sear, simmer, bake)")
    if not (
        _TIME_RE.search(combined)
        or _TEMP_RE.search(combined)
        or _HEAT_RE.search(combined)
        or _DONENESS_RE.search(combined)
    ):
        errors.append(
            "steps contain no actionable information (time, temperature, heat level, or doneness check)"
        )
    return errors


class StepValidationError(ValueError):
    """Raised when realization returns recipe steps that fail `validate_recipe_steps` even after one retry."""


def build_realization_messages(
    concept: RecipeConcept,
    constraints: Optional[str] = None,
    correction: Optional[List[str]] = None,
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
    correction_block = ""
    if correction:
        correction_block = (
            "\nYOUR PREVIOUS RESPONSE WAS REJECTED for these step-quality errors:\n"
            + "\n".join(f"- {e}" for e in correction)
            + "\nFix ONLY the steps to satisfy the rules and return the corrected JSON now.\n"
        )
    user = (
        f"Realize the following concept into a complete recipe:{constraint_block}"
        f"{concept_block}{correction_block}"
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

def _realization_raw(provider: LLMProvider, messages: List[dict]) -> dict:
    """One realization attempt: structured output first, chat + JSON-extraction fallback."""
    try:
        return provider.structured(messages, schema=RECIPE_SCHEMA)
    except Exception:
        raw = provider.chat(messages)
        return _extract_json(raw)


def realize_concept(
    provider: LLMProvider,
    concept: RecipeConcept,
    constraints: Optional[str] = None,
    max_step_retries: int = 1,
) -> Recipe:
    """Realize a single RecipeConcept into a full Recipe.

    Defense-in-depth: the returned steps are programmatically validated. If the first attempt
    produces invalid steps, the specific errors are fed back and a single directed retry is made
    (realization only — ideation / CIE are NOT re-run). If the retry still fails, a
    `StepValidationError` is raised so the caller can surface a real error or fall back to the
    *labeled* Demo provider — never silently accept placeholder steps, never mislabel a fallback
    as Live.
    """
    messages = build_realization_messages(concept, constraints=constraints)
    last_errors: List[str] = []
    for attempt in range(max_step_retries + 1):
        data = _realization_raw(provider, messages)
        recipe = _parse_recipe(data, concept)
        errors = validate_recipe_steps(recipe.steps)
        if not errors:
            return recipe
        last_errors = errors
        if attempt < max_step_retries:
            messages = build_realization_messages(
                concept, constraints=constraints, correction=errors
            )
    raise StepValidationError(
        "Recipe steps failed validation after "
        f"{max_step_retries + 1} attempt(s): " + "; ".join(last_errors)
    )


def realize_concepts(
    provider: LLMProvider,
    concepts: List[RecipeConcept],
    constraints: Optional[str] = None,
) -> List[Recipe]:
    """Realize several concepts (order preserved)."""
    return [realize_concept(provider, c, constraints=constraints) for c in concepts]
