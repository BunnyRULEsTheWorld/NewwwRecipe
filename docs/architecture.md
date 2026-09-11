# Architecture

Creative Recipe AI is a backend pipeline (no frontend in MVP). The **CIE framework is the
independent core**; the LLM (Hy3) is an isolated, swappable adapter.

## Pipeline

```
Input Ingredients
  -> Ingredient Understanding
  -> Creative Ideation              (produces a six-stage InnovationTrace + N RecipeConcepts)
  -> Stage-A CIE Evaluation         (culinary_knowledge_grounding, existing_culinary_precedent_analysis,
                                      innovation_delta_quality, mechanistic_plausibility, innovation_value)
  -> Concept Ranking / Top-K        (default keep 2, diversity-aware)
  -> Recipe Realization             (top concepts -> full Recipes)
  -> Stage-B CIE Evaluation         (realization_quality, plan-level estimate only)
  -> Final Ranking                  (Final = direct six-dimension weighted sum; no 0.75/0.25 stage blend)
  -> Output                         (Markdown / JSON)
```

## Web frontend / API adapter flow

The interactive fridge UI is a thin layer over the existing backend. No recipe-generation, scoring or ranking logic was duplicated in the frontend.

The ingredient-selection experience follows an "open fridge" metaphor with three progressive states:

1. **Landing** — the closed refrigerator dominates the view and is the single interactive control.
2. **Ingredient selection** — the fridge opens; controls (search, categories, basket, pagination) live outside the fridge while ingredient cutouts are picked from inside the open refrigerator.
3. **Preferences** — once at least two ingredients are chosen, a compact preference panel appears (cuisine, flavor, cooking time, allergies, craving) before generating the recipe.

```text
React + TypeScript (web/src)
  -> Vite dev proxy / FastAPI static-files mount
    -> FastAPI adapter (src/creative_recipe/web/)
      -> Config + Pipeline (pipeline.py)
        -> Creative Ideation (recipe/ideation.py) — six-stage Innovation Trace
        -> Recipe Realization (recipe/realization.py)
        -> CIE v3 scorer (cie/scorer.py + cie/dimensions/)
      -> JSON response { recipe, concept, trace, cie, meta }
```

Adapter responsibilities:

- `ingredient_catalog.py` — serve the canonical 65-ingredient manifest and validate on-disk assets.
- `models.py` — Pydantic request/response models for the canonical CIE v3 contract.
- `service.py` — map the HTTP request to the existing `Config` / `Pipeline` objects and rank concepts.
- `app.py` — FastAPI app, health check, `/api/ingredients`, `/api/recipes/generate`, static asset mounts, CORS.

The canonical CIE v3 contract returned by the API includes the six dimension scores, their canonical weights (15/15/25/20/15/10), and a single direct weighted total produced by the backend scorer. `stage_a_score`/`stage_b_score` are still present as secondary diagnostics but are **not** used as the primary total in either backend ranking or frontend display.

## Module map

See README → "Project Structure". Key packages:

- `llm/` — `LLMProvider` (abstract) · `Hy3LLMClient` (OpenAI-compatible) · `FakeProvider` (offline).
- `recipe/` — `ideation.py` (Creative Ideation) · `realization.py` (Recipe Realization).
- `cie/` — `framework.py` (Stage-A/B eval + report) · `dimensions/` (six self-contained specs)
  · `scorer.py` (weighted aggregation + ranking + Top-K) · `prompts.py` (LLM-as-judge prompts).
- `output/` — `formatter.py` (Markdown/console) · `exporter.py` (JSON).
- `interfaces/` — `feedback.py` (abstract `FeedbackSink`, MVP only an interface).

## Key design decisions

1. **CIE is the core module** (`src/creative_recipe/cie/`). Recipe generation/selection are its consumers.
2. **Hy3 is an isolated adapter** (`src/creative_recipe/llm/`): business code depends only on the
   `LLMProvider` interface; swapping models never touches domain logic.
3. **InnovationTrace is an explicit product of Creative Ideation**, consumed by CIE as review
   evidence — it is *not* generated post-hoc. It is auditable, not a claim about internal thinking.
4. **API key only from environment** (`HY3_API_KEY`); `HY3_BASE_URL` is configurable, never hardcoded.
5. **Structured output + fallback**: every LLM call uses JSON schema; on failure it falls back to
   `chat()` + robust JSON extraction (bare JSON / fenced ```` ```json ```` / first–last braces).
6. **No training / fine-tuning**: the system is pure prompt + inference (LLM-as-judge for evaluation).
7. **MVP scope**: storage/leaderboard/image generation are deferred; only a `feedback` interface is
   kept as an extension point. Benchmark case sets live under `data/` (curated set tracked; runtime
   / private dirs git-ignored).

## Extension points

- New model → new `LLMProvider`.
- New CIE dimension → new file in `cie/dimensions/` + register in `cie/dimensions/__init__.py`.
- Weight calibration → `WEIGHTS` in `cie/dimensions/__init__.py`, later learned from feedback.
- Image generation / leaderboard → add interfaces under `interfaces/` and wire into `pipeline.py`.
