# WorkBuddy Repository Instructions

These instructions apply to all future automated edits in this repository.

## Source of truth

- GitHub `main` is the only canonical project version.
- Read `PROJECT_STATE.md` before making project-level decisions.
- Read `docs/versioning.md` before any repository synchronization or release task.

## Before changing files

1. Update local `main` from `origin/main` with fast-forward only.
2. Create a dedicated task branch.
3. Inspect the current repository state and relevant files before editing.
4. Do not assume a local export, ZIP, attachment, or filename containing `final` is newer than Git history.

## Protected project facts

Do not silently alter these facts unless the task explicitly asks for a researched change and the corresponding artifacts are updated consistently:

- Innovation Trace currently has six stages: Existing Culinary Context; Ingredient & Technique Knowledge; Innovation Delta; Mechanistic Justification; Creative Hypothesis; Risk & Constraint.
- CIE research weights are 15 / 15 / 25 / 20 / 15 / 10 percent for the six dimensions documented in `PROJECT_STATE.md`.
- Current benchmark MVP has 30 frozen cases.
- Current canonical trace-conditioned metrics are Accuracy 73.3%, Macro-F1 0.675, Mean Spearman 0.570, MAE 0.661, ranking pairwise accuracy 86.7%, parse/API success 100%.
- These metrics must not be described as evidence-only results.

## Benchmark integrity

- Treat frozen benchmark cases, gold annotations and canonical result files as versioned research artifacts.
- Do not regenerate missing historical artifacts from memory or approximate values.
- If an expected artifact is missing, report it as missing and locate/import the original working copy.
- Changes to frozen data should be explicit `data:` commits and should update documentation and validation outputs together.

## Secrets and generated files

Never commit:

- `.env`
- API keys or tokens
- virtual environments
- caches / temporary files
- IDE metadata

Use `.env.example` for configuration examples.

## Validation

Before proposing integration:

```bash
git diff --check
pytest
```

Also run task-specific validation for benchmark/evaluation changes. Inspect output files instead of assuming a successful process means correct results.

## Integration policy

- Ordinary development must not be done directly on `main`.
- Prefer small coherent commits.
- Rebase the task branch on current `origin/main` before integration.
- Never force-push `main`.
- After a milestone is complete and reproducible, use a Git tag rather than creating another copied “latest” folder.
