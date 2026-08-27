# NewwwRecipe

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务个人作品。  
> 本项目不是腾讯官方发布项目。

NewwwRecipe 是一个基于 Hy3 的创意菜谱生成与评估项目。

项目最开始想解决的问题很简单：如果家里只有一些零散食材，能不能让模型给出真正值得尝试的新做法？实际做下来，我发现“生成一道菜”并不难，更难的是判断一个结果到底有没有创意，以及这种创意是不是建立在合理的料理知识上。

所以现在项目主要有三部分：

- **NewwwRecipe 应用**：根据食材、口味和简单约束生成候选料理；
- **CIE（Culinary Innovation Evaluation）**：给候选料理做结构化评价和排序；
- **CIE-Culinary-Bench**：用来开发和验证 CIE 的评测数据集。

目前工作量主要集中在 CIE 和 benchmark 上，应用侧会在评测流程稳定后接上。

## CIE 怎么评

我不只让评估器看最终菜谱，还会给它一份结构化的 Innovation Trace。这样可以检查模型是基于什么已有做法、做了什么变化，以及这些变化有没有料理知识或机制上的依据。

Trace 目前分成六部分：

1. **Existing Culinary Context**：最接近哪些已有菜品、技法或食材用法；
2. **Ingredient & Technique Knowledge**：涉及哪些食材和烹饪知识；
3. **Innovation Delta**：相比已有做法具体改了什么；
4. **Mechanistic Justification**：为什么这种变化在风味、质地或烹饪机制上可能成立；
5. **Creative Hypothesis**：希望得到什么新的风味、口感或食用体验；
6. **Risk & Constraint**：这个方案可能在哪里失败。

CIE 再从六个维度打分：

| 维度 | 权重 |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

另外有一些约束。例如，如果对已有做法的判断都不可靠，Innovation Delta 不能只因为“变化很大”就得到高分；“这个组合很少见”本身也不能算机制解释。

详细规则见 [`docs/cie_framework_v3.md`](docs/cie_framework_v3.md)。

## 现在做到哪了

截至 2026-08-27，已经完成一个可以实际运行的 benchmark MVP。

目前有：

- 30 个 case 的冻结数据集；
- schema、gold annotation、rubric、provenance 和数据质量说明；
- 可以调用真实 Hy3 的评测 runner；
- 一次完整的 anonymous trace-conditioned 主实验；
- 对旧 baseline 和失败 run 的单独归档。

当前主实验共有 33 条评测记录，33 条都成功完成并解析。

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

在更早的阶段还做过一个三个案例的小测试：Low / Partial / High-value 三档的得分顺序为 `4.20 < 6.60 < 8.50`。这个结果现在只保留作 smoke test，正式结果以完整 benchmark 实验为准。

## 这些结果目前有什么限制

现在的主实验属于 **trace-conditioned** 设置，也就是 evaluator 可以看到完整的 Innovation Trace。Trace 中的信息可能让任务变得更容易，因此这组结果还不能单独说明 CIE 在更弱信息条件下同样可靠。

接下来会补几组实验：

- **evidence-only**：去掉完整 trace，只保留更受限的信息；
- **repeated scoring**：同一样本重复评估，观察分数和排序波动；
- **human agreement**：和人工标注比较；
- **adversarial validation**：测试堆砌术语、虚构先例、随机加入稀有食材等做法会不会骗到高分。

历史上有一次 partial run 只成功了 16/33 条，另外 17 条是 `APIConnectionError`。这批结果只保留作运行记录，不计入正式 benchmark 指标。

## NewwwRecipe 应用

应用场景是“冰箱里有什么”。用户可以选择或输入已有食材，再补充口味和简单约束。系统生成多个候选，用 CIE 排序后再展示结果，而不是直接返回第一次生成的菜谱。

计划流程：

```text
用户输入食材 / 偏好
        ↓
      Hy3 生成
        ↓
多个 Recipe Concept + Innovation Trace
        ↓
      CIE 评估
        ↓
     排序和筛选
        ↓
菜谱 + 做法 + 创意解释 + 风险提示
```

## 仓库结构

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── docs/                    # 项目方案、CIE 设计和实验记录
├── src/                     # NewwwRecipe 与 CIE 实现
├── data/                    # CIE-Culinary-Bench
├── scripts/                 # benchmark / validation 脚本
├── results/                 # 实验结果
└── examples/                # 典型 case 和 demo 输出
```

当前公开仓库还在从本地开发目录同步，部分已经完成的代码和数据文件尚未全部上传。

## 环境

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

然后在本地 `.env` 中填写 API Key。真实密钥不会提交到仓库。

## 文档

- [项目方案](docs/submission_proposal.md)
- [CIE v3 设计说明](docs/cie_framework_v3.md)
- [早期三案例测试记录](docs/cie_validation_report.md)

## 最终提交前的工作

- 把完整 benchmark、runner 和结果文件同步到公开仓库；
- 完成 evidence-only、重复评测、人工一致性和对抗性实验；
- 整理典型失败案例；
- 接通 NewwwRecipe 的生成、评价和 UI 流程；
- 完成最终评测和 2 分钟以内的 demo。

## API Key

API Key 只通过环境变量或本地 `.env` 传入；仓库只保留 `.env.example`。
