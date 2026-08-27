# NewwwRecipe 项目方案

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务  
> 任务方向：开放式场景——AI 应用与评判标准设计  
> 项目性质：个人 / 活动作品，非腾讯官方发布项目

## 1. 项目简介

NewwwRecipe 是一个基于 Hy3 的创意菜谱生成与评估项目。

最开始的想法是做一个“冰箱里有什么就做什么”的菜谱应用：用户输入现有食材，模型给出一些不那么常规、但确实值得尝试的新做法。实际开发过程中，我很快发现生成菜谱本身不是最难的部分。更麻烦的是，开放式生成没有唯一答案，很难判断一个结果到底是真的有创意，还是只是把少见食材、复杂技法和专业术语堆在一起。

因此项目现在分成三部分：

1. **NewwwRecipe 应用**：根据食材、口味和简单约束生成多个候选料理；
2. **CIE（Culinary Innovation Evaluation）**：对候选进行结构化评价和排序；
3. **CIE-Culinary-Bench**：用来开发和验证 CIE 的评测数据集。

目前项目进度主要集中在 CIE 和 benchmark。应用侧会在评测流程稳定后继续接入生成、筛选和 UI。

## 2. 使用场景和目标用户

### 2.1 使用场景

用户面对家中已有食材时，经常会遇到两种情况：一是只会按照熟悉的方式做，二是让大模型随便生成后，得到的结果虽然新奇，但不一定靠谱。

NewwwRecipe 希望在这两者之间做一个筛选：先生成多个候选，再检查它们的料理依据、具体变化、可执行性和风险，最后再展示给用户。

### 2.2 目标用户

- 希望利用家中现有食材尝试新做法的普通用户；
- 喜欢跨菜系、风味实验和创意料理的烹饪爱好者；
- 对开放式生成评价、LLM-as-judge 或 benchmark 感兴趣的开发者。

## 3. 为什么需要单独做评价

创意料理没有标准答案，不能像选择题一样直接判断对错。

如果只看最终菜谱，容易出现几类问题：

- 少见组合被误认为有创意；
- 解释听起来专业，但实际没有可靠的料理知识支撑；
- 模型没有说明自己和已有做法相比到底改了什么；
- 结果看起来有趣，但实际难以执行；
- 同一个输入一次能生成很多方案，但缺少可靠的筛选依据。

所以 NewwwRecipe 没有把“生成”和“展示”直接连在一起，而是在中间加入 CIE 评价。

## 4. 系统设计

目前的应用流程设计如下：

```text
用户输入食材 / 偏好 / 简单约束
                ↓
              Hy3
                ↓
      生成多个候选 Recipe
                ↓
 Recipe Concept + Innovation Trace
                ↓
              CIE
                ↓
      六维评分 + 规则检查
                ↓
            排序 / 筛选
                ↓
 菜谱 + 做法 + 创意解释 + 风险提示
```

应用最终不会直接返回第一次采样的结果，而是先生成多个候选，再进行评价和排序。

## 5. Innovation Trace

为了避免只看最终文字，我给每个候选增加了一份结构化 Innovation Trace。

Trace 目前包含六部分：

### 5.1 Existing Culinary Context

记录最接近的已有料理、类似技法和类似食材用法。主要作用是给“创新”找一个参照，避免模型直接声称某个组合从未出现过。

### 5.2 Ingredient & Technique Knowledge

记录当前方案涉及的食材和技法知识，包括风味、香气、质地、脂肪相互作用和烹饪机制等。

### 5.3 Innovation Delta

说明相较于已有做法到底改了什么。目前主要区分：

- Ingredient Role Shift；
- Technique Innovation；
- Flavor Architecture Innovation；
- Texture Innovation；
- Presentation / Experience Innovation。

这里不会把“变化越大”直接当成“越创新”。如果只是随机替换很多食材，但没有合理依据，分数不应该自动变高。

### 5.4 Mechanistic Justification

要求给出可以检查的理由，例如烹饪科学、风味交互、化学机制、已有经验或 precedent。

### 5.5 Creative Hypothesis

说明这次变化希望得到什么新的风味、口感、食用体验或食材利用方式。

### 5.6 Risk & Constraint

记录比例、技法、原料和执行上的风险，以及方案可能失败的地方。

## 6. CIE 评分方法

CIE 当前使用六个维度：

