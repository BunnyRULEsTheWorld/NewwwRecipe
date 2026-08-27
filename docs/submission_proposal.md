# Creative Recipe AI × CIE-Bench 项目方案

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务  
> 任务方向：开放式场景——AI 应用与评判标准设计  
> 项目性质：个人 / 活动作品，非腾讯官方发布项目

---

## 1. 项目概述

本项目拟基于 Hy3 构建一个面向真实用户的**创意料理生成与筛选应用**，并围绕该应用设计一套可复用的开放式创新能力评价框架 **CIE-Bench（Culinary Innovation Evaluation Benchmark）**。

项目的核心问题不是“让模型生成更奇怪的菜谱”，而是：

> 如何判断一个大语言模型是否真正产生了**有依据、有增量、有价值**的创新，而不是仅仅生成新奇、流畅、看起来合理的文本？

因此，本项目将“创意料理”作为可观察、可解释、可验证的应用载体，把模型输出从单纯的 Recipe 扩展为：

```text
Recipe Concept
+
Culinary Innovation Reasoning Trace
```

并以此为输入完成多维度评价、自动/半自动筛选、失败模式分析和能力边界研究。

项目的核心假设为：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

---

## 2. 目标用户与真实问题

### 2.1 目标用户

1. 希望利用家中现有食材获得新做法的普通用户；
2. 对创意料理、跨菜系搭配、风味实验感兴趣的烹饪爱好者；
3. 希望研究或评测大语言模型开放式创新能力的开发者与研究者。

### 2.2 用户痛点

现有菜谱生成类大模型应用通常存在以下问题：

- 容易把“罕见组合”误当成“创新”；
- 能给出看似专业的解释，但缺少真实料理知识与机制支撑；
- 无法说明与已有菜品相比究竟改变了什么；
- 缺少对失败风险、可执行性和实际价值的审查；
- 生成结果很多，但缺少可靠的自动筛选机制。

### 2.3 引入大模型的必要性

创意料理属于典型的开放式任务：不存在唯一标准答案，输入食材组合、用户偏好与烹饪条件也高度多样。传统规则系统难以覆盖跨食材、跨技法、跨菜系的知识组合。

Hy3 在本项目中承担两类角色：

- **生成端**：基于食材、偏好和约束生成 Recipe Concept 与结构化 Innovation Trace；
- **评估端**：在固定 Rubric 下执行 LLM-as-judge，对创新过程与结果进行结构化评分和归因。

生成与评价在实验设计中尽量分离，避免“同一模型既生成又自我认可”导致的评价偏差。

---

## 3. 总体设计思路

项目采用“**生成 → 显式推理轨迹 → 评价 → 筛选 → 解释反馈**”的闭环。

```text
用户输入食材 / 偏好 / 状态
          │
          ▼
   Hy3 Creative Generator
          │
          ├── Recipe Concept
          └── Innovation Trace
                  │
                  ▼
             CIE Evaluator
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Rubric评分   规则约束   风险/证据检查
       └──────────┼──────────┘
                  ▼
        候选排序 / 筛选 / 归因
                  │
                  ▼
        用户可读的创意料理结果
```

系统不会只问“这个菜有没有创意”，而会审查：

1. 模型理解了哪些已有料理知识；
2. 找到了哪些可改变的位置；
3. 相比已有方案到底改变了什么；
4. 为什么这种变化在机制上可能成立；
5. 这种变化创造了什么新价值；
6. 它可能在哪里失败。

---

## 4. Innovation Trace：显式创新过程

CIE v3 将创新过程拆成六个阶段。

### Stage 1 — Existing Culinary Context

定位最接近的已有料理、技法或食材用途，禁止通过“从未存在过”之类未经证实的叙述制造创新感。

### Stage 2 — Ingredient & Technique Knowledge

分析食材与技法的真实知识基础，包括风味、香气、质地、脂肪相互作用、烹饪机制等。

### Stage 3 — Innovation Delta

回答“相比已有料理，真正发生了什么变化”。重点识别：

- Ingredient Role Shift；
- Technique Innovation；
- Flavor Architecture Innovation；
- Texture Innovation；
- Presentation / Experience Innovation。

