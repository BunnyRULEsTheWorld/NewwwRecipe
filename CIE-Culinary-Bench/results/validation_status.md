# Evaluation & Validation Status

_Last updated: 2026-08-27. Supersedes the pre-run version of this file, which stated
"Empirical Hy3 run: NOT RUN" — that is now out of date._

## Headline

**Formal benchmark validation: INCOMPLETE.**

One empirical Hy3 run has been completed, but it is `trace_conditioned` (not `evidence_only`),
it has `runs=1` (no repeat-consistency), and the discrimination validation has not been executed.
Do **not** describe this benchmark's validation as complete.

## Status table

| Item | Status | Evidence / blocker |
|---|---|---|
| Dataset / schema validation | **PASS** | `scripts/validate_dataset.py` |
| Prompt-construction dry run | **PASS** | `results/dry_run_requests.jsonl` (30 cases, 3 ranking sets, 4 good/medium/bad groups × 3 repeats) |
| **trace_conditioned anonymous run** | **COMPLETE — 33/33, runs=1** | [`results/closed_evidence_anonymous_v1/`](closed_evidence_anonymous_v1/) · `experiment_complete: true` · parse 100% · API failures 0 |
| **evidence_only run** | **NOT RUN** | `evidence_only` input view not yet implemented; design in [`docs/protocol_audit_v1.md`](../docs/protocol_audit_v1.md) §3 |
| **≥3 repeat consistency** | **NOT RUN** | Canonical run is `runs=1`. Modal-agreement / within-case score SD not measured. |
| **good_medium_bad empirical validation** | **NOT RUN** | `validation_cases/good_medium_bad_cases.jsonl` exists (4 groups) but `benchmark_pipeline.py` does not yet execute the good > medium > bad discrimination task. |
| **human_evidence_aware realization_quality** | **NOT RUN** | Track not implemented. Per audit §4 (option A+C), `realization_quality` is unidentifiable under evidence-only input and belongs in this separate diagnostic track. |
| **Formal benchmark validation** | **INCOMPLETE** | Blocked on the four NOT RUN rows above. |

## What the one completed run does and does not show

`results/closed_evidence_anonymous_v1/` — 33/33 units OK, `experiment_signature`
`c6748060722a762c07537ac9c828efd05f65e4d9a67e8ffb03c4f49bdf8d0a52`:

- Classification accuracy 73.3%, macro-F1 0.675
- Mean dimension Spearman ρ 0.570, mean MAE 0.661
- Ranking pairwise accuracy 86.7%

**Construct caveat.** The judge was shown the full `innovation_trace` as released, which is itself
part of the human gold annotation and contains evaluator conclusions (`strength` present in
**30/30** samples, plus verdict-bearing prose in `chemical_or_culinary_basis` and
`existing_culinary_context.relationship`). These numbers therefore measure **alignment with a
supplied human reasoning chain**, not evidence-only innovation evaluation. See
[`docs/protocol_audit_v1.md`](../docs/protocol_audit_v1.md).

## Track naming vs measurement construct

The runtime `track` identifier recorded in `experiment_manifest.json` is `closed_evidence`, because
that string participated in the `experiment_signature` hash at execution time and is frozen for
reproducibility. After the leakage audit, the **measurement construct** of that same experiment is
re-interpreted as `trace_conditioned`.

> `track` / config provenance ≠ evaluation construct name.

## Result directories

| Directory | Status |
|---|---|
| [`closed_evidence_anonymous_v1/`](closed_evidence_anonymous_v1/) | **Canonical** — 33/33 `trace_conditioned` run. The only citable result. |
| [`baseline_with_id/`](baseline_with_id/) | **Deprecated** — real dataset IDs exposed in prompts (leaky by construction). |
| [`deprecated_partial_run2/`](deprecated_partial_run2/) | **Deprecated** — 16/33 succeeded, 17 `APIConnectionError`. Provenance / migration history only. |

## Next steps (require Hy3 API; not yet executed)

1. Implement the `evidence_only` input view per audit §3 (`strength` and `innovation_delta.magnitude` → gold-side; strip evaluator conclusions).
2. Switch `evidence_only` scoring to 5 dimensions (drop `realization_quality`) and bump `prompt_template_version`.
3. Run `evidence_only` with **runs ≥ 3** and report modal agreement + within-case score SD.
4. Execute the `good > medium > bad` discrimination validation.
5. Re-test the 5 adversarial traps and CIE-025 under `evidence_only`.
6. Implement `human_evidence_aware` as a separate diagnostic track for `realization_quality`.

Dataset, gold labels and rubric remain frozen and unmodified.
