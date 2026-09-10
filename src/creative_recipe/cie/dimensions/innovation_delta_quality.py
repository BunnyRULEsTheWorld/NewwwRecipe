"""Innovation Delta Quality — canonical CIE v3 Stage-A dimension (weight 0.25, highest).

Canonical source: `CIE-Culinary-Bench/schema/scoring_rubric.json` -> innovation_delta_quality.

Primary trace evidence: `innovation_trace.innovation_delta` (stage 3).
Asks whether the before -> after change produces a MEANINGFUL culinary role or structural
change. `magnitude` expresses size of change only and must never be read as value.
"""
from ...types import Stage
from . import DimensionSpec
from ..prompts import build_eval_messages, format_concept

SPEC = DimensionSpec(
    key="innovation_delta_quality",
    label="Innovation Delta Quality",
    stage=Stage.A,
    weight=0.25,
    question="before→after 的变化是否产生有意义的料理角色或结构变化？",
    cognitive_mapping=(
        "Delta quality — judge the SUBSTANCE of the before -> after change recorded in "
        "`innovation_trace.innovation_delta`. Decoration, stacking more of the same category, or "
        "pure technique display is weak. A high score requires a changed culinary ROLE, STRUCTURE "
        "or technique PURPOSE. `magnitude` is the size of the change, NOT its value: a magnitude-5 "
        "change can still score low here."
    ),
    anchors={
        1: "1｜没有可辨识的变化，或只是改了名字/摆盘称呼（纯命名创新）。",
        2: "2｜装饰性变化、同类食材堆叠，或只为展示技术而加技术。",
        3: "3｜有意义的局部替换或改良（例：替换一种食材的呈现，但整体角色结构不变）。",
        4: "4｜关键食材角色、菜品结构或技法用途发生改变，形成新的组织方式。",
        5: "5｜形成可迁移的新能力或范式——该变化可被复用到其它菜品或体系上。",
    },
    build_messages=lambda target, ctx=None: build_eval_messages(SPEC, format_concept(target), ctx),
)
