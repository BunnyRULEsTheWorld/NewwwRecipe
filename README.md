# NewwwRecipe

> 2026 腾讯犀牛鸟开源人才培养计划 · 混元大语言模型实战任务个人作品。  
> 本项目不是腾讯官方发布项目。

NewwwRecipe 是一个基于 Hy3 的创意菜谱生成与评估项目。

项目最开始想解决的问题很简单：如果家里只有一些零散食材，能不能让模型给出真正值得尝试的新做法？实际做下来，我发现“生成一道菜”并不难，更难的是判断一个结果到底有没有创意，以及这种创意是不是建立在合理的料理知识上。

所以现在项目主要有三部分：

- **NewwwRecipe 应用**：根据食材、口味和简单约束生成候选料理；
- **CIE（Culinary Innovation Evaluation）**：给候选料理做结构化评价和排序；
- **CIE-Culinary-Bench**：用来开发和验证 CIE 的评测数据集。

> 项目当前唯一正式状态见 [`PROJECT_STATE.md`](PROJECT_STATE.md)。版本同步与 WorkBuddy 更新流程见 [`docs/versioning.md`](docs/versioning.md)。

目前工作量主要集中在 CIE 和 benchmark 上，应用侧会在评测流程稳定后接上。

## CIE 怎么评

我不只让评估器看最终菜谱，还会给它一份结构化的 Innovation Trace。这样可以检查模型是基于什么已有做法、做了什么变化，以及这些变化有没有料理知识或机制上的依据。

Trace 目前分成六部分：

1. **Existing Culinary Context**：最接近哪些已有菜品、技法或食材用法；
2. **Ingredient & Technique Knowledge**：涉及哪些食材和烹饪知识；
3. **Innovation Delta**：相比已有做法具体改了什么；
4. **Mechanistic Justification**：为什么这种变化在风味、质地或烹饪机制上可能成立；
5. **Creative Hypothesis**：希望得到什么新的风味、口感或食用体验；
6. **Risk & Constraint**：这个方案可能在哪里失败。

CIE 再从六个维度打分：

| 维度 | 权重 |
| --- | ---: |
| Culinary Knowledge Grounding | 15% |
| Existing Culinary Precedent Analysis | 15% |
| Innovation Delta Quality & Magnitude | 25% |
| Mechanistic Plausibility | 20% |
| Innovation Value / Exploration | 15% |
| Realization Quality | 10% |

另外有一些约束。例如，如果对已有做法的判断都不可靠，Innovation Delta 不能只因为“变化很大”就得到高分；“这个组合很少见”本身也不能算机制解释。

详细规则见 [`docs/cie_framework_v3.md`](docs/cie_framework_v3.md)。

## 现在做到哪了

截至 2026-08-31，已经完成一个可以实际运行的 benchmark MVP，并完成一次仓库状态重新整理。

目前有：

- 30 个 case 的冻结数据集；
- schema、gold annotation、rubric、provenance 和数据质量说明；
- 可以调用真实 Hy3 的评测 runner；
- 一次完整的 anonymous trace-conditioned 主实验；
- 对旧 baseline 和失败 run 的单独归档。

当前主实验共有 33 条评测记录，33 条都成功完成并解析。

| Metric | Result |
| --- | ---: |
| Accuracy | 73.3% |
| Macro-F1 | 0.675 |
| Mean Spearman | 0.570 |
| MAE | 0.661 |
| Ranking pairwise accuracy | 86.7% |
| Parse / API success | 100% |

在更早的阶段还做过一个三个案例的小测试：Low / Partial / High-value 三档的得分顺序为 `4.20 < 6.60 < 8.50`。这个结果现在只保留作 smoke test，正式结果以完整 benchmark 实验为准。

## 这些结果目前有什么限制

现在的主实验属于 **trace-conditioned** 设置，也就是 evaluator 可以看到完整的 Innovation Trace。Trace 中的信息可能让任务变得更容易，因此这组结果还不能单独说明 CIE 在更弱信息条件下同样可靠。

