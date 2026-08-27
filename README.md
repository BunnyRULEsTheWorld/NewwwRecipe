# CIE-Bench / Creative Recipe AI

> Personal project for the 2026 Tencent Rhino-Bird Open Source Practice — Hunyuan Large Language Model Project.  
> 本项目为个人 / 活动作品，**并非腾讯官方发布项目**。

## 项目定位

**CIE-Bench（Culinary Innovation Evaluation Benchmark）** 是一套面向开放式创新任务的评价框架；**Creative Recipe AI** 是它的真实应用载体。

本项目不是单纯让 LLM “生成更奇怪的菜谱”，而是研究：

> 如何判断一个模型是否真正提出了**有知识依据、有创新增量、有实际价值**的创意，而不是仅靠稀有组合、漂亮叙事或专业术语制造“看起来很创新”的文本？

核心命题：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

评价对象不仅包含最终 Recipe Concept，还包含结构化 **Culinary Innovation Reasoning Trace**，使创新过程可以被审查、评分和归因。

## CIE 核心框架

CIE v3 将创新过程拆成六阶段 Innovation Trace：

1. Existing Culinary Context
2. Ingredient & Technique Knowledge
3. Innovation Delta
4. Mechanistic Justification
5. Creative Hypothesis
6. Risk & Constraint

六维 Rubric：

| 维度 | 权重 |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

框架还加入 Precedent 强制、Grounding Ceiling、Mechanistic Justification、Innovation Magnitude 非单调奖励、Risk & Constraint 等 anti-hallucination 机制。

## 当前进展（2026-08-27）

项目已经从三案例概念验证推进到 **benchmark MVP + canonical evaluation run** 阶段。

### 已完成

- CIE-Culinary-Bench 的核心数据方案、schema / gold / rubric、provenance 与质量控制设计已冻结；
- 当前核心 benchmark 为 **30-case frozen dataset**；
- 可复现评测 runner 已打通真实 Hy3 调用；
- 当前 canonical 主结果保存在 `results/closed_evidence_anonymous_v1/` 对应的 **anonymous trace-conditioned** 评测轨道；
- canonical run：**33 / 33 成功完成，Parse/API success = 100%**；
- 当前 trace-conditioned 指标：

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

早期三案例 smoke test 也完成了 Low / Partial / High-value 的正确排序：

```text
High 8.50 > Partial 6.60 > Low 4.20
```

### 尚未完成 / 正在补齐

当前结果**不能直接等同于最终 benchmark 有效性结论**。下一阶段重点是把不同信息条件拆成独立验证轨道，并完成：

- Evidence-only track；
- ≥3 次重复评测与分数波动分析；
- 与人工标注的一致性验证；
- Good > Medium > Bad 判别力验证的系统化统计；
- adversarial / anti-gaming 验证；
- human-evidence-aware track；
- 典型失败模式与能力边界分析。

历史上出现过一次 **16 / 33 成功、17 个 APIConnectionError** 的 partial run；该结果已迁入 `results/deprecated_partial_run2/`，仅保留 provenance，**不作为有效 benchmark 结果**。带 ID 的 baseline 也已 deprecated，当前 canonical 结果以 anonymous trace-conditioned run 为准。

## Creative Recipe AI 应用

面向“冰箱里有什么”的真实场景：用户选择或输入已有食材、偏好与简单状态约束，Hy3 生成多个候选 Recipe Concept + Innovation Trace，CIE 对候选进行评价、筛选和解释，再向用户展示最终创意料理。

目标流程：

```text
User Input
   ↓
Hy3 Creative Generator
   ↓
Recipe Concept + Innovation Trace
   ↓
CIE Evaluator
   ↓
Rubric + Rules + Evidence / Risk Checks
   ↓
Ranking / Filtering / Attribution
   ↓
User-facing Recipe
```

## 仓库结构

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── docs/
│   ├── submission_proposal.md
│   ├── cie_framework_v3.md
│   └── cie_validation_report.md
├── src/                     # 应用与 CIE 正式实现
├── data/                    # CIE-Culinary-Bench
├── scripts/                 # benchmark runner / validation
├── results/                 # canonical / deprecated / validation results
└── examples/                # 典型 case 与 demo 输出
```

> 当前公开仓库仍在从本地开发版本同步完整代码与 benchmark artifact；本 README 中“已完成”描述的是当前项目真实开发状态，而不代表所有 artifact 已经全部上传到本公开仓库。

## 环境要求

- Python 3.11+
- Hy3 API access
- OpenAI-compatible Python SDK

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

真实 API Key 仅写入本地 `.env`，不得提交到 GitHub。

## 文档

- [项目方案](docs/submission_proposal.md)
- [CIE v3 Framework](docs/cie_framework_v3.md)
- [早期三案例 Validation Report](docs/cie_validation_report.md)

## 最终交付目标

- 可运行的 Hy3 Creative Recipe AI；
- CIE 评价框架与自动 / 半自动评测流程；
- CIE-Culinary-Bench（含难例、反例、provenance 与数据说明）；
- 判别力、一致性与对抗性验证；
- 完整评测结果与典型 case 归因；
- 模型失败模式与能力边界分析；
- 2 分钟以内 demo 视频或 GIF。

## Security

- API Key 仅通过环境变量 / `.env` 传入；
- `.env` 已加入 `.gitignore`；
- 仓库只提供 `.env.example`，不包含真实密钥。
