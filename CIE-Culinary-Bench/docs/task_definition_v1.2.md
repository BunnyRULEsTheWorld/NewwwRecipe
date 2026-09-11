# CIE-Culinary-Bench — Benchmark Validation Protocol v1.2

**Stage:** Protocol definition only (pre-formal-experiment).
**Hard constraints for this step:**
- No Hy3 API calls.
- No UI / no runner implementation.
- No modification of frozen dataset, gold labels, scoring rubric, or historical results.
- This document defines *what we measure and how we compare fairly*. It does **not** execute anything.

**Relationship to prior frozen docs:**
- `task_definition.md` (v1.1) is the frozen benchmark task file — **not overwritten**.
- `protocol_audit_v1.md` is the frozen leakage-audit — its findings are adopted here as binding constraints (the 73.3% / macro-F1 0.675 is `trace_conditioned`, **not** evidence-only).
- `scoring_rubric.md` / `scoring_rubric.json` (v1.1) are reused as the CIE rubric.
- `closed_evidence_anonymous_v1/*` (33/33) is the frozen `trace_conditioned` run — **not re-run, not edited**.

---

## 0. 本阶段的唯一目标

把"我们究竟要测什么、怎么公平比较"定义清楚。这一步的产物是文档，不是代码、不是实验结果。

---

## 1. 研究问题与测量目标（RQ1–RQ5）

CIE 的核心研究问题不是"Hy3 能不能给菜打分"，而是：

| RQ | 问题 | 由哪些 setting 回答 |
|---|---|---|
| **RQ1** | 只看中性料理事实时，LLM 能否独立判断一项料理创新是否有价值？ | E0, E2 |
| **RQ2** | CIE 是否真的比普通 Vanilla LLM Judge 更有效，而不是 Hy3 本身就会判断创新？ | E0 vs E1 vs E2 |
| **RQ3** | CIE 的提升来自哪里？区分：普通 judging / CIE rubric / CIE structured reasoning / curated Innovation Trace / human-evidence | E0→E1→E2→E3→E4 的贡献链 |
| **RQ4** | CIE evaluator 是否稳定、有判别力、能抵抗"假创新"诱骗？ | 所有 setting 的 reliability / discrimination / adversarial 指标 |
| **RQ5** | Innovation Trace 是否真的帮助 Generate→Evaluate→Select 的筛选阶段？ | E2 vs E3（curated trace benefit） |

---

## 2. 五个实验设置（逐层叠加信息/结构）

五个 setting 是**累积式**的：每一个在上一层的输入基础上叠加一类信息或结构。这种"阶梯"设计让每一个增量贡献都可被单独归因。

### E0 — Vanilla LLM Judge（最低 baseline）
- **目的**：建立"不给 CIE，只让普通 Hy3 自己判断料理创新"的底线。
- **Input**：仅中性料理事实（`evidence_only_view`，见 §3）。**禁止**提供：CIE rubric、CIE 维度定义、六类 category 名称、Innovation Trace、gold reasoning、human evaluation、benchmark tags、gold labels。
- **Prompt**：只给非常通用的任务，例如：
  > "以下是关于一道菜的料理事实。请判断它的创新程度，并解释你的推理。"
  输出为**自由文本**（可附带一个整体 1–5"创新质量"整数，但**不强制**任何 6 类或 5 维 schema）。
- **测量方式**：E0 原始输出经 §4 定义的冻结 `cie_eval_adapter` 映射为可比较分数（见公平性设计）。
- **回答**："如果不给模型 CIE，只让普通 Hy3 判断，效果如何？"

### E1 — CIE Rubric-only
- **Input**：与 E0 **完全相同**（`evidence_only_view`）。
- **增加**：CIE 评价定义 / scoring rubric。核心命题：
  > Innovation ≠ mere novelty  
  > Innovation = Novel Change + Grounding + Value
- **不要求**模型显式生成六阶段 Innovation Trace。
- **贡献**：E0→E1 的提升估计 **Rubric Contribution**（"一个更好的创新定义本身是否有帮助？"）。