接下来会补几组实验：

- **evidence-only**：去掉完整 trace，只保留更受限的信息；
- **repeated scoring**：同一样本重复评估，观察分数和排序波动；
- **human agreement**：和人工标注比较；
- **adversarial validation**：测试堆砌术语、虚构先例、随机加入稀有食材等做法会不会骗到高分。

历史上有一次 partial run 只成功了 16/33 条，另外 17 条是 `APIConnectionError`。这批结果只保留作运行记录，不计入正式 benchmark 指标。

## NewwwRecipe 应用

应用场景是“冰箱里有什么”。用户可以选择或输入已有食材，再补充口味和简单约束。系统生成多个候选，用 CIE 排序后再展示结果，而不是直接返回第一次生成的菜谱。

计划流程：

```text
用户输入食材 / 偏好
        ↓
      Hy3 生成
        ↓
多个 Recipe Concept + Innovation Trace
        ↓
      CIE 评估
        ↓
     排序和筛选
        ↓
菜谱 + 做法 + 创意解释 + 风险提示
```

## 交互式冰箱前端

项目现在包含一个可运行的网页前端，用来完整体验“冰箱里有什么”的创意菜谱流程。

### 技术栈

- React + TypeScript + Vite
- 手绘水彩/儿童绘本视觉风格
- FastAPI 薄适配器复用现有 `creative_recipe` pipeline
- `localStorage` 保存收藏

### 前端目录

- `web/` — React 源码与 Vite 配置；
- `src/creative_recipe/web/` — FastAPI 适配器（`app.py`、`service.py`、`ingredient_catalog.py`）；
- `ingredient/` — 65 张透明 PNG 食材插图；
- `fronted asset/` — 场景插图：厨房背景、冰箱三态、空篮子、搅拌碗、食谱书、收藏盒。

### 前置条件

- Python 3.11+
- Node.js 20+ / npm 9+
- Windows 开发（不需要 Docker）

