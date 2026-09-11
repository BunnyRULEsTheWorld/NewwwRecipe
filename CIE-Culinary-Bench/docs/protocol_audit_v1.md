# CIE-Culinary-Bench v1.1 — Protocol Audit v1

**Semantic annotation leakage audit + evidence_only redesign proposal**

- Audit date: 2026-08-27
- Method: **READ-ONLY** on the frozen dataset (`data/cie_culinary_bench.jsonl`, 30 cases + 3 ranking sets). No Hy3 API calls. No dataset / gold / rubric modification. No UI.
- Inputs reviewed: `docs/task_definition.md`, `schema/scoring_rubric.json`, all 30 `innovation_trace` structures (dumped verbatim), leakage keyword scan.
- Companion action: the current 33/33 run is relabeled **`trace_conditioned`** (see §4); its files are NOT deleted or re-run.

---

## 0. TL;DR

1. The previous `closed_evidence` *field-exclusion* layer worked: `cie_annotation.*`, `human_evaluation_signal`, `benchmark_tags`, and ranking `gold_ordering` never entered the prompt.
2. **But a new leakage was found**: `innovation_trace` *itself* is a gold annotation containing human evaluator conclusions. The model was fed the full trace, including a `strength` verdict in **30/30** samples and explicit gold reasoning in many. Therefore the reported **73.3% / macro-F1 0.675 is `trace_conditioned`, not evidence-only**.
3. Proposed fix: an `evidence_only` input view that STRIPs / MOVEs_TO_GOLD the evaluator-judgment fields (§3).
4. `realization_quality` is **unidentifiable** under strict evidence-only (its definition requires external execution/human evidence) → recommend dropping it from the evidence-only track and evaluating it only in the `human_evidence_aware` diagnostic track (§5).
5. **Benchmark validation is NOT complete**: only `runs=1`, no ≥3-repeat consistency, no `good>medium>bad` discrimination (§6).

---

## 1. What is still valid (keep)

| Item | Status | Note |
| --- | --- | --- |
| Run integrity | ✅ valid | 33/33 completed, parse 100%, 0 API failure, 0 retry. |
| `closed_evidence` field exclusion | ✅ valid | `cie_annotation`, `human_evaluation_signal`, `benchmark_tags`, `gold_ordering` excluded from prompt. |
| 6-dimension rubric structure | ✅ valid | `schema/scoring_rubric.json` (v1.1) is sound and reusable. |
| Task 1/2/3 protocol | ✅ valid | Classification / per-dimension scoring / pairwise ranking definitions are kept. |
| LLM-as-judge harness | ✅ valid | `Hy3LLMClient` + `Config` reuse, structured output, strict schema. |
| Runner reliability | ✅ valid | `experiment_signature`, true resume (status+`prompt_sha256`+`exp_sig`), incremental persistence, connection-abort, `--analyze`. |
| ID anonymization | ✅ valid | `CIE-Axx` → neutral tokens; no ID-encodes-category leak. |

These are retained when moving to `evidence_only`.

---

## 2. Semantic annotation leakage (new finding)

### 2.1 Root cause

`task_definition.md` §0 defines `closed_evidence` as `{culinary_context, dish_information, innovation_trace}` and hides `cie_annotation` / `human_evaluation_signal` / `benchmark_tags`. The assumption was that `innovation_trace` is "auditable reasoning chain" rather than a label. **In fact `innovation_trace` is authored by the same human evaluators who produced the gold labels**, and several of its sub-fields are *the conclusion*, not *the evidence*.

### 2.2 Leaking fields (evidence from the 30-sample dump)