### E2 — CIE Evidence-only（未来 benchmark 主实验）
- **Input**：**仅中性 culinary evidence**（`evidence_only_view`）。
- **模型必须自己完成**六阶段：
  `Existing Culinary Context → Ingredient & Technique Knowledge → Innovation Delta → Mechanistic Justification → Creative Hypothesis → Risk & Constraint → CIE Evaluation`
- **绝对禁止**把 dataset 中人工 gold Innovation Trace 的评价性内容放入 prompt。模型生成的 trace 必须是 **model-generated reasoning artifact**，不是 gold trace 的复制。
- **评分维度**：evidence-only 下**只评价 5 个维度**（realization_quality 不进入主赛道，理由见 §3 / protocol_audit_v1 §5）：
  1. Culinary Knowledge Grounding
  2. Existing Culinary Precedent Analysis
  3. Innovation Delta Quality
  4. Mechanistic Plausibility
  5. Innovation Value
- **贡献**：E1→E2 的提升估计 **Structured Reasoning Contribution**（"显式结构化创新分析过程是否帮助创新评价？"）。

### E3 — Trace-conditioned（已有 33/33 anonymous run，冻结）
- **Input**：料理事实 + 人工 curated Innovation Trace（即 33/33 已跑的 `closed_evidence_anonymous_v1`）。
- **不是** evidence-only。现有正式结果**保留、不重跑、不修改**：
  - Accuracy 73.3% · Macro-F1 0.675 · Mean Spearman 0.570 · MAE 0.661 · Ranking pairwise accuracy 86.7%
- **贡献**：E2 vs E3 研究 **Curated Trace Benefit**（"如果已有高质量显式创新分析，evaluator 能否更好地筛选？"）。

### E4 — Human-evidence-aware（未来 diagnostic / extended track）
- **Input**：料理事实 + 必要的 structured reasoning + 真实 human / execution evidence（专业评委反馈、比赛结果、实际执行问题、用户真实烹饪反馈）。
- **主要用途**：评价 `realization_quality`。
- **腾讯项目阶段**：protocol 正式定义即可，不要求完整运行。

---

## 3. Evidence-only 输入视图（正式 schema）

基于 `protocol_audit_v1.md` §3，定义运行时构造的 `evidence_only_view`。原则：模型可以知道"发生了什么"，但**不能知道人工 evaluator 认为这件事好不好**。

**决策图例**：KEEP（中性事实，安全）· STRIP（从 prompt 移除）· MOVE_TO_GOLD（仅存 gold，永不入 prompt）· REWRITE_NEUTRAL（保留结构、删除价值判断措辞）。

### 3.1 运行时输入构成
```
evidence_only_view = {
  culinary_context,            # 全盘 KEEP
  dish_information,            # 全盘 KEEP
  innovation_trace_neutralized # 仅保留下列中性事实字段（见下表）
}
# 显式排除（永不进入 prompt）：
#   metadata, human_evaluation_signal, cie_annotation, benchmark_tags,
#   以及 trace 中的 judgment 字段（见下表 STRIP / MOVE_TO_GOLD）
```

### 3.2 逐字段决策表

