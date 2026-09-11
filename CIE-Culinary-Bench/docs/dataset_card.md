# Dataset Card

## 摘要

CIE-Culinary-Bench v1.1 评估模型能否区分 novelty magnitude 与 innovation quality。样本覆盖真实竞赛、被专业机构/餐厅资料记录的创新料理、传统成熟菜和人工对抗案例。核心标签不是一个脱离语境的总分，而是 `innovation_trace`、创新类别、失败模式、六维评分和可复核的 gold reasoning。

## 数据组成

| split | 数量 | 主要用途 |
|---|---:|---|
| competition_set | 9 | 利用节目/评审结果观察“概念—执行”差距 |
| expert_set | 11 | 同时覆盖结构/变革正例与有专业反馈的表层反例 |
| baseline_set | 5 | 防止模型把成熟传统自动误判为“无价值”或“创新” |
| adversarial_set | 5 | 测试怪异名称、堆料和幅度偏差 |

共 30 条。v1.1 以真实、有多层证据的 CIE-025 补齐原候选池缺失的第 30 条。

## 证据模型

来源按可审计性分层：P1 官方/创作者一手资料；P2 Michelin、World's 50 Best、Smithsonian 等权威机构；P3 可靠媒体或经编辑的专业食物媒体；P4 经测试配方/背景资料；A1 benchmark 分析性推断；SYN 完全人工构造。P1/P2 不等于一定“好吃”，只表示来源更接近创作者或专业评价。

竞赛案例公开可检索材料并不都提供完整菜名、配方和逐字评语。缺证据时保留抽象描述、降低 `realization_quality` 的置信度，并在披露文件中标记；没有为了填满字段而伪造评委原话。

## 推荐任务

1. 给定菜品材料，预测创新类别与六维分数。
2. 生成 `innovation_delta` 与可证伪的 failure condition。
3. 区分“有先例的机制迁移”与“随机组合”。
4. 对好/中/差推理做 pairwise ranking。
5. 在 adversarial set 上测 novelty bias 与 technique inflation。

## 不推荐用途

- 将分数当作厨师、菜系或文化的绝对排名。
- 从个别节目剪辑推断完整职业能力。
- 把分析性化学解释当作经过实验室验证的定论。
- 用于临床饮食、过敏管理或 HACCP 合规替代。

## 局限与偏差

样本小、中文叙述占主、地域覆盖不均；竞赛证据受节目剪辑与公开索引限制；专家集存在知名餐厅选择偏差；baseline 不是低质量，很多传统菜在 grounding 和 realization 上反而高分；`final_result` 为兼容用户 schema 只能选四个离散值，因此“praised”有时表示权威资料正面收录，不表示竞赛获奖。

## 版本与复现

版本：1.1；检索截止：2026-08-26。来源 URL、访问日期、每案 citation ID 和自动校验结果均随包提供。更新公开证据时应保留旧版本并重新双人复核有争议标签。
