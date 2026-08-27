# CIE-Bench v3 Validation Report

## 1. Validation Objective

验证 CIE v3 是否能够区分：

```text
High-value Innovation > Partial Innovation > Ordinary Recipe
```

而不是错误地将“越奇怪”排序得越高。

## 2. Experimental Design

### 2.1 生成与评价分离

实验不让同一个即时生成过程同时承担 idea 生成与评价。三个案例的 Recipe Concept 与 Culinary Innovation Reasoning Trace 预先固定，再交由 Hy3 Judge 评分。

### 2.2 Judge

- 模型：真实 Hy3；
- 接口：OpenAI-compatible；
- 方法：LLM-as-judge；
- 输出：六维 `score (1–10)`、`reason` 与 Innovation Delta 结构化分析。

## 3. Test Cases

### Case A — 番茄芝士焗鸡

- Level：Low Innovation
- 经典组合，合理但创新增量很低。

### Case B — Mochicken Bake

- Level：Partial Innovation
- coffee + chicken + cheese；
- 存在 coffee BBQ sauce、coffee-rubbed meat 等 precedent；
- 主要为 coffee glaze + cheese bake 的有限 technique bridge。

### Case C — 咖啡盐渍烟熏鸡

- Level：High-value Innovation
- Ingredient Role Shift：咖啡由普通饮品/调味角色迁移到腌渍、风味固定与烟熏体系中的功能材料；
- Technique Innovation：coffee curing × 烟熏；
- Flavor Architecture Innovation：形成多层风味结构；
- 有 precedent 与机制支撑。

## 4. Results

| Case | 水平 | CIE v3 总分 |
| --- | --- | ---: |
| A 番茄芝士焗鸡 | Low Innovation | **4.20** |
| B Mochicken Bake | Partial Innovation | **6.60** |
| C 咖啡盐渍烟熏鸡 | High-value Innovation | **8.50** |

```text
EXPECTED: C (High) > B (Partial) > A (Low)
ACTUAL:   C (8.50) > B (6.60) > A (4.20)
RESULT:   PASS
```

## 5. Interpretation

- Case A 虽然知识描述与 precedent 容易成立，但 Innovation Delta 与 Innovation Value 很低，因此整体得分最低；
- Case B 被识别为有依据的有限技法桥接，得分居中；
- Case C 的角色迁移、技法组合与风味结构重构均有机制支撑，因此得分最高。

结果初步支持：

```text
Innovation = Novel Change + Grounding + Value
Novelty ≠ Innovation
```

## 6. Current Limitation

该实验目前属于**初步判别力验证**。后续最终提交仍需补充：

- 更大样本上的判别力实验；
- 重复评分稳定性；
- 与人工标注的一致性；
- 对抗性样本验证；
- 完整结果表与失败模式分析。
