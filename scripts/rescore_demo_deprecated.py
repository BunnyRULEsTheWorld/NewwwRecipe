"""DEPRECATED — historical artifact, NOT part of the canonical CIE v3 contract.

This script was a one-off demo that re-scored the saved Mochicken Bake run with a *proposed CIE v2
rubric*: a 1-10 scale, the OLD six dimension names (creative_exploration_value, culinary_realisability,
communication_quality, ...), and the OLD four-field trace (ingredient_knowledge / concept_bridge /
creative_hypothesis / preliminary_feasibility_reasoning). None of that matches the current canonical
CIE v3 contract (1-5 integer scale, six canonical dimensions, six-stage trace). It is kept ONLY so the
historical result in examples/mochicken_bake_demo_cie_v2.json remains reproducible.

It is NOT a current runnable entry point and relies on a real Hy3 `.env`. By default it refuses to run
(exit code 2). To run it anyway, set RUN_DEPRECATED_CIE_SCRIPT=1.

Canonical scoring now lives in `src/creative_recipe/cie/` (see cie.scorer.total_score). Do not use this
script as a reference for the current contract.

The v2 rubric it encoded (weights summed to 1.0):
    1. Culinary Knowledge Grounding   (15%)
    2. Innovation Delta Quality       (25%)
    3. Mechanistic Plausibility       (20%)
    4. Creative Exploration Value      (15%)
    5. Culinary Realizability         (15%)
    6. Communication Quality           (10%)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Dict

# Allow running as a plain script while still importing the package.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from creative_recipe.config import Config  # noqa: E402
from creative_recipe.llm.hy3 import Hy3LLMClient  # noqa: E402

EXAMPLE_PATH = os.path.join(ROOT, "examples", "mochicken_bake_demo.json")

# Proposed CIE v2 rubric — six dimensions with explicit weights.
V2_DIMENSIONS: Dict[str, dict] = {
    "culinary_knowledge_grounding": {
        "label": "Culinary Knowledge Grounding",
        "weight": 0.15,
        "prompt": (
            "Culinary Knowledge Grounding (0.15): Does the recipe show accurate, non-trivial "
            "understanding of the ingredients' culinary properties, roles, and how they behave "
            "under the chosen technique? Score 1-10."
        ),
    },
    "innovation_delta_quality": {
        "label": "Innovation Delta Quality",
        "weight": 0.25,
        "prompt": (
            "Innovation Delta Quality (0.25): How genuinely novel is the move BEYOND a trivial "
            "ingredient substitution? Score 1-10. High scores require a real culinary idea (new "
            "technique, bridge, or sensory combination), not merely swapping one protein for another."
        ),
    },
    "mechanistic_plausibility": {
        "label": "Mechanistic Plausibility",
        "weight": 0.20,
        "prompt": (
            "Mechanistic Plausibility (0.20): Are the claimed flavor/texture mechanisms actually "
            "explained and physically sound (e.g. reduction, Maillard, emulsification, melting)? "
            "Score 1-10."
        ),
    },
    "creative_exploration_value": {
        "label": "Creative Exploration Value",
        "weight": 0.15,
        "prompt": (
            "Creative Exploration Value (0.15): How broadly does the idea explore the possibility "
            "space (cuisine, technique, presentation) rather than staying within one narrow frame? "
            "Score 1-10."
        ),
    },
    "culinary_realisability": {
        "label": "Culinary Realizability",
        "weight": 0.15,
        "prompt": (
            "Culinary Realizability (0.15): Can an ordinary home cook execute it with standard "
            "equipment and the given ingredients, with no contradictory or impossible steps? "
            "Score 1-10."
        ),
    },
    "communication_quality": {
        "label": "Communication Quality",
        "weight": 0.10,
        "prompt": (
            "Communication Quality (0.10): Is the dish name and creative explanation clear, and "
            "does it explain WHY the idea works (the bridge logic), not just restate the steps? "
            "Score 1-10."
        ),
    },
}


def build_recipe_block(data: dict) -> str:
    """Render the saved best_recipe + its InnovationTrace into a text block for the judge."""
    recipe = data["best_recipe"]
    report = data["best_report"]
    trace = report.get("trace", {})

    ings = "\n".join(
        f"  - {i['name']}" + (f" ({i.get('quantity')})" if i.get("quantity") else "")
        for i in recipe.get("ingredients", [])
    )
    seas = "\n".join(
        f"  - {s['name']}" + (f" ({s.get('quantity')})" if s.get("quantity") else "")
        for s in recipe.get("seasonings", [])
    )
    steps = "\n".join(f"  {n}. {s}" for n, s in enumerate(recipe.get("steps", []), 1))

    return (
        f"DISH NAME: {recipe.get('name')}\n"
        f"INGREDIENTS:\n{ings}\n"
        f"SEASONINGS:\n{seas}\n"
        f"STEPS:\n{steps}\n"
        f"CREATIVE EXPLANATION: {recipe.get('creative_explanation')}\n"
        f"ORIGINAL CREATIVE HYPOTHESIS (preserved): {recipe.get('creative_hypothesis')}\n\n"
        f"INNOVATION TRACE (from Creative Ideation):\n"
        f"  ingredient_knowledge          : {trace.get('ingredient_knowledge')}\n"
        f"  concept_bridge                : {trace.get('concept_bridge')}\n"
        f"  creative_hypothesis           : {trace.get('creative_hypothesis')}\n"
        f"  preliminary_feasibility       : {trace.get('preliminary_feasibility_reasoning')}\n"
    )


def build_schema() -> dict:
    """Strict JSON schema matching the v2 rubric output."""
    dim_props = {
        "score": {"type": "integer", "minimum": 1, "maximum": 10},
        "reason": {"type": "string"},
    }
    properties: Dict[str, dict] = {}
    required = []
    for key in V2_DIMENSIONS:
        properties[key] = {
            "type": "object",
            "properties": dim_props,
            "required": ["score", "reason"],
        }
        required.append(key)
    properties["innovation_delta_verdict"] = {
        "type": "string",
        "enum": ["PROTEIN_SUBSTITUTION_ONLY", "PARTIAL", "GENUINE_COOKING_INNOVATION"],
    }
    properties["innovation_delta_analysis"] = {"type": "string"}
    required += ["innovation_delta_verdict", "innovation_delta_analysis"]

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "cie_v2_eval",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def build_messages(recipe_block: str) -> list:
    system = (
        "You are a senior culinary-innovation evaluator. You will score a recipe against a "
        "proposed CIE v2 rubric. For EACH dimension return an integer score 1-10 and a concise, "
        "evidence-based reason that references observable facts in the recipe (no vague praise). "
        "Then give a focused Innovation Delta analysis: decide whether the coffee+chicken idea is "
        "merely a protein substitution or a genuine cooking innovation, and explain why. "
        "Return ONLY the requested JSON."
    )
    user = (
        "RECIPE TO EVALUATE:\n\n"
        f"{recipe_block}\n"
        "DIMENSIONS TO SCORE (return all six with score + reason):\n"
        + "\n".join(f"- {d['label']} ({w*100:.0f}%): {d['prompt']}" for d, w in
                    ((V2_DIMENSIONS[k], V2_DIMENSIONS[k]["weight"]) for k in V2_DIMENSIONS))
        + "\n\nAlso return:\n"
        "- innovation_delta_verdict: one of PROTEIN_SUBSTITUTION_ONLY / PARTIAL / GENUINE_COOKING_INNOVATION\n"
        "- innovation_delta_analysis: 2-4 sentences explaining the verdict."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def main() -> None:
    if os.environ.get("RUN_DEPRECATED_CIE_SCRIPT") != "1":
        sys.stderr.write(
            "DEPRECATED: scripts/rescore_demo_deprecated.py uses the OLD CIE v2 rubric "
            "(1-10 scale, old dimension names, old four-field trace) and is NOT part of the "
            "canonical CIE v3 contract. It is kept only as a historical artifact. To run it anyway "
            "(requires a real Hy3 .env), set RUN_DEPRECATED_CIE_SCRIPT=1.\n"
        )
        raise SystemExit(2)
    if not os.path.exists(EXAMPLE_PATH):
        raise SystemExit(f"Example JSON not found: {EXAMPLE_PATH}")
    with open(EXAMPLE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 72)
    print("CIE v2 RE-SCORE — Mochicken Bake (real Hy3, proposed rubric)")
    print("=" * 72)

    provider = Hy3LLMClient.from_env()  # reads .env, no code change in src/
    recipe_block = build_recipe_block(data)
    result = provider.structured(build_messages(recipe_block), schema=build_schema())

    # Compute weighted total.
    total = 0.0
    print("\nDIMENSION SCORES (1-10):\n")
    for key, meta in V2_DIMENSIONS.items():
        entry = result.get(key, {})
        score = entry.get("score")
        reason = entry.get("reason", "")
        if not isinstance(score, (int, float)):
            score = 0
        total += score * meta["weight"]
        print(f"  [{meta['weight']*100:>2.0f}%] {meta['label']}: {score}/10")
        print(f"         reason: {reason}\n")

    total = round(total, 3)
    print(f"  >>> V2 WEIGHTED TOTAL = {total:.2f} / 10\n")

    print("INNOVATION DELTA ANALYSIS:")
    print(f"  verdict : {result.get('innovation_delta_verdict')}")
    print(f"  analysis: {result.get('innovation_delta_analysis')}\n")

    # Persist the v2 result alongside the example for reference.
    out_path = os.path.join(ROOT, "examples", "mochicken_bake_demo_cie_v2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_example": "mochicken_bake_demo.json",
                "rubric": "cie_v2 (proposed, not in src/)",
                "dimensions": {k: {"label": V2_DIMENSIONS[k]["label"],
                                   "weight": V2_DIMENSIONS[k]["weight"]} for k in V2_DIMENSIONS},
                "scores": {k: result.get(k) for k in V2_DIMENSIONS},
                "weighted_total": total,
                "innovation_delta_verdict": result.get("innovation_delta_verdict"),
                "innovation_delta_analysis": result.get("innovation_delta_analysis"),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"(v2 result also written to: {out_path})")


if __name__ == "__main__":
    main()