| Field | Leak type | Severity | Example (verbatim) |
| --- | --- | --- | --- |
| `mechanistic_justification.strength` | **Score/category verdict** | 🔴 critical | `weak` / `medium` / `strong` present in **30/30** samples (e.g. CIE-005/006/007 = `strong`; CIE-A01/A02/A03/A05 = `weak`). Maps almost 1:1 onto `innovation_delta_quality` / `innovation_value`. |
| `mechanistic_justification.chemical_or_culinary_basis` | **Gold reasoning conclusion** | 🔴 critical | CIE-001 *"技术复杂度→创新价值的推论不成立。公开报道转述评审认为基础吃味仍接近街边豆花"*; CIE-002 *"评价应把菜好吃与创新增量分开"*; CIE-003 *"创新证据较弱"*; CIE-006 *"这是'概念可行、关键部件失效'的典型"*; CIE-012 *"系统级创新"*; CIE-025 *"本体质量与镀金 delta 分开评"*. |
| `existing_culinary_context.relationship` | **Meta-guidance steering to verdict** | 🟠 high | CIE-001 *"创新判断的关键不是设备数量"*; CIE-002 *"所谓创新主要来自把多个蟹种并列，而不是创建新角色或新技术"*; CIE-A01 *"陷阱在于本设定没有桥接配料"*. |
| `innovation_delta.magnitude` (1–5) | **Score-level judgment** | 🟠 high | Integer magnitude of change present in all 30; directly the target of the `innovation_delta_quality` dimension. |
| `risk_and_constraint.tradeoff` | **Value conclusion** | 🟡 medium | CIE-004 *"概念层次多于味觉层次"*; CIE-025 *"成本与注意力被转向不可证明的味觉增益"*. |
| `risk_and_constraint.failure_condition` / `risk` | Mixed | 🟡 medium | mostly neutral (blind-taste framing), but CIE-001 *"只感到更复杂地做了一碗普通豆花"*, CIE-004 *"鲍鱼沦为昂贵填充"* are verdict-flavored. |
| `creative_hypothesis` | Mixed | 🟡 medium | Usually neutral intent; occasionally outcome claim, e.g. CIE-025 *"转化为可观看、可分享…的奢侈仪式"*. |
| `ingredient_and_technique_knowledge` | Mostly neutral | 🟢 low | Culinary facts; a few conditional value clauses (e.g. CIE-002 *"差异必须可感知才有叠加价值"*). |

### 2.3 Keyword-scan index (substring hits in `innovation_trace`)

```
30/30  carry `strength` (gold verdict)
explicit evaluator conclusions:
  CIE-001  不成立 / 评审 / 创新价值 / 认为 / strength
  CIE-002  strength            (relationship + basis carry verdicts)
  CIE-003  只是 / 不足以 / strength
  CIE-004  不足以 / strength    (tradeoff verdict)
  CIE-005  只是 / strength
  CIE-006  并非 / strength
  CIE-007  strength
  CIE-011  创新价值 / strength
  CIE-012  噱头 / 系统级创新 / strength
  CIE-015  创新价值 / 只是 / strength
  CIE-017  不成立 / strength
  CIE-018  可靠证据 / 并非 / strength
  CIE-019  噱头 / strength
  CIE-024  只是 / strength
  CIE-025  创新价值 / strength   (full expert-review verdict embedded)
  CIE-A01  陷阱 / 噱头 / 并非 / weak
  CIE-A02  不足以 / weak
  CIE-A03  weak
  CIE-A04  陷阱 / 并非 / medium
  CIE-A05  weak
  (remaining cases: strength only, but basis/relationship still carry verdicts)
```

### 2.4 Consequence

The 73.3% classification / 0.675 macro-F1 must be read as **`trace_conditioned`**: the model judged *with* the human reasoning chain in front of it. It is **not** evidence of the model's ability to evaluate innovation from neutral culinary facts alone. The 100% Adversarial-Trap rate is also partly aided by trace phrases like *"陷阱在于…"*, so it is not a clean measure of content-based trap detection either.

---

## 3. Proposed `evidence_only` input view (field-by-field)

Decision legend: **KEEP** (neutral fact, safe) · **STRIP** (remove from prompt) · **MOVE_TO_GOLD** (keep only in gold, never in prompt) · **REWRITE_NEUTRAL** (keep structure, delete value/verdict wording).

