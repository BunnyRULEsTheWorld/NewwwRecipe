# CIE-Bench: A Grounded Innovation Evaluation Framework for LLM-generated Culinary Ideas

> CIE v3 Specification

Creative Recipe AI 项目的核心贡献不是“用 LLM 生成创意菜谱”，而是设计一个面向 LLM 创新能力的评价框架。菜谱生成只是一个应用情境，用于展示 CIE 如何评价与筛选 AI 产生的创新想法。

## 1. Positioning & Scope

CIE-Bench（Culinary Innovation Evaluation Benchmark）是一个创新能力评价基准框架。

- 评价对象：LLM 在开放式创新任务中产生的想法及其推理过程；
- 应用场景：创意料理生成；
- 核心命题：评估模型是否真正产生创新，而不仅是生成新奇、流畅、看似合理的文本。

核心假设：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

仅有 Novel Change 而无 Grounding，容易退化为“奇怪”；仅有 Grounding 而无 Novel Change，则只是“合理但常规”。

## 2. 评价对象

CIE 评价：

```text
Recipe Concept
+
Culinary Innovation Reasoning Trace
```

而不是只评价最终 Recipe。原因是最终文本可能来自 lucky sampling；创新能力需要通过可观察的创新过程进行审查。

## 3. Innovation Trace v3

### Stage 1 — Existing Culinary Context

定位最接近的已有料理、类似技法和类似食材用途，防止凭空制造“从未存在”的创新故事。

### Stage 2 — Ingredient & Technique Knowledge

分析 flavor compounds、aroma、texture、fat interaction、cooking mechanism 等知识基础。

### Stage 3 — Innovation Delta

判断相比已有料理真正发生了什么变化，可包括：

- Ingredient Role Shift
- Technique Innovation
- Flavor Architecture Innovation
- Texture Innovation
- Presentation / Experience Innovation

必须描述 before state、after state、innovation type 与 magnitude。Magnitude 不采用“越大越好”的单调奖励。

### Stage 4 — Mechanistic Justification

至少给出 culinary science、flavor interaction、chemical mechanism、cooking principle 或 historical precedent 中的一类依据。“因为很搭”“因为少见”不能作为有效机制解释。

### Stage 5 — Creative Hypothesis

明确创新希望创造什么新体验，而不是重复食材组合本身。

### Stage 6 — Risk & Constraint

说明创新可能失败的位置、比例风险、技法限制与实现边界。

## 4. CIE v3 Rubric

| 维度 | 权重 | 评价目标 |
| --- | ---: | --- |
| Culinary Knowledge Grounding | 15% | 是否真正理解料理知识 |
| Existing Culinary Precedent Analysis | 15% | 是否能放回已有料理空间比较 |
| Innovation Delta Quality & Magnitude | 25% | 改变是否真实、有效并影响体验 |
| Mechanistic Plausibility | 20% | 创新是否有可靠机制支撑 |
| Innovation Value / Exploration | 15% | 是否创造新的风味、口感、体验或利用价值 |
| Realization Quality | 10% | 是否可执行、合理、表达清楚 |

总分：

```text
CIE Score = Σ(score_d × weight_d), score_d ∈ [1,10]
```

## 5. Anti-hallucination Mechanisms

1. **Precedent 强制**：创新主张必须定位已有料理空间；
2. **Grounding 天花板**：若 Culinary Knowledge Grounding < 5，则 Innovation Delta ≤ 6；
3. **机制禁令**：禁止以“很搭/少见”等空洞理由替代机制；
4. **Magnitude 非单调**：随机大幅改变不得自动获得高分；
5. **风险自省**：要求模型声明失败边界；
6. **过程评价**：以 Reasoning Trace 作为核心输入，减少对幸运生成文本的误判。

## 6. 工程关系

- 生产版 CIE 用于 Creative Recipe AI 的实际生成筛选流程；
- CIE v3 是研究化、严格化规格，用于 benchmark 与有效性实验；
- 验证结果见 `cie_validation_report.md`。
