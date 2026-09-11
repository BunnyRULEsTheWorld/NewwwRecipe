# CIE-Culinary-Bench v1.1 — Error Analysis

## 1. Classification errors

5 misclassified case(s):

| ID | Gold | Pred | Reasoning (excerpt) |
| --- | --- | --- | --- |
| CIE-004 | Incremental Innovation | Structural Innovation | 保留卷制平台，鱼香改宫保并多层重组；食材角色与风险明确，先例比较清晰，结构角色改变，机制完整有风险，收益局部，公开证据有限未证平衡。 |
| CIE-012 | Transformative Innovation | Structural Innovation | Noma将采集提升为菜单系统核心，改变食材角色与供应结构；证据具官方回顾与专家认可，各维机制与风险清晰，但缺跨场景验证与范式迁移明证，故评Structural与4分档。 |
| CIE-015 | Transformative Innovation | Structural Innovation | 证据扎实：绿橄榄汁反向球化形成薄膜球体，继承外形反转固液结构；机制与风险明确，多家餐厅复现。属关键结构改变，非范式新建。 |
| CIE-016 | Transformative Innovation | Structural Innovation | 以球化膜替面皮，保留 ravioli 包裹-释放逻辑，结构改变明确；多源证据支持历史实现，机制与风险清晰，属结构创新。 |
| CIE-017 | Transformative Innovation | Structural Innovation | 案例将用餐从菜品序列扩展为跨空间多感官叙事系统，整合先例改变结构，机制与收益明确，获米其林等认可，实现稳定，属结构创新。 |

## 2. Largest dimension-score deviations (top 10)

| ID | Total | per-dim (gold→pred) |
| --- | --- | --- |
| CIE-A01 | 8 | culinary:2→5, existing:2→4, mechanistic:1→3, innovation:1→2 |
| CIE-008 | 7 | culinary:5→4, existing:5→3, mechanistic:5→4, innovation:4→3, realization:5→3 |
| CIE-009 | 6 | existing:5→4, mechanistic:5→4, innovation:2→1, realization:1→4 |
| CIE-020 | 6 | existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→3 |
| CIE-022 | 6 | culinary:5→4, existing:5→3, mechanistic:5→4, innovation:2→1, realization:5→4 |
| CIE-A02 | 6 | culinary:3→5, existing:3→4, innovation:2→3, mechanistic:2→3, innovation:1→2 |
| CIE-011 | 5 | culinary:5→4, existing:5→3, mechanistic:5→4, realization:5→4 |
| CIE-012 | 5 | culinary:5→4, existing:5→4, innovation:5→4, innovation:5→4, realization:5→4 |
| CIE-013 | 5 | culinary:5→4, existing:5→4, mechanistic:5→4, innovation:5→4, realization:5→4 |
| CIE-015 | 5 | culinary:5→4, innovation:5→4, mechanistic:5→4, innovation:5→4, realization:5→4 |

## 3. Ranking errors

2 imperfect ranking set(s):

| Set | Dimension | Gold (high→low) | Pred (high→low) | Pairwise acc |
| --- | --- | --- | --- | --- |
| RANK-IV-01 | innovation_value | CIE-015 > CIE-008 > CIE-018 > CIE-025 > CIE-A04 | CIE-015 > CIE-018 > CIE-008 > CIE-025 > CIE-A04 | 90.0% |
| RANK-RQ-01 | realization_quality | CIE-023 > CIE-010 > CIE-025 > CIE-001 > CIE-009 | CIE-023 > CIE-009 > CIE-010 > CIE-025 > CIE-001 | 70.0% |

## 4. Bias diagnosis (heuristic)

- **Novelty / Technique Inflation** (pred ranked higher than gold on non-trap cases): 1 case(s)
  - examples: CIE-004(Incremental Innovation→Structural Innovation)
- **Conventionality Bias** (pred ranked lower than gold): 4 case(s)
  - examples: CIE-012(Transformative Innovation→Structural Innovation), CIE-015(Transformative Innovation→Structural Innovation), CIE-016(Transformative Innovation→Structural Innovation), CIE-017(Transformative Innovation→Structural Innovation)
- **Adversarial Weirdness** (gold trap but pred not trap, or false alarm): 0 case(s)
- **Ingredient Stacking** (gold low but pred high; flagged by benchmark_tags): 0 case(s)
- **Note**: Ingredient-stacking uses `benchmark_tags` only as a diagnostic hint (not fed to the judge); `input_ingredients` is not provided at dataset top-level, so this signal is advisory and should be confirmed by manual review.

---
*Heuristic bias diagnosis from gold vs prediction category ranks. See `summary.json` for quantitative metrics.*