创新幅度不是越大越好；随机的大幅改变若缺少知识依据，不应获得高创新分。

### Stage 4 — Mechanistic Justification

要求给出烹饪科学、风味交互、化学机制、烹饪原理或历史先例等可辩护依据。

### Stage 5 — Creative Hypothesis

明确该创新希望创造的新体验，而不是简单复述食材组合。

### Stage 6 — Risk & Constraint

要求模型主动说明可能失败的位置、比例风险、技术边界和实现限制。

---

## 5. CIE-Bench 六维评估方法

CIE v3 使用 6 个可操作维度，由 Hy3 按 1–10 分结构化评分，并给出评分理由。

| 维度 | 权重 | 核心问题 |
| --- | ---: | --- |
| Culinary Knowledge Grounding | 15% | 是否真正理解料理知识，而非表面描述 |
| Existing Culinary Precedent Analysis | 15% | 是否能定位已有料理空间并进行比较 |
| Innovation Delta Quality & Magnitude | 25% | 是否存在真实、有效的创新增量 |
| Mechanistic Plausibility | 20% | 创新是否有可靠机制或经验依据 |
| Innovation Value / Exploration | 15% | 改变是否带来新的风味、口感、体验或利用价值 |
| Realization Quality | 10% | 最终方案是否可执行、合理、表达清楚 |

总分：

```text
CIE Score = Σ(score_d × weight_d)
```

### 5.1 可操作判定规则

为减少“较好”“基本符合”等模糊评价，本项目在 Rubric 中加入硬约束：

- 无法定位已有 precedent → Existing Culinary Precedent Analysis 不得进入高分档；
- `Culinary Knowledge Grounding < 5` 时，`Innovation Delta ≤ 6`；
- “因为很搭”“因为少见”等空洞理由不能作为 Mechanistic Justification；
- Innovation Magnitude 不采用单调奖励；
- 必须声明 Risk & Constraint，否则难以进入高可信创新档。

这些机制用于抑制“创新幻觉”，即模型通过稀有组合、复杂术语或漂亮叙事伪装创新。

---

## 6. 重点技术

### 6.1 Hy3 OpenAI-Compatible 调用

项目通过 Hy3 的 OpenAI-compatible 接口调用模型，API Key 仅通过环境变量传入，不硬编码或提交至 GitHub。

### 6.2 Structured Output

生成端与评价端均采用结构化字段，使 Recipe Concept、Innovation Trace、六维评分、理由、Innovation Delta 可被脚本直接解析、统计与复现。

### 6.3 LLM-as-Judge + Rule Constraints

评估不是单纯依赖一次自由文本打分，而采用：

- 固定 Rubric；
- 结构化 LLM-as-judge；
- Grounding Ceiling 等规则约束；
- 结果持久化；
- 人工抽检与一致性实验。

### 6.4 生成与评价分离

在有效性验证中固定 Recipe Concept 与 Innovation Trace，再由 Hy3 Judge 评分，以尽量隔离“生成器质量”与“评价框架质量”。

### 6.5 Benchmark 数据治理

CIE-Culinary-Bench 将记录：

- 样本来源；
- 菜品/概念描述；
- 参考依据；
- 难度与样本类型；
- 人工判断；
- fabrication disclosure；
- source registry。

样本集将包含普通样本、难例、反例和对抗性样本，而非只保留容易得分的案例。

---

## 7. 应用侧交互设计

应用主界面围绕真实“冰箱里有什么”的使用场景设计。

### 7.1 首页

标题：**What do we have?**

用户可以：

- 从冰箱式分类界面选择蔬菜、肉类等食材；
- 直接输入已有食材；
- 填写口味偏好和简单状态约束。

### 7.2 生成过程

系统生成多个候选创意并执行 CIE 评价与筛选，而不是直接展示第一次采样结果。

### 7.3 结果页

展示：

- 菜品名称与视觉结果；
- 食材与调料；
- 制作步骤；
- 食材特点；
- 搭配与机制解释；
- 最接近的已有料理及差异；
- 创新亮点；
- 尝试成本与失败风险；
- CIE 六维评分与解释。