| Field | Decision | Rationale |
| --- | --- | --- |
| `existing_culinary_context.precedents` | **KEEP** | Neutral list of prior dishes. |
| `existing_culinary_context.relationship` | **STRIP** (or REWRITE_NEUTRAL to a pure factual comparison sentence, no *"创新关键 / 所谓创新"*) | Currently meta-guidance toward the verdict. |
| `ingredient_and_technique_knowledge` | **KEEP** (REWRITE_NEUTRAL any value clause) | Neutral culinary facts; the core of "evidence". |
| `innovation_delta.before` | **KEEP** | Neutral description. |
| `innovation_delta.after` | **KEEP** | Neutral description. |
| `innovation_delta.change_type` | **KEEP** | Neutral structural descriptors. |
| `innovation_delta.magnitude` | **MOVE_TO_GOLD** | Score-level judgment (1–5); target of `innovation_delta_quality`. |
| `mechanistic_justification.flavor_mechanism` | **KEEP** (REWRITE_NEUTRAL: drop trailing verdict sentences) | Falsifiable mechanism = good evidence. |
| `mechanistic_justification.texture_mechanism` | **KEEP** (REWRITE_NEUTRAL) | Same. |
| `mechanistic_justification.chemical_or_culinary_basis` | **STRIP** / **MOVE_TO_GOLD** | Carries the gold conclusion ("不成立", "创新证据较弱", "系统级创新"). |
| `mechanistic_justification.strength` | **MOVE_TO_GOLD** | Direct gold verdict, 30/30 leakage. |
| `risk_and_constraint.risk` | **KEEP** | Neutral feasibility risk. |
| `risk_and_constraint.failure_condition` | **KEEP** (REWRITE_NEUTRAL verdict phrasing) | Blind-taste framing is neutral. |
| `risk_and_constraint.tradeoff` | **REWRITE_NEUTRAL** / **STRIP** | Remove value conclusions ("概念层次多于味觉层次"). |
| `creative_hypothesis` | **REWRITE_NEUTRAL** | Keep structural intent, strip outcome/value claims ("奢侈仪式"). |

**Resulting `evidence_only` view (what the model may see):**
`culinary_context` + `dish_information` + a *neutralized* `innovation_trace` containing only:
`precedents`, `ingredient_and_technique_knowledge`, `innovation_delta.{before,after,change_type}`, `mechanistic_justification.{flavor_mechanism,texture_mechanism}` (verdict-free), `risk_and_constraint.{risk,failure_condition}` (verdict-free), and a *neutralized* `creative_hypothesis`.

Everything else (`relationship`, `magnitude`, `strength`, `chemical_or_culinary_basis`, value-laden `tradeoff`) is **removed from the prompt** and stored only in gold.

---

## 4. `trace_conditioned` track definition (rename of current run)

- **Definition**: input = `closed_evidence` view **+ the full `innovation_trace` as released** (i.e. including human evaluator conclusions). It measures a *different construct*: "given the human reasoning chain, does the model agree / align with the human judgment?" This is a legitimate **diagnostic / alignment** track, but it is **not** "evidence-only innovation evaluation".
- **Current 33/33 results = `trace_conditioned`**. They are retained (no delete, no re-run) and relabeled:
  - `results/closed_evidence_anonymous_v1/experiment_manifest.json` → `"evaluation_type": "trace_conditioned"`.
  - `results/closed_evidence_anonymous_v1/summary.json` → `"evaluation_type": "trace_conditioned"` + note that 73.3% is **not** evidence-only.
  - `results/closed_evidence_anonymous_v1/evaluation_report.md` → header note.
- **Do not** cite 73.3% as the benchmark's evidence-only number. The evidence-only number does not exist yet (§6).

---

## 5. `realization_quality` — unidentifiability and recommended handling

### 5.1 Why it is unidentifiable under evidence-only

