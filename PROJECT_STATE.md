# Project State — NewwwRecipe

> Canonical project baseline. Last consolidated: 2026-08-31.
>
> **Source of truth:** the `main` branch of this repository.

## 1. Project identity

NewwwRecipe is a personal project for the 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务, Task 1: open-ended AI application + custom evaluation criteria.

The project has three connected parts:

1. **NewwwRecipe application** — given ingredients / preferences / simple constraints, generate candidate creative recipes with Hy3.
2. **CIE (Culinary Innovation Evaluation)** — evaluate and rank generated culinary ideas.
3. **CIE-Culinary-Bench** — benchmark used to develop and validate CIE.

## 2. Current CIE research baseline

### Innovation Trace

The current research specification uses six stages:

1. Existing Culinary Context
2. Ingredient & Technique Knowledge
3. Innovation Delta
4. Mechanistic Justification
5. Creative Hypothesis
6. Risk & Constraint

### Scoring dimensions

| Dimension | Weight |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

The detailed research specification is in `docs/cie_framework_v3.md`.

## 3. Benchmark baseline

Current benchmark MVP status:

- 30 frozen cases;
- anonymous trace-conditioned main experiment completed;
- 33 / 33 evaluation records completed and parsed successfully;
- earlier 3-case Low / Partial / High-value experiment retained only as a smoke test;
- one historical partial run (16 / 33 success, 17 / 33 `APIConnectionError`) is not part of the formal metrics.

### Main experiment metrics

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

### Interpretation constraint

These results are **trace-conditioned**. The evaluator can see the full Innovation Trace, which contains information that may make the task easier. Therefore these results must **not** be described as evidence-only validation.

Planned validation additions:

- evidence-only / reduced-information evaluation;
- repeated scoring stability;
- human agreement;
- adversarial validation;
- failure-mode analysis.

## 4. Repository synchronization status

As of this consolidation, GitHub contains the up-to-date project narrative and CIE research documents, but the repository still has placeholder-only directories for parts of the implementation / benchmark package.

The following directories must ultimately contain the real project artifacts rather than only README placeholders:

- `src/` — application + CIE implementation;
- `data/` — frozen CIE-Culinary-Bench data, schema, annotations and provenance as applicable;
- `scripts/` — benchmark / validation runners;
- `results/` — canonical result tables / machine-readable outputs;
- `examples/` — representative cases and demo outputs.

Do **not** invent or regenerate missing artifacts merely to make the repository look complete. Import the actual files from the working copy that produced the recorded experiments.

## 5. Version rule from now on

There is exactly one formal latest version:

> **`origin/main` on GitHub**

Local folders, exported ZIPs, chat attachments and WorkBuddy workspaces are working copies only. They become official only after they are committed and pushed to GitHub.

All future updates must follow `docs/versioning.md` and the instructions in `AGENTS.md`.

## 6. Next milestone

The next repository milestone is to replace placeholder directories with the actual local implementation / benchmark artifacts, verify the commands from a clean checkout, then tag the repository baseline before continuing application UI and additional validation experiments.
