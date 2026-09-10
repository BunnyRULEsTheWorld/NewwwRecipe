# Local ↔ GitHub Reconciliation Report

- **Date:** 2026-08-28
- **Operator:** WorkBuddy (reconciliation only — no Hy3 call, no Gate 2, no UI, no push)
- **GitHub source of truth:** `https://github.com/BunnyRULEsTheWorld/NewwwRecipe` @ `main` (commit `0f4fb6b docs: simplify results note`)
- **Canonical working tree (NEW):** `C:\Users\SUNYIXI\Desktop\canonical_NewwwRecipe`
- **Local snapshot (UNTOUCHED):** `C:\Users\SUNYIXI\Desktop\NewwwRecipe!!!\creative-recipe-ai`

## Method

1. The local folder was treated as a read-only `LOCAL_SNAPSHOT`; it was **not** modified, not pulled, not merged in place.
2. `main` was fetched via a **fresh shallow clone** into an independent directory (`canonical_NewwwRecipe`) — this is the `CANONICAL_WORKTREE`.
3. GitHub `main` currently tracks **only 12 scaffold files**. Every substantive development artifact (source, tests, scripts, examples, the entire benchmark) was **absent from GitHub**, so content collisions were minimal.
4. The 12 GitHub-tracked files were treated as **GitHub-wins** and were **never overwritten** by local versions.
5. Local-only paths were copied in. Build artifacts, caches, and secrets were excluded.

---

## A. GitHub-wins files (kept as GitHub `main` versions)

All 12 tracked files on `main` are authoritative and were preserved verbatim. Six of them differed from the local versions; the local versions were **deliberately not merged** (per instruction). Diff magnitude (changed lines, local vs GitHub):

| File | Status | Local→GitHub diff | Decision |
|---|---|---|---|
| `README.md` | GitHub-wins | **347** changed lines | keep GitHub (local narrative discarded) |
| `docs/cie_framework_v3.md` | GitHub-wins | **382** changed lines | keep GitHub |
| `docs/cie_validation_report.md` | GitHub-wins | **249** changed lines | keep GitHub |
| `.gitignore` | GitHub-wins | **52** changed lines | keep GitHub |
| `.env.example` | GitHub-wins | **15** changed lines | keep GitHub |
| `requirements.txt` | GitHub-wins | **14** changed lines | keep GitHub (see D & H) |
| `docs/submission_proposal.md` | GitHub-wins | local had no copy | keep GitHub |
| `data/README.md` | GitHub-wins | local had no `data/` | keep GitHub |
| `scripts/README.md` | GitHub-wins | local had no copy | keep GitHub |
| `results/README.md` | GitHub-wins | local had no root `results/` | keep GitHub |
| `src/README.md` | GitHub-wins | local had no copy | keep GitHub |
| `examples/README.md` | GitHub-wins | local had no copy | keep GitHub |

> The 6 differing files are recorded as **human-decision conflicts** in section H — the local versions contained substantive additions (version pins, extra ignore rules, project narrative) that were *not* carried over.

---

## B. Local-only files/directories imported into canonical tree

| Path | Files | Notes |
|---|---|---|
| `src/creative_recipe/` | 82 | Real package source (preserves GitHub `src/README.md` placeholder) |
| `tests/` | 10 (`.py`) | `__init__.py` + 9 `test_*.py` (preserves GitHub `tests/README.md`) |
| `scripts/cie_v3_validation.py`, `scripts/rescore_demo.py` | 2 | Real implementations (preserves GitHub `scripts/README.md`) |
| `examples/*.json` (3 result/demo files) | 3 | `cie_v3_validation_result.json`, `mochicken_bake_demo.json`, `mochicken_bake_demo_cie_v2.json` (preserves GitHub `examples/README.md`) |
| `docs/architecture.md`, `docs/cie_framework.md` | 2 | Local-only docs (do **not** overwrite GitHub `cie_framework_v3.md`) |
| `CIE-Culinary-Bench/` | 45 | **Entire benchmark preserved** — `data/`, `schema/`, `validation_cases/`, `scripts/`, `results/` (incl. frozen `dry_run_requests.jsonl` + `closed_evidence_anonymous_v1`), `docs/`, `manifest.json`, `README.md`, `.env.example`, `requirements.txt`. Not flattened. |
| `LICENSE` | 1 | Local-only, imported to root |

