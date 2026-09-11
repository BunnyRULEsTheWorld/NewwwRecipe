# CIE-Culinary-Bench v1.1 — Error Analysis

## 1. Classification errors

8 misclassified case(s):

| ID | Gold | Pred | Reasoning (excerpt) |
| --- | --- | --- | --- |
| CIE-007 | Structural Innovation | Incremental Innovation | 基于 gnocchi 先例同盘组织冬春模块过渡，知识精确且主动限定证据边界，机制完整指风险，实现证据有限，属增量改良。 |
| CIE-010 | Structural Innovation | Incremental Innovation | Noma将garum逻辑移入肉类加koji，先例比较与酶学机制清晰，角色转通用鲜味液，专业证据实现；属底物与技术转移的增量改良，非范式颠覆。 |
| CIE-012 | Transformative Innovation | Structural Innovation | Noma将民间采集提升为菜单研发与供应链核心系统，改变食材角色与餐厅结构；证据引官方回顾与长期菜单，机制完整含风险，但先例比较较概括，实现稳定。 |
| CIE-014 | Structural Innovation | Incremental Innovation | 经典味型装入轻泡炸壳，载体工程改良；先例比较清晰，机制完整含风险，体验提升但成本高昂，食评证实稳定实现。 |
| CIE-015 | Transformative Innovation | Structural Innovation | 液体橄榄以反向球化重构橄榄结构，证据扎实角色精确；先例比较有限；结构交互改变明确；机制完整含风险；有复用价值；elBulli等专业实现稳定。 |
| CIE-016 | Transformative Innovation | Structural Innovation | 证据支持 elBulli 2003 液态豌豆球替代面皮，保留 ravioli 包裹释放结构；先例比较与机制风险清晰，专业认可实现稳定，属结构创新。 |
| CIE-017 | Transformative Innovation | Structural Innovation | Alchemist整合多领域为餐饮系统，改变用餐结构；先例比较概括，机制情境化含风险，价值限高端场景，获米其林等认可实现稳定。 |
| CIE-018 | Incremental Innovation | Conventional | 咖啡 rub 牛排承袭香料 rub 与咖啡 savory 先例，已成通用做法；知识边界清晰，机制完整含风险，专业配方佐证实现，但仅为局部风味替换，收益有限。 |

## 2. Largest dimension-score deviations (top 10)

| ID | Total | per-dim (gold→pred) |
| --- | --- | --- |
| CIE-009 | 6 | existing:5→4, mechanistic:5→4, innovation:2→1, realization:1→4 |
| CIE-012 | 6 | culinary:5→4, existing:5→3, innovation:5→4, innovation:5→4, realization:5→4 |
| CIE-017 | 6 | culinary:5→4, existing:4→3, innovation:5→4, innovation:5→3, realization:5→4 |
| CIE-021 | 6 | existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→3 |
| CIE-A01 | 6 | culinary:2→4, existing:2→3, mechanistic:1→3, innovation:1→2 |
| CIE-015 | 5 | existing:4→3, innovation:5→4, mechanistic:5→4, innovation:5→4, realization:5→4 |
| CIE-022 | 5 | existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→4 |
| CIE-023 | 5 | existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→4 |
| CIE-024 | 5 | existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→4 |
| CIE-003 | 4 | culinary:3→5, existing:4→3, mechanistic:3→4 |

## 3. Ranking errors

1 imperfect ranking set(s):

| Set | Dimension | Gold (high→low) | Pred (high→low) | Pairwise acc |
| --- | --- | --- | --- | --- |
| RANK-RQ-01 | realization_quality | CIE-023 > CIE-010 > CIE-025 > CIE-001 > CIE-009 | CIE-009 > CIE-023 > CIE-010 > CIE-025 > CIE-001 | 60.0% |

## 4. Bias diagnosis (heuristic)

- **Novelty / Technique Inflation** (pred ranked higher than gold on non-trap cases): 0 case(s)
- **Conventionality Bias** (pred ranked lower than gold): 8 case(s)
  - examples: CIE-007(Structural Innovation→Incremental Innovation), CIE-010(Structural Innovation→Incremental Innovation), CIE-012(Transformative Innovation→Structural Innovation), CIE-014(Structural Innovation→Incremental Innovation), CIE-015(Transformative Innovation→Structural Innovation), CIE-016(Transformative Innovation→Structural Innovation), CIE-017(Transformative Innovation→Structural Innovation), CIE-018(Incremental Innovation→Conventional)
- **Adversarial Weirdness** (gold trap but pred not trap, or false alarm): 0 case(s)
- **Ingredient Stacking** (gold low but pred high; flagged by benchmark_tags): 0 case(s)
- **Note**: Ingredient-stacking uses `benchmark_tags` only as a diagnostic hint (not fed to the judge); `input_ingredients` is not provided at dataset top-level, so this signal is advisory and should be confirmed by manual review.

---
*Heuristic bias diagnosis from gold vs prediction category ranks. See `summary.json` for quantitative metrics.*
