# 腾讯犀牛鸟实战任务产出映射

本 ZIP 是 benchmark / evaluation component，不冒充完整应用提交。依据项目任务书，当前状态如下。

_最后更新：2026-08-27。权威状态见 `results/validation_status.md`；协议审计见 `docs/protocol_audit_v1.md`。_

> ⚠️ **不要声称 benchmark validation 已完成。** 已有 1 次真实 Hy3 run（33/33、`runs=1`），但它是
> `trace_conditioned` 而非 `evidence_only`，且重复一致性与判别力实证均未运行。
> **formal benchmark validation = INCOMPLETE。**

| 要求 | 状态 | 本包证据 / 后续动作 |
|---|---|---|
| 5个以上关键维度及可操作标准 | 已完成 | 六维 rubric；`docs/scoring_rubric.md` 与机器可读 JSON |
| 样本来源、构造与覆盖说明 | 已完成 | 30条数据、61条来源、source registry、fabrication disclosure |
| 难例与反例 | 已完成 | 5条完全合成 trap、失败竞赛实例、CIE-025 luxury bias 反例 |
| 自动/半自动评测流程 | 已完成 | `scripts/benchmark_pipeline.py`：增量落盘、真 resume（status+prompt_sha256+experiment_signature 三校验）、指数退避、连接错误熔断、`--analyze` 离线指标 |
| 判别力验证**材料** | 已完成 | 4组 good/medium/bad（`validation_cases/good_medium_bad_cases.jsonl`） |
| 判别力**实证结果** | **未运行** | runner 尚未执行 good > medium > bad 判别任务 |
| 一致性验证**设计** | 已完成 | 设计为3次重复，输出 modal agreement 与 within-case score SD |
| 一致性**实证结果** | **未运行** | 已完成的正式 run 为 `runs=1`，未做 ≥3 次重复 |
| 对抗性验证设计 | 已完成 | trap accuracy、CIE-025 overrating rate、五类对抗 prompt |
| 在自构样本上完整运行 Hy3 | **部分完成** | `results/closed_evidence_anonymous_v1/`：33/33 units、parse 100%、API failures 0、`experiment_complete: true`；但仅 `runs=1` |
| 完整结果表与典型归因 | **已生成（附 construct 限定）** | `evaluation_report.md`（含 confusion matrix / Spearman / MAE / QWK / ranking）与 `error_analysis.md`（8 例分类错误、最大维度偏差、ranking 错误、bias 诊断）。数字为 `trace_conditioned`，非 evidence-only |
| **输入视图无语义泄漏** | **未达成** | `innovation_trace` 属人工 gold annotation 且含评价性结论（`strength` 在 30/30 样本存在）。见 `docs/protocol_audit_v1.md`；`evidence_only` 视图尚未实现 |
| `evidence_only` run | **未运行** | 依赖上一行的视图实现 |
| `human_evidence_aware` track（`realization_quality`） | **未运行** | 审计 §4 采纳 A+C：`realization_quality` 在 evidence-only 输入下不可辨识，移入该诊断赛道 |
| 面向真实用户的可运行应用 | 不在本数据 ZIP 内 | 需在项目仓库实现料理创意生成/评审界面并调用 Hy3 |
| 2分钟 demo/GIF | 不在本数据 ZIP 内 | 应在应用与最终 validation 完成后录制 |

## 已完成 run 的引用口径

- 可引用：`results/closed_evidence_anonymous_v1/`（classification 73.3% / macro-F1 0.675、mean
  dimension Spearman 0.570 / mean MAE 0.661、ranking pairwise 86.7%），**必须同时标注
  `trace_conditioned` 与 `runs=1`**。
- 不可引用：`results/baseline_with_id/`（prompt 暴露真实 ID，构造性泄漏）、
  `results/deprecated_partial_run2/`（16/33 成功、17 次 APIConnectionError）。
- `experiment_manifest.json` 中 `track = closed_evidence` 为运行时 provenance（参与
  `experiment_signature`，冻结不改）；measurement construct 为 `trace_conditioned`。
  **track/config provenance ≠ evaluation construct name。**

API Key 必须通过环境变量传入，不得硬编码。仓库与 README 应继续标注为个人/活动作品，而非腾讯官方项目。
