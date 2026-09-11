# DEPRECATED — Partial Run 2 (16/33)

> ⛔ **NOT A VALID BENCHMARK RESULT.** Nothing in this directory may be cited, reported, or
> compared as a CIE-Culinary-Bench evaluation outcome. It is preserved **only** for provenance
> and migration history.

## What this is

The second anonymized-ID attempt (`benchmark_pipeline.py v1.1.1`, `--force`, log `run2.log`).
It aborted partway through because of repeated upstream connection failures.

| Fact | Value |
|---|---|
| Units attempted | 33 (30 classification+scoring, 3 ranking) |
| **Succeeded** | **16 / 33** (`status == "ok"`) |
| **Failed** | **17 / 33** — all `APIConnectionError: Connection error.` |
| Ranking sets completed | **0 / 3** |
| Parse success rate | 48.5% (16/33) |
| Retries burned | 34 |
| `experiment_complete` | `false` / `null` — never reached 33/33 |
| Status flag | `deprecated: true`, `superseded_by: results/closed_evidence_anonymous_v1/` |

Failure boundary: `CIE-001` … `CIE-016` succeeded; `CIE-017` … `CIE-025`, `CIE-A01` … `CIE-A05`
and all 3 ranking sets failed with connection errors.

## Why the numbers inside are invalid

`evaluation_report.md` / `summary.json` in this directory contain partial metrics computed over
**16 of 30** cases only (e.g. classification accuracy 62.5%, macro-F1 0.528, Adversarial Trap
detection `n/a`, ranking `n/a`). Because:

- the sample is truncated, not random — it is the first 16 IDs in file order;
- **all 5 Adversarial Trap cases and all 3 ranking sets are missing**;
- the Transformative / Structural cases are under-represented;

these figures are **not** an estimate of model performance and must never be quoted.

## Why it is preserved

The 16 successful rows here are genuine anonymized `closed_evidence` responses. They were the
**`--migrate-from` source** for the canonical run: `benchmark_pipeline.py` recomputed
`prompt_sha256` for each row under the current prompt/config, verified all 16 matched
byte-for-byte (0 mismatches), stamped the current `experiment_signature`, and carried them
forward **without re-calling the API**. The remaining 17 units were then re-run.

So this directory is the audit trail proving that 16 of the canonical run's 33 rows were reused
rather than re-generated.

Original path of the migration source (before this cleanup):
`results/predictions.jsonl` → now `results/deprecated_partial_run2/predictions.jsonl`.

## Where the real result is

**Canonical run:** [`../closed_evidence_anonymous_v1/`](../closed_evidence_anonymous_v1/) —
33/33 complete, `experiment_complete: true`.

Note that even the canonical run is labelled **`trace_conditioned`**, not `evidence_only`, after
the semantic-annotation-leakage audit. See [`../../docs/protocol_audit_v1.md`](../../docs/protocol_audit_v1.md)
and [`../validation_status.md`](../validation_status.md).

## Files

| File | Note |
|---|---|
| `predictions.jsonl` | 33 rows: 16 `ok`, 17 `api_error`. Migration source of record. |
| `summary.json` | Partial metrics — `deprecated: true`. Do not cite. |
| `evaluation_report.md` | Partial report over 16 cases. Do not cite. |
| `error_analysis.md` | Partial error analysis over 16 cases. Do not cite. |

Dataset, gold labels and rubric were never modified by this run.
