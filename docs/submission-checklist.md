# NewwwRecipe 提交前检查清单（Submission Checklist）

> 本清单用于 Release Hy3 提交前的逐条核对。每一项都需有可验证证据，禁止把“部分完成”写成“完成”。
> 项目唯一正式基线见 [`PROJECT_STATE.md`](../PROJECT_STATE.md)，仓库同步规则见 [`AGENTS.md`](../AGENTS.md) 与 [`docs/versioning.md`](../docs/versioning.md)。

## 1. 步骤质量可靠性修复（Reliability fixes）

- [x] `src/creative_recipe/recipe/realization.py` 新增 `validate_recipe_steps()`
  - 步骤必须是 **4–7 个字符串**，每个非空；
  - 拒绝字面量 `"placeholder"` 及 `prepare the ingredients` / `cook until done` / `season as needed` / `serve and enjoy` 等占位句；
  - 整体必须包含**显式动作动词**，且至少包含一项**可执行信息**（时间 / 温度 / 火候 / 熟度）；
  - **不改变**现有 API / schema 字段结构。
- [x] 单次定向重试：`build_realization_messages` 支持 `correction` 参数，把校验错误作为反馈；`realize_concept` 在首次不合格时至多重试 **1 次**。
- [x] 两次仍不合格 → 抛出 `StepValidationError` → 服务层进入**明确标注**的 Demo fallback；绝不静默接受占位步骤，绝不把 fallback 标为 `Live · Hy3`。
- [x] `src/creative_recipe/llm/hy3.py`：`timeout=240.0`、`max_retries=2`（原为 60 / 3）。
- [x] `web/vite.config.ts`：`/api` 代理 `timeout: 0`、`proxyTimeout: 0`，支持长请求。
- [x] `realization.py`：强化生产 prompt（明确步骤数量、可执行信息、禁止占位句）。

## 2. 单元测试

- [x] `tests/test_realization.py`：合法 4–7 步、`"placeholder"`、空步、少于 4、多于 7、含糊 `Cook until done`、缺少可执行信息、首次失败重试成功、两次均失败抛错。
- [x] 修复 `tests/test_pipeline.py` / `tests/test_pipeline_e2e.py` / `tests/test_scoring_invariants.py` 中旧的 3 步占位 fixture（现已为合法 5 步，原先被新校验正确拦截，属护栏生效而非回归）。

## 3. 真实 Hy3 端到端验证（Live UI run）

- [x] 停止旧后端 `RVc6MP`，确认端口释放；重启后端（新 realization.py + hy3.py）与前端。
- [x] `GET /api/health`：`provider=hy3`、`demo_mode=false`。
- [x] 响应元数据：`meta.provider="hy3"`、`demo_mode=false`、`fallback_reason=null`。
- [x] 页面徽标 `Live · Hy3`（`badgeMode="live"`、`badgeText="Live · Hy3"`）。
- [x] 真实菜谱 “Coffee Galantine with Coffee-Chicken Aspic”，**7 个可执行步骤**（`stepsValid=true`、`stepCount=7`）。
- [x] CookingMode 显示 `Step 1 of 7`（非 `Nicely done` fallback）。
- [x] CIE 六维评分（`cieDimCount=6`），加权总分 **3.55**。
- [x] Innovation Trace 六阶段正常渲染（`TraceTimeline.tsx` 对 `trace.stages` 逐项渲染，六阶段均显示）。
- [x] 风险提示非空（`riskNoteLen=243`）；无 console / page / failed-request / broken-image 错误。
- [ ] 说明：验证脚本的 `traceStageCount` 统计因选择器 `[data-testid="trace-timeline"] > *` 只数到 2 个 wrapper（`h3` + `ol`），属脚本选择器缺陷；已读 `TraceTimeline.tsx` 源码确认六阶段均渲染，不影响“live 成功”结论。

## 4. 真实结果截图（1440×900）

- [x] `docs/screenshots/landing-1440x900.png`（更新）
- [x] `docs/screenshots/fridge-open-1440x900.png`（更新）
- [x] `docs/screenshots/preferences-1440x900.png`（更新）
- [x] `docs/screenshots/recipe-result-live-1440x900.png`（新增）
- [x] `docs/screenshots/cooking-mode-live-1440x900.png`（新增）