| 字段 | 决策 | 理由 |
|---|---|---|
| `culinary_context.traditional_reference` | **KEEP** | 中性既有料理参照。 |
| `culinary_context.innovation_space` | **KEEP** | 中性标签列表。 |
| `dish_information.*` | **KEEP** | 实际食材、技法、客观烹饪过程。 |
| `innovation_trace.existing_culinary_context.precedents` | **KEEP** | 中性既有菜列表（事实）。 |
| `existing_culinary_context.relationship` | **STRIP**（或 REWRITE_NEUTRAL 为纯事实比较句，删除"创新关键/所谓创新"等元引导） | 当前含指向结论的元引导。 |
| `innovation_trace.ingredient_and_technique_knowledge` | **KEEP**（REWRITE_NEUTRAL 任何价值从句） | 中性料理事实，是"证据"核心。 |
| `innovation_delta.before` | **KEEP** | 中性描述。 |
| `innovation_delta.after` | **KEEP** | 中性描述。 |
| `innovation_delta.change_type` | **KEEP** | 中性结构描述符。 |
| `innovation_delta.magnitude` | **MOVE_TO_GOLD** | 1–5 评分级判断，是 `innovation_delta_quality` 的目标。 |
| `mechanistic_justification.flavor_mechanism` | **KEEP**（REWRITE_NEUTRAL 删除尾部结论句） | 可证伪机制 = 好证据。 |
| `mechanistic_justification.texture_mechanism` | **KEEP**（REWRITE_NEUTRAL） | 同上。 |
| `mechanistic_justification.chemical_or_culinary_basis` | **STRIP / MOVE_TO_GOLD** | 携带 gold 结论（"不成立""系统级创新"）。 |
| `mechanistic_justification.strength` | **MOVE_TO_GOLD** | 直接 gold 结论，30/30 泄漏。 |
| `risk_and_constraint.risk` | **KEEP** | 中性可行性风险。 |
| `risk_and_constraint.failure_condition` | **KEEP**（REWRITE_NEUTRAL 结论措辞） | 盲尝框架为中性。 |
| `risk_and_constraint.tradeoff` | **REWRITE_NEUTRAL / STRIP** | 删除价值结论（"概念层次多于味觉层次"）。 |
| `creative_hypothesis` | **REWRITE_NEUTRAL** | 保留结构意图，删除结果/价值宣称（"奢侈仪式"）。 |

**模型允许的语义边界（明确清单）：**
- 允许：`实际食材`、`实际技法`、`客观 cooking process`、`客观 culinary precedent`、`可验证的 ingredient/technique facts`。
- 禁止：`strength = weak/strong`、`magnitude = 4`、"技术复杂度没有转化成价值"、"这是系统级创新"、"这是一个陷阱"、"评价关键在于…"、专家最终价值判断、gold reasoning、category implication。
- "precedent information"本身也须是事实描述，不得夹带"所以这不算创新"之类结论。

### 3.3 realization_quality 的处理（protocol_audit_v1 §5 采用 A+C）
- **A.** evidence-only（E2）主赛道**剔除** `realization_quality`。
- **C.** `realization_quality` **只在** E4（human_evidence_aware）中评价，且需显式提供 human/execution evidence，单独报告。
- 因此 E2 的 Task-2 为 **5 维**；其 mean_spearman / mean_mae 仅基于 5 维（不得与 6 维混算）。

---

## 4. Vanilla vs CIE 的公平比较设计（核心）

### 4.1 受控不变量（E0 / E1 / E2 之间必须一致）
| 类别 | 取值 |
|---|---|
| Cases | 同一 30 条 |
| Neutral evidence | 同一 `evidence_only_view` |
| Model | 同一 Hy3 endpoint |
| Temperature | 同一值（建议沿用 0.2） |
| reasoning_effort | 同一值（沿用 `no_think`） |
| API configuration | 同一配置 |
| Runs | 同一 runs 数（核心实验 ≥3） |
| 输出约束 | E1/E2 使用同一 canonical output schema（5 维 + 6 类 + ranking） |

**唯一允许的差别**是 prompt 的*指令脚手架*：
- E0：通用创新判断（**无** CIE 名称/维度/rubric）。
- E1：+ CIE rubric。
- E2：+ CIE rubric + 六阶段结构化推理要求。

### 4.2 category-name 困境——明确解决
> 若 Vanilla Judge 不知道 CIE 六类 category 名称，classification accuracy 是否仍可公平比较？若直接给六类定义，是否已不是真正 Vanilla？

