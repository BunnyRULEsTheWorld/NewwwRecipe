"""Creative Ideation stage.

Responsibility:
    From the user's ingredients (+ optional constraints), generate N RecipeConcepts.
    Each concept is grounded in an explicit InnovationTrace that is PRODUCED by this stage, as a
    six-stage trajectory (canonical CIE v3):

        Stage 1  existing_culinary_context
          -> Stage 2  ingredient_and_technique_knowledge
          -> Stage 3  innovation_delta
          -> Stage 4  mechanistic_justification
          -> Stage 5  creative_hypothesis
          -> Stage 6  risk_and_constraint

    The trace is the explicit, auditable innovation trajectory. It is NOT a claim about the
    model's true internal thinking — it is a structured reasoning artifact the LLM is asked to
    emit so the creative process is transparent and reviewable (and so Stage-A CIE can audit it).

    This stage does NOT produce full Recipes — that is Recipe Realization (next stage).

Outputs: List[RecipeConcept]
"""
from __future__ import annotations

import json
import re
from typing import List, Optional

from ..llm.base import LLMProvider
from ..types import Ingredient, InnovationTrace, RecipeConcept

# --------------------------------------------------------------------------------------
# Prompt (versioned, testable)
# --------------------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Creative Ideation engine of a recipe AI system.

Given a set of available ingredients and optional constraints, you propose multiple CREATIVE recipe concepts.
Each concept must be grounded in an explicit six-stage InnovationTrace that records your reasoning:

Stage 1 — existing_culinary_context: closest existing dishes/traditions/prior techniques (precedents, most specific first) and how the new idea inherits from and departs from them (relationship).
Stage 2 — ingredient_and_technique_knowledge: per-ingredient knowledge (ingredient + property, with limits) and per-technique knowledge (technique + principle, and what it does NOT do).
Stage 3 — innovation_delta: the concrete before -> after change (before, after, change_type as a list of strings, magnitude 0-5 expressing SIZE of change only, never value).
Stage 4 — mechanistic_justification: why the change should work (flavor_mechanism, texture_mechanism, chemical_or_culinary_basis, and a self-assessed strength of weak|medium|strong).
Stage 5 — creative_hypothesis: the novel idea being proposed (a non-obvious combination or technique).
Stage 6 — risk_and_constraint: falsifiable risks (risk), tradeoffs (tradeoff), and a failure_condition under which the idea should be judged a failure.

Rules:
- You do NOT write full recipes yet; you only propose concepts.
- Use ONLY the provided ingredients (you may combine them in new, surprising ways).
- Make the concepts DISTINCT from each other (vary cuisine, technique, and creative angle).
- Keep concept names short and evocative.
- magnitude expresses SIZE of change only, never innovation value.

