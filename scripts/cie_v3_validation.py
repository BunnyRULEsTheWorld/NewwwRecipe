"""CIE v3 VALIDATION EXPERIMENT (temporary script — does NOT modify src/).

Purpose
-------
Validate whether an "AI culinary-innovation evaluation framework" can RANK ideas by genuine
innovation value, NOT by strangeness:

    Expected: High-value innovation  >  Partial innovation  >  Ordinary recipe
    NOT:      Strange idea           >  Normal idea

Core hypothesis encoded in the rubric:
    Novelty != Innovation.
    True innovation needs ALL of:
      (1) a clear new change vs existing cuisine,
      (2) that change backed by culinary knowledge / science / historical precedent,
      (3) that change improves flavor / texture / experience / expression value.

What this script does
--------------------
1. Defines THREE fixed cases (Recipe Concept + 5-part Culinary Innovation Reasoning Trace):
     Case A (Low)    : ordinary tomato-cheese chicken        (classic combo, ~no delta)
     Case B (Medium) : Mochicken Bake (coffee+chicken+cheese) (partial technique bridge)
     Case C (High)   : coffee-cured & smoke-roasted chicken   (role shift + technique + flavor arch)
   The traces are authored by the experiment designer so the JUDGE (Hy3) is tested on ranking,
   not on generating the ideas.
2. Asks real Hy3 (LLM-as-judge, via the existing Hy3LLMClient) to score each case on the CIE v3
   six dimensions + a structured Innovation Delta analysis.
3. Computes weighted totals, ranks, and compares Expected vs Actual.

Run (from project root, .env present):
    PYTHONPATH=src python scripts/cie_v3_validation.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from creative_recipe.config import Config  # noqa: E402
from creative_recipe.llm.hy3 import Hy3LLMClient  # noqa: E402

OUT_PATH = os.path.join(ROOT, "examples", "cie_v3_validation_result.json")

# ------------------------------------------------------------------------------------------
# CIE v3 rubric (weights sum to 1.0)
# ------------------------------------------------------------------------------------------
V3_DIMENSIONS: Dict[str, dict] = {
    "culinary_knowledge_grounding": {
        "label": "Culinary Knowledge Grounding",
        "weight": 0.15,
        "brief": "AI 是否真正理解食材、技法、风味机制；低分只描述表面属性，高分解释为何某种结构/技术能支持创新。",
    },
    "existing_culinary_precedent": {
        "label": "Existing Culinary Precedent Analysis",
        "weight": 0.15,
        "brief": "能否把创新放入已有料理空间比较：最接近哪些已有料理？相比新增了什么？防止编造'从未存在'的故事得高分。",
    },
    "innovation_delta_quality": {
        "label": "Innovation Delta Quality and Magnitude",
        "weight": 0.25,
        "brief": ("核心维度。评价 A.改变类型(角色迁移/技法/风味结构/口感/体验) B.变化是否真正改变体验 C.变化幅度。"
                  "注意：幅度不是越大越好；若 Culinary Knowledge Grounding 不足(评分<5)，本维度最高不得超过6分。"),
    },
    "mechanistic_plausibility": {
        "label": "Mechanistic Plausibility",
        "weight": 0.20,
        "brief": "创新是否有可靠依据：风味化学、烹饪机制、厨艺经验、已有 culinary evidence。禁止'因为很搭/因为少见'这类无依据解释。",
    },
    "innovation_value_exploration": {
        "label": "Innovation Value / Exploration",
        "weight": 0.15,
        "brief": "是否带来价值(更好味觉/新口感/新体验/更好食材利用)，而非'更奇怪'。",
    },
    "realization_quality": {
        "label": "Realization Quality",
        "weight": 0.10,
        "brief": "若落地：做法是否合理、可执行、表达清楚。",
    },
}


# ------------------------------------------------------------------------------------------
# Fixed experimental cases (authored traces — the judge evaluates these, it does not write them)
# ------------------------------------------------------------------------------------------
CASES: List[dict] = [
    {
        "case_id": "A",
        "level": "Low Innovation",
        "concept_name": "番茄芝士焗鸡 (Tomato-Cheese Baked Chicken)",
        "ingredients": ["chicken", "tomato", "cheese"],
        "trace": {
            "existing_culinary_context": (
                "建立在大量已有料理上：chicken parmigiana(意式番茄芝士鸡)、caprese(卡布里沙拉)、"
                "千层面、番茄+芝士+蛋白 是 ubiquitous 经典组合。无需寻找罕见 precedent，因为本身即经典。"
            ),
            "innovation_delta": (
                "几乎无变化。只是将三种经典伴侣组合后烘焙。属于经典重组，没有 Ingredient Role Shift、"
                "没有 Technique Innovation、没有 Flavor Architecture 变化。类似 'coffee beef -> coffee chicken' 的"
                "纯蛋白替换思路，但这里连替换都没有，只是常规组合。"
            ),
            "mechanistic_justification": (
                "番茄酸度平衡芝士脂肪、芝士提供 umami 与美拉德上色、鸡肉提供蛋白——全是教科书级已知机制，"
                "不构成任何新依据。"
            ),
            "creative_hypothesis": "制作一道家常美味烤鸡。没有提出任何新体验目标。",
            "risk_and_constraint": "芝士过热焦化；番茄出水稀释酱汁。属常规烹饪风险，无任何针对'创新'的约束。",
        },
    },
    {
        "case_id": "B",
        "level": "Medium Innovation",
        "concept_name": "Cafe Pollo Melt (咖啡鸡肉焗)",
        "ingredients": ["chicken", "coffee", "cheese"],
        "trace": {
            "existing_culinary_context": (
                "precedent: coffee BBQ sauce(如咖啡可乐肋排)、coffee-rubbed brisket、coffee-glazed meats、"
                "咖啡烤肉/咖啡卤汁。咖啡用于肉类的 savory 用法已有先例。"
            ),
            "innovation_delta": (
                "将咖啡收汁(reduction)为 savory glaze 涂于鸡肉，再覆熔芝士。属于 Technique bridge("
                "reduction glaze) + 有限的 Ingredient Role Shift(咖啡从饮品 -> glaze)。但整体框架仍是 "
                "melt/焗，变化有限，不是全新料理结构。"
            ),
            "mechanistic_justification": (
                "咖啡 simmer 8-10min 蒸发浓缩成浆(water evaporation, concentration)，刷涂附着于鸡肉；"
                "芝士 broil 融化(thermal softening / fat rendering)。机制物理成立。"
            ),
            "creative_hypothesis": (
                "将咖啡烘焙香迁移到肉类，形成 bitter-savory-comfort 的新感官组合体验。"
            ),
            "risk_and_constraint": (
                "咖啡浓度过高产生苦味，需控制比例；芝士过热焦化；技法(收汁/刷涂/融化)标准但需控时。"
            ),
        },
    },
    {
        "case_id": "C",
        "level": "High Innovation",
        "concept_name": "咖啡盐渍烟熏鸡 (Coffee-Cured Smoke-Roasted Chicken)",
        "ingredients": ["chicken", "coffee", "salt", "tea(for smoke)"],
        "trace": {
            "existing_culinary_context": (
                "precedent: coffee-cured meats(咖啡腌培根/咖啡腌牛排, 如 NYT coffee-cured bacon)、"
                "中式樟茶鸭(tea-smoked duck)、salt curing/盐渍法、盐曲。咖啡用于腌渍与烟熏的 savory 用法"
                "在成熟菜系中已有验证。"
            ),
            "innovation_delta": (
                "三类变化叠加：(1) Ingredient Role Shift——咖啡从饮品/glaze 变为腌渍与风味固定剂"
                "(curing / flavor-fixative)，深入蛋白基质而非仅表面；(2) Technique Innovation——将"
                "咖啡腌渍 + 茶熏烤 两种成熟技法组合成新流程(coffee brine cure + tea-smoke roast)；"
                "(3) Flavor Architecture Innovation——构建三层结构：腌渍 umami + 咖啡烘焙芳香"
                "(melanoidins/roast aromatics) + 烟熏酚类(guaiacol)，形成'在咖啡炭火上烤'的 savory 体验"
                "而无液态咖啡。"
            ),
            "mechanistic_justification": (
                "咖啡 melanoidins 与肉类美拉德路径共享，腌渍时咖啡因/绿原酸作为风味载体渗透蛋白；"
                "烟熏酚类(guaiacol, syringol)与脂肪结合固定香气；盐渍使表面蛋白变性利于上色与保水；"
                "已有 culinary evidence：咖啡腌培根与樟茶鸭各自验证可行，本方案是两者机制的可辩护组合。"
            ),
            "creative_hypothesis": (
                "把咖啡的烘焙香通过腌渍+烟熏迁移进蛋白基质，创造'仿佛在咖啡炭火上炙烤'的新型 savory 体验，"
                "而非简单浇咖啡汁。"
            ),
            "risk_and_constraint": (
                "腌渍过久 -> 过咸；咖啡粉直接烤易焦 -> 用浓缩液/粗粉控制；烟熏时间需控防苦；需低温慢熏。"
                "优秀创新明确知道自身限制。"
            ),
        },
    },
]


# ------------------------------------------------------------------------------------------
# Judge prompt + schema
# ------------------------------------------------------------------------------------------
def build_case_block(case: dict) -> str:
    t = case["trace"]
    return (
        f"CASE: {case['case_id']} ({case['level']})\n"
        f"CONCEPT: {case['concept_name']}\n"
        f"INGREDIENTS: {', '.join(case['ingredients'])}\n\n"
        "CULINARY INNOVATION REASONING TRACE:\n"
        f"  1. Existing Culinary Context : {t['existing_culinary_context']}\n"
        f"  2. Innovation Delta          : {t['innovation_delta']}\n"
        f"  3. Mechanistic Justification : {t['mechanistic_justification']}\n"
        f"  4. Creative Hypothesis       : {t['creative_hypothesis']}\n"
        f"  5. Risk and Constraint       : {t['risk_and_constraint']}\n"
    )


def build_judge_messages(case_block: str) -> List[dict]:
    system = (
        "你是资深料理创新评审。请按 CIE v3 rubric 评价一个 'Recipe Concept + Culinary Innovation "
        "Reasoning Trace'（不是最终菜谱）。对每个维度给 1-10 整数分与基于可追溯事实的简洁理由（禁止空泛吹捧）。\n"
        "关键原则：Novelty(新颖) != Innovation(创新)。真正创新须同时满足：(1)相对已有料理有明确新变化；"
        "(2)该变化有料理知识/科学机制/历史案例支持；(3)该变化提升风味/口感/体验/表达价值。\n"
        "对 Innovation Delta Quality 维度：若 Culinary Knowledge Grounding 评分 <5，则 Innovation Delta "
        "最高不得超过 6 分。变化幅度不是越大越好——随机堆十种陌生食材幅度高但 Grounding 低，不应高分；"
        "有效创新 = 适度新颖变化 + 强机制支持。\n"
        "返回严格 JSON，不要多余文字。"
    )
    dims_text = "\n".join(
        f"- {k}: {m['label']} ({m['weight']*100:.0f}%)\n  {m['brief']}"
        for k, m in V3_DIMENSIONS.items()
    )
    user = (
        f"{case_block}\n"
        "请评价以下六个维度（都返回 score 1-10 + reason）：\n"
        f"{dims_text}\n\n"
        "并额外返回 Innovation Delta 详细分析对象，包含：\n"
        "  innovation_type   : 变化类型(如 Ingredient Role Shift / Technique Innovation / "
        "Flavor Architecture Innovation / Texture Innovation / Presentation-Experience Innovation / None)\n"
        "  existing_precedent: 最接近的已有料理\n"
        "  before_state      : 变化前的料理状态\n"
        "  after_state       : 变化后的料理状态\n"
        "  magnitude_score   : 变化幅度 1-10\n"
        "  value_gain        : 该变化带来的价值(味觉/口感/体验/表达)\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_judge_schema() -> dict:
    dim_props = {
        "score": {"type": "integer", "minimum": 1, "maximum": 10},
        "reason": {"type": "string"},
    }
    properties: Dict[str, dict] = {}
    required: List[str] = []
    for key in V3_DIMENSIONS:
        properties[key] = {"type": "object", "properties": dim_props, "required": ["score", "reason"]}
        required.append(key)

    delta_props = {
        "innovation_type": {"type": "string"},
        "existing_precedent": {"type": "string"},
        "before_state": {"type": "string"},
        "after_state": {"type": "string"},
        "magnitude_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "value_gain": {"type": "string"},
    }
    properties["innovation_delta_analysis"] = {
        "type": "object",
        "properties": delta_props,
        "required": list(delta_props.keys()),
    }
    required.append("innovation_delta_analysis")

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "cie_v3_eval",
            "strict": True,
            "schema": {"type": "object", "properties": properties, "required": required},
        },
    }


def call_judge(provider: Hy3LLMClient, case_block: str) -> dict:
    messages = build_judge_messages(case_block)
    schema = build_judge_schema()
    try:
        return provider.structured(messages, schema=schema)
    except Exception:
        # Fallback: plain chat + extract first JSON object.
        text = provider.chat(messages)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def weighted_total(scores: Dict[str, dict]) -> float:
    total = 0.0
    for key, meta in V3_DIMENSIONS.items():
        s = scores.get(key, {}).get("score", 0)
        total += (s or 0) * meta["weight"]
    return round(total, 3)


def main() -> None:
    provider = Hy3LLMClient.from_env()  # reads .env; no change to src/

    results = []
    for case in CASES:
        case_block = build_case_block(case)
        print("=" * 78)
        print(f"CASE {case['case_id']} — {case['level']}: {case['concept_name']}")
        print("=" * 78)
        print("\n[1] INNOVATION TRACE (evaluated object)\n")
        print(case_block)

        eval_result = call_judge(provider, case_block)

        print("[2] SIX-DIMENSION SCORES (1-10)\n")
        for key, meta in V3_DIMENSIONS.items():
            entry = eval_result.get(key, {})
            print(f"  [{meta['weight']*100:>2.0f}%] {meta['label']}: {entry.get('score')}/10")
            print(f"         reason: {entry.get('reason')}\n")

        delta = eval_result.get("innovation_delta_analysis", {})
        print("[3] INNOVATION DELTA ANALYSIS")
        print(f"  innovation_type   : {delta.get('innovation_type')}")
        print(f"  existing_precedent: {delta.get('existing_precedent')}")
        print(f"  before_state      : {delta.get('before_state')}")
        print(f"  after_state       : {delta.get('after_state')}")
        print(f"  magnitude_score   : {delta.get('magnitude_score')}")
        print(f"  value_gain        : {delta.get('value_gain')}\n")

        wt = weighted_total(eval_result)
        print(f"  >>> V3 WEIGHTED TOTAL = {wt:.2f} / 10\n")

        results.append({
            "case_id": case["case_id"],
            "level": case["level"],
            "concept_name": case["concept_name"],
            "scores": {k: eval_result.get(k) for k in V3_DIMENSIONS},
            "innovation_delta_analysis": delta,
            "weighted_total": wt,
        })

    # Rank by weighted total (desc = best).
    ranked = sorted(results, key=lambda r: r["weighted_total"], reverse=True)
    print("=" * 78)
    print("RANKING (by V3 weighted total)")
    print("=" * 78)
    for i, r in enumerate(ranked, 1):
        print(f"  {i}. Case {r['case_id']} ({r['level']}) — {r['weighted_total']:.2f}")

    print("\nEXPECTED ranking:  C (High) > B (Medium) > A (Low)")
    actual_order = " > ".join(f"{r['case_id']}({r['level']})" for r in ranked)
    print(f"ACTUAL   ranking:  {actual_order}")

    ok = [r["case_id"] for r in ranked] == ["C", "B", "A"]
    if ok:
        print("\nRESULT: PASS — CIE v3 correctly ranked genuine innovation above partial and ordinary.")
    else:
        print("\nRESULT: MISMATCH — CIE v3 failed to separate true innovation. Diagnosis:")
        print("  - If A > B: rubric rewards 'classic correctness' too much / delta penalty too weak.")
        print("  - If B > C or A > C: judge treats familiarity/feasibility as innovation, or cannot")
        print("    credit role-shift + technique-combo + flavor-architecture stacking.")
        print("  - Re-examine whether Dimension 3 cap (grounding<5 -> delta<=6) and precedence")
        print("    analysis are actually being applied by the judge.")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "rubric": "cie_v3 (proposed, not in src/)",
                "dimensions": {k: {"label": V3_DIMENSIONS[k]["label"],
                                   "weight": V3_DIMENSIONS[k]["weight"]} for k in V3_DIMENSIONS},
                "expected_ranking": ["C", "B", "A"],
                "actual_ranking": [r["case_id"] for r in ranked],
                "pass": ok,
                "cases": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n(v3 result written to: {OUT_PATH})")


if __name__ == "__main__":
    main()
