"""Backend pipeline orchestration (no frontend).

Full flow (canonical CIE v3 contract):
  Input Ingredients
  -> Creative Ideation              (produces a six-stage InnovationTrace + N RecipeConcepts)
  -> Stage-A CIE Evaluation         (culinary_knowledge_grounding, existing_culinary_precedent_analysis,
                                      innovation_delta_quality, mechanistic_plausibility, innovation_value)  on concepts
  -> Concept Ranking / Top-K        (default keep 2)              diversity-aware
  -> Recipe Realization             (top concepts -> full Recipes)
  -> Stage-B CIE Evaluation         (realization_quality, plan-level only)  on realized recipes
  -> Final Ranking                  (Final = direct six-dimension weighted sum via cie.scorer.total_score;
                                      NO 0.75/0.25 stage blend)  via cie.scorer
  -> Output                         (formatter / exporter)

N (num_concepts), Top-K (top_k_concepts) and final selection (top_k_final) are configurable.
All LLM calls go through an LLMProvider (Hy3 or Fake), so the whole pipeline runs offline with FakeProvider.
"""
from __future__ import annotations

from typing import List, Optional

from .llm.base import LLMProvider
from .recipe.ideation import generate_concepts
from .recipe.realization import realize_concepts
from .cie.framework import evaluate_stage_a, evaluate_stage_b, build_report
from .cie.scorer import weighted_total, rank_reports, select_top_k
from .types import Ingredient, PipelineResult, Recipe, RecipeConcept, ConceptEval, EvalReport


def run(
    provider: LLMProvider,
    ingredients: List[Ingredient],
    constraints: Optional[str] = None,
    num_concepts: int = 5,
    top_k_concepts: int = 2,
    top_k_final: int = 1,
) -> PipelineResult:
    """End-to-end creative recipe generation + two-stage CIE evaluation + selection."""
    concepts = generate_concepts(
        provider, ingredients, constraints=constraints, num_concepts=num_concepts
    )
    if not concepts:
        return PipelineResult(inputs=ingredients, concepts=[], recipes=[], reports=[])

    # Stage A — evaluate concepts; rank; keep Top-K (diversity-aware).
    concept_evals = evaluate_stage_a(provider, concepts, ctx={"constraints": constraints})
    stage_a_reports = [
        EvalReport(
            concept_name=c.concept_name,
            trace=c.trace,
            stage_a=e.scores,
            stage_b=[],
            stage_a_score=weighted_total(e.scores),
            total_score=weighted_total(e.scores),
            rank=0,
        )
        for c, e in zip(concepts, concept_evals)
    ]
    ranked_a = rank_reports(stage_a_reports)
    top_a = select_top_k(ranked_a, k=top_k_concepts)
    top_concepts: List[RecipeConcept] = [
        next(c for c in concepts if c.concept_name == r.concept_name) for r in top_a
    ]

    # Recipe Realization — realize the selected concepts.
    recipes = realize_concepts(provider, top_concepts, constraints=constraints)

    # Stage B — evaluate realized recipes (with their InnovationTrace) then combine with Stage A.
    traces = [c.trace for c in top_concepts]
    recipe_evals = evaluate_stage_b(
        provider, recipes, traces=traces, ctx={"constraints": constraints}
    )
    reports: List[EvalReport] = []
    for r, re in zip(recipes, recipe_evals):
        concept = next(c for c in top_concepts if c.concept_name == r.concept_name)
        ce = next(e for e in concept_evals if e.concept_name == r.concept_name)
        reports.append(build_report(concept, ce, r, re))
    final_reports = rank_reports(reports)

    best_report = final_reports[0] if final_reports else None
    best_recipe: Optional[Recipe] = None
    if best_report is not None:
        best_recipe = next(
            (r for r in recipes if r.concept_name == best_report.concept_name), None
        )

    # Limit the surfaced reports to top_k_final if requested (ranking already global).
    surfaced = select_top_k(final_reports, k=max(top_k_final, 1))

    return PipelineResult(
        inputs=ingredients,
        concepts=concepts,
        recipes=recipes,
        reports=surfaced,
        best_recipe=best_recipe,
        best_report=best_report,
    )
