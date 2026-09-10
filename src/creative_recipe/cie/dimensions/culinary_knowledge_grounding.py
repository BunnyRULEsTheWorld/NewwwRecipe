"""Culinary Knowledge Grounding — canonical CIE v3 Stage-A dimension (weight 0.15).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json` -> culinary_knowledge_grounding.

Primary trace evidence: `innovation_trace.ingredient_and_technique_knowledge` (stage 2).
Asks whether ingredients, techniques and their culinary roles are accurate, specific and
explicitly bounded — NOT whether they sound impressive.
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_concept

SPEC = DimensionSpec(
    key="culinary_knowledge_grounding",
    label="Culinary Knowledge Grounding",
    stage=Stage.A,
    weight=0.15,
    question="材料、技术及其料理角色是否准确、具体且有边界？",
    cognitive_mapping=(
        "Domain-knowledge grounding — accuracy, specificity and explicit boundaries of the stated "
        "ingredient properties and technique principles. Read "
        "`innovation_trace.ingredient_and_technique_knowledge` as the primary evidence. Rare "
        "ingredients, brand names and the sheer NUMBER of techniques are never credit."
    ),
    anchors={
        1: "1｜与基本料理事实冲突，或捏造材料/技术属性（例如声称某食材具有它并不具备的性质）。",
        2: "2｜只罗列材料与技术名词，料理角色泛化（'提鲜''增香'），未说明其如何起作用。",
        3: "3｜主要材料的角色与物理/风味属性基本正确，但缺少条件与适用范围。",
        4: "4｜说明材料与技术之间的相互作用、生效条件与已知风险（例如浓缩会同时放大豆腥）。",
        5: "5｜知识扎实且角色精确，并主动限定证据边界——明确指出哪些属性成立、哪些未经证实。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_concept(target), ctx),
)
