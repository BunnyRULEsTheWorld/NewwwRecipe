# CIE-Culinary-Bench — Experiment Matrix v1

**Companion to** `task_definition_v1.2.md`. This file is the executable specification of the five settings: input views, prompt-scaffold deltas, output schema, the frozen evaluation adapter, metric applicability, and the contribution chain.

**Status:** definition only. No runner, no Hy3 calls, no UI.

---

## 1. Master Table（总表）

| Setting | Input | CIE Rubric? | Structured Reasoning? | Gold Trace? | Human Evidence? | Dimensions | Runs | Purpose | Primary Comparison |
|---|---|:--:|:--:|:--:|:--:|---|---:|---|---|
| **E0** Vanilla LLM Judge | neutral `evidence_only_view` | ✗ | ✗ | ✗ | ✗ | adapter-derived (5) | ≥3 (core) | 最低 baseline | vs E1 |
| **E1** CIE Rubric-only | neutral `evidence_only_view` | ✓ | ✗ | ✗ | ✗ | 5 evidence-only | ≥3 (core) | Rubric contribution | vs E0, vs E2 |
| **E2** CIE Evidence-only | neutral `evidence_only_view` | ✓ | ✓ (model generates) | ✗ | ✗ | 5 evidence-only | ≥3 (core) | Structured reasoning contribution | vs E1, vs E3 |
| **E3** Trace-conditioned | neutral + curated gold trace | ✓ | ✓ (trace given) | ✓ | ✗ | 6 (legacy run) | 1 (frozen 33/33) | Curated trace benefit | vs E2 |
| **E4** Human-evidence-aware | neutral + reasoning + human/exec evidence | ✓ | ✓ | (opt) | ✓ | 6 (incl. realization) | diagnostic | Realization quality | vs E3 |

**Contribution chain (the causal ladder):**
```
E0 ──(+CIE rubric)──▶ E1 ──(+structured reasoning)──▶ E2 ──(+curated gold trace)──▶ E3 ──(+human/exec evidence)──▶ E4
 │                       │                              │                              │                              │
Rubric Contribution   Structured Reasoning        Curated Trace               Human Evidence
=E1−E0                Contribution =E2−E1         Benefit =E3−E2             Contribution =E4−E3
```

- **E0 → E1** = rubric contribution
- **E1 → E2** = structured reasoning contribution
- **E2 → E3** = curated trace contribution
- **E3 → E4** = human evidence contribution

---

## 2. Per-Setting Specification

### 2.0 Common frozen controls (apply to E0/E1/E2)
- Model: `hy3` (same endpoint)
- Temperature: `0.2` (same)
- reasoning_effort: `no_think` (same)
- API configuration: identical
- Cases: same 30
- Neutral evidence: same `evidence_only_view` (§4)
- ID anonymization: **enabled** (mandatory; prevents `CIE-Axx` split leakage)
- No `metadata` / `human_evaluation_signal` / `cie_annotation` / `benchmark_tags` in any prompt

### 2.1 E0 — Vanilla LLM Judge
- **System/Instruction (neutral, no CIE):**
  > "You are given neutral culinary facts about a dish. Judge how innovative the dish is and explain your reasoning. Do not use external knowledge beyond what is provided. Be specific about what changed and whether the change adds culinary value."
- **Output**: free text. Optionally one holistic 1–5 integer ("overall innovation quality") — allowed but NOT required.
- **No** 6-class list, **no** 5-dimension list, **no** CIE rubric, **no** trace.
- **Scoring for comparison**: ALL via `cie_eval_adapter` (§3) → canonical 5-dim + 6-class + ranking. The 6-class for E0 is explicitly `adapter-derived`.

### 2.2 E1 — CIE Rubric-only
- Same instruction as E0 **plus** the CIE rubric text (Innovation = Novel Change + Grounding + Value; the 5 evidence-only dimension definitions in **neutral wording** drawn from `scoring_rubric.json`).
- **Does NOT require** the model to emit a six-stage trace.
- **Output schema** (canonical, shared with E2): see §3.2.

### 2.3 E2 — CIE Evidence-only
- Same as E1 **plus** an instruction requiring the model to **generate its own** six-stage analysis:
  > "Before giving scores, walk through: (1) existing culinary context, (2) ingredient & technique knowledge, (3) innovation delta, (4) mechanistic justification, (5) creative hypothesis, (6) risk & constraint, then (7) CIE evaluation."