| 维度 | 权重 | 主要看什么 |
| --- | ---: | --- |
| Culinary Knowledge Grounding | 15% | 食材和料理知识是否可靠 |
| Existing Culinary Precedent Analysis | 15% | 是否能找到并正确比较已有做法 |
| Innovation Delta Quality & Magnitude | 25% | 是否真的有明确且有效的变化 |
| Mechanistic Plausibility | 20% | 这些变化是否有机制或经验依据 |
| Innovation Value / Exploration | 15% | 是否带来新的风味、口感、体验或利用价值 |
| Realization Quality | 10% | 是否合理、可执行并表达清楚 |

总分按六个维度加权得到。

除了 LLM-as-judge 打分，还加了几条硬约束：

- 无法合理说明 precedent 时，相关维度不能直接进入高分档；
- 基础料理知识本身不可靠时，Innovation Delta 的分数上限会被限制；
- “很少见”“很特别”“很搭”不能单独作为机制解释；
- 变化幅度大并不自动加分；
- 高分方案需要明确说明风险和限制。

这些规则主要是为了减少几种常见的假高分情况。

## 7. 重点技术

### 7.1 Hy3 调用

项目通过 Hy3 的 OpenAI-compatible 接口调用模型。API Key 使用环境变量或 `.env` 传入，不写入源码或公开仓库。

### 7.2 Structured Output

Recipe Concept、Innovation Trace、六维评分、理由和错误信息都使用结构化字段，方便脚本解析、保存和统计。

### 7.3 LLM-as-Judge + 规则约束

CIE 不是单纯让模型自由评价“这道菜有多创新”，而是给定固定 rubric，再配合规则限制和结果记录。

### 7.4 Benchmark Runner

目前的 runner 会保存每条样本的输入、输出、解析状态、评分和 provenance，并区分：

- 完整正式 run；
- partial / failed run；
- 已废弃 baseline；
- 后续的 evidence-only、repeat、adversarial 等不同实验设置。

这样可以避免因为 API 失败或实验设置不同，把不能比较的结果混在一起。

### 7.5 匿名评测

当前主实验隐藏了显式 case ID，减少模型直接利用样本编号等信息的可能性。

## 8. CIE-Culinary-Bench

当前 benchmark 的核心数据集包含 30 个冻结 case。

与数据集配套的内容包括：

- schema；
- gold annotation；
- rubric；
- provenance；
- source registry；
- fabrication disclosure；
- annotation guideline；
- quality report。

目前先控制样本规模，优先保证每个 case 的来源、标注和设计目的能够说明清楚。数据集中包含低创新、部分创新、高创新以及 grounding、mechanism、feasibility 等不同问题类型。

benchmark 冻结后，不会为了让某一次实验结果更好而修改 gold 或 rubric。

## 9. 当前实验结果

### 9.1 三案例早期测试

CIE v3 开发早期先用三个差异明显的案例做过一次小测试：

| Case | 预期水平 | CIE 分数 |
| --- | --- | ---: |
| A | Low Innovation | 4.20 |
| B | Partial Innovation | 6.60 |
| C | High-value Innovation | 8.50 |

得到的顺序是 `C > B > A`，和预期一致。

这个测试现在只作为开发早期的 smoke test 保存，不作为主要实验结果。

### 9.2 当前主实验

目前已经完成一次真实 Hy3 的 anonymous trace-conditioned run。

- frozen benchmark：30 cases；
- runner 记录：33 条；
- 33 / 33 成功完成并解析；
- Parse / API success：100%。

结果如下：

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

这组结果是当前 benchmark 的主要运行结果，但它还有一个明显限制：evaluator 可以看到完整 Innovation Trace，因此输入本身可能给了较强提示。

### 9.3 Partial run 的处理

此前有一次 run2 只成功了 16 / 33 条，另外 17 条是 `APIConnectionError`。

这批结果已经单独归档，只保留作运行记录，不算正式 benchmark 结果。迁移到后续完整 run 时，对可复用记录进行了 prompt hash 校验，没有把失败 run 和完整结果混在一起。

## 10. 接下来需要补的验证

官方任务要求至少做判别力验证和一致性验证，并鼓励对抗性验证。当前还需要补以下几组实验。

### 10.1 Evidence-only

去掉完整 Innovation Trace，只给 evaluator 更受限的 recipe / evidence 信息，再重新评测。