Return STRICT JSON of the form:
{
  "concepts": [
    {
      "concept_name": "string",
      "ingredients": ["string", ...],
      "creative_angle": "string",
      "core_idea": "string",
      "trace": {
        "existing_culinary_context": {
          "precedents": ["string", ...],
          "relationship": "string"
        },
        "ingredient_and_technique_knowledge": {
          "ingredient_knowledge": [{"ingredient": "string", "property": "string"}, ...],
          "technique_knowledge": [{"technique": "string", "principle": "string"}, ...]
        },
        "innovation_delta": {
          "before": "string",
          "after": "string",
          "change_type": ["string", ...],
          "magnitude": 0
        },
        "mechanistic_justification": {
          "flavor_mechanism": "string",
          "texture_mechanism": "string",
          "chemical_or_culinary_basis": "string",
          "strength": "weak|medium|strong"
        },
        "creative_hypothesis": "string",
        "risk_and_constraint": {
          "risk": "string",
          "tradeoff": "string",
          "failure_condition": "string"
        }
      }
    }
  ]
}
"""


def build_ideation_messages(
    ingredients: List[Ingredient],
    constraints: Optional[str] = None,
    num_concepts: int = 5,
) -> List[dict]:
    """Assemble the chat messages for the ideation call."""
    ing_lines = "\n".join(
        f"- {i.name}" + (f" ({i.quantity})" if i.quantity else "")
        + (f"  [{i.note}]" if i.note else "")
        for i in ingredients
    )
    constraint_block = f"\nConstraints: {constraints}\n" if constraints else "\n"
    user = (
        f"Available ingredients:\n{ing_lines}"
        f"{constraint_block}"
        f"Propose exactly {num_concepts} distinct creative recipe concepts as JSON."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


# --------------------------------------------------------------------------------------
# JSON schema for strict structured output (forwarded to Hy3 / OpenAI-compatible providers)
# --------------------------------------------------------------------------------------

CONCEPT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "recipe_concepts",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concept_name": {"type": "string"},
                            "ingredients": {"type": "array", "items": {"type": "string"}},
                            "creative_angle": {"type": "string"},
                            "core_idea": {"type": "string"},
                            "trace": {
                                "type": "object",
                                "properties": {
                                    "existing_culinary_context": {
                                        "type": "object",
                                        "properties": {
                                            "precedents": {"type": "array", "items": {"type": "string"}},
                                            "relationship": {"type": "string"},
                                        },
                                        "required": ["precedents", "relationship"],
                                    },
                                    "ingredient_and_technique_knowledge": {
                                        "type": "object",
                                        "properties": {
                                            "ingredient_knowledge": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "ingredient": {"type": "string"},
                                                        "property": {"type": "string"},
                                                    },
                                                    "required": ["ingredient", "property"],
                                                },
                                            },
                                            "technique_knowledge": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "technique": {"type": "string"},
                                                        "principle": {"type": "string"},
                                                    },
                                                    "required": ["technique", "principle"],
                                                },
                                            },
                                        },
                                        "required": ["ingredient_knowledge", "technique_knowledge"],
                                    },
                                    "innovation_delta": {
                                        "type": "object",
                                        "properties": {
                                            "before": {"type": "string"},
                                            "after": {"type": "string"},
                                            "change_type": {"type": "array", "items": {"type": "string"}},
                                            "magnitude": {"type": "integer"},
                                        },
                                        "required": ["before", "after", "change_type", "magnitude"],
                                    },
                                    "mechanistic_justification": {
                                        "type": "object",
                                        "properties": {
                                            "flavor_mechanism": {"type": "string"},
                                            "texture_mechanism": {"type": "string"},
                                            "chemical_or_culinary_basis": {"type": "string"},
                                            "strength": {"type": "string"},
                                        },
                                        "required": [
                                            "flavor_mechanism",
                                            "texture_mechanism",
                                            "chemical_or_culinary_basis",
                                            "strength",
                                        ],
                                    },
                                    "creative_hypothesis": {"type": "string"},
                                    "risk_and_constraint": {
                                        "type": "object",
                                        "properties": {
                                            "risk": {"type": "string"},
                                            "tradeoff": {"type": "string"},
                                            "failure_condition": {"type": "string"},
                                        },
                                        "required": ["risk", "tradeoff", "failure_condition"],
                                    },
                                },
                                "required": [
                                    "existing_culinary_context",
                                    "ingredient_and_technique_knowledge",
                                    "innovation_delta",
                                    "mechanistic_justification",
                                    "creative_hypothesis",
                                    "risk_and_constraint",
                                ],
                            },
                        },
                        "required": [
                            "concept_name",
                            "ingredients",
                            "creative_angle",
                            "core_idea",
                            "trace",
                        ],
                    },
                }
            },
            "required": ["concepts"],
        },
    },
}


# --------------------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from an LLM text response (fallback path)."""
    text = (text or "").strip()
    # 1) whole string is JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) fenced code block ```json ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 3) first '{' to last '}'
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    raise ValueError("Could not parse JSON from LLM response")


def _parse_concepts(data: dict, num_concepts: int) -> List[RecipeConcept]:
    """Validate raw dict into typed RecipeConcept objects (drops nothing, validates all)."""
    if not isinstance(data, dict):
        raise ValueError("LLM output was not a JSON object")
    raw = data.get("concepts")
    if not isinstance(raw, list) or not raw:
        raise ValueError("LLM output missing a non-empty 'concepts' array")
    concepts = [RecipeConcept(**item) for item in raw]
    # keep at most num_concepts (model may return more); order preserved
    return concepts[:num_concepts]


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def generate_concepts(
    provider: LLMProvider,
    ingredients: List[Ingredient],
    constraints: Optional[str] = None,
    num_concepts: int = 5,
) -> List[RecipeConcept]:
    """Generate N creative RecipeConcepts, each with an InnovationTrace.

    Uses structured output first; on any failure (schema rejected, malformed JSON, network/
    parse error) falls back to a plain chat call whose text is parsed for JSON.
    """
    if not ingredients:
        return []
    messages = build_ideation_messages(ingredients, constraints=constraints, num_concepts=num_concepts)
    try:
        data = provider.structured(messages, schema=CONCEPT_SCHEMA)
        return _parse_concepts(data, num_concepts)
    except Exception:
        # Fallback: ask for prose/JSON via chat and extract JSON robustly.
        raw = provider.chat(messages)
        data = _extract_json(raw)
        return _parse_concepts(data, num_concepts)