- **Must NOT** be given the gold `innovation_trace` evaluative content. The model's generated trace is a `model-generated reasoning artifact`.
- **Dimensions scored**: exactly the 5 evidence-only dimensions. `realization_quality` excluded.
- **Output schema**: canonical (§3.2).

### 2.4 E3 — Trace-conditioned (FROZEN, do not re-run)
- Uses `closed_evidence_anonymous_v1` (33/33). Input = neutral + full curated gold trace.
- Results retained as-is: Acc 73.3% · Macro-F1 0.675 · Mean Spearman 0.570 · MAE 0.661 · Ranking pairwise 86.7%.
- Labeled `trace_conditioned`; never cited as evidence-only.

### 2.5 E4 — Human-evidence-aware (diagnostic, protocol only)
- Input = neutral + structured reasoning + human/execution evidence (`human_evaluation_signal` fields, judge comments, competition results, real execution issues, user feedback).
- Primary use: score `realization_quality` (the 6th dimension, unavailable under evidence-only).
- Reported separately from the evidence-only main track.

---

## 3. cie_eval_adapter（冻结、对模型不可见）

The single measurement instrument that makes E0/E1/E2 comparable. **Never shown to any evaluated model.** Applied identically to all settings' raw outputs for the *primary* contrast.

### 3.1 Neutral dimension descriptions (convergent-but-not-identical to CIE)
The adapter scores 5 dimensions on a 1–5 integer scale using **neutral** culinary-evaluation language:

| Canonical dim | Neutral adapter prompt phrasing (not labeled "CIE") |
|---|---|
| culinary_knowledge_grounding | "Are the stated ingredients/techniques and their culinary roles accurate, specific, and bounded?" |
| existing_culinary_precedent_analysis | "Does it locate the nearest prior dish and compare inheritance vs deviation?" |
| innovation_delta_quality | "Does the before→after change produce a meaningful culinary-role or structure change?" |
| mechanistic_plausibility | "Are the flavor/texture/process mechanisms valid and falsifiable?" |
| innovation_value | "Does the change yield identifiable, cost-proportioned eating/cultural/system benefit?" |

