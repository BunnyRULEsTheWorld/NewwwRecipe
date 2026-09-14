"""Offline mock providers for tests and demos (no network / no API key).

- `FakeProvider`     : minimal stub returning deterministic text; for unit tests that only need
  a trivial `chat`/`structured` response.
- `DemoProvider`     : a *scripted* fake that emulates Hy3 end-to-end for demos — it returns
  realistic recipe concepts (with a six-stage InnovationTrace), realized recipes, and per-dimension
  CIE scores depending on the prompt. Drives `python -m creative_recipe generate --provider fake` and `demo`.

Both implement the same LLMProvider interface as Hy3LLMClient.
"""
import json
import re
from typing import Any, Dict, List, Optional

from .base import LLMProvider

# Default CIE scores used by DemoProvider (canonical 1-5 scale, per dimension key).
# Stored as strict integers to avoid any float/truncation ambiguity downstream.
_DEMO_SCORES = {
    "culinary_knowledge_grounding": 4,
    "existing_culinary_precedent_analysis": 4,
    "innovation_delta_quality": 5,
    "mechanistic_plausibility": 4,
    "innovation_value": 4,
    "realization_quality": 4,
}

# A small built-in concept set for the demo (chicken / coffee / cheese), with a six-stage trace.
_DEMO_CONCEPTS = [
    {
        "concept_name": "Coffee-Braised Chicken with Melted Cheese Crust",
        "ingredients": ["chicken", "coffee", "cheese"],
        "creative_angle": "Coffee as a savory braising liquid, finished with a bubbling cheese crust.",
        "core_idea": "Slow-braise chicken in strong black coffee, then broil under cheese.",
        "trace": {
            "existing_culinary_context": {
                "precedents": ["coq au vin (wine-braised chicken)", "coffee-rubbed brisket", "cafe de Paris butter"],
                "relationship": "Inherits the wine-braised-chicken template but swaps the acid/sweet braise liquid for coffee's bitter-roast base; departs by capping with a melted-cheese crust rather than a reduction.",
            },
            "ingredient_and_technique_knowledge": {
                "ingredient_knowledge": [
                    {"ingredient": "chicken", "property": "mild protein and collagen; collagen converts to gelatin when slow-cooked, giving body. Overcooks to dryness above ~74C internal."},
                    {"ingredient": "coffee", "property": "bitter, roasty Maillard compounds (pyrazines); reduces to a glaze without curdling; astringency tightens proteins slightly."},
                    {"ingredient": "cheese", "property": "fat + glutamates for umami; melts and browns (Maillard) under direct heat; separates if overheated."},
                ],
                "technique_knowledge": [
                    {"technique": "braising", "principle": "low moist heat dissolves collagen into gelatin; keeps chicken juicy. Does NOT brown the surface much."},
                    {"technique": "broiling", "principle": "direct radiant heat browns and bubbles the cheese crust; too long burns milk solids."},
                ],
            },
            "innovation_delta": {
                "before": "Chicken braised in wine/stock, finished plainly.",
                "after": "Chicken braised in reduced black coffee, finished under a melted-cheese crust.",
                "change_type": ["ingredient substitution", "flavor architecture"],
                "magnitude": 3,
            },
            "mechanistic_justification": {
                "flavor_mechanism": "Coffee's roast pyrazines echo the toasted notes wine reduction gives, while cheese glutamates fill the savory gap left by removing stock.",
                "texture_mechanism": "Collagen-to-gelatin braise keeps meat succulent; cheese adds a crisp bubbly lid via Maillard.",
                "chemical_or_culinary_basis": "Maillard + pyrazine bitterness is a known savory enhancer; remains unproven whether coffee beats stock on preference.",
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
        "concept_name": "Coffee-Rubbed Cheese-Stuffed Chicken Skewers",
        "ingredients": ["chicken", "coffee", "cheese"],
        "creative_angle": "Dry coffee rub plus a molten cheese core for a grill-friendly take.",
        "core_idea": "Cube chicken, stuff with cheese, coat in ground coffee rub, grill on skewers.",
        "trace": {
            "existing_culinary_context": {
                "precedents": ["coffee-rubbed steak", "cheese-stuffed chicken breast", "yakitori"],
                "relationship": "Combines the coffee-rub technique from barbecue with the cheese-stuffed poultry idea; formats both on a skewer for grill speed.",
            },
            "ingredient_and_technique_knowledge": {
                "ingredient_knowledge": [
                    {"ingredient": "ground coffee", "property": "acts as a dry rub: bitter + aromatic; burns above medium heat. Use finely ground, not brewed."},
                    {"ingredient": "cheese", "property": "inside keeps chicken juicy; melts at ~55C; seals the core so chicken stays moist."},
                    {"ingredient": "chicken", "property": "neutral canvas; cubes cook fast on a skewer."},
                ],
                "technique_knowledge": [
                    {"technique": "dry rubbing", "principle": "surface spice forms a crust via Maillard; no liquid added. Burns if heat is too high."},
                    {"technique": "skewer grilling", "principle": "even surface exposure; fast cook. Core must reach safe temperature without burning the rub."},
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
                "chemical_or_culinary_basis": "Dry spice crusting is a standard barbecue mechanism; cheese melt point is well established. Unproven: whether coffee reads as 'burnt' to some palates.",
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
    {
        "concept_name": "Coffee-Cheese Chicken Carbonara Twist",
        "ingredients": ["chicken", "coffee", "cheese"],
        "creative_angle": "A coffee-laced cream sauce over chicken and cheese, riffing on carbonara.",
        "core_idea": "Make a coffee-infused cream sauce, toss with chicken and cheese.",
        "trace": {
            "existing_culinary_context": {
                "precedents": ["spaghetti carbonara", "espresso chicken", "mole (chocolate-chili sauce)"],
                "relationship": "Borrow carbonara's cream+cheese emulsion and lace it with coffee the way cocoa is laced into mole for bitter depth.",
            },
            "ingredient_and_technique_knowledge": {
                "ingredient_knowledge": [
                    {"ingredient": "coffee", "property": "reduces into a syrup; a little adds bitter depth, too much curdles cream."},
                    {"ingredient": "cream", "property": "emulsifies with cheese (carbonara base); splits if boiled hard."},
                    {"ingredient": "cheese", "property": "pecorino/parmesan give umami and body to the sauce."},
                ],
                "technique_knowledge": [
                    {"technique": "emulsion", "principle": "starch + fat + gentle heat hold a sauce; violent boil breaks it. Off-heat tossing prevents split."},
                    {"technique": "infusion", "principle": "steeping coffee in warm cream extracts bitter notes without brewing harshness."},
                ],
            },
            "innovation_delta": {
                "before": "Cream/cheese carbonara sauce, no coffee.",
                "after": "Cream/cheese sauce infused with a little coffee for bitter depth, over chicken.",
                "change_type": ["flavor architecture", "ingredient substitution"],
                "magnitude": 2,
            },
            "mechanistic_justification": {
                "flavor_mechanism": "Coffee's roast notes deepen a cream/cheese sauce the way cocoa deepens chili.",
                "texture_mechanism": "Gentle emulsion keeps the sauce silky; coffee adds no grit if strained.",
                "chemical_or_culinary_basis": "Cocoa-in-mole is the direct analogy; emulsions are well understood. Unproven: ideal coffee dose before 'ashtray'.",
                "strength": "medium",
            },
            "creative_hypothesis": "Infuse the cream sauce with a little coffee to add bitter depth, then combine with chicken and cheese.",
            "risk_and_constraint": {
                "risk": "Cream splits if boiled, or coffee turns the sauce ashy.",
                "tradeoff": "Less bright than lemon/zest carbonara; more bitter.",
                "failure_condition": "Sauce breaks into oil/water or tastes of burnt coffee.",
            },
        },
    },
]


# Executable, demo recipe steps per concept (4-7 concrete steps each: explicit action,
# technique, time/temperature, and doneness where it matters). Chicken recipes include the
# 74 C / 165 F safety doneness; the prompt is generic and not hard-coded to chicken.
_DEMO_STEPS: Dict[str, List[str]] = {
    "Coffee-Braised Chicken with Melted Cheese Crust": [
        "Pat the chicken dry, season it with salt and black pepper, and let it stand for 5 minutes.",
        "Heat a small oven-safe skillet over medium-high heat, add a little oil, and sear the "
        "chicken about 2 minutes per side.",
        "Lower the heat, add the brewed coffee gradually, cover, and simmer gently for 8-10 "
        "minutes; avoid high heat or the coffee turns bitter.",
        "Uncover, spoon the liquid over the chicken, and cook until the thickest part reaches "
        "74 C / 165 F.",
        "Sprinkle the cheese over the chicken and broil briefly for 1-2 minutes, watching "
        "continuously so it melts without scorching.",
        "Rest for 3 minutes before serving.",
    ],
    "Coffee-Rubbed Cheese-Stuffed Chicken Skewers": [
        "Cut the chicken into 3 cm cubes and toss with salt, black pepper, and the finely "
        "ground coffee rub.",
        "Tuck a small piece of cheese into the center of each cube, then thread the cubes onto skewers.",
        "Preheat a grill or grill pan to medium (about 200 C / 400 F).",
        "Grill the skewers 4-5 minutes per side, turning once, until the surfaces are browned "
        "and the rub is fragrant.",
        "Check the thickest piece reaches 74 C / 165 F; move to a cooler zone if the rub "
        "darkens too fast.",
        "Rest 2 minutes off the heat, then serve.",
    ],
    "Coffee-Cheese Chicken Carbonara Twist": [
        "Steep 1 tsp ground coffee in 80 ml warm cream for 5 minutes, then strain out the grounds.",
        "Cook the chicken pieces in a little oil over medium heat until opaque, about 5-6 "
        "minutes; set aside.",
        "Off the heat, whisk the coffee cream with the grated cheese into a sauce; keep it gentle "
        "so it does not split.",
        "Toss the chicken with the sauce, loosening with a splash of warm water if it is too thick.",
        "Warm through 1-2 minutes; do not boil or the emulsion will break.",
        "Serve immediately with extra grated cheese.",
    ],
}


class FakeProvider(LLMProvider):
    def __init__(
        self,
        fixed_text: str = "Fake provider response",
        fixed_structured: Optional[dict] = None,
    ) -> None:
        self.fixed_text = fixed_text
        self.fixed_structured = fixed_structured
        self.last_messages: Optional[List[Dict[str, str]]] = None
        self.last_schema: Optional[dict] = None
        self.structured_calls: int = 0
        self.chat_calls: int = 0

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        self.last_messages = messages
        self.chat_calls += 1
        return self.fixed_text

    def structured(self, messages: List[Dict[str, str]], schema: Optional[dict] = None, **kwargs: Any) -> dict:
        self.last_messages = messages
        self.last_schema = schema
        self.structured_calls += 1
        if self.fixed_structured is not None:
            return self.fixed_structured
        return {"result": self.fixed_text, "ok": True}


class DemoProvider(LLMProvider):
    """Scripted offline provider that emulates the Hy3 pipeline for demos.

    Inspects the system prompt to decide what to return:
      - ideation  -> a set of recipe concepts (with a six-stage InnovationTrace)
      - realization -> a realized recipe for the requested concept
      - CIE eval   -> a per-dimension score (1-5, canonical scale)
    """

    def __init__(self, scores: Optional[Dict[str, int]] = None) -> None:
        self.scores = dict(_DEMO_SCORES)
        if scores:
            self.scores.update(scores)
        self.structured_calls: int = 0

    def _system(self, messages: List[Dict[str, str]]) -> str:
        return messages[0]["content"] if messages else ""

    def _user(self, messages: List[Dict[str, str]]) -> str:
        return messages[1]["content"] if len(messages) > 1 else ""

    def structured(self, messages: List[Dict[str, str]], schema: Optional[dict] = None, **kwargs: Any) -> dict:
        self.structured_calls += 1
        sys = self._system(messages)
        if "Creative Ideation engine" in sys:
            return {"concepts": _DEMO_CONCEPTS}
        if "Recipe Realization engine" in sys:
            name = self._concept_name(self._user(messages)) or _DEMO_CONCEPTS[0]["concept_name"]
            concept = next((c for c in _DEMO_CONCEPTS if c["concept_name"] == name), _DEMO_CONCEPTS[0])
            return self._recipe_dict(concept)
        if "Creative Innovation Evaluation" in sys:
            m = re.search(r"key=(\w+)", self._user(messages))
            key = m.group(1) if m else "innovation_delta_quality"
            return {"score": self.scores.get(key, 4), "reason": f"{key} judged (demo)"}
        return {"score": 4.0, "reason": "demo default"}

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        # Fallback path: mirror structured() but return a JSON string.
        return json.dumps(self.structured(messages, schema=None))

    @staticmethod
    def _concept_name(user_text: str) -> Optional[str]:
        m = re.search(r"Concept name\s*:\s*(.+)", user_text)
        return m.group(1).strip() if m else None

    @staticmethod
    def _recipe_dict(concept: dict) -> dict:
        steps = _DEMO_STEPS.get(
            concept["concept_name"],
            [
                "Prep the given ingredients.",
                f"Apply the idea (preserving the creative hypothesis): {concept['core_idea']}",
                "Cook until done; rest and serve.",
            ],
        )
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
            "steps": list(steps),
            "creative_explanation": f"{concept['creative_angle']} (faithful to InnovationTrace: {concept['trace']['creative_hypothesis']})",
        }
