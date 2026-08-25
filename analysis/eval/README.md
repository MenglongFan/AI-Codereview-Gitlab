# AI Code Review 评估集使用说明（README）

## 背景

目标是把 AI Code Review 的精确率从实测基线 **69%** 提升到 **85%+**。
本评估集提供量化验证底座：任何 prompt / 策略改动后，跑同一批用例，
对照 ground_truth 复测精确率/检出率，与基线对比判断「是否真的变好」。

## 当前基线（2026-08-25 实测）

| 指标 | 基线值 | 来源 |
|------|--------|------|
| 精确率 Precision | **69%**（20/29） | analysis/reports/mr_hitrate_verification.md |
| 检出率 Recall | **约 74%** | analysis/reports/mr_hitrate_verification.md |
| 历史报告质量 | 12 条标注：9 条 A/B，3 条 C，0 条 D | analysis/reports/history_baseline.md |

## 目录结构

```
analysis/eval/
├── eval_schema.md      # 评估单元、TP/FP/FN 判定规则、分级、样本分层
├── README.md           # 本文档
├── score.py            # 评分脚本（仅标准库）
└── cases/
    ├── mr-32.json      # 真实 diff 用例：eagle_v2 util.go（+76/-8）
    ├── mr-33.json      # 真实 diff 用例：etl_station 压测接口（+430/-59）
    ├── mr-34.json      # 真实 diff 用例：eagle_v2 spacemap（+3/-3）
    ├── mr-36.json      # 真实 diff 用例：five_knowledge TagCategory.vue（+309/-40）
    ├── mr-42.json      # 真实 diff 用例：etl_station FusionAlgoContextLoader（+458/-367）
    └── hist-*.json     # 历史标注用例 12 条（id 3,4,5,9,12,16,20,26,27,31,34,36）
```

## 复测流程（Prompt 改动 → 量化对比）

1. **改动 prompt**：编辑 `conf/prompt_templates.yml`（code_review_prompt / agentic prompt）。

2. **重新生成 review 结果**：对每个 `mr-*` 用例的 diff，用改动后的系统重新跑一次 review，
   产出结果保存为 JSON：
   ```json
   {"case_id": "mr-32", "findings": [
     {"location": "internal/data-process/subscriber/utils/util.go:EnsureHostNetwork", "severity": "high-value", "text": "..."}
   ]}
   ```
   （可将结果文件放 `analysis/eval/results/<run_id>/` 下，run_id 如 `prompt-v2`。）

3. **运行评分脚本**：
   ```bash
   python3 analysis/eval/score.py --results analysis/eval/results/prompt-v2.json
   ```

4. **查看输出**：脚本输出每条用例的 TP/FP/FN 明细、精确率/检出率，以及对比基线 69%/74% 的差异。
   自动匹配不上的条目标记 `needs_review`，需人工复核后修正。

5. **对比结论**：
   - 精确率/检出率同时 ≥ 基线 → 改动有效；
   - 精确率升但检出率降 → 过度保守（过滤了误报但也漏了真问题），需平衡；
   - 两指标都 ≥ 85% → 达成 Destination。

## 历史标注用例的用法

`hist-*` 用例无真实 diff ground_truth，用于复测「报告质量评级」：
对同样一份 commit 信息 + diff 摘要，让新系统产出 review 报告，
用 `score.py --hist` 模式按 `analysis/exports/sample_labels.json` 的标注维度
（结构完整性、具体/空泛、误报计数、可落地性、分数校准）重新评级，对比质量分布变化。

## 判定口径（重要）

- 每条 review 意见 vs ground_truth：同文件 + 同函数/行号近似 + 现象一致 → TP；
- 基于外部文档/commit message 而非代码 diff 的推测性意见 → FP；
- ground_truth 中标 `"fn": true` 的条目：真实缺陷但历史 review 未检出 → 计入检出率分母。
