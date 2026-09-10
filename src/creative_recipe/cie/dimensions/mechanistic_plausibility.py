"""Mechanistic Plausibility — canonical CIE v3 Stage-A dimension (weight 0.20).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json` -> mechanistic_plausibility.

Primary trace evidence: `innovation_trace.mechanistic_justification` (stage 4), cross-checked
against `innovation_trace.risk_and_constraint` (stage 6).
Asks whether the flavor, texture and process mechanisms hold AND are falsifiable.
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_concept

SPEC = DimensionSpec(
    key="mechanistic_plausibility",
    label="Mechanistic Plausibility",
    stage=Stage.A,
    weight=0.20,
    question="风味、质构和工艺机制是否成立且可证伪？",
    cognitive_mapping=(
        "Mechanistic reasoning and falsifiability — read "
        "`innovation_trace.mechanistic_justification` (flavor / texture / chemical-or-culinary "
        "basis / self-assessed strength) and cross-check `innovation_trace.risk_and_constraint`. "
        "Slogans such as 'they share aroma molecules' with no stated condition are NOT mechanisms. "
        "Top scores require multiple consistent mechanisms, explicit conditions, and a stated "
        "counterfactual or failure condition that could refute the claim."
    ),
    anchors={
        1: "1｜机制明显矛盾，或完全没有给出机制，只有结论。",
        2: "2｜只有口号式说法或'共享分子'套话（例：只说'它们共享分子'却无任何机制与生效条件、无边界）。",
        3: "3｜至少一个机制成立（风味或质构），但约束条件不完整。",
        4: "4｜风味与质构机制都完整成立，并指出主要风险与生效条件。",
        5: "5｜多机制彼此一致、条件明确，并给出可执行的反事实或验证方式（可被证伪）。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_concept(target), ctx),
)
