# CIE-Bench / Creative Recipe AI

> Personal project for the 2026 Tencent Rhino-Bird Open Source Practice — Hunyuan Large Language Model Project.  
> 本项目为个人/活动作品，**并非腾讯官方发布项目**。

## 项目简介

CIE-Bench（Culinary Innovation Evaluation Benchmark）是一套面向开放式创新任务的创新能力评价框架。项目以“创意料理生成”作为可观察、可验证的真实应用场景，核心关注点不是让大语言模型生成更“奇怪”的菜谱，而是评估模型是否能够在已有知识基础上提出**有依据、有增量、有价值**的创新。

核心假设：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

项目通过 Hy3 完成生成与 LLM-as-judge 评测，并将最终 Recipe Concept 与结构化 Culinary Innovation Reasoning Trace 一并纳入评价。

## 核心设计

CIE v3 将创新过程显式拆成六阶段 Innovation Trace：

1. Existing Culinary Context
2. Ingredient & Technique Knowledge
3. Innovation Delta
4. Mechanistic Justification
5. Creative Hypothesis
6. Risk & Constraint

评价器采用六维 Rubric：

| 维度 | 权重 |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

同时设置 Precedent 强制、Grounding 天花板、Mechanistic Justification、Magnitude 非单调、Risk & Constraint 等 anti-hallucination 机制，避免“越奇怪越创新”。

## 当前阶段结果

已使用真实 Hy3（经 OpenAI-compatible 接口）完成 CIE v3 的初步判别力验证：

```text
EXPECTED:  High > Partial > Low
ACTUAL:    8.50 > 6.60 > 4.20
RESULT:    PASS
```

这说明框架在初步实验中能够将“高价值创新”“部分创新”“普通但合理的料理”正确排序。

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
├── src/                     # 应用与 CIE 正式实现（持续同步）
├── data/                    # CIE-Culinary-Bench 样本集
├── scripts/                 # 评测/验证脚本
├── results/                 # 完整评测结果与统计
└── examples/                # 典型 case 与 demo 输出
```

> 当前仓库正在从本地开发版本向公开提交结构同步。方案阶段优先公开研究设计与已完成验证；最终提交前将补齐可运行应用、完整 benchmark、评测脚本、完整结果和 demo。

## 环境要求

- Python 3.11+
- Hy3 API access
- OpenAI-compatible Python SDK

安装依赖：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

配置环境变量：

```bash
copy .env.example .env
```

然后在 `.env` 中填写本地密钥。**禁止将真实 API Key 提交至仓库。**

## 文档

- [方案文档](docs/submission_proposal.md)
- [CIE v3 Framework](docs/cie_framework_v3.md)
- [CIE v3 Validation Report](docs/cie_validation_report.md)

## 最终交付目标

按照实战任务要求，最终仓库将包含：

- 可运行的 Hy3 创意料理应用
- CIE 评价框架与自动/半自动评测流程
- CIE-Culinary-Bench 评测样本集（含难例/反例）
- 判别力、一致性与对抗性验证
- 完整评测结果与典型 case 归因分析
- 模型失败模式与能力边界分析
- 2 分钟以内 demo 视频或 GIF

## Security

- API Key 仅通过环境变量或 `.env` 传入。
- `.env` 已加入 `.gitignore`。
- 仓库仅提供 `.env.example`，不包含任何真实密钥。