## 5. 正式 demo 视频

- [x] 输出 `docs/demo/newwwrecipe-live-demo.mp4`。
- [x] 从同一次真实 Hy3 录像（`provider=hy3`、`demo_mode=false`、`fallback_reason=null`）重新剪辑，未重新调用 Hy3，未混用 DemoProvider 素材。
- [x] 时长 **97 s**（在 80–105 s 目标区间内，< 120 s 硬上限）。
- [x] 分辨率 **1440×900**，h264（High），yuv420p，25 fps，约 **3.05 MB**（< 20 MB）。
- [x] 结构：0–6 s Landing；6–12 s 冰箱开门；12–25 s 选材（Chicken / Coffee 含 freeze 停留）；25–36 s Preferences；36–44 s Loading + “Generation wait shortened”；44–76 s Result / CIE / Innovation Trace（同一次真实 Hy3 调用的 live screenshot 经 freeze + 轻微 zoom 延长）；76–94 s Cooking Mode；94–97 s 结束字幕。
- [x] 用 `ffmpeg -i` 验证通过：duration / resolution / decode / size 四项均达标。
- [ ] ⚠️ **已知限制**：原始真实录像在 Cooking Mode 中仅停留在 `Step 1 of 7`，未点击 Next 进入 Step 2；`save-recipe` 点击未在画面中产生可见的 Favorites 计数变化。本次剪辑**未伪造**这些动作，因此最终视频未展示多步烹饪导航与收藏操作。后续若额度恢复，可重新录制一次包含完整 Cooking Mode 导航与 Save/Favorites 的真实 Hy3 流程并替换。

## 6. 全量测试（Test suites）

- [ ] Python（pytest，离线 `PYTHON_DOTENV_DISABLED=1` 且不设 `HY3_API_KEY`，目标 **133 passed**）。
- [ ] 数据集校验：`CIE-Culinary-Bench/scripts/validate_dataset.py`。
- [ ] 资产审计：65 张食材 PNG + 8 张场景 PNG 均可解码 / 加载，食材抠图保留 alpha。
- [ ] 前端：`npm run typecheck` / `npm run lint` / `npm run test` / `npm run build`。
- [ ] `git diff --check` 无空白错误。

## 7. 密钥与 Git 跟踪审计

- [ ] `.env` 不被跟踪，仓库仅保留 `.env.example`；无任何密钥 / API key 出现在 diff 或提交中。
- [ ] 缓存 / 临时文件（`.venv`、`node_modules`、`__pycache__`、`*.pyc`）被 `.gitignore` 覆盖。
- [ ] 仅显式文件暂存，不使用 `git add .` / `git add -A`。

## 8. 提交与合入

- [ ] `git commit`（显式文件，`chore: prepare final Hy3 submission`）。
- [ ] `git fetch`。
- [ ] `git switch main` && `git pull --ff-only origin main`。
- [ ] `git merge --no-ff feat/interactive-fridge-frontend -m "merge: release NewwwRecipe submission"`。
- [ ] 在 `main` 上重新全量验证。
- [ ] `git push origin main`（**非强制**）。
- [ ] 推送后检查公开仓库 / README / 图片 / 视频 / benchmark / 默认分支。

## 9. 保留的已确认修改

- `hy3.py`：`timeout 240` / `max_retries 2`。
- `vite.config.ts`：长请求代理（`timeout: 0`、`proxyTimeout: 0`）。
- `realization.py`：强化生产 prompt + 步骤质量校验 + 单次定向重试。

---

### 硬性约束（全程遵守）

- 不读取 / 打印 / 截图 / 提交 `.env` 或任何密钥。
- 不伪造 live 结果；失败必须明确标注并停止上报。
- 不 redesign UI / geometry / PNG / benchmark；不改变现有 API / schema 字段结构。
- 仅显式文件暂存；绝不 `git add .` / `-A`；绝不 force-push `main`。
- 任一关键步骤失败（调用失败 / 步骤无效 / 视频失败 / 测试失败 / 远端分叉 / GitHub 鉴权失败）→ 立即停止并给出明确阻塞信息。
