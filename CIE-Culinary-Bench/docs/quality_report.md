# Quality Report

## 结论

结构验证通过：30 cases、61 个来源条目、引用全部可解析。

v1.1 共 30 条：competition 9 + expert 11 + baseline 5 + adversarial 5。新增 CIE-025 是具有官方、专业评论、媒体与科学背景来源的真实餐厅案例。

## 自动检查

- 全部样本一级字段与用户 schema 一致，ID 唯一且 `metadata.id` 对齐。
- 所有 magnitude 为 0–5 整数；六维分数为 1–5 整数；类别、split、human signal 枚举均受控。
- 文内 citation ID 均能在 source registry 解析。
- JSON 与 JSONL 条数一致；schema 与标准库验证器随包提供。

## 规模

- 样本数：30
- 来源条目：61
- UTF-8 JSON 字符数（单条，含缩进）：min 3,963 / median 4,733 / max 6,381
- 空白切分词数不适用于中文，故不把字符数伪称为模型 token 数；不同 tokenizer 会给不同结果。
- split：{'competition_set': 9, 'expert_set': 11, 'baseline_set': 5, 'adversarial_set': 5}

| Category | Count | Share |
|---|---:|---:|
| Conventional | 6 | 20.0% |
| Surface Innovation | 4 | 13.3% |
| Incremental Innovation | 5 | 16.7% |
| Structural Innovation | 6 | 20.0% |
| Transformative Innovation | 4 | 13.3% |
| Adversarial Trap | 5 | 16.7% |

分布用于诊断而非训练先验；不为追求预设百分比而改写有证据支撑的 gold label。

## 证据审查

完全人工构造：CIE-A01–A05。证据特别有限/需谨慎解释：。竞赛 `judge_comment` 在无逐字稿时统一标注为证据性转述；未使用伪引号。所有机制、风险、评分和 gold reasoning 默认是分析性标注。

## 人工自检要点

1. Conventional 不等于低质量：Carbonara、宫保鸡丁等 realization 可高。
2. Magnitude 不等于 innovation value：A05 幅度高但价值/实现低。
3. 技术复杂不等于创新：CIE-001 明确拆开 knife work 与 eating value。
4. 高级食材数量不等于结构创新：CIE-002/003 检验 ingredient stacking。
5. 类型评价不覆盖具体实例：CIE-009 将压鸭类别与节目执行分离。
6. 食品安全表述避免民间毒理断言：A03 采用可控风险与感官机制表达。

## 尚未完成的外部验证

本包提供好/中/差输出与对抗提示，但未声称已经运行目标模型、完成人类双标或计算 kappa。正式论文实验应报告模型版本、prompt、温度、重复次数、盲评流程和置信区间。
