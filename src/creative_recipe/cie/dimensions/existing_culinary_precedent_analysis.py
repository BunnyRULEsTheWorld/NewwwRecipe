"""Existing Culinary Precedent Analysis — canonical CIE v3 Stage-A dimension (weight 0.15).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json`
-> existing_culinary_precedent_analysis.

Primary trace evidence: `innovation_trace.existing_culinary_context` (stage 1).
Asks whether the CLOSEST precedents were found and whether inheritance vs. deviation is
compared accurately. Naming a whole cuisine ("Sichuan food") is not a precedent.
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_concept

SPEC = DimensionSpec(
    key="existing_culinary_precedent_analysis",
    label="Existing Culinary Precedent Analysis",
    stage=Stage.A,
    weight=0.15,
    question="是否找到最近先例并准确比较继承与偏离？",
    cognitive_mapping=(
        "Precedent retrieval and differential comparison — locate the CLOSEST existing dish(es) or "
        "technique lineage and state precisely what is INHERITED and what DEVIATES. Read "
        "`innovation_trace.existing_culinary_context.precedents` and `.relationship` as the primary "
        "evidence. A broad cuisine label is not a precedent; a fabricated precedent scores 1."
    ),
    anchors={
        1: "1｜没有给出先例，或先例是虚构的/与本概念无实际关系。",
        2: "2｜只报出大菜系或宽泛传统（'属于中式''分子料理'），无法定位到具体原型。",
        3: "3｜给出了最近原型，但继承与偏离的比较有限（未说明具体替代与差别，只说'类似但不同'）。",
        4: "4｜逐项比较继承、替换与偏离（哪一步照旧、哪一步换掉、换掉后关系如何变化）。",
        5: "5｜识别并行先例与历史脉络，并考虑替代解释（说明为何不是另一条已有路径的重复）。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_concept(target), ctx),
)