`git status` reports these as **11 untracked top-level groups**, 0 modified tracked files.

---

## C. Files intentionally excluded

- `__pycache__/`, `*.pyc`, `.pytest_cache/` — build artifacts (also covered by `.gitignore`).
- `creative-recipe-ai/.pytest_cache/` (root) — excluded.
- `CIE-Culinary-Bench/run*.log` (3 temp run logs) — excluded from the tree; they are not frozen provenance. `dry_run_requests.jsonl` was **kept** (frozen provenance).
- `creative-recipe-ai/.env` — copied into the canonical tree for **local execution only**; it is git-ignored and **not staged** (verified: does not appear in `git status`).
- Local versions of the 6 GitHub-wins files (see A) — **not** merged back.
- No secret contents were printed or committed.

---

## D. Remaining structural inconsistencies (not resolved — deferred by instruction)

1. **Root scaffold vs nested real code.** GitHub `README.md` describes a `data/ scripts/ results/` root layout, but the actual code lives under `src/creative_recipe/`, and the benchmark lives under `CIE-Culinary-Bench/`. The root `data/`, `scripts/`, `results/` on GitHub are placeholder `README.md`s only. No flattening was performed (you deferred this decision).
2. **Benchmark location.** `CIE-Culinary-Bench/` remains a self-contained sub-tree; its `results/` were **not** moved to root `results/`, and `manifest.json` paths were not changed.
3. **Two framework docs.** Both `docs/cie_framework.md` (local-only, imported) and `docs/cie_framework_v3.md` (GitHub-wins) now coexist. Filenames differ, so no collision, but the dual docs may confuse readers — flag for later cleanup.
4. **`requirements.txt` pin mismatch.** GitHub's version is unpinned (`openai`, `pydantic`, …); the local version had precise pins (`openai>=1.30.0`, `typer>=0.12.0,<0.13`, etc.). The **dependency set is identical** (7 packages), so the imported code is fully described — only pins differ. GitHub-wins kept the unpinned form.
5. **Narrative drift.** Local `README.md` and the two GitHub-wins docs diverged (hundreds of lines). The protocol docs (`task_definition_v1.2.md`, `experiment_matrix_v1.md`) were checked and do **not** depend on the discarded local README text to stand — they reference only `CIE-Culinary-Bench/` internal paths, which are all present.

---

## E. Frozen benchmark hash check (no drift)

SHA-256 of each frozen file compared between the **local source** and the **canonical copy**. All matched exactly:

| File | Result |
|---|---|
| `CIE-Culinary-Bench/data/cie_culinary_bench.jsonl` | ✅ MATCH |
| `CIE-Culinary-Bench/schema/cie_sample.schema.json` | ✅ MATCH |
| `CIE-Culinary-Bench/docs/scoring_rubric.md` | ✅ MATCH |
| `CIE-Culinary-Bench/docs/task_definition.md` (frozen) | ✅ MATCH |
| `CIE-Culinary-Bench/docs/protocol_audit_v1.md` | ✅ MATCH |
| `CIE-Culinary-Bench/docs/task_definition_v1.2.md` (new) | ✅ MATCH |
| `CIE-Culinary-Bench/docs/experiment_matrix_v1.md` (new) | ✅ MATCH |
| `CIE-Culinary-Bench/manifest.json` | ✅ MATCH |
| `CIE-Culinary-Bench/results/dry_run_requests.jsonl` | ✅ MATCH |
| `CIE-Culinary-Bench/results/closed_evidence_anonymous_v1/summary.json` | ✅ MATCH |
| `CIE-Culinary-Bench/results/closed_evidence_anonymous_v1/experiment_manifest.json` | ✅ MATCH |

