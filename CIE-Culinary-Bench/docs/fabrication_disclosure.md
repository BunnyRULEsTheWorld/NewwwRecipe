# Fabrication & Inference Disclosure

## 明确完全合成

`CIE-A01` 至 `CIE-A05` 是用户指定的 adversarial cases。菜名、具体组装、human evaluation、final result、creative hypothesis 和所有分数均为 benchmark 构造，不对应真实餐厅或真实评委。相关字段已写“人工 benchmark 判定（完全合成）”，元数据 `source.type=artificial`，URL 为空。

## 分析性标注（不是来源原话）

所有案例中的 `innovation_delta`、`mechanistic_justification`、`creative_hypothesis`、`risk_and_constraint`、六维分数和 `gold_reasoning`，除非句尾有 citation ID，均为数据集作者基于列示来源的分析。它们是 benchmark 的目标标签，不是化学实验结论，也不是厨师自述。

## 公开证据有限或对象需拆分

- CIE-001–009：节目级来源能确认《一饭封神》赛制、厨师阵容和专业评审语境，但公开索引未稳定提供每道菜的完整逐字评语。`judge_comment` 因此均为明确标注的证据性转述，不是伪造引语。
- CIE-003、CIE-005、CIE-007：精确菜名/配方在可公开检索页面中的证据尤其有限。本版只保留用户给定菜名和保守的料理结构分析，打上 `limited_public_evidence` / `evidence_gap`；未补造厨师姓名。
- CIE-004：菜名和“2.0/宫保方向”来自候选池与公开节目讨论线索；对具体风味机制的判断属于分析性标注。
- CIE-009：Le Colvert 的现代压鸭作为菜类受到 Michelin 等专业资料认可；候选池中的节目实例则被作为 execution failure。数据集明确区分“类型有价值”与“本次实例失败”，不把餐厅评价伪装成节目评语。
- CIE-018、CIE-019：是“现代料理参考型”而非单一可验证餐厅作品。来源证明技术/风味先例，human signal 表示经编辑资料的正面采用，不代表某场竞赛结果。
- CIE-023：Carbonara 起源存在争议；本版只把 20 世纪中期已有书面记录作为可证事实，不断言单一起源故事。
- CIE-025：专业评论肯定的是评论者当次吃到的牛排本体，同时严厉批评金箔汉堡和餐厅整体价值；没有来源提供“同一块牛排有/无金箔”的受控盲尝。本版据此只得出“金箔味觉增益未被证明”，不伪造专家对 Golden Tomahawk 的实验结论。

## 未做的事

本版没有编造任何带引号的专家逐字评价，没有宣称浏览过无法访问的付费正文，也没有把“蟹与柿子同食必然中毒”等民间说法写成事实。第30条 CIE-025 是公开存在的真实餐厅案例，不是合成补位。