用户可选择“重新生成”或“收藏/下一步”。

---

## 8. 评测样本与实验设计

### 8.1 样本覆盖

计划使用 CIE-Culinary-Bench，覆盖：

- 常规合理但低创新样本；
- 有局部变化的 Partial Innovation；
- 有角色迁移/技法/结构重构的 High-value Innovation；
- 随机稀有组合；
- 伪专业术语堆砌；
- 虚假 precedent / 虚假引用；
- 可执行性差但叙事漂亮的样本。

### 8.2 判别力验证

构造明显不同质量的 Low / Partial / High-value 输出，验证 CIE 是否能够正确排序。

### 8.3 一致性验证

计划进行：

- 同一输出重复多次评分的方差分析；
- CIE 结果与人工标注的一致程度比较；
- 对关键维度计算一致性指标。

### 8.4 对抗性验证

主动构造通过以下方式“骗分”的输出：

- 增加篇幅；
- 堆砌专业术语；
- 随机加入陌生食材；
- 编造历史先例；
- 伪造机制解释。

检验 CIE 的 anti-hallucination 规则能否阻断虚假高分。

---

## 9. 已完成的阶段性验证

当前已经使用真实 Hy3 完成 CIE v3 的初步判别力实验。

三个固定案例覆盖：

- Case A：普通合理料理，Low Innovation；
- Case B：有限技法桥接，Partial Innovation；
- Case C：角色迁移 + 技法组合 + 风味结构重构，High-value Innovation。

结果：

| Case | 预期水平 | CIE v3 总分 |
| --- | --- | ---: |
| A | Low Innovation | 4.20 |
| B | Partial Innovation | 6.60 |
| C | High-value Innovation | 8.50 |

```text
EXPECTED: C > B > A
ACTUAL:   8.50 > 6.60 > 4.20
RESULT:   PASS
```

该初步结果支持 CIE 的核心命题：框架能够区分“合理”“部分创新”和“高价值创新”，而不是简单把“罕见”当作“创新”。

需要强调的是：该实验目前主要证明**初步判别力**，尚不能替代后续更大样本上的一致性、对抗性和人工相关性验证。

---

## 10. 系统/仓库架构

计划采用如下公开仓库结构：

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
│
├── src/
│   └── creative_recipe/
│       ├── generator/          # Hy3 创意生成
│       ├── cie/                # CIE 正式评价器
│       ├── pipeline/           # 生成→评价→排序
│       └── ui/                 # 应用界面
│
├── data/
│   └── CIE-Culinary-Bench/
│       ├── data/
│       ├── docs/
│       └── schema/
│
├── scripts/
│   ├── run_app.py
│   ├── run_evaluation.py
│   ├── cie_v3_validation.py
│   └── consistency_test.py
│
├── docs/
│   ├── submission_proposal.md
│   ├── cie_framework_v3.md
│   ├── cie_validation_report.md
│   ├── evaluation_method.md
│   └── final_analysis_report.md
│
├── results/
│   ├── full_evaluation.csv
│   ├── consistency/
│   └── adversarial/
│
└── examples/
    ├── demo_cases/
    └── cie_v3_validation_result.json
