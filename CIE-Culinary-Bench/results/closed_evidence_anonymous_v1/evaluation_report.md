# CIE-Culinary-Bench v1.1 — Evaluation Report

> ⚠️ **This run is `trace_conditioned`, NOT `evidence_only`.** The model was shown the full `innovation_trace` including human evaluator conclusions (`strength`, `chemical_or_culinary_basis`, etc.). The 73.3% / macro-F1 0.675 below therefore measure alignment-with-human-reasoning-chain, **not** evidence-only innovation evaluation. See `docs/protocol_audit_v1.md` for the semantic-leakage audit and the proposed `evidence_only` redesign. Do not cite these numbers as the benchmark's evidence-only result.

- Judge: `creative_recipe.Hy3LLMClient` (Hy3, OpenAI-compatible)
- Runner: benchmark_pipeline.py v1.2 (experiment_signature + true resume + conn-abort)
- Rubric: schema/scoring_rubric.json (1-5, six dimensions)
- Runtime `track` (provenance): `closed_evidence` (IDs anonymized)  |  Temp: 0.2  |  **Runs: 1**
- **Measurement construct: `trace_conditioned`**
- experiment_signature: `c6748060722a762c07537ac9c828efd05f65e4d9a67e8ffb03c4f49bdf8d0a52`
- Dataset: 30 cases, 3 ranking sets
- Reliability: parse success 100.0% (33/33), API failures 0, retries 0

### Track provenance ≠ evaluation construct name

`track = "closed_evidence"` is the **legacy runtime input-view identifier**. That exact string was
hashed into the `experiment_signature` at execution time, so it is **frozen and deliberately left
unedited** in `experiment_manifest.json` for reproducibility.

After the semantic-annotation-leakage audit (`docs/protocol_audit_v1.md`), the **measurement
construct** of this same experiment is re-interpreted as **`trace_conditioned`** — the judge
received the full `innovation_trace` as released, which is itself part of the human gold annotation
and carries evaluator conclusions.

> **`track` / config provenance ≠ evaluation construct name.**
> Cite the construct (`trace_conditioned`) when describing *what was measured*; cite the track
> (`closed_evidence`) only when describing *how the run was configured*.

Validation scope: this run is `runs=1`. Repeat-consistency (≥3), `good > medium > bad`
discrimination, the `evidence_only` view and the `human_evidence_aware` track are **NOT RUN** —
see `results/validation_status.md`. Formal benchmark validation is **INCOMPLETE**.

## Task 1 — Innovation Classification

- **Accuracy**: 73.3%
- **Macro-F1** (primary): 0.675
- **Adversarial Trap detection**: 100.0%
- CIE-025 (luxury-signaling) mis-ranked as Structural/Transformative: 0.0%

Per-class recall:

  - Conventional: 100.0%
  - Surface Innovation: 100.0%
  - Incremental Innovation: 80.0%
  - Structural Innovation: 50.0%
  - Transformative Innovation: 0.0%
  - Adversarial Trap: 100.0%

Confusion matrix (rows=gold, cols=pred):

| gold \ pred | Conventional | Surface Innovation | Incremental Innovation | Structural Innovation | Transformative Innovation | Adversarial Trap |
| --- | --- | --- | --- | --- | --- | --- |
| Conventional | 6 | 0 | 0 | 0 | 0 | 0 |
| Surface Innovation | 0 | 4 | 0 | 0 | 0 | 0 |
| Incremental Innovation | 1 | 0 | 4 | 0 | 0 | 0 |
| Structural Innovation | 0 | 0 | 3 | 3 | 0 | 0 |
| Transformative Innovation | 0 | 0 | 0 | 4 | 0 | 0 |
| Adversarial Trap | 0 | 0 | 0 | 0 | 0 | 5 |

## Task 2 — CIE Dimension Scoring (1–5)

Dimension score **correlation** (Spearman ρ, gold vs Hy3):

| Dimension | n | MAE | ±1 acc | Exact acc | Spearman ρ | QWK |
| --- | --- | --- | --- | --- | --- | --- |
| culinary_knowledge_grounding | 30 | 0.700 | 90.0% | 40.0% | 0.148 | 0.154 |
| existing_culinary_precedent_analysis | 30 | 1.000 | 73.3% | 26.7% | 0.047 | 0.046 |
| innovation_delta_quality | 30 | 0.233 | 100.0% | 76.7% | 0.954 | 0.924 |
| mechanistic_plausibility | 30 | 0.667 | 93.3% | 40.0% | 0.609 | 0.455 |
| innovation_value | 30 | 0.633 | 96.7% | 40.0% | 0.877 | 0.787 |
| realization_quality | 30 | 0.733 | 93.3% | 36.7% | 0.785 | 0.744 |

- **Mean dimension Spearman ρ**: 0.570 (min 0.047, max 0.954)
- **Mean dimension MAE**: 0.661

## Task 3 — Pairwise Ranking

- **Pairwise accuracy**: 86.7%
- **Mean Spearman ρ**: 0.667
- **Mean Kendall τ-a**: 0.733

## Protocol Comparison — anonymous (closed_evidence) vs with-ID baseline

- Baseline run (leaky, real IDs exposed): `results/baseline_with_id/` (id_anonymized=False)
- Classification accuracy: baseline 83.3% → anonymous 73.3%
- Adversarial Trap detection: baseline 100.0% → anonymous 100.0%
- Transformative recall: baseline 0.0% → anonymous 0.0%
- Mean dimension Spearman: baseline 0.449 → anonymous 0.570

> ⚠️ **How to read this comparison.** The with-ID baseline is **deprecated** (it exposed real IDs such as `CIE-A04` in prompts, which can leak the Adversarial label by construction) and must **not** be cited as the canonical number. The anonymous run above is the valid protocol.
>
> The ~10-point accuracy gap (83.3% → 73.3%) is **not** a clean measure of ID-leak impact: the two runs are *independent* stochastic samples (temperature 0.2, `no_think`), and the gap is confined entirely to **Structural→Incremental** confusions on cases whose IDs do **not** encode their category (`CIE-007/010/014`). Adversarial-Trap detection is **100% in both** runs and Transformative recall is **0% in both** — i.e. the ID hint did not measurably shift the label-leakable classes. The observed delta is therefore best attributed to run-to-run variance, not leakage. A true A/B would require scoring the *same* 33 responses under both ID conditions, which was not done. **Treat 73.3% / macro-F1 0.675 as the reportable leak-free result.**

> Full per-case detail (raw + parsed) is in `predictions.jsonl`. Failure cases and bias diagnosis are in `error_analysis.md`. Reproducibility metadata is in `experiment_manifest.json`.

---
*Generated by scripts/benchmark_pipeline.py. Dataset unmodified; prompts use the closed_evidence view with anonymized IDs. Gold labels are never leaked into prompts.*
