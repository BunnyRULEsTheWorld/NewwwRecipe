# CIE v3 早期三案例测试记录

这份文件记录的是 CIE v3 开发早期的一次小规模测试。它的作用只是确认当时的 rubric 至少能够把三个差异明显的案例排出预期顺序，不应把它当作完整 benchmark 的验证结果。

## 1. 测试目的

当时选了三个固定案例，分别代表：

- Low Innovation；
- Partial Innovation；
- High-value Innovation。

希望先检查一个最基本的问题：如果三个案例的创新程度差异很明显，CIE 能不能给出正确的相对排序。

## 2. 测试设置

为了减少即时生成带来的随机性，三个案例的 Recipe Concept 和 Culinary Innovation Reasoning Trace 都提前固定，再交给 Hy3 Judge 评分。

- 模型：Hy3；
- 接口：OpenAI-compatible；
- 方法：LLM-as-judge；
- 输出：六维 1–10 分评分、评分理由和 Innovation Delta 分析。

## 3. 三个案例

### Case A — 番茄芝士焗鸡

- 预期：Low Innovation；
- 理由：组合和做法都比较常见，合理，但新增内容有限。

### Case B — Mochicken Bake

- 预期：Partial Innovation；
- coffee + chicken + cheese；
- 能找到 coffee BBQ sauce、coffee-rubbed meat 等相近做法；
- 主要变化是把 coffee glaze 和 cheese bake 组合起来，属于有限的 technique bridge。

### Case C — 咖啡盐渍烟熏鸡

- 预期：High-value Innovation；
- 咖啡不再只是普通饮品或调味，而进入腌渍、风味固定和烟熏体系；
- 同时包含 coffee curing、烟熏和多层风味结构的组合；
- 可以找到相应 precedent 和机制解释。

## 4. 结果

| Case | 预期水平 | CIE v3 总分 |
| --- | --- | ---: |
| A 番茄芝士焗鸡 | Low Innovation | **4.20** |
| B Mochicken Bake | Partial Innovation | **6.60** |
| C 咖啡盐渍烟熏鸡 | High-value Innovation | **8.50** |

得到的顺序是：

```text
C (8.50) > B (6.60) > A (4.20)
```

和预期顺序一致。

## 5. 当时能得到的结论

这个小测试说明，当三个案例差异比较明显时，当前 rubric 至少没有把“常规但合理”和“有明显创新变化”的案例排反。

但三个样本远远不足以说明 evaluator 已经可靠。后续项目已经扩展到 30-case frozen benchmark，并开始做完整评测；这份文件只保留作为 CIE v3 的早期开发记录。

后续还需要用更大样本检查：

- 判别力；
- 重复评分稳定性；
- 与人工标注的一致性；
- adversarial cases；
- 不同信息条件下的表现差异。
