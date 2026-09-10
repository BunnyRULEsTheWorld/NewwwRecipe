"""P3-A.5: CIE rubric must be operational, on the canonical 1-5 scale, and carry mandatory considerations.

Aligned to the canonical CIE v3 contract (six dimensions, 1-5 integer anchors).
"""
from creative_recipe.cie.dimensions import (
    REGISTRY,
    WEIGHTS,
    STAGE_A_SPECS,
    STAGE_B_SPECS,
)

# Canonical CIE v3 scale is 1-5 (integer levels).
EXPECTED_BAND_KEYS = {1, 2, 3, 4, 5}
# Vague / non-operational words that must NOT appear in any anchor text.
BANNED = ["较好", "优秀", "有一定创新", "good", "excellent", "creative"]


def _anchor_blob(spec):
    return " ".join(spec.anchors.values())


def test_six_dimensions_present():
    assert len(REGISTRY) == 6


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == 1.0
    assert WEIGHTS == {
        "culinary_knowledge_grounding": 0.15,
        "existing_culinary_precedent_analysis": 0.15,
        "innovation_delta_quality": 0.25,
        "mechanistic_plausibility": 0.20,
        "innovation_value": 0.15,
        "realization_quality": 0.10,
    }


def test_stage_split_is_five_plus_one():
    assert len(STAGE_A_SPECS) == 5
    assert len(STAGE_B_SPECS) == 1
    assert {s.key for s in STAGE_B_SPECS} == {"realization_quality"}


def test_each_dimension_has_five_bands_on_canonical_scale():
    for key, spec in REGISTRY.items():
        assert set(spec.anchors.keys()) == EXPECTED_BAND_KEYS, (
            f"{key}: expected band keys {sorted(EXPECTED_BAND_KEYS)}, got {sorted(spec.anchors.keys())}"
        )


def test_innovation_delta_quality_separates_magnitude_from_value():
    idq = REGISTRY["innovation_delta_quality"]
    text = (idq.cognitive_mapping + " " + _anchor_blob(idq)).lower()
    for kw in ["magnitude", "value"]:
        assert kw in text, f"Innovation Delta Quality missing mandatory consideration: {kw}"


def test_mechanistic_plausibility_falsifiable_mechanisms():
    mp = REGISTRY["mechanistic_plausibility"]
    text = (mp.cognitive_mapping + " " + _anchor_blob(mp)).lower()
    for kw in ["机制", "falsif", "证伪", "refute"]:
        assert kw in text, f"Mechanistic Plausibility missing mandatory consideration: {kw}"


def test_no_vague_praise_in_anchors():
    for key, spec in REGISTRY.items():
        blob = _anchor_blob(spec).lower()
        for b in BANNED:
            assert b not in blob, f"{key}: anchor uses vague/non-operational term '{b}'"


def test_anchors_are_operational_not_generic():
    # Each band must name at least one concrete, observable behavior signal (a quoted example,
    # an ingredient/technique word, a stated step, or a named difference) — not bare adjectives.
    MARKERS = [
        "（", "如", "例", "步骤", "属性", "连接", "菜名", "组合", "菜", "差别",
        "变体", "概念", "食材", "现有", "替代", "风味", "质地", "温度", "时间",
        "解释", "名称", "机制", "顺序", "矛盾",
    ]
    for key, spec in REGISTRY.items():
        for score, desc in spec.anchors.items():
            assert any(tok in desc for tok in MARKERS), (
                f"{key}@{score}: anchor is not operational enough -> {desc}"
            )