**绑定决策：**
1. **生成时（generation time）**：E0 **绝不**看到六类 category 名称、五维维度名称或 CIE rubric。其 prompt 只给通用判断任务，输出为自由文本。这是"真 Vanilla"。
2. **评测时（evaluation time）**：一个**冻结、对模型不可见**的 `cie_eval_adapter`（定义见 `experiment_matrix_v1.md`）把每个 setting 的**原始输出**映射为 gold 对齐的 canonical schema：5 个 evidence-only 维度分数（1–5）、6 类 category、ranking。adapter 的维度描述用**中性料理评价语言**撰写（与 CIE 措辞"收敛但不逐字相同"），使 E1/E2 不因字面名称匹配而占便宜。
3. **主对比指标 = 与分类法无关的指标**：逐维 Spearman ρ、MAE（5 维）、mean Spearman（5 维）、ranking（pairwise accuracy / Spearman / Kendall τ）。这些对**所有 setting 用同一 adapter 计算**，因此 E0 缺少 category 知识不会偏置比较。
4. **6 类 accuracy** 对所有 setting 报告，但 E0 的结果明确标注为 **adapter-derived（adapter 从自由文本推断类别）**，作为**次要**指标；E0 vs CIE 的标题对比建立在 ranking + 维度相关性之上，而非 6 类 accuracy。

→ 归因因此干净：E0→E1→E2 的任何提升都可归因于（rubric）与（structured reasoning），因为测量仪器（adapter）完全相同。

### 4.3 依赖变量（Dependent Metrics）
见 §5。对每个 setting 报告对应适用指标；E0/E1/E2 的核心对比以 §4.2.3 的主对比指标为准。

---

## 5. 需要报告的主指标

### 5.1 Classification（适用 E1/E2/E3；E0 为 adapter-derived 次要）
- Accuracy、Macro-F1（主，因样本小且类别不完全平衡）
- Per-class recall、Confusion matrix

### 5.2 Dimension scoring（E2 仅 5 维；E3/E4 可含 6 维）
- Per-dimension Spearman ρ、Mean Spearman
- MAE（越低越好）、可选 QWK

### 5.3 Ranking
- Pairwise accuracy、Spearman ρ、Kendall τ-a
- 注意：E2 evidence-only **仅用** `RANK-IV-01`（innovation_value）与 `RANK-IDQ-01`（innovation_delta_quality）；`RANK-RQ-01`（realization_quality）因维度被剔除而不适用于 E2（见 §8 数据集问题 #1）。

### 5.4 Reliability（核心实验 ≥3 runs）
- classification modal agreement、exact 3-run agreement
- within-case score SD（每样本每维）、ranking agreement

### 5.5 Discrimination（已有 Good/Medium/Bad cases）
目标：score(Good) > score(Medium) > score(Bad)。
- strict ordering accuracy（每组三条均满足 good>medium>bad）
- pairwise ordering accuracy
- margin（相邻档位的平均分差）
- 注：当前 `good_medium_bad_cases.jsonl` 提供的是**定性 mock assessment + expected_properties**，未给数值分锚点；见 §8 #2。

### 5.6 Adversarial（至少覆盖五类）
- Technique Inflation、Ingredient Stacking、Weirdness Bias、Luxury/Authority Bias、Scientific Hallucination
- 重点比较 **Vanilla vs CIE Evidence-only**
- trap detection rate、overrating rate、hallucination rate（若可可靠定义；hallucination rate 定义为"声称的料理/科学事实不被 evidence_only_view 支持且与 gold/source registry 矛盾"，标注为实验性/可选）

---

## 6. 实验执行顺序（Gate 1–10）

本阶段只到 Gate 1–2（定义）。后续 gate 为正式执行计划，**本次不执行**。

| Gate | 内容 | 本次状态 |
|---|---|---|
| 1 | Task Definition / Experiment Matrix 审查 | ✅ 本步完成 |
| 2 | 实现 input view + prompts + runner | ⏸ 本次不实现 |
| 3 | dry-run：检查所有实际 prompt，确认无 gold/semantic leakage，Vanilla/CIE 输入公平 | 未来 |
| 4 | small smoke test：每 setting 跑少量 case | 未来 |
| 5 | 单次 full run：E0 / E1 / E2 | 未来 |
| 6 | 审查结果与 protocol | 未来 |
| 7 | 核心配置正式 ≥3 runs | 未来 |
| 8 | Good > Medium > Bad | 未来 |
| 9 | Adversarial Vanilla vs CIE | 未来 |
| 10 | 统一 failure analysis / ablation analysis | 未来 |

