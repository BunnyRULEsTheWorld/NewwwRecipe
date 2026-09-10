# CIE Framework — Design & Rubrics

> ⚠️ **DEPRECATED — historical design (pre-CIE-v3 alignment).**
>
> This document describes the **pre-alignment** application design: a four-field `InnovationTrace`
> (`ingredient_knowledge` / `concept_bridge` / `creative_hypothesis` / `preliminary_feasibility_reasoning`)
> and an older six-dimension set (`ingredient_intelligence` / `flavor_bridge_quality` / `creative_leap` /
> `exploration_value` / `culinary_feasibility` / `communication_quality`) combined with a
> `0.75 × Stage-A + 0.25 × Stage-B` blend.
>
> The application backend has since been **aligned to the canonical CIE v3 contract** (see
> `docs/cie_framework_v3.md` and `PROJECT_STATE.md` §2.1). The live contract is now:
> - six-stage `InnovationTrace` (field-compatible with `CIE-Culinary-Bench/schema/cie_sample.schema.json`);
> - six dimensions `culinary_knowledge_grounding` / `existing_culinary_precedent_analysis` /
>   `innovation_delta_quality` / `mechanistic_plausibility` / `innovation_value` / `realization_quality`
>   with weights 0.15 / 0.15 / 0.25 / 0.20 / 0.15 / 0.10;
> - final score = **direct six-dimension weighted sum** (`cie.scorer.total_score`), no stage blend.
>
> The implementation of record lives under `src/creative_recipe/`; this file is kept only as a
> historical reference.

---

The **Creative Innovation Evaluation (CIE)** framework is the core evaluation engine of Creative
Recipe AI. It is **two-stage, six-dimension**, and framed as a **neural-science-inspired
cognitive-process mapping** — deliberately *not* a claim about specific brain regions, and
*not* about the model's private internal reasoning.

> ⚠️ The InnovationTrace produced during Creative Ideation is an **explicit, auditable reasoning
> artifact** the LLM is asked to emit. It makes the creative process transparent and reviewable.
> It does **not** equal the model's true internal thought process.

---

## InnovationTrace (explicit, auditable — NOT the model's internal thought)

Produced in **Creative Ideation**, used as review evidence in Stage A:

1. **Ingredient Knowledge** — what is understood about the given ingredients (properties, function, potential).
2. **Concept Bridge** — how the ingredients are linked into one coherent concept.
3. **Creative Hypothesis** — the novel idea being proposed (a non-obvious combination or technique).
4. **Preliminary Feasibility Reasoning** — an early check that the idea can actually be cooked.

---

## Stage A — evaluated on the RecipeConcept (before realization)

| Dimension | Weight | Cognitive-process mapping |
|-----------|--------|---------------------------|
| Ingredient Intelligence | 0.15 | Concept activation & analogy over ingredient semantics |
| Flavor Bridge Quality   | 0.25 | Cross-ingredient flavor association & pairing |
| Creative Leap           | 0.20 | Constrained divergent thinking: novel combination that stays conceptually coherent |
| Exploration Value       | 0.15 | Exploratory search / option-generation fluency |

### Five-band rubric (inter-rater reliable)

Every dimension is scored on a **1–10** scale using **five explicit bands**. Each band names the
*concrete, observable behavior* that places a target in it — never vague praise. Two independent
evaluators applying these anchors should land within **±1 point**.

| Band | Meaning |
|------|---------|
| **1–2** | 明确低质量表现 — clearly low-quality behavior |
| **3–4** | 较弱表现 — weak behavior |
| **5–6** | 中等表现 — moderate behavior |
| **7–8** | 高质量表现 — high-quality behavior |
| **9–10** | 专家级表现 — expert-level behavior |

**Ingredient Intelligence** — concept activation & analogy
- 1-2: treats ingredients as generic labels; factual errors; substitutions that break the dish.
- 3-4: only names the most basic role (e.g. "chicken is meat"); generic substitution talk.
- 5-6: names 1-2 properties correctly; one reasonable substitution/complement, shallow depth.
- 7-8: describes multiple ingredients' properties + functional roles; a justified non-obvious substitute.
- 9-10: characterizes every given ingredient's properties/complementarity; proves a minimal viable combo.