### 3.2 Canonical output schema (what E1/E2 emit natively; what adapter extracts for E0)
```json
{
  "classification": "<one of 6 neutral classes>",
  "scores": {
    "culinary_knowledge_grounding": 1,
    "existing_culinary_precedent_analysis": 1,
    "innovation_delta_quality": 1,
    "mechanistic_plausibility": 1,
    "innovation_value": 1
  },
  "reasoning": "<free text>",
  "ranking": "<for ranking tasks: ordered case-id list for a given dimension>"
}
```
The 6 neutral classes (gold-aligned, used by the adapter's mapping; **E0 never sees them at generation time**):
`Conventional, Surface Innovation, Incremental Innovation, Structural Innovation, Transformative Innovation, Adversarial Trap`.

### 3.3 Adapter fairness rules
- The adapter is a **constant** across settings → any E0→E1→E2 delta isolates prompt-scaffold/information, not measurement.
- For E1/E2, also retain the **native** structured output as a cross-check; report adapter-derived (primary) and native (secondary) together.
- The adapter's 6-class mapping for E0 is flagged `adapter-derived` in all reports.
- **Primary contrast metrics** are taxonomy-independent (§5 below), so even if E0 never saw the 6 labels, the comparison is fair.

---

## 4. evidence_only_view — runtime construction

Pseudocode (definition only; not executed this step):
```
def build_evidence_only_view(sample):
    view = {
        "culinary_context": sample["culinary_context"],          # KEEP all
        "dish_information": sample["dish_information"],          # KEEP all
        "innovation_trace_neutralized": neutralize_trace(sample["innovation_trace"])
    }
    # Explicitly drop (never serialize into prompt):
    #   metadata, human_evaluation_signal, cie_annotation, benchmark_tags
    return view

def neutralize_trace(trace):
    return {
        "precedents": trace["existing_culinary_context"]["precedents"],            # KEEP
        # relationship: STRIP (or REWRITE_NEUTRAL -> pure factual comparison)
        "ingredient_knowledge": trace["ingredient_and_technique_knowledge"]["ingredient_knowledge"],  # KEEP (verdict-clauses rewritten neutral)
        "technique_knowledge":  trace["ingredient_and_technique_knowledge"]["technique_knowledge"],  # KEEP
        "delta_before": trace["innovation_delta"]["before"],                      # KEEP
        "delta_after":  trace["innovation_delta"]["after"],                       # KEEP
        "delta_change_type": trace["innovation_delta"]["change_type"],           # KEEP
        # delta.magnitude: MOVE_TO_GOLD (drop)
        "flavor_mechanism": trace["mechanistic_justification"]["flavor_mechanism"],        # KEEP (verdict-free)
        "texture_mechanism": trace["mechanistic_justification"]["texture_mechanism"],      # KEEP (verdict-free)
        # chemical_or_culinary_basis: STRIP / MOVE_TO_GOLD
        # strength: MOVE_TO_GOLD
        "risk": trace["risk_and_constraint"]["risk"],                             # KEEP
        "failure_condition": trace["risk_and_constraint"]["failure_condition"],  # KEEP (verdict-free)
        # tradeoff: REWRITE_NEUTRAL / STRIP
        "creative_hypothesis": REWRITE_NEUTRAL(trace["creative_hypothesis"])     # keep structure, strip value claims
    }
    # Explicitly excluded verdict fields stored only in gold:
    #   magnitude, strength, chemical_or_culinary_basis, relationship (verdict), tradeoff (verdict)
```

**Allowed semantics (model may know):** actual ingredients, actual techniques, objective cooking process, objective culinary precedent, verifiable ingredient/technique facts.
**Forbidden semantics (model must NOT know):** strength/magnitude verdicts, "system-level innovation", "this is a trap", expert final value judgment, gold reasoning, category implication.

---

## 5. Metric Applicability Matrix

| Metric | E0 | E1 | E2 | E3 | E4 |
|---|:--:|:--:|:--:|:--:|:--:|
| 6-class Accuracy / Macro-F1 | adapter-derived (secondary) | ✓ | ✓ | ✓ (frozen) | ✓ |
| Per-dim Spearman (5 evidence-only) | ✓ (adapter) | ✓ | ✓ | partial | ✓ |
| Mean Spearman (5 dim) | ✓ (adapter) | ✓ | ✓ | — | ✓ |
| MAE (5 dim) | ✓ (adapter) | ✓ | ✓ | — | ✓ |
| QWK (optional) | ✓ (adapter) | ✓ | ✓ | ✓ | ✓ |
| Ranking pairwise / Spearman / Kendall | ✓ (adapter) | ✓ | ✓ (2 sets only) | ✓ (3 sets) | ✓ |
| Reliability (≥3 runs, modal/exact/SD) | ✓ | ✓ | ✓ | ✗ (frozen 1) | diagnostic |
| Discrimination (good>medium>bad) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Adversarial (5 types, trap/overrating/hallucination rate) | ✓ | ✓ | ✓ | ✓ (frozen) | ✓ |

**Ranking-set eligibility:**
- E2 (evidence-only): `RANK-IV-01` (innovation_value), `RANK-IDQ-01` (innovation_delta_quality). `RANK-RQ-01` excluded (realization_quality dropped).
- E3/E4: all three sets including `RANK-RQ-01`.

---

## 6. Invariants (frozen controls — must hold in every run)
1. Dataset, gold labels, rubric, historical results: **untouched**.
2. E3 = the frozen 33/33; never re-run or edited.
3. `evidence_only_view` excludes all verdict fields (§4).
4. ID anonymization enabled for E0/E1/E2.
5. Same model / temperature / reasoning_effort / API config across E0/E1/E2.
6. Any prompt change bumps `prompt_template_version` and recomputes `experiment_signature`.
7. Parse-failure counted as failure; no silent retry-to-success.

---

## 7. Open decisions for human sign-off (mirrors task_definition_v1.2 §9)
1. E0 optional holistic 1–5? (recommend: allow, optional)
2. Adapter implementation: frozen neutral LLM-judge (recommend) vs deterministic rules.
3. E2 ranking: 2 sets acceptable, or add a 3rd evidence-only set?
4. good_medium_bad anchor dimension + numeric targets?
5. Runs policy: ≥3 for E0/E1/E2 core; E3 frozen; E4 diagnostic.
6. E4 mandatory in Tencent phase, or protocol-only? (user leans protocol-only)
