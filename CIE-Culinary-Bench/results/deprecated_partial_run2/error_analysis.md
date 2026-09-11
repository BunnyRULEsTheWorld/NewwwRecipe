# CIE-Culinary-Bench v1.1 — Error Analysis

## 1. Classification errors

6 misclassified case(s):

| ID | Gold | Pred | Reasoning (excerpt) |
| --- | --- | --- | --- |
| CIE-007 | Structural Innovation | Incremental Innovation | 基于 gnocchi 先例同盘组织冬春模块过渡，知识精确且主动限定证据边界，机制完整指风险，实现证据有限，属增量改良。 |
| CIE-010 | Structural Innovation | Incremental Innovation | Noma将garum逻辑移入肉类加koji，先例比较与酶学机制清晰，角色转通用鲜味液，专业证据实现；属底物与技术转移的增量改良，非范式颠覆。 |
| CIE-012 | Transformative Innovation | Structural Innovation | Noma将民间采集提升为菜单研发与供应链核心系统，改变食材角色与餐厅结构；证据引官方回顾与长期菜单，机制完整含风险，但先例比较较概括，实现稳定。 |
| CIE-014 | Structural Innovation | Incremental Innovation | 经典味型装入轻泡炸壳，载体工程改良；先例比较清晰，机制完整含风险，体验提升但成本高昂，食评证实稳定实现。 |
| CIE-015 | Transformative Innovation | Structural Innovation | 液体橄榄以反向球化重构橄榄结构，证据扎实角色精确；先例比较有限；结构交互改变明确；机制完整含风险；有复用价值；elBulli等专业实现稳定。 |
| CIE-016 | Transformative Innovation | Structural Innovation | 证据支持 elBulli 2003 液态豌豆球替代面皮，保留 ravioli 包裹释放结构；先例比较与机制风险清晰，专业认可实现稳定，属结构创新。 |

## 2. Largest dimension-score deviations (top 10)

| ID | Total | per-dim (gold→pred) |
| --- | --- | --- |
| CIE-009 | 6 | existing:5→4, mechanistic:5→4, innovation:2→1, realization:1→4 |
| CIE-012 | 6 | culinary:5→4, existing:5→3, innovation:5→4, innovation:5→4, realization:5→4 |
| CIE-015 | 5 | existing:4→3, innovation:5→4, mechanistic:5→4, innovation:5→4, realization:5→4 |
| CIE-003 | 4 | culinary:3→5, existing:4→3, mechanistic:3→4 |
| CIE-007 | 4 | culinary:4→5, innovation:4→3, innovation:4→3, realization:4→3 |
| CIE-008 | 4 | existing:5→4, mechanistic:5→4, innovation:4→3, realization:5→4 |
| CIE-010 | 4 | culinary:5→4, existing:5→4, mechanistic:5→4, innovation:5→4 |
| CIE-011 | 4 | culinary:5→4, existing:5→4, mechanistic:5→4, realization:5→4 |
| CIE-014 | 4 | culinary:5→4, mechanistic:5→4, innovation:4→3, realization:5→4 |
| CIE-016 | 4 | culinary:5→4, innovation:5→4, mechanistic:5→4, innovation:5→4 |

## 3. Ranking errors

- None. All ranking sets achieved perfect pairwise accuracy.

## 4. Bias diagnosis (heuristic)

- **Novelty / Technique Inflation** (pred ranked higher than gold on non-trap cases): 0 case(s)
- **Conventionality Bias** (pred ranked lower than gold): 6 case(s)
  - examples: CIE-007(Structural Innovation→Incremental Innovation), CIE-010(Structural Innovation→Incremental Innovation), CIE-012(Transformative Innovation→Structural Innovation), CIE-014(Structural Innovation→Incremental Innovation), CIE-015(Transformative Innovation→Structural Innovation), CIE-016(Transformative Innovation→Structural Innovation)
- **Adversarial Weirdness** (gold trap but pred not trap, or false alarm): 0 case(s)
- **Ingredient Stacking** (gold low but pred high; flagged by benchmark_tags): 0 case(s)
- **Note**: Ingredient-stacking uses `benchmark_tags` only as a diagnostic hint (not fed to the judge); `input_ingredients` is not provided at dataset top-level, so this signal is advisory and should be confirmed by manual review.

---
*Heuristic bias diagnosis from gold vs prediction category ranks. See `summary.json` for quantitative metrics.*
