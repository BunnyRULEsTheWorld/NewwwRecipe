# CIE-Bench / Creative Recipe AI

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务个人作品。  
> 本项目并非腾讯官方发布项目。

## 这个项目在做什么

我想做一个能根据现有食材生成创意料理的应用，但在实际尝试过程中，很快遇到了一个问题：

**什么样的菜谱才算“有创意”？**

如果只看新奇程度，模型很容易通过加入少见食材、复杂技法或者专业术语得到一个“看起来很创新”的结果，但这些组合不一定合理，也不一定真的比已有做法多了新的价值。

所以项目目前分成两部分：

- **Creative Recipe AI**：根据用户现有食材、偏好和约束生成候选料理；
- **CIE-Bench**：评估这些候选到底是不是有依据、有实际变化、并且值得尝试的创新。

CIE-Bench 目前也是这个项目中投入最多的部分。

## CIE 怎么评

除了最终菜谱，我还让模型输出一份结构化的 Innovation Trace，用来说明它是怎么得到这个创意的。Trace 目前分为六部分：

1. Existing Culinary Context：最接近哪些已有菜品、技法或食材用法；
2. Ingredient & Technique Knowledge：用了哪些食材和烹饪知识；
3. Innovation Delta：相比已有做法具体改了什么；
4. Mechanistic Justification：为什么这种变化在风味、质地或烹饪机制上可能成立；
5. Creative Hypothesis：希望得到什么新的体验；
6. Risk & Constraint：这个方案可能在哪里失败。

在此基础上，CIE 用六个维度进行评分：

| 维度 | 权重 |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

另外还加了一些限制，例如：如果连已有 precedent 都说不清楚，相关维度不能直接打高分；如果基础知识本身不可靠，Innovation Delta 也不能因为“变化很大”就拿高分。

## 现在做到哪了

截至 2026-08-27，已经完成了一个可以实际跑的 benchmark MVP。

目前包括：

- 一套 30 个 case 的冻结 benchmark；
- 对应的 schema、gold annotation、rubric、provenance 和质量控制文档；
- 可以调用真实 Hy3 的评测 runner；
- 一次完整的 anonymous trace-conditioned 主实验；
- 对部分失败 run 和旧 baseline 的单独归档。

当前主实验一共运行了 33 条记录，33 条全部成功解析。

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

早期还做过一个三个案例的小测试，用来确认 rubric 至少能把明显不同的结果排开：

```text
High 8.50 > Partial 6.60 > Low 4.20
```

这个结果现在只作为 smoke test 保留，不作为主要实验结论。

## 目前还不能说明什么

现在这套主实验把完整 Innovation Trace 提供给 evaluator，所以分数里可能包含较强的信息提示。换句话说，当前结果能说明 **这套 evaluator 在 trace-conditioned 条件下已经可以工作**，但还不能直接说明它在信息更少的情况下同样可靠。

接下来主要补四类实验：

- evidence-only：去掉可能过强的 trace 信息后重新评测；
- repeated scoring：同一个样本重复评估，观察波动；
- human agreement：和人工标注比较；
- adversarial validation：测试堆术语、伪引用、随机稀有组合等方式能不能骗到高分。

这些结果完成之后，才能更完整地讨论 CIE 的可靠性和适用范围。

## Creative Recipe AI

应用侧目前按“冰箱里有什么”这个场景设计。

用户可以输入或选择已有食材，再补充口味偏好和简单约束。系统生成多个候选，而不是直接返回第一次采样结果；随后用 CIE 对候选进行评分和筛选，再把最终结果展示给用户。

计划中的流程：

```text
用户输入
  ↓
Hy3 生成多个候选料理
  ↓
Recipe Concept + Innovation Trace
  ↓
CIE 评估
  ↓
候选排序和筛选
  ↓
展示料理、做法、创意解释和风险
```

## 仓库结构

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── docs/                    # 项目方案、CIE 设计和实验说明
├── src/                     # 应用与 CIE 实现
├── data/                    # CIE-Culinary-Bench
├── scripts/                 # benchmark 和验证脚本
├── results/                 # 实验结果
└── examples/                # 典型 case 和 demo 输出
```

当前公开仓库还在从本地开发目录继续同步，已经完成但尚未上传的 artifact 会逐步补进对应目录。

## 运行环境

- Python 3.11+
- Hy3 API access
- OpenAI-compatible Python SDK

创建环境：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

复制环境变量模板：

```bash
copy .env.example .env
```

然后在本地 `.env` 中填写 API Key。真实密钥不会提交到仓库。

## 文档

- [项目方案](docs/submission_proposal.md)
- [CIE v3 Framework](docs/cie_framework_v3.md)
- [早期三案例 Validation Report](docs/cie_validation_report.md)

## 最终提交前还要完成

- 补齐公开仓库中的完整 benchmark、runner 和结果文件；
- 完成 evidence-only、重复评测、人工一致性和对抗性实验；
- 整理典型失败案例和模型能力边界；
- 完成 Creative Recipe AI 的应用整合和 UI；
- 录制 2 分钟以内的 demo 视频或 GIF。

## Security

API Key 只通过环境变量或本地 `.env` 传入；仓库只保留 `.env.example`。