`scoring_rubric.json` defines `realization_quality` as *"具体实例是否被可靠证据证明实现了目标?"*, with anchors *"专业认可且实现稳定"* (4) and *"长期、重复、跨场景验证"* (5), and the global rule *"无实际人类证据时 realization_quality 不得仅凭漂亮推理给5"*. The dimension therefore **intrinsically depends on external execution / human evidence**.

A strict `evidence_only` view strips `human_evaluation_signal` **and** the trace's evaluator conclusions. The model then has **no legitimate basis** to score `realization_quality` above ~3. The dimension becomes:
- either a guess (unidentifiable / degenerate), or
- implicitly leak-prone (if the model infers "realized" from neutralized-but-verdict-tinged text).

### 5.2 Option selection (benchmark-validity view)

| Option | Verdict |
| --- | --- |
| **A. evidence_only drops `realization_quality`** | ✅ adopt (part of combined plan) |
| **B. add `neutral_execution_evidence`** | ⚠️ insufficient alone — any "execution evidence" is by nature human/observational; putting it in `evidence_only` contradicts the track definition. Its proper home is the `human_evidence_aware` track. |
| **C. move `realization_quality` to `human_evidence_aware`** | ✅ adopt (part of combined plan) |

**Recommendation: A + C.** The `evidence_only` main track scores **5 dimensions** (drop `realization_quality`); `realization_quality` is evaluated **only** in the `human_evidence_aware` diagnostic track, with explicitly provided human/execution evidence, reported separately per `task_definition.md` §0. This keeps both tracks valid and non-confounded.

> Note: switching Task-2 to 5 dimensions changes `experiment_signature` (rubric hash / prompt version). The `trace_conditioned` 33/33 therefore cannot be retrofitted as `evidence_only`; `evidence_only` requires its own (future) run, ideally ≥3 repeats.

---

## 6. Subsequent final validation protocol — what is **NOT** done

Per `task_definition.md` §有效性验证, the following are **outstanding**. Do **not** claim the benchmark validation is complete.

| Requirement | Status | Action needed (future, needs Hy3) |
| --- | --- | --- |
| ≥3 repeated runs, modal agreement + within-case SD | ❌ runs=1 | Re-run evidence_only config ≥3×; report per-sample per-dimension SD. |
| `good>medium>bad` discrimination (`good_medium_bad_cases.jsonl`) | ❌ not run | Run the 3-tier set; require each group satisfies good>medium>bad. (File must exist; create if missing.) |
| Adversarial check under evidence-only | ❌ only trace_conditioned | Re-test 5 traps + CIE-025 in evidence_only to confirm detection is content-based, not trace-"陷阱" aided. |
| Consistency bound to evidence_only schema | ❌ current 73.3% is trace_conditioned | All headline numbers must come from the evidence_only run. |
| `realization_quality` in human_evidence_aware | ❌ | Implement Option C; report separately. |

**Current honest status**: *trace_conditioned* 33/33 ran once (run integrity OK). **Formal benchmark validation is incomplete.** Headline evidence-only metrics do not yet exist.

### Concrete next-step checklist (for later, not now)
1. Implement `evidence_only` view per §3 (revise `closed_view()` / prompt builder).
2. Task-2 evidence_only = 5 dims; `realization_quality` → `human_evidence_aware` only.
3. Bump `prompt_template_version` and recompute `experiment_signature`.
4. Run evidence_only ≥3× → modal agreement + within-case SD.
5. Run `good_medium_bad` discrimination.
6. Re-run 5 adversarial + CIE-025 under evidence_only.
7. Pin prompt+data version per `experiment_signature`; compare across versions.

---

## 7. Appendix — relabel action record

- `results/closed_evidence_anonymous_v1/*` (predictions/manifest/summary/report): `evaluation_type` set to `trace_conditioned`; 73.3% explicitly marked **not** evidence-only.
- Dataset, gold labels, rubric: **untouched**.
- No Hy3 call made during this audit.
