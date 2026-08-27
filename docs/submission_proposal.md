# Creative Recipe AI × CIE-Bench 项目方案

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务  
> 任务方向：开放式场景——AI 应用与评判标准设计  
> 项目性质：个人 / 活动作品，非腾讯官方发布项目

---

## 1. 项目概述

本项目基于 Hy3 构建一个面向真实用户的**创意料理生成与筛选应用 Creative Recipe AI**，并围绕该应用设计一套开放式创新能力评价框架 **CIE-Bench（Culinary Innovation Evaluation Benchmark）**。

项目核心并不是“让模型生成更奇怪的菜谱”，而是回答：

> 如何判断大语言模型是否真正产生了**有知识依据、有创新增量、有实际价值**的创新，而不是仅仅生成新奇、流畅、看起来专业的文本？

因此，本项目把创意料理作为一个可观察、可解释、可构造难例和反例的开放式任务场景，并将评价对象从单纯的最终 Recipe 扩展为：

```text
Recipe Concept
+
Culinary Innovation Reasoning Trace
```

核心命题为：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

当前项目已经从最初的框架设计与三案例概念验证，推进到 **30-case frozen benchmark + 可复现 runner + 33/33 canonical Hy3 主评测** 阶段。

---

## 2. 目标用户与真实问题

### 2.1 目标用户

1. 希望利用家中已有食材获得新做法的普通用户；
2. 对创意料理、跨菜系搭配、风味实验感兴趣的烹饪爱好者；
3. 希望研究或评测大语言模型开放式创新能力的开发者与研究者。

### 2.2 用户痛点

现有菜谱生成类 LLM 应用通常存在以下问题：

- 容易把“罕见组合”误认为“创新”；
- 能生成看似专业的解释，但缺乏可靠料理知识或机制支撑；
- 无法明确说明与已有菜品相比究竟改变了什么；
- 缺少对失败风险、可执行性和实际价值的审查；
- 一次生成很多结果，却缺少可靠的自动筛选机制。

### 2.3 引入大模型的必要性

创意料理不存在唯一标准答案，食材、偏好、烹饪条件和创新方向高度组合化，传统规则系统难以覆盖。

Hy3 在项目中承担两类角色：

- **生成端**：根据用户输入生成 Recipe Concept 与结构化 Innovation Trace；
- **评估端**：在固定 Rubric 与规则约束下执行 LLM-as-judge，对候选进行结构化评分和归因。

在 benchmark 有效性验证中，生成与评价尽量解耦，以减少“模型自己生成、自己认可”的偏差。

---

## 3. 总体设计思路与系统架构

项目采用“**生成 → 显式创新过程 → 评价 → 筛选 → 解释反馈**”闭环。

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
   Rubric评分   规则约束   Evidence / Risk Check
       └──────────┼──────────┘
                  ▼
        候选排序 / 筛选 / 归因
                  │
                  ▼
        用户可读的创意料理结果
