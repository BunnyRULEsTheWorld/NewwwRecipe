# Annotation Guideline v1.1

## 1. 标注顺序

先固定比较对象（传统 reference），再记录材料/技术知识，随后写 before→after 的 delta；只有在 delta 可定位后才写机制、假设、风险、类别与分数。不要从“高级餐厅/昂贵食材/陌生名字”倒推高创新。

## 2. 创新类别

| 类别 | 可操作定义 | 排除条件 |
|---|---|---|
| Conventional | 主要遵循成熟原型；局部变体不改变角色或体验结构 | 不能因“经典”而给低 realization |
| Surface Innovation | 变化集中于外形、命名、装饰、堆料或技术展示，核心食用逻辑基本不变 | 若角色/结构显著改变，升至 Incremental/Structural |
| Incremental Innovation | 在既有原型内产生明确、机制可解释的局部价值 | 仅替换同类材料且无效果证据不够 |
| Structural Innovation | 重写至少一个关键角色、质构架构、技法用途或上菜结构 | 幅度大但无机制/价值不能自动进入 |
| Transformative Innovation | 创造可迁移的新料理能力、范式或完整体验系统，并有强证据支持 | 一次性的视觉奇观不够 |
| Adversarial Trap | 人工设计来诱发 novelty bias；可包含局部合理机制，但整体证据链刻意缺失 | 标签不等于“永远不可能做成” |

类别不是六维平均分的机械映射。传统菜可以 grounding/realization 很高但仍为 Conventional；失败的大胆实验可以 delta 大但 value/realization 低。

## 3. 六维 1–5 锚点

### culinary_knowledge_grounding

1：与基本料理事实冲突；2：泛泛罗列材料；3：说明主要角色/属性；4：说明相互作用和条件；5：来源扎实、角色精确且主动限定边界。

### existing_culinary_precedent_analysis

1：无先例或虚构先例；2：只报大菜系；3：给出最近原型；4：逐项比较继承与偏离；5：还能识别并行先例、历史脉络和替代解释。

### innovation_delta_quality

1：无可辨变化或纯命名；2：装饰/同类堆叠；3：有意义的局部替换；4：关键角色、结构或技术用途改变；5：形成可迁移的新能力/范式。此项评“变化质量”，不是 magnitude。

### mechanistic_plausibility

1：明显矛盾；2：只有口号；3：至少一个机制成立但缺约束；4：风味/质构机制完整并指出风险；5：多机制一致、条件明确且可被实验推翻。

### innovation_value

1：没有可识别的食用/文化/系统收益；2：主要是新奇；3：改善一个局部目标；4：产生显著且可复用的料理价值；5：扩展料理边界或建立新范式。

### realization_quality

1：公开结果失败或完全未验证且风险高；2：主要执行问题；3：结果混合/证据有限；4：专业认可且实现稳定；5：长期、重复、跨场景验证。无品尝证据时不因推理漂亮给 5。

## 4. Magnitude 与质量

`magnitude` 只表示 before→after 的变化幅度（0 无变化，5 范式/系统变化），不表示好坏。A05 可 magnitude=4 但 innovation_value=2；成熟 Carbonara 可 magnitude=0 且 realization=5。

## 5. Failure Mode

- Technique Inflation：技术数量/难度被误当价值。
- Random Combination：组合缺少桥梁机制与主次。
- Novelty Bias：怪异/首次见被误当创新成功。
- Ingredient Stacking：增加数量或价格而未重构关系。
- Execution Failure：概念可能成立但实际火候、质构、调味或服务失败。
- Presentation-Function Mismatch：造型妨碍入口、温度或分享逻辑。
- Evidence Gap：公开证据不足以确认实现结果。

允许多标签；无显著失败可使用 `None`。

## 6. Human signal 与引语

只在有可定位逐字稿时使用引号。其余写“证据性转述（非逐字引语）”，并指出来自节目结果、创作者自述、专业指南还是研究者判断。宣传文案可证明“创作者意图”，不能单独证明感官成功。

## 7. 标注复核

两名标注者先独立完成类别和六维分，再对差值≥2或类别跨两级的项目仲裁。仲裁优先核对：比较对象是否一致、证据是否支持 actual execution、是否把 magnitude 当 quality、是否把品牌声望当结果。建议报告 exact agreement、quadratic weighted kappa 与 Spearman；本 v1.1 提供 gold seed，不声称已经完成多人一致性实验。