### 安装

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd web
npm install
```

### 启动开发服务器

#### 方式一：两条命令

**终端 1 — 后端**

```cmd
cd C:\path\to\NewwwRecipe
set PYTHONPATH=src
.venv\Scripts\python.exe -m uvicorn creative_recipe.web.app:app --host 127.0.0.1 --port 8000 --log-level warning
```

**终端 2 — 前端**

```cmd
cd C:\path\to\NewwwRecipe\web
npm run dev
```

然后打开 http://127.0.0.1:5173/。

#### 方式二：小启动器（单窗口）

```cmd
python scripts\dev_server.py
```

该启动器会同时拉起后端与前端，并按 `Ctrl+C` 一并结束。

### Demo 模式与真实模型

未填写 API key 时，后端自动使用仓库内置 `DemoProvider` 进入 Demo 模式，可在离线环境完整浏览 UI。页面右上角会显示 “Demo mode” 徽标。

要使用真实模型：

```bash
copy .env.example .env
```

然后在 `.env` 中填写 `HY3_API_KEY`、`HY3_BASE_URL` 等配置。真实密钥只保存在本地 `.env`，不会提交。

配置了真实密钥但生成调用失败时，后端会自动回退到离线 `DemoProvider`，页面右上角显示 “Demo fallback” 徽标并附带一条非阻塞提示；系统从不伪造 live 结果，也不会把失败静默当成成功。

### 步骤质量可靠性

后端在菜谱 realization 层内置了程序化步骤校验，避免模型返回占位 / 无效步骤被前端当成真实结果：

- `validate_recipe_steps()` 校验步骤为 4–7 个非空字符串，拒绝 `"placeholder"` 及 `Prepare the ingredients`、`Cook until done`、`Season as needed`、`Serve and enjoy` 等占位句；
- 整体必须包含显式动作动词，且至少包含一项可执行信息（时间 / 温度 / 火候 / 熟度）；
- 若 Hy3 首次返回不合格步骤，后端会把具体校验错误作为反馈，进行**至多一次**定向重试；若仍不合格，则抛出 `StepValidationError`，由服务层进入**明确标注**的 Demo fallback，绝不静默接受占位步骤，也绝不把 fallback 标为 `Live · Hy3`；
- 不改变现有 API / schema 字段结构，只对 prompt 与生成后处理做了加固。

该逻辑有配套单元测试覆盖（合法 4–7 步、占位、空步、过少 / 过多、含糊 `Cook until done`、首次失败重试成功、两次均失败抛错）。

### API 端点

- `GET /api/health` — 健康检查，返回食材/场景资源数量与 demo 状态；
- `GET /api/ingredients` — 65 种食材清单；
- `POST /api/recipes/generate` — 返回菜谱、canonical CIE v3 六维评分、Innovation Trace、加权总分与元数据。

### CIE v3 合同

接口与前端严格使用 canonical 六维：

1. `culinary_knowledge_grounding` — 15%
2. `existing_culinary_precedent_analysis` — 15%
3. `innovation_delta_quality` — 25%
4. `mechanistic_plausibility` — 20%
5. `innovation_value` — 15%
6. `realization_quality` — 10%

总分由后端直接加权计算；前端不还原旧 Stage-A/Stage-B 75/25 公式。`stage_a_score`/`stage_b_score` 仅作为诊断字段返回，不在 UI 中用作主总分。

## 仓库结构

```text
.
├── README.md
├── PROJECT_STATE.md          # 当前唯一正式项目基线
├── AGENTS.md                 # WorkBuddy / 自动化修改规则
├── .env.example
├── .gitignore
├── requirements.txt
├── docs/                     # 项目方案、CIE、版本管理与实验记录
├── src/                      # NewwwRecipe 与 CIE 实现
├── data/                     # CIE-Culinary-Bench
├── scripts/                  # benchmark / validation 脚本
├── results/                  # 实验结果
└── examples/                 # 典型 case 和 demo 输出
```

当前公开仓库仍在从本地开发目录同步：`src/`、`data/`、`scripts/`、`results/`、`examples/` 中部分真实实现和实验文件尚未完整进入 GitHub。缺失文件必须从实际产生实验结果的工作副本导入，不应凭记忆重新生成。

## 环境

- Python 3.11+
- Node.js 20+ / npm 9+（用于前端）
- Hy3 API access（真实模型调用时）
- OpenAI-compatible Python SDK

### Python 依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

然后在本地 `.env` 中填写 API Key。真实密钥不会提交到仓库。

### 前端依赖

```bash
cd web
npm install
```

## 文档

- [当前项目状态](PROJECT_STATE.md)
- [版本管理与同步流程](docs/versioning.md)
- [项目方案](docs/submission_proposal.md)
- [CIE v3 设计说明](docs/cie_framework_v3.md)
- [早期三案例测试记录](docs/cie_validation_report.md)

## 最终提交前的工作

- [x] 接通 NewwwRecipe 的生成、评价和 UI 流程（交互式冰箱前端）；
- [x] 真实 Hy3 端到端验证（提供真实密钥时徽标显示 “Live · Hy3”，不伪造 live 结果）；
- [x] 步骤质量可靠性修复：realization 层程序化步骤校验 + 单次定向重试，杜绝占位步骤；
- [x] 录制正式 demo 视频（< 120 s，1440×900，已用 ffmpeg 验证）—— [`docs/demo/newwwrecipe-live-demo.mp4`](docs/demo/newwwrecipe-live-demo.mp4)（97 s，同一次真实 Hy3 素材重新剪辑，无伪造 Live）。
- [ ] 把完整 benchmark、runner 和结果文件同步到公开仓库；
- [ ] 完成 evidence-only、重复评测、人工一致性和对抗性实验；
- [ ] 整理典型失败案例。

提交前检查清单见 [`docs/submission-checklist.md`](docs/submission-checklist.md)。

## API Key

API Key 只通过环境变量或本地 `.env` 传入；仓库只保留 `.env.example`。