```

---

## 11. 预期效果

### 11.1 应用效果

最终用户能够输入有限食材，获得不只“可做”，而且经过 CIE 筛选的创意料理方案；结果能够解释为什么创新、与什么已有料理接近、改变在哪里、为什么可能成立以及有什么风险。

### 11.2 评估效果

期望 CIE-Bench 能够：

1. 区分普通合理输出、局部创新和高价值创新；
2. 不把单纯的稀有组合奖励为高创新；
3. 对缺少知识 grounding 或机制依据的输出进行降分；
4. 对重复评估保持可接受的稳定性；
5. 与人工创新判断形成较高的一致性；
6. 在对抗性样本上识别术语堆砌、虚假 precedent 与创新幻觉。

### 11.3 研究与工程产出

最终形成：

- 一个可运行的真实用户应用；
- 一套开放式创新评价 Rubric；
- 一个带来源、难例、反例的 benchmark；
- 自动/半自动评测脚本；
- 判别力、一致性与对抗性实验；
- 模型失败模式和能力边界分析。

---

## 12. 时间规划

### 8 月 27 日 — 方案提交与公开仓库初始化

- 完成方案文档；
- 建立公开 GitHub 仓库；
- 完成 README、环境配置样例、依赖说明；
- 公开 CIE v3 设计与初步验证结果；
- 检查 API Key 与隐私安全。

### 8 月 28 日—8 月 30 日 — 核心代码同步与 Pipeline 打通

- 整理并同步 `src/creative_recipe/`；
- 固化 Hy3 client 与 structured output；
- 打通 generator → Innovation Trace → evaluator → ranking；
- 增加最小可运行 CLI/demo。

### 8 月 31 日—9 月 3 日 — Benchmark 与完整评测

- 完成 CIE-Culinary-Bench 数据与 schema 整理；
- 补充难例、反例和 adversarial cases；
- 运行完整评测并输出结果表；
- 完成人工标注与一致性验证。

### 9 月 4 日—9 月 6 日 — 应用 UI 与用户闭环

- 完成冰箱式食材选择界面；
- 接入生成、CIE 评分、结果解释；
- 完成重新生成、偏好约束、收藏等核心交互；
- 检查异常处理与 API 调用稳定性。

### 9 月 7 日—9 月 8 日 — 分析与对抗性验证

- 完成一致性实验；
- 完成对抗性验证；
- 归纳模型失败模式；
- 分析 CIE 的能力边界与局限。

### 9 月 9 日 — Demo 与最终文档

- 录制 2 分钟以内 demo 视频或 GIF；
- 完善 README 运行方式；
- 完成最终分析报告；
- 在全新环境复现运行流程。

### 9 月 10 日 — 最终提交

- 最终仓库安全检查；
- 检查数据、脚本、结果、文档、demo 是否齐全；
- 提交公开仓库链接。

---

## 13. 风险与应对

### 风险 1：LLM-as-judge 自身存在波动

**应对**：重复评估、固定 prompt/temperature、记录原始输出，并与人工标注对照。

### 风险 2：Benchmark 中存在人工主观偏差

**应对**：提供可操作 Rubric、source registry、annotation guideline，并记录分歧样本。

### 风险 3：模型生成虚假科学解释

**应对**：通过 Precedent、Grounding Ceiling、Mechanistic Plausibility 与证据可追溯机制联合限制。

### 风险 4：项目变成“UI 很漂亮但评价研究很弱”

**应对**：以 CIE-Bench、评测材料和实验验证为主交付，UI 作为真实应用载体而不是项目核心贡献。

### 风险 5：时间有限导致范围失控

**应对**：优先保证“可运行应用 + benchmark + evaluator + 完整实验 + README + demo”闭环，额外视觉与功能仅在核心闭环完成后扩展。

---

## 14. 最终提交物映射

| 官方要求 | 本项目对应产出 |
| --- | --- |
| 开源项目仓库 | Creative Recipe AI + CIE-Bench GitHub 仓库 |
| 应用源码 | `src/creative_recipe/` |
| README / 环境配置 / 运行说明 | 根目录 `README.md`、`.env.example`、`requirements.txt` |
| 评测样本集 | `data/CIE-Culinary-Bench/` |
| 评估方法说明 | `docs/cie_framework_v3.md` / `docs/evaluation_method.md` |
| 评测脚本 | `scripts/` |
| 完整结果表格 | `results/full_evaluation.csv` |
| 有效性验证 | 判别力、一致性、对抗性实验 |
| 分析报告 | `docs/final_analysis_report.md` |
| Demo | 2 分钟以内视频或 GIF |

---

## 15. 项目定位总结

本项目并不试图证明“Hy3 会做饭”，而是尝试解决一个更一般的问题：

> 在没有唯一标准答案的开放式生成任务中，如何评价大语言模型是否产生了真正有价值的创新？

创意料理只是这一问题的实验场。CIE-Bench 希望把原本主观的“有创意”拆成可观察、可解释、可复现的创新过程，并通过 Hy3 应用与系统实验验证其有效性。
