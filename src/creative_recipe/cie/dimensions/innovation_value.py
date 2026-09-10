"""Innovation Value — canonical CIE v3 Stage-A dimension (weight 0.15).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json` -> innovation_value.

Primary trace evidence: `innovation_trace.innovation_delta` (magnitude is NOT value) plus the
framing in `existing_culinary_context` and `mechanistic_justification`. Asks whether the change
delivers an identifiable, proportionate edible / cultural / systemic gain — NOT mere novelty.
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_concept

SPEC = DimensionSpec(
    key="innovation_value",
    label="Innovation Value",
    stage=Stage.A,
    weight=0.15,
    question="变化是否带来可识别且与代价相称的食用、文化或系统收益？",
    cognitive_mapping=(
        "Outcome value of the proposed change — an identifiable, proportionate gain in edible "
        "experience, culture, or system behaviour. Read `innovation_trace.innovation_delta` "
        "(note: magnitude encodes SIZE of change, never value) and weigh it against "
        "`risk_and_constraint.tradeoff`. Rare ingredients and the sheer NUMBER of techniques are "
        "never credit; novelty without a gain is not value."
    ),
    anchors={
        1: "1｜无可识别收益，仅为猎奇或净损失（代价高于收益）。",
        2: "2｜有变化/传播点，但体验没有稳定提升（例：只在社交平台照片上显得新颖）。",
        3: "3｜有限、局部或仅特定场景下的提升（如只在某一菜系语境或单次场景成立）。",
        4: "4｜明显且可复用的料理价值，收益与代价相称（例：该价值可迁移到其它菜品）。",
        5: "5｜扩展了料理边界或建立了可迁移的新范式（价值可识别、可复用）。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_concept(target), ctx),
)
