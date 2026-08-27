# results

这里保存 benchmark 的评测结果和后续验证实验。

截至 2026-08-27，当前主实验是一次 anonymous trace-conditioned run：

- benchmark：30 frozen cases；
- runner records：33 / 33 成功；
- Parse / API success：100%；
- Accuracy：73.3%；
- Macro-F1：0.675；
- Mean Spearman：0.570；
- MAE：0.661；
- Ranking pairwise accuracy：86.7%。

之前有一次 run2 只成功了 16 / 33 条，另外 17 条是 `APIConnectionError`。这批结果已经单独归档，只保留作运行记录，不计入正式 benchmark 指标。

接下来会继续补：

- evidence-only；
- repeated scoring；
- human agreement；
- adversarial validation。

不同实验设置的结果会分开保存，不混在同一组指标里。