**Flavor Bridge Quality** — cross-ingredient flavor association & pairing
*(Mandatory: explain at least one connection among taste / aroma / texture / cooking mechanism.)*
- 1-2: connection missing, contradictory, or unexplained; conflicting flavors with no relief.
- 3-4: "they're both tasty" only; no mechanism; generic "East-meets-West".
- 5-6: one connection named (e.g. coffee's bitterness softened by cheese fat) but single-dimension, shallow.
- 7-8: ≥2 mechanisms explained (taste: bitter×umami; texture: crisp×soft; or coffee reducing to a glaze).
- 9-10: ≥2 mutually-reinforcing connections; names which one is "the bridge"; verifiable by tasting.

**Creative Leap** — constrained divergent thinking (novel yet coherent, not mere deviation)
*(Mandatory: name the closest existing dish(es), state the novelty difference, argue why NOT random.)*
- 1-2: fully conventional (e.g. tomato-egg stir-fry) or random splicing with no rationale; novelty only for shock.
- 3-4: slight novelty but reducible to a known variant; difference is "just a renamed dish".
- 5-6: a clearly different combo, but weak "why not random" argument ("I think it works").
- 7-8: names the closest existing dish; states concrete differences (ingredient/technique/concept); non-random rationale from flavor/function constraints.
- 9-10: anchors 1-2 closest dishes, contrasts each difference; proves constraint-driven (not random); shows perceptible value gain.

**Exploration Value** — exploratory search / fluency
- 1-2: concepts are reworded copies of one idea; no other region of the space touched.
- 3-4: 2 similar angles (e.g. two seasoned braises); no cross-cuisine/technique.
- 5-6: 2-3 distinct angles (roast / cure / sauce) but within one cuisine.
- 7-8: cross-cuisine or cross-technique exploration; angles clearly differ, all grounded in the given ingredients.
- 9-10: covers orthogonal dimensions (technique×cuisine×presentation); each concept opens a unique subspace; maximizes use of given ingredients.

---

## Stage B — evaluated on the realized Recipe (after realization)

| Dimension | Weight | Cognitive-process mapping |
|-----------|--------|---------------------------|
| Culinary Feasibility | 0.15 | Procedural planning / action feasibility |
| Communication Quality | 0.10 | Linguistic encoding / narrative clarity |

### Five-band rubric (1-2 / 3-4 / 5-6 / 7-8 / 9-10)

**Culinary Feasibility** — procedural planning
- 1-2: missing key step / contradictory order / impossible technique.
- 3-4: doable but gaps (no temp/time); vague order ("stir a bit").
- 5-6: steps complete & ordered but timing/heat vague ("medium heat a few min").
- 7-8: concrete, ordered, reproducible (temp/time/state cue); ordinary equipment.
- 9-10: reproducible to the detail (prep, heat thresholds, failure signs); honors the trace's feasibility reasoning; matching yield/time.

**Communication Quality** — linguistic encoding
- 1-2: name unrelated to dish; explanation too vague to infer intent.
- 3-4: plain but understandable name; explanation only restates steps, no "why".
- 5-6: name names core ingredients; explanation states the method but not the creative point.
- 7-8: memorable, accurate name; explanation says where the idea came from and why it works.
- 9-10: attractive yet accurate name; one-two sentences link bridge + novelty + feasibility into a coherent narrative.

---

## Creative Leap — definition

Achieve an **effective novel combination while preserving conceptual coherence** — *not* mere
deviation from convention. A high score rewards purpose and fit, not weirdness for its own sake.

---

## Final scoring

Each dimension is scored 1–10 by an **LLM-as-judge** (Hy3) using the rubric above; scoring uses
structured JSON output and falls back to chat + JSON extraction on failure.

Scoring is **two-stage**, then blended:

1. **Stage-A Innovation Score** — the weights-normalized average of the four Stage-A dimensions
   (II / FBQ / CL / EV). This selects Top-K concepts (diversity-aware, default K=2).
2. **Stage-B Realization Score** — the weights-normalized average of the two Stage-B dimensions
   (CF / CQ), evaluated on the realized recipes.
3. **Final blend** — the core contribution of this project is *innovation evaluation*, so Stage A
   dominates:

```
FINAL_STAGE_WEIGHTS = {"stage_a": 0.75, "stage_b": 0.25}

Final Score = 0.75 × Stage-A Innovation Score + 0.25 × Stage-B Realization Score
```

The six-dimension per-stage weights (summing to 1.0 within each stage) come from
`cie/dimensions/__init__.py::WEIGHTS`; the cross-stage blend `FINAL_STAGE_WEIGHTS` lives in
`cie/scorer.py` and is the single source of truth.

- **Final Ranking** orders candidates by the blended Final Score; Top-1 is the chosen best.

---

## Extensibility

- **Add a dimension**: create `src/creative_recipe/cie/dimensions/<key>.py` exporting a `SPEC`
  (`DimensionSpec` with key/label/stage/weight/cognitive_mapping/anchors/build_messages`), then
  register it in `cie/dimensions/__init__.py` (REGISTRY + STAGE_*_KEYS) and add its weight to `WEIGHTS`.
- **Calibrate weights**: the default weights live in `cie/dimensions/__init__.py::WEIGHTS`. Future
  work can learn weights from human feedback collected via `interfaces/feedback.py`.
- **Swap the judge model**: implement a new `LLMProvider` (mirror `llm/hy3.py`); no business code changes.
