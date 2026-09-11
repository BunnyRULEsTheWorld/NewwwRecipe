# Benchmark Task Definition v1.1

## 0. 目标与数据视图

CIE-Culinary-Bench 测的是“料理创新判断”，不是菜名识别或餐厅声望记忆。主赛道统一使用 `closed_evidence` 视图：输入 `culinary_context`、`dish_information` 与 `innovation_trace`，隐藏 `metadata`、`human_evaluation_signal`、`cie_annotation` 和 `benchmark_tags`。这样模型能看到可审计的料理事实与 reasoning chain，但看不到人类结果或 gold label。

诊断赛道 `human_evidence_aware` 可额外提供 `human_evaluation_signal`，用于测量专业/公众证据能带来多少增益；结果必须与主赛道分开报告。严禁把 `gold_reasoning`、分数或标签泄漏进 prompt。

## Task 1: Innovation Classification

输入：单个样本的 `closed_evidence`。输出：六类之一：`Conventional`、`Surface Innovation`、`Incremental Innovation`、`Structural Innovation`、`Transformative Innovation`、`Adversarial Trap`，以及不超过180字的依据。

主要指标：Accuracy、Macro-F1。附加指标：按类别 recall、Adversarial Trap detection accuracy。Macro-F1 为主，因为样本小且类别数量不完全相等。

## Task 2: CIE Scoring

输入：与 Task 1 相同。输出：六个 1–5 整数分和简短理由。必须逐维打分，不能先给总分再反推；`magnitude` 不等于 `innovation_delta_quality`。

主要指标：六维 Macro-MAE（越低越好）、逐维 Spearman rho、Quadratic Weighted Kappa。附加指标：±1 accuracy、完全一致率。若重复运行，报告每个样本每维标准差及全局 mean within-case SD。

## Task 3: Innovation Ranking

输入：3–5 个样本的 `closed_evidence` 与一个指定维度。输出：从高到低的 case ID 列表；不得用餐厅名气、价格或技术数量代替指定维度。正式 ranking sets 使用 gold 分数互不相同的案例，避免未定义 tie-break。

主要指标：Pairwise Accuracy、Spearman rho；附加指标：Kendall tau-a。一个预测顺序中的每一对案例都参与 pairwise 计分。

## 有效性验证协议

1. 判别力：对 `good_medium_bad_cases.jsonl` 的三档输出进行评判，要求每组三条均满足 good > medium > bad。
2. 一致性：同一配置至少运行3次，报告分类 modal agreement 与评分 mean within-case SD。
3. 对抗性：报告五个合成 trap 的识别率，并单独检查 CIE-025 是否因 24K、名人和高价被误判为 Structural/Transformative。
4. 完整评测：保存模型名、endpoint 类型、prompt SHA-256、温度、reasoning effort、时间、原始响应和解析错误；解析失败计为失败，不静默重试到成功。

## 防止数据泄漏

该数据集仅有30条，不划分传统 train/test。它是 gold evaluation set，不建议在这些标签上微调。若进行 few-shot，必须公开示例 ID，并从对应指标分母中移除；跨版本比较时固定 prompt 和数据版本。

## 官方提交最低报告项

Hy3 主赛道需给出：30条 classification/scoring 完整表、全部 ranking sets、三次重复一致性、五条 adversarial 结果、至少3个典型失败归因。其他模型只能作为对照，不能替代 Hy3 结果。