**Historical experiment signature:** the E3 `closed_evidence_anonymous_v1` block (`summary.json` + `experiment_manifest.json`) is byte-identical to the local frozen copy — no drift.

---

## F. Protocol documents preservation check

- `CIE-Culinary-Bench/docs/task_definition_v1.2.md` — present, **267 lines**, content intact.
- `CIE-Culinary-Bench/docs/experiment_matrix_v1.md` — present, **197 lines**, content intact.
- Internal path references (to `data/`, `schema/`, `validation_cases/`, `results/`, `docs/`, `manifest.json` inside `CIE-Culinary-Bench/`) all resolve — the benchmark sub-tree was preserved as a unit, so no broken links.
- Neither protocol doc depends on the discarded local root `README.md` or local `docs/cie_framework_v3.md` to be valid. Any minor narrative mismatch with GitHub's latest docs was recorded (D.5), not auto-fixed.

---

## G. Offline validation (no Hy3)

- **Dataset sanity (offline):** `cie_culinary_bench.jsonl` parses as 30 valid JSON records. Category distribution intact: Surface 4, Incremental 5, Structural 6, Conventional 6, Transformative 4, Adversarial Trap 5. IDs present (`CIE-001`…). No corruption.
- **Test suite:** 9 test files + 2 scripts exist. A static scan shows `tests/test_pipeline_e2e.py`, `tests/test_providers.py`, `scripts/cie_v3_validation.py`, `scripts/rescore_demo.py` contain live-API / network code. **These were NOT executed** (would call Hy3 / external endpoints, violating the no-Hy3 rule). The remaining test files were not run because they share the same import graph and would require a configured environment + dependency install. **No tests were executed in this reconciliation.** A safe next step (separate from this task) is to run `pytest tests/` in a venv with a valid `.env` once Gate 2 begins.

---

## H. git status summary & open human-decision conflicts

**`git status` (canonical tree):**
- Modified tracked files: **0** (all 12 GitHub-wins files untouched).
- Untracked (imported local-only): **11 groups** — `CIE-Culinary-Bench/`, `LICENSE`, `docs/architecture.md`, `docs/cie_framework.md`, `examples/*.json` (×3), `scripts/*.py` (×2), `src/creative_recipe/`, `tests/`.
- `.env`: ignored, not staged. ✅

**Conflicts requiring your decision (do NOT auto-resolve):**
1. **`requirements.txt` pins** — GitHub kept unpinned; local had precise pins. Adopt local pins? (deps set is identical, so low risk either way).
2. **`.env.example` additions** — local had 15 extra lines not carried over. Review for needed variables.
3. **`README.md` narrative** — local had 347 more lines (project-specific). Re-sync or keep GitHub's scaffold?
4. **`.gitignore` additions** — local had 52 extra lines. Verify no needed ignore rules were dropped.
5. **`docs/cie_framework_v3.md` / `docs/cie_validation_report.md`** — local versions differed by 382 / 249 lines. Confirm GitHub `main` is truly the intended latest (it is the source of truth per your rule, but the large diff suggests the local copies may have held fixes).
6. **Flatten `CIE-Culinary-Bench`?** Deferred by instruction. Decide later whether to merge into root `data/ scripts/ results/`.
7. **Commit / push** — not performed (you forbade push). The imported content is currently untracked, ready for you to review and commit when desired.

---

## Summary

The canonical working tree at `C:\Users\SUNYIXI\Desktop\canonical_NewwwRecipe` now contains the GitHub `main` scaffold (authoritative, untouched) **plus** all local development work, with the benchmark fully preserved and zero frozen-hash drift. The two new protocol documents survived intact. No Hy3 was called, no frozen dataset/gold/rubric/result was modified, and no push was made.
