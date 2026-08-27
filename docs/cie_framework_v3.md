# CIE v3 设计说明

CIE（Culinary Innovation Evaluation）是 NewwwRecipe 里用来评估创意料理的模块。它不是单独的应用，而是为生成结果提供一套比较稳定的判断标准。

做这个模块的原因很直接：模型很容易生成“少见”“复杂”或者“听起来专业”的菜谱，但这些特征本身并不能说明结果真的有创意。CIE 因此会同时看已有料理背景、具体变化、料理知识依据、实际价值和可执行性。

## 1. 评价对象

CIE 当前评估两部分内容：

```text
Recipe Concept
+
Culinary Innovation Reasoning Trace
```

只看最终菜谱会漏掉很多信息。例如，一个结果可能只是碰巧生成得不错，但它并没有说明和已有做法相比改了什么，也没有解释为什么这种变化合理。Innovation Trace 用来把这些信息固定成结构化字段，方便后续评分和实验。

## 2. Innovation Trace v3

### Stage 1 — Existing Culinary Context

先找最接近的已有料理、类似技法和类似食材用法。这样做主要是避免模型直接声称“这是全新的”，却不给任何参照。

### Stage 2 — Ingredient & Technique Knowledge

记录与当前方案有关的食材和技法知识，例如风味、香气、质地、脂肪相互作用和烹饪机制。

### Stage 3 — Innovation Delta

说明与已有做法相比到底变了什么。目前主要记录：

- Ingredient Role Shift
- Technique Innovation
- Flavor Architecture Innovation
- Texture Innovation
- Presentation / Experience Innovation

这里不把“变化越大”直接等同于“越创新”。随机替换很多食材，如果没有合理依据，也不应该自动得到高分。

### Stage 4 — Mechanistic Justification

要求给出至少一种可以检查的理由，例如烹饪科学、风味交互、化学机制、烹饪经验或已有先例。

“因为很搭”“因为少见”这类表述不能单独作为有效解释。

### Stage 5 — Creative Hypothesis

说明这次变化希望得到什么新的风味、口感、食用体验或食材利用方式。

### Stage 6 — Risk & Constraint

记录比例、技法、原料或执行上的潜在风险，以及方案可能失败的地方。

## 3. CIE v3 Rubric

| 维度 | 权重 | 主要看什么 |
| --- | ---: | --- |
| Culinary Knowledge Grounding | 15% | 食材和料理知识是否可靠 |
| Existing Culinary Precedent Analysis | 15% | 是否能找到并正确比较已有做法 |
| Innovation Delta Quality & Magnitude | 25% | 是否真的有明确且有效的变化 |
| Mechanistic Plausibility | 20% | 这些变化是否有机制或经验依据 |
| Innovation Value / Exploration | 15% | 是否带来新的风味、口感、体验或利用价值 |
| Realization Quality | 10% | 是否合理、可执行并表达清楚 |

总分按六个维度加权计算：

```text
CIE Score = Σ(score_d × weight_d), score_d ∈ [1,10]
```

## 4. 额外约束

为了避免一些明显的“骗分”情况，当前版本还加了几条限制：

1. **Precedent 要求**：如果无法说明最接近的已有做法，相关维度不能直接进入高分档；
2. **Grounding Ceiling**：如果基础料理知识本身很不可靠，Innovation Delta 的上限会被限制；
3. **机制解释要求**：不能只靠“少见”“特别”“很搭”来证明合理性；
4. **Magnitude 不单调加分**：变化幅度大并不自动意味着分数高；
5. **Risk & Constraint**：高分方案需要说明可能失败的地方；
6. **Trace 参与评分**：当前主实验会让 evaluator 看到结构化 trace，因此后续必须再做 evidence-only 实验，检查 trace 是否给了过多提示。

## 5. 和 NewwwRecipe 的关系

NewwwRecipe 的应用流程会先生成多个候选料理，再让 CIE 进行评价和排序。CIE v3 是目前用于 benchmark 和实验的较严格版本，后续应用侧可以根据交互速度和可解释性需要做精简。

目前的早期测试记录见 [`cie_validation_report.md`](cie_validation_report.md)，完整 benchmark 结果和后续一致性、对抗性实验会放在 `results/` 中。