只有完成 Gate 1–10 后才冻结项目版 benchmark，然后进入 Application Backend → UI。

---

## 7. Human Annotation 的定位

当前 gold 仍属 **curated gold seed**，**不声称**已具备强 human consensus。

v1.2 明确：论文级未来工作包括：
- ≥2 independent annotators
- category agreement、Cohen's kappa、QWK、score correlation
- adjudication protocol
- 最好含具料理背景的 annotator

腾讯项目阶段：human agreement 可作 **optional enhancement**，不是本轮必需数据。

---

## 8. 数据集本身对实验设计的阻碍 / 注意点

> 以下问题不影响"定义 protocol"，但会在正式执行时成为障碍或控制点，提前列出。

1. **RANK-RQ-01（realization_quality）与 E2 evidence-only 不兼容**：该维度在 E2 被剔除，因此 E2 只能用 `RANK-IV-01` 与 `RANK-IDQ-01` 两个 ranking set（2/3）。需决定：是否新增一个 evidence-only 友好的第 3 个 ranking set，还是 E2 阶段仅报告 2 个 set。
2. **good_medium_bad_cases.jsonl 缺数值锚点**：当前为定性 mock assessment + expected_properties，未给每个 quality tier 的数值分。严格 "strict ordering accuracy" 需定义所用分数维度（建议 `innovation_value` 或整体 holistic 分）并最好补数值目标。这是执行前需补齐的缺口。
3. **innovation_trace 本身就是 gold annotation**：E2 虽 STRIP 评价字段，但中性化后的 trace 仍把"先例/机制"等分析框架提供给模型——这是设计允许的事实脚手架，但意味着 E2 的"from scratch"是相对而非绝对的。需在报告中如实说明。
4. **ID 编码泄漏控制（必需控制，非 bug）**：`CIE-Axx` 的 `A` 前缀编码 adversarial split。必须**持续启用 ID 匿名化**（已被 protocol_audit 验证为有效），否则模型可从 ID 推断类别。这是强制不变量。
5. **小样本与类别不平衡**：n=30，Transformative n=4（在 trace_conditioned 中 recall=0）。已选 Macro-F1 为主指标，但 Transformative 仍将是难点；evidence-only E2 也可能在此类表现弱，需在 failure analysis 中单列。
6. **realization_quality 的可用性边界**：gold 含 6 维含 realization，但 E2 不可公平使用；6 维完整 scoring 仅在 E4 可用，E3（trace_conditioned）中 realization 也受 trace 内容混杂影响，报告时需单独标注。

---

## 9. 仍需人工决策的问题

1. E0 是否允许输出一个整体 1–5 holistic 分（仍为自由文本，不强制 schema）？建议：允许，但可选。
2. `cie_eval_adapter` 用 LLM-judge 还是确定性规则实现？（协议层只需定义其行为；实现留到 Gate 2。）建议：用冻结的 neutral 指令 LLM-judge，且对 E1/E2 同时保留 native 结构化输出做交叉校验。
3. E2 的 ranking 只用 2 个 set 是否可接受，还是需补第 3 个 evidence-only ranking set？（见 §8 #1）
4. good_medium_bad_cases 的判别测试用哪个分数维度作锚点，是否补数值目标？（见 §8 #2）
5. 核心实验的 runs 数：建议 ≥3；是否要求每 setting 都 ≥3，还是仅 E0/E1/E2 核心三设置 ≥3、E3 沿用冻结单次、E4 按需。
6. 是否将 E4 列入腾讯项目阶段必须运行，还是仅保持 protocol 定义（用户已倾向后者）。

---

## 10. 与 v1.1 的关系总结
- v1.1 的 task / rubric / dataset / 33/33 run 全部**冻结并复用**。
- v1.2 不修改上述任何文件，只**新增**本协议层：把"评测构造"从 `trace_conditioned` 重新解释为需要独立 evidence-only 运行，并定义 E0–E4 五设置与公平比较框架。
- 任何引用 73.3% / macro-F1 0.675 的地方，必须标注为 `trace_conditioned`，**不得**称为 evidence-only 结果。
