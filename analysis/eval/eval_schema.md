# AI Code Review 评估集 Schema 说明

> 本目录固化 AI Code Review（GitLab + LLM 代码审查）准确率评估的历史资产，
> 使之成为可重复运行的评估集。本文件定义评估单元、判定规则、问题分级与样本分层。

## 1. 评估单元（Evaluation Unit）

一个评估单元 = **一份 diff（输入） + 一份期望检出问题清单 ground_truth（标准答案） + 一组判定规则**。

- `diff`：某一次真实 MR 的变更内容（GitLab diff JSON 数组，每项含 new_path/old_path/diff 字符串）。
  本评估集的 diff 不内嵌在 case 中，而是以相对路径引用 `analysis/exports/gitlab_export/review_<id>_diff.json`。
- `ground_truth`：该 diff 中「真实存在的问题」清单，每条含：位置（文件 + 函数/行号）、现象描述、严重度分级、判定结论（真 TP / 漏 FN）。
- 判定规则：如何把「评测模型新产出的 review 问题」与 ground_truth 一一对应，判定 TP/FP/FN。

## 2. TP / FP / FN 判定规则

针对一次待评测的 review，其产出的每一条问题意见，与该用例的 ground_truth 对照：

- **TP（真阳性 / 命中）**：问题意见指出的缺陷在 diff 中真实存在，且与某条 ground_truth 对应。
  判定依据：**同文件 + 同函数/行号近似 + 现象一致**。
- **FP（假阳性 / 误报）**：问题意见指出的缺陷在 diff 中不存在，或基于错误前提/外部文档推测，
  与任何 ground_truth 都不对应。
- **FN（漏报）**：某条 ground_truth 中已确认为真实的缺陷，但该 review 没有检出。

**指标计算：**
- **精确率（Precision）= TP / (TP + FP)** —— 检出的意见中真实命中的比例。
- **检出率（Recall）= TP / (TP + FN)** —— 真实缺陷中被检出的比例。

> 注意：ground_truth 中带 `FN` 标签的条目代表「应当被检出但未检出」的缺陷，
> 它们不参与 TP/FP 计数，但会拉低检出率。精确率只由 review 实际产出的意见决定。

## 3. 问题条目分级（severity）

ground_truth 中每条问题按严重度分级，评测时可用于加权或过滤：

| 级别 | 含义 | 示例 |
|------|------|------|
| `high-value` | 高风险/核心缺陷：安全、并发竞态、数据一致性、核心功能缺失 | 路径穿越、resultId 丢失、增删改查全占位 |
| `medium` | 中等问题：接口契约、资源控制、健壮性、潜在风险 | N+1 查询、异步异常吞噬、防重复提交不严 |
| `trivial` | 琐碎/轻微：命名、空行、注释错别字、日志拼接 | 多余空行、childs→children、注释错别字 |

评测建议：核心指标按全部等级计算；也可单独统计 `high-value` 的精确率/检出率，
以评估「对核心风险的把握能力」。

## 4. 样本来源分层

本评估集样本分两层：

- **真实 diff 用例（`mr-*`，5 条）**：来自 GitLab API 导出的真实 commit diff
  （`review_{32,33,34,36,42}_diff.json`）。ground_truth 依据 `analysis/reports/mr_hitrate_verification.md`
  的逐条验证结论（TP 项）与补充漏报（FN 项）构建。用于**精确率/检出率**的量化复测。
- **历史标注用例（`hist-*`，12 条）**：来自 `analysis/exports/sample_labels.json` 的人工标注
  （quality_grade A/B/C/D、结构完整率、误报/漏报计数等）。用于**报告质量评级**的复测与回归。

## 5. 样本新增流程

1. 选择一次真实的 MR/commit（优先有明确业务风险、规模适中的 diff）。
2. 导出 GitLab diff 到 `analysis/exports/gitlab_export/review_<id>_diff.json`。
3. 人工审查 diff，列出真实存在的问题（位置 + 现象 + 严重度），作为 ground_truth。
4. 在 `cases/` 下新增 `mr-<id>.json`，引用 diff 文件路径。
5. 运行 `python3 analysis/eval/score.py --dry-run` 校验格式。

## 6. 目录约定

```
analysis/eval/
├── eval_schema.md      # 本文档
├── README.md           # 使用说明（复测流程）
├── score.py            # 评分脚本（标准库，无第三方依赖）
└── cases/
    ├── mr-32.json      # 真实 diff 用例（5 条）
    ├── mr-33.json
    ├── mr-34.json
    ├── mr-36.json
    ├── mr-42.json
    └── hist-*.json     # 历史标注用例（12 条）
```
