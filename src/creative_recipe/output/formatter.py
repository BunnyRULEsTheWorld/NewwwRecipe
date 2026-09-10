"""Render a PipelineResult as human-readable Markdown / text."""
from __future__ import annotations

from typing import List

from ..types import EvalReport, InnovationTrace, PipelineResult, Recipe

_DIM_LABELS = {
    "culinary_knowledge_grounding": "Culinary Knowledge Grounding",
    "existing_culinary_precedent_analysis": "Existing Culinary Precedent Analysis",
    "innovation_delta_quality": "Innovation Delta Quality",
    "mechanistic_plausibility": "Mechanistic Plausibility",
    "innovation_value": "Innovation Value",
    "realization_quality": "Realization Quality (plan-level)",
}

# Canonical six-dimension weights (mirror cie.dimensions.WEIGHTS) for the displayed formula.
_DIM_WEIGHTS = {
    "culinary_knowledge_grounding": 0.15,
    "existing_culinary_precedent_analysis": 0.15,
    "innovation_delta_quality": 0.25,
    "mechanistic_plausibility": 0.20,
    "innovation_value": 0.15,
    "realization_quality": 0.10,
}


def _fmt_recipe_md(recipe: Recipe) -> str:
    lines = [f"### {recipe.name}", ""]
    if recipe.concept_name:
        lines.append(f"_from concept: {recipe.concept_name}_")
        lines.append("")
    lines.append("**Ingredients (hero)**")
    for i in recipe.ingredients:
        q = f" ({i.quantity})" if i.quantity else ""
        n = f"  _[{i.note}]_" if i.note else ""
        lines.append(f"- {i.name}{q}{n}")
    lines.append("")
    if recipe.seasonings:
        lines.append("**Seasonings (调料)**")
        for s in recipe.seasonings:
            q = f" ({s.quantity})" if s.quantity else ""
            n = f"  _[{s.note}]_" if s.note else ""
            lines.append(f"- {s.name}{q}{n}")
        lines.append("")
    lines.append("**Steps**")
    for n, s in enumerate(recipe.steps, 1):
        lines.append(f"{n}. {s}")
    lines.append("")
    lines.append(f"**Creative explanation**: {recipe.creative_explanation}")
    if recipe.creative_hypothesis:
        lines.append("")
        lines.append(f"_Original creative hypothesis (preserved): {recipe.creative_hypothesis}_")
    return "\n".join(lines)


def _fmt_trace_md(trace: InnovationTrace) -> str:
    eck = trace.existing_culinary_context
    iatk = trace.ingredient_and_technique_knowledge
    delta = trace.innovation_delta
    mj = trace.mechanistic_justification
    rc = trace.risk_and_constraint
    return "\n".join([
        "**InnovationTrace (six-stage)**",
        f"- Stage 1 Existing Culinary Context: precedents={eck.precedents}; relationship={eck.relationship}",
        f"- Stage 2 Ingredient & Technique Knowledge: ingredient_knowledge={iatk.ingredient_knowledge}; technique_knowledge={iatk.technique_knowledge}",
        f"- Stage 3 Innovation Delta: before={delta.before} | after={delta.after} | change_type={delta.change_type} | magnitude={delta.magnitude}",
        f"- Stage 4 Mechanistic Justification: flavor={mj.flavor_mechanism}; texture={mj.texture_mechanism}; basis={mj.chemical_or_culinary_basis}; strength={mj.strength}",
        f"- Stage 5 Creative Hypothesis: {trace.creative_hypothesis}",
        f"- Stage 6 Risk & Constraint: risk={rc.risk}; tradeoff={rc.tradeoff}; failure_condition={rc.failure_condition}",
    ])


def _fmt_scores_md(report: EvalReport) -> str:
    sa = report.stage_a_score or 0.0
    sb = report.stage_b_score or 0.0
    all_scores = list(report.stage_a) + list(report.stage_b)
    lines = [
        f"**Final CIE score**: {report.total_score:.2f} / 5  (rank #{report.rank})",
        "_Final = Σ (weight_d × score_d) over all six dimensions (canonical CIE v3 direct weighted sum; "
        "no 0.75/0.25 stage blend)_",
        "",
    ]
    lines.append("| Dimension | Weight | Score | Reason |")
    lines.append("| --- | --- | --- | --- |")
    for s in all_scores:
        w = _DIM_WEIGHTS.get(s.dimension, 0.0)
        lines.append(
            f"| {_DIM_LABELS.get(s.dimension, s.dimension)} | {w:.2f} | {s.score:.1f} | {s.reason} |"
        )
    lines.append(
        f"| **Total** | **1.00** | **{report.total_score:.2f}** | direct six-dimension weighted sum |"
    )
    lines.append("")
    lines.append(
        f"_Diagnostic only — Stage-A aggregate (5 dims): {sa:.2f} · Stage-B aggregate (1 dim): {sb:.2f}_"
    )
    return "\n".join(lines)


def format_result(result: PipelineResult) -> str:
    """Full Markdown report: best recipe, its scores, and the ranked alternatives."""
    out: List[str] = ["# Creative Recipe AI — Result", ""]
    ings = ", ".join(i.name for i in result.inputs) or "(none)"
    out.append(f"**Input ingredients**: {ings}")
    out.append("")

    if result.best_recipe:
        out.append("## Best recipe")
        out.append("")
        out.append(_fmt_recipe_md(result.best_recipe))
        out.append("")
        if result.best_report:
            out.append(_fmt_trace_md(result.best_report.trace))
            out.append("")
            out.append(_fmt_scores_md(result.best_report))
    else:
        out.append("_No recipe was produced._")

    if len(result.reports) > 1:
        out.append("")
        out.append("## All candidates (ranked)")
        out.append("")
        for r in result.reports:
            out.append(f"- #{r.rank} **{r.concept_name}** — {r.total_score:.2f}")
    return "\n".join(out)


def format_console(result: PipelineResult) -> str:
    """Compact plain-text summary for CLI / console output."""
    if not result.best_recipe:
        return "No recipe produced."
    r = result.best_recipe
    rep = result.best_report
    sa = rep.stage_a_score if rep else 0.0
    sb = rep.stage_b_score if rep else 0.0
    lines = [
        f"== {r.name} == (Final CIE {rep.total_score:.2f}/5, rank #{rep.rank})",
        f"   Stage-A {sa:.2f} (5 dims) | Stage-B {sb:.2f} (1 dim) — total is the six-dimension direct weighted sum",
        "Ingredients: " + ", ".join(i.name for i in r.ingredients),
        "Seasonings: " + (", ".join(s.name for s in r.seasonings) or "(none)"),
        "Steps:",
    ]
    lines += [f"  {n}. {s}" for n, s in enumerate(r.steps, 1)]
    lines.append("Why: " + r.creative_explanation)
    return "\n".join(lines)