```

评价不只问“这道菜有没有创意”，而是审查：

1. 模型理解了哪些已有料理知识；
2. 最接近的 precedent 是什么；
3. 相比已有方案到底改变了什么；
4. 为什么这种变化在机制上可能成立；
5. 这种变化创造了什么新价值；
6. 它可能在哪里失败。

---

## 4. Innovation Trace：让创新过程可审查

CIE v3 将创新过程显式拆成六阶段：

### Stage 1 — Existing Culinary Context
定位最接近的已有料理、技法或食材用途，避免使用“世界上从未存在”等未经验证的叙述制造创新感。

### Stage 2 — Ingredient & Technique Knowledge
分析风味、香气、质地、脂肪相互作用、烹饪机制等真实知识基础。

### Stage 3 — Innovation Delta
回答“与已有方案相比，真正发生了什么变化”。重点识别 Ingredient Role Shift、Technique Innovation、Flavor Architecture Innovation、Texture Innovation、Presentation / Experience Innovation 等。

### Stage 4 — Mechanistic Justification
要求给出可辩护的烹饪科学、风味交互、厨艺经验或先例依据，而不是“因为很搭”“因为少见”等空洞理由。

### Stage 5 — Creative Hypothesis
明确该变化试图创造什么新的风味、口感、食用体验或食材利用价值。

### Stage 6 — Risk & Constraint
要求主动说明比例风险、技术边界、失败模式与实现限制。

---

## 5. CIE 六维评估方法

| 维度 | 权重 | 核心问题 |
| --- | ---: | --- |
| Culinary Knowledge Grounding | 15% | 是否真正理解料理知识 |
| Existing Culinary Precedent Analysis | 15% | 是否能定位并比较已有料理空间 |
| Innovation Delta Quality & Magnitude | 25% | 是否存在真实、有效的创新增量 |
| Mechanistic Plausibility | 20% | 创新是否具有可靠机制或经验依据 |
| Innovation Value / Exploration | 15% | 改变是否创造新的实际价值 |
| Realization Quality | 10% | 是否合理、可执行且表达清楚 |

```text
CIE Score = Σ(score_d × weight_d)
```

### 5.1 Anti-gaming / Anti-hallucination 机制

- Precedent 强制：创新主张必须先定位已有料理空间；
- Grounding Ceiling：若 Grounding 低于阈值，Innovation Delta 不允许进入高分档；
- Mechanistic Justification 禁止使用“少见所以创新”等空洞解释；
- Innovation Magnitude 不采用“变化越大分越高”的单调奖励；
- Risk & Constraint 强制暴露潜在失败边界；
- Benchmark 中加入难例、反例与后续 adversarial 样本，检验评价器是否会被篇幅、术语和伪造依据骗分。

---

## 6. 重点技术

### 6.1 Hy3 OpenAI-Compatible 调用

通过 Hy3 的 OpenAI-compatible 接口调用模型，API Key 通过环境变量 / `.env` 注入，不写入源码或公开仓库。

### 6.2 Structured Output

Recipe Concept、Innovation Trace、六维评分、理由、错误信息均采用结构化字段，便于自动解析、统计、复现和 case-level 归因。

### 6.3 LLM-as-Judge + Rule Constraints

评估流程不是单次自由文本打分，而是固定 Rubric、结构化 judge 输出、规则约束、结果持久化和人工抽检共同组成。

### 6.4 Anonymous / Trace-conditioned Evaluation

当前 canonical 主评测采用 **anonymous trace-conditioned** 轨道：隐藏 case 身份信息，但允许评价器访问为该案例准备的结构化 trace，以重点检验“给定创新过程信息后，CIE 是否能够做出稳定、区分性的评价”。

### 6.5 可审计 Benchmark Runner

Runner 保存 prompt、输出、解析状态、评分和 provenance，并区分：

- canonical 完整结果；
- partial / failed run；
- deprecated baseline；
- 后续 evidence-only / repeat / adversarial 等独立轨道。

这样可以避免将 API 失败、旧 baseline 或不同信息条件下的结果混为同一个 benchmark 结论。

---

## 7. CIE-Culinary-Bench 数据设计

当前核心 benchmark 为 **30-case frozen dataset**，其设计目标不是追求样本数量，而是先建立一个可追溯、可审计、覆盖多种创新质量和失败模式的 v1 核心集。

数据治理包括：

- dataset / schema / gold / rubric 分离；
- case provenance；
- source registry；
- fabrication disclosure；
- annotation guideline；
- quality report；
- 难例与反例覆盖；
- benchmark 冻结后避免为追逐结果而修改 gold/rubric。

数据覆盖低创新、部分创新、高价值创新以及不同类型的 grounding / mechanism / feasibility 问题。

---

## 8. 当前已经完成的评测与验证

### 8.1 早期三案例 smoke test

最初使用 Low / Partial / High-value 三个固定案例验证框架是否至少具备基础排序能力：

```text
EXPECTED: High > Partial > Low
ACTUAL:   8.50 > 6.60 > 4.20
RESULT:   PASS
```

该实验现在仅作为**早期 smoke test**，不再作为 benchmark 的主要有效性证据。

### 8.2 Canonical 30-case Benchmark Run

当前主实验已完成真实 Hy3 的 anonymous trace-conditioned canonical run。

- frozen benchmark：30 cases；
- runner 实际评测记录：33 / 33 成功；
- Parse / API success：100%；
- 未将中途失败的 partial run 作为有效结果；
- 带显式 case ID 的旧 baseline 已 deprecated。

当前主指标：

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

这组结果说明：在 trace-conditioned 条件下，CIE 已表现出一定的类别判别、相对排序和连续评分能力，但尚不能据此宣称“评价框架已经被充分验证”。

### 8.3 Partial Run 处理

曾出现一次 run2 partial：

```text
16 / 33 succeeded
17 / 33 APIConnectionError
```

该批结果已迁入 `results/deprecated_partial_run2/`，仅用于 provenance / migration history，**不作为 benchmark 有效结果**。其中成功的 16 条在迁移到 canonical run 时按 prompt hash 校验复用，没有重复调用 API。

---

## 9. 仍需完成的有效性验证

官方任务要求至少完成判别力验证与一致性验证，并鼓励对抗性验证。当前后续重点如下：

### 9.1 Evidence-only Track

移除人工整理的完整 Innovation Trace，只给更受限的 evidence / recipe 信息，观察模型表现下降幅度。

目的：回答当前较好的 trace-conditioned 表现中，有多少来自 CIE rubric 本身，有多少来自输入 trace 提供了较强信息。

### 9.2 重复评分一致性

对同一输出进行至少 3 次独立评测，统计：

- 总分标准差；
- 维度分数波动；
- class label agreement；
- ranking stability。

### 9.3 与人工标注一致性

由人工依据同一 rubric 对样本进行盲评，与 Hy3 judge 结果比较，计算准确率 / F1、Spearman 或其他一致性统计。

### 9.4 系统化判别力验证

将 Good / Medium / Bad 或 High / Partial / Low 设计为成组样本，统计 evaluator 是否能够稳定满足预期排序，而不是只展示少数成功案例。

### 9.5 Adversarial Validation

构造可能骗分的输出，例如：

- 增加篇幅；
- 堆砌专业术语；
- 伪造历史 precedent；
- 随机加入陌生食材；
- 提供漂亮但错误的机制解释；
- 在可执行性很差的情况下强化“创新叙事”。

检验 CIE 的 anti-gaming 规则能否有效降低其分数。

---

## 10. 应用侧交互设计

应用主界面围绕真实“冰箱里有什么”的使用场景设计。

### 首页

标题：**What do we have?**

用户可以从冰箱式分类界面选择蔬菜、肉类等食材，也可以直接文本输入，并补充口味偏好或简单状态约束。

### 生成与筛选

系统不是直接返回第一次采样，而是生成多个候选，并由 CIE 进行评价、筛选和解释。

### 结果页

展示：

- 菜品名称；
- 食材与调料；
- 制作步骤；
- 食材特点；
- 搭配 / 机制解释；
- 最接近的已有料理及差异；
- 创新亮点；
- 尝试成本与失败风险；
- CIE 六维评分与解释。

用户可选择重新生成或收藏 / 下一步。

---

## 11. 预期效果

项目最终希望实现三层效果：

### 应用层

用户输入已有食材后，可以获得不仅“新奇”，而且经过 CIE 筛选、具有解释和风险提示的创意方案。

### 工程层

形成可运行、可复现、可审计的 Hy3 应用与 benchmark pipeline，API 失败、解析失败和历史结果都有明确 provenance。

### 研究层

形成一个针对开放式创新能力的可操作研究原型，回答：

- Novelty 与 Innovation 如何区分；
- 如何让创新过程可观察；
- LLM-as-judge 在不同信息条件下是否可靠；
- evaluator 会被哪些 anti-pattern 欺骗；
- Hy3 的创新评价能力边界在哪里。

---

## 12. 时间规划

### 8 月 27 日：方案与 benchmark MVP 收口

已完成 / 当日提交：

- 项目方案文档；
- CIE 框架说明；
- 30-case frozen benchmark 核心设计；
- canonical trace-conditioned run；
- GitHub 公开仓库基础结构与安全配置；
- 当前实验结果与边界说明。

### 8 月 28 日—8 月 31 日：有效性验证补强

- 完成 evidence-only track；
- 完成 repeated scoring；
- 完成人工一致性抽检；
- 完成 Good / Medium / Bad 系统化判别力实验；
- 构造并运行 adversarial cases。

### 9 月 1 日—9 月 4 日：应用侧整合

- Creative Recipe Generator；
- CIE evaluator 接入候选排序；
- 结果页解释字段；
- 基本 UI 流程打通。

### 9 月 5 日—9 月 7 日：完整评测与分析

- 在 frozen benchmark 上跑最终版本；
- 输出完整结果表；
- failure taxonomy；
- 典型 case 分析；
- 模型能力边界总结。

### 9 月 8 日—9 月 9 日：公开仓库与 Demo

- README / 环境 / 一键运行命令复核；
- 同步 benchmark / scripts / results；
- 清理私密信息和开发残留；
- 录制 2 分钟以内 demo 视频或 GIF。

### 9 月 10 日：最终提交

- 最终 GitHub 仓库；
- 完整评测材料；
- 有效性验证结果；
- 分析报告；
- Demo。

---

## 13. 当前风险与应对

### 风险 1：Trace-conditioned 可能高估 evaluator 能力

应对：将 evidence-only 作为独立轨道，明确不同信息条件，禁止混报结果。

### 风险 2：LLM-as-judge 存在随机波动

应对：重复评测 + 人工一致性验证。

### 风险 3：小 benchmark 可能过拟合规则

应对：冻结 gold/rubric；加入 adversarial / challenge set；不因单次结果反复调整 benchmark。

### 风险 4：API 连接失败污染结果

应对：保存 per-case 状态、prompt hash 与 migration provenance；partial run 不作为正式 benchmark 结果。

### 风险 5：应用展示挤占研究验证时间

应对：优先保证 benchmark、验证、结果分析完整，再完成 UI polish。

---

## 14. 最终产出

1. **开源项目仓库**：Creative Recipe AI、CIE evaluator、环境配置与运行说明；
2. **评测材料**：CIE-Culinary-Bench、schema / gold / rubric、评测脚本；
3. **有效性验证**：判别力、一致性、evidence-only 与 adversarial 实验；
4. **完整结果**：表格、指标、case-level 输出和错误分析；
5. **分析报告**：设计依据、失败模式、能力边界与典型规律；
6. **Demo**：2 分钟以内的视频或 GIF。

---

## 15. 项目当前结论

截至 2026 年 8 月 27 日，本项目已完成从“创新评价概念”到“**可运行 benchmark MVP**”的关键跨越：已有 frozen dataset、可复现 runner、真实 Hy3 canonical run 以及基础判别 / 排序指标。

当前最需要继续验证的不是“系统能不能跑”，而是：

> **这个 evaluator 在信息更受限、重复采样、人工对照和对抗攻击下，是否仍然可靠。**

这将是最终提交前的核心实验主线。