这个实验主要用来判断：当前 trace-conditioned 设置里的表现，有多少来自 evaluator 本身，有多少来自 trace 提供的提示。

### 10.2 重复评分

对同一样本至少重复评测 3 次，统计：

- 总分标准差；
- 维度分数波动；
- class label agreement；
- ranking stability。

### 10.3 人工一致性

由人工按照同一 rubric 对样本盲评，再和 Hy3 judge 结果比较。

### 10.4 系统化判别力实验

不再只展示三个成功案例，而是构造多组 High / Partial / Low 或 Good / Medium / Bad 样本，统计是否能够稳定保持预期排序。

### 10.5 Adversarial cases

会重点测试几类可能骗分的做法：

- 增加篇幅；
- 堆砌专业术语；
- 编造 precedent；
- 随机加入陌生或稀有食材；
- 给出听起来漂亮但实际错误的机制解释；
- 明显不可执行，但强化“创新”叙述。

## 11. NewwwRecipe 界面设计

首页暂定标题为 **What do we have?**。

用户可以：

- 从冰箱式分类界面选择蔬菜、肉类等食材；
- 直接输入已有食材；
- 补充口味偏好和简单状态约束。

系统生成多个候选并经过 CIE 筛选后，在结果页展示：

- 菜品名称；
- 食材和调料；
- 制作步骤；
- 食材特点；
- 搭配和机制解释；
- 最接近的已有料理及差异；
- 创意点；
- 尝试成本和失败风险；
- CIE 六维评分和解释。

用户可以选择重新生成，或者收藏 / 进入下一步。

## 12. 预期效果

最终希望做到以下几件事：

1. NewwwRecipe 可以根据现有食材生成多个候选，并经过 CIE 排序后再展示；
2. CIE 的评分过程能够被脚本记录和复现，而不是只展示一次模型输出；
3. benchmark 中包含普通样本、难例、反例和对抗性样本；
4. 最终报告能够说明哪些类型的创新容易判断、哪些容易出错，以及 Hy3 在这些 case 上的表现边界；
5. GitHub 仓库包含运行说明、环境配置、评测脚本、数据、结果和 demo。

## 13. 时间规划

### 8 月 27 日

- 完成并提交项目方案；
- 整理 CIE 设计说明；
- 整理 30-case frozen benchmark；
- 完成当前 trace-conditioned 主实验；
- 建立公开 GitHub 仓库基础结构。

### 8 月 28 日—8 月 31 日

- 跑 evidence-only；
- 跑 repeated scoring；
- 完成人工一致性抽检；
- 完成多组 High / Partial / Low 判别力实验；
- 构造并运行 adversarial cases。

### 9 月 1 日—9 月 4 日

- 接通 NewwwRecipe generator；
- 把 CIE 接入候选排序；
- 完成结果页主要字段；
- 打通基础 UI 流程。

### 9 月 5 日—9 月 7 日

- 跑最终 benchmark；
- 输出完整结果表；
- 整理失败类型；
- 选取典型 case；
- 完成主要分析。

### 9 月 8 日—9 月 9 日

- 检查 README、环境和运行命令；
- 同步完整 benchmark、scripts 和 results；
- 清理密钥和开发残留；
- 录制 2 分钟以内 demo 视频或 GIF。

### 9 月 10 日

完成最终提交。

## 14. 主要风险

### Trace 提供的信息过强

处理方式：单独跑 evidence-only，并把两种实验设置分开报告。

### LLM-as-judge 有随机波动

处理方式：重复评测，并和人工标注比较。

### benchmark 规模较小

处理方式：冻结 gold / rubric，不围绕单次结果反复修改数据；另外加入 challenge / adversarial cases。

### API 连接失败影响结果

处理方式：保存 per-case 状态和运行记录，partial run 不计入正式指标。

### UI 占用过多时间

处理方式：先完成 benchmark 和验证，再做界面细节。

## 15. 最终提交内容

最终计划提交：

1. NewwwRecipe 应用源码；
2. CIE evaluator；
3. CIE-Culinary-Bench 及其说明文件；
4. benchmark / validation 脚本；
5. 判别力、一致性、evidence-only 和 adversarial 实验结果；
6. 完整结果表、典型案例和错误分析；
7. README、环境配置和运行说明；
8. 2 分钟以内 demo 视频或 GIF。
