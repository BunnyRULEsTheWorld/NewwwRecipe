"""Realization Quality — canonical CIE v3 Stage-B dimension (weight 0.10).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json` -> realization_quality.

APPLICATION-SIDE INTERPRETATION (per the CIE v3 alignment contract, section 6):
    In this application, `realization_quality` is ONLY a PLAN-LEVEL estimate of whether the
    generated recipe is complete, internally consistent, constraint-satisfying, and
    plan-level implementable. It is explicitly NOT a claim of:
      - actual cooking verification,
      - human tasting / panel validation,
      - chef endorsement, or
      - long-term, repeated empirical experimentation.
    The canonical benchmark rubric's upper anchors assume real evidence; this application must
    NOT award those on the strength of pretty reasoning alone. Concretely: levels 1-4 describe the
    RIGOR OF THE PLAN; the engine (`evaluate_stage_b`) UNCONDITIONALLY caps realization_quality at 4,
    so this application never produces a 5. Level 5 is RESERVED for a FUTURE independent, structured,
    trusted empirical evaluation pipeline (real cooking, tasting/panel validation, or repeated
    real-world verification) — it is intentionally NOT reachable from the current application, which
    has no trusted empirical-evidence input channel. The anchors below describe plan-level rigor,
    with 5 explicitly documented as reserved/future-only.

Primary trace evidence: `innovation_trace.creative_hypothesis` + `risk_and_constraint`
(faithfulness of the realized recipe to the proposed idea and its stated failure condition).
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_recipe

SPEC = DimensionSpec(
    key="realization_quality",
    label="Realization Quality (plan-level)",
    stage=Stage.B,
    weight=0.10,
    question="生成的菜谱方案是否完整、一致、满足约束且计划级可实现（仅方案层估计，非实际验证）？",
    cognitive_mapping=(
        "PLAN-LEVEL realization quality of the generated recipe: completeness of steps, internal "
        "consistency, satisfaction of stated constraints, and plan-level implementability. It is "
        "NOT actual cooking / tasting / chef validation / longitudinal proof. Check faithfulness "
        "to `innovation_trace.creative_hypothesis` and whether `risk_and_constraint.failure_condition` "
        "is plausibly avoided by the plan. Levels 1-4 describe plan-level rigor; the engine UNCONDITIONALLY "
        "caps realization_quality at 4, so level 5 is never produced by this application — it is reserved "
        "for a future independent empirical pipeline."
    ),
    anchors={
        1: "1｜缺少关键步骤/材料，无法照做；或与原始创新假设明显冲突。",
        2: "2｜主体可照做，但步骤含糊、约束未满足，或创新点未在方案中体现。",
        3: "3｜步骤基本完整可执行、约束大体满足，但部分细节欠明确。",
        4: "4｜步骤完整一致、约束满足、忠实体现创新假设，计划级可行性高（无实际烹饪/品尝验证时的最高等级）。",
        5: "5｜为未来独立、结构化、可信的实证评估管线预留（真实烹饪、品尝/专家评审、重复实证）。当前应用无可信实证输入通道，运行结果不会产生 5 分；realization_quality 由引擎无条件封顶为 4（方案层，非实证）。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_recipe(target, ctx.get("trace") if ctx else None), ctx),
)
