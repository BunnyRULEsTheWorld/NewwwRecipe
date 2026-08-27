# results

本目录用于保存 CIE-Culinary-Bench 的正式评测结果、重复评分一致性实验、对抗性验证以及必要的统计摘要。

截至 2026-08-27，当前主结果已经从早期三案例 smoke test 推进到 **anonymous trace-conditioned canonical run**：

- benchmark core：30 frozen cases；
- runner records：33 / 33 成功；
- Parse / API success：100%；
- Accuracy：73.3%；
- Macro-F1：0.675；
- Mean Spearman：0.570；
- MAE：0.661；
- Ranking pairwise accuracy：86.7%。

历史 run2 partial 仅完成 16 / 33，另有 17 个 `APIConnectionError`，已迁入 `deprecated_partial_run2/`，只保留 provenance / migration history，**不属于有效 benchmark 结果**。

当前 canonical 轨道为 trace-conditioned；后续仍需独立补齐 evidence-only、repeated scoring、human agreement 与 adversarial validation，禁止把不同信息条件下的结果混报为同一结论。
