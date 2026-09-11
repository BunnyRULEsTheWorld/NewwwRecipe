# CIE-Culinary-Bench v1.1

CIE-Culinary-Bench 是一个面向大语言模型的料理创新评估基准。它不把“陌生、昂贵、技术复杂”自动视作创新，而要求模型回答四件事：料理从何而来、发生了什么可定位的变化、为什么在味觉/质构/工艺上可能成立，以及人类证据是否支持其实现。

## 本版范围

- 30 个样本：9 个竞技案例、11 个专家/餐厅/文献案例、5 个传统 baseline、5 个完全人工构造的 adversarial trap。
- v1.1 新增真实餐厅案例 CIE-025（Nusr-Et 24K Gold Tomahawk），补足 Surface Innovation 与 luxury-signaling 反例；不是为凑数而合成的菜。
- 每条样本保留用户指定的七个一级字段，并为事实性叙述加入 `[source-id]` 引用标记。
- 人工推理、机制判断和 1–5 分是 benchmark annotation，不冒充厨师原话。

## 文件

- `data/cie_culinary_bench.json`：主数据（JSON array）。
- `data/cie_culinary_bench.jsonl`：逐行版本。
- `docs/dataset_card.md`：用途、范围、限制与推荐任务。
- `docs/annotation_guideline.md`：可操作评分锚点、类别判定与复核流程。
- `docs/task_definition.md`：Classification、Scoring、Ranking 三项正式任务协议。
- `docs/scoring_rubric.md` / `schema/scoring_rubric.json`：人类可读与机器可读的1–5锚点。
- `docs/project_submission_checklist.md`：逐项映射腾讯任务书，并诚实标出仍待完成的部分。
- `docs/protocol_audit_v1.md`：**semantic annotation leakage 审计**；说明为何已完成的实证 run 只能记为 `trace_conditioned`、以及 `evidence_only` 视图的重设计方案。
- `docs/source_registry.md` / `.json`：来源、证据层级和每案映射。
- `docs/fabrication_disclosure.md`：合成内容及证据不足项逐案披露。
- `docs/quality_report.md`：自动校验、覆盖率、长度和已知限制。
- `schema/cie_sample.schema.json`：JSON Schema。
- `validation_cases/`：好/中/差输出、对抗提示、正式 ranking sets。
- `scripts/validate_dataset.py`：数据验证器。
- `scripts/run_evaluation.py`：Hy3/OpenAI-compatible 调用与原始输出留档。
- `scripts/score_predictions.py`：Macro-F1、MAE、Spearman、QWK、ranking 和一致性指标。
- `results/`：实证运行结果与验证状态，见下节「当前实证状态」。

## 快速验证

```bash
python scripts/validate_dataset.py data/cie_culinary_bench.json docs/source_registry.json
```

## 当前实证状态（2026-08-27）

**Hy3 已实际运行过，但 formal benchmark validation 仍为 INCOMPLETE。** 权威状态见
[`results/validation_status.md`](results/validation_status.md)。

| 项目 | 状态 |
|---|---|
| trace_conditioned anonymous run | **COMPLETE — 33/33, runs=1** |
| evidence_only run | **NOT RUN** |
| ≥3 次重复一致性 | **NOT RUN** |
| good_medium_bad 实证判别 | **NOT RUN** |
| human_evidence_aware `realization_quality` | **NOT RUN** |
| formal benchmark validation | **INCOMPLETE** |

已完成的那一次 run 在 `results/closed_evidence_anonymous_v1/`（classification 73.3% / macro-F1
0.675、mean dimension Spearman 0.570、ranking pairwise 86.7%）。

> ⚠️ **该数字是 `trace_conditioned`，不是 `evidence_only`。** 模型看到了完整
> `innovation_trace`，而它本身属于人工 gold annotation 并含评价性结论（`strength` 在 30/30 样本
> 全部存在）。因此这些数字衡量的是「与给定人类推理链的一致性」，**不能**作为 evidence-only 料理创新
> 评估结果引用。详见 [`docs/protocol_audit_v1.md`](docs/protocol_audit_v1.md)。
>
> `experiment_manifest.json` 中 `track = closed_evidence` 是**运行时 provenance 标识**（参与
> `experiment_signature` 哈希，故冻结不改）；审计后其 measurement construct 重新解释为
> `trace_conditioned`。即：**track/config provenance ≠ evaluation construct name。**

结果目录：

```
results/
├── closed_evidence_anonymous_v1/   # 权威 run：33/33 trace_conditioned（唯一可引用）
├── baseline_with_id/               # 已弃用：prompt 中暴露真实 ID（构造性泄漏）
├── deprecated_partial_run2/        # 已弃用：16/33 成功、17 次 APIConnectionError
├── dry_run_requests.jsonl          # 打包期 prompt 构造 dry-run 留档（v1.1 冻结件）
└── validation_status.md            # 权威验证状态
```

## 运行 Hy3 评测

当前使用的 runner 是 `scripts/benchmark_pipeline.py`，它复用主项目的 `Hy3LLMClient` / `Config`，
从项目根 `.env` 读取 `HY3_API_KEY` / `HY3_BASE_URL` / `HY3_MODEL`；不要把 API Key 写进仓库。

```bash
# 在 creative-recipe-ai/.env 中配置 HY3_API_KEY / HY3_BASE_URL / HY3_MODEL
cd CIE-Culinary-Bench
PYTHONPATH=../src python scripts/benchmark_pipeline.py            # 增量落盘 + resume
PYTHONPATH=../src python scripts/benchmark_pipeline.py --analyze  # 仅离线重算指标（0 次 API）
```

`benchmark_pipeline.py` 会写出 `predictions.jsonl` / `experiment_manifest.json` / `summary.json` /
`evaluation_report.md` / `error_analysis.md`；只有 33/33 全部 `status == "ok"` 时才置
`experiment_complete: true` 并输出 headline metrics，否则标记为 partial。

早期附带的参考脚本（使用 `CIE_API_*` 变量，非当前 runner）：

```bash
python scripts/run_evaluation.py --task all --runs 3 --output results/hy3_predictions.jsonl
python scripts/score_predictions.py results/hy3_predictions.jsonl
```

仅检查请求构造、标签泄漏与任务数量时：

```bash
python scripts/run_evaluation.py --task all --runs 3 --dry-run --output results/dry_run_requests.jsonl
```

## 引用约定

事实性句子中的 `[CIE-xxx-Sn]` 指向 `docs/source_registry.*`。`judge_comment` 在没有公开逐字稿时使用“证据性转述（非逐字引语）”，绝不加伪引号。无引用的 `creative_hypothesis`、机制、风险、分数和 `gold_reasoning` 默认是研究团队基于已列证据的分析性标注。

## 使用边界

该数据集用于模型评价与研究，不是配方、食品安全或医疗建议。涉及食品安全的表述采用风险管理语言，不把民间禁忌写成确定毒理结论。商业名称和商标归各权利人所有；本包只保存短篇事实性摘要与外链，不复制网页正文。

本仓库是个人/活动作品，不是腾讯或 Hy3 官方 benchmark。
