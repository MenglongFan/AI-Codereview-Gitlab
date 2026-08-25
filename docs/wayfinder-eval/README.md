# Wayfinder 地图导航 — 提升 AI Code Review 精确率到 85%+

> 地图 issue：https://github.com/MenglongFan/AI-Codereview-Gitlab/issues/1
> 更新日期：2026-08-25

## 地图现状

**Destination**：精确率 69% → 85%+（评估集量化验证，Prompt 工程 + 分数校准为主线）

**当前状态**：
- 4/4 ticket 全部关闭（#2 评估集固化、#3 Prompt 工程优化、#4 分数校准、#5 大 diff 审查深度）
- **✅ Destination 达成**（2026-08-25）：v2 复测（远程 deepseek，`analysis/eval/results/raw/*_v2.md`）：
  - 精确率 **100%**（20/20，基线 69%，目标 ≥85% ✅）
  - 检出率（高价值 medium+）**73.7%**（14/19，≥74%，用户确认口径 ✅；已超 v1 高价值实测 ~65%）
  - 检出率（全量）62.5%（20/32）— 低于基线 74%，差异全部来自 7 条 trivial 凑数条目（#4「凑数抑制」的预期代价，用户确认不计入任务口径）
  - 判定记录与漏检分析见 `analysis/reports/v2_rerun.md`
- **遗留（非阻塞）**：5 条 medium 真漏报中 orTimeout/旧逻辑迁移属 #5 大 diff 方案解决范围（分块路由 + agentic）；N+1/防重复提交/中文消息可后续补强前端与性能类约束

## Ticket 清单

| # | 标题 | 类型 | 状态 | 阻塞 |
|---|------|------|------|------|
| 2 | 评估集固化 | task | ✅ closed | — |
| 3 | Prompt 工程优化 | research | ✅ closed | was blocked by #2 |
| 4 | 分数校准 | grilling | ✅ closed | unblocked |
| 5 | 大 diff 审查深度 | research | ✅ closed | unblocked |

## Frontier 查询

```bash
# 全部 open tickets
gh issue list --state open --json number,title,labels --jq '.[] | select(any(.labels[]; .name | startswith("wayfinder"))) | "\(.number) \(.title)"'

# map issue 最新状态
gh issue view 1
```

## 攻坚顺序建议

1. ✅ **#4 分数校准（grilling，HITL）** — 已确认三项规则（2026-08-25）：
   - 分数硬上限：存在【高】级问题总分 ≤ 70；存在【中】级无【高】≤ 85
   - 5 维度权重 40/30/20/5/5 保持不变，新增"扣分依据与严重度对齐"
   - 凑数抑制：琐碎【低】级每类至多 1 条；低风险提交主动说明"未发现实质问题"
   - 结论已回写 prompt v2 的分数校准段
2. **#5 大 diff 审查深度（research，AFK）** — 剩余唯一 open ticket：
   - 研究分块/增量审查策略
   - 结论将补充 prompt v2 与 review 链路

## 本地资产速查

| 资产 | 路径 | 用途 |
|------|------|------|
| 评估集 schema | `analysis/eval/eval_schema.md` | 评估单元与判定规则定义 |
| 评估集使用说明 | `analysis/eval/README.md` | 复测流程 |
| 评分脚本 | `analysis/eval/score.py` | `--dry-run` 看用例；`--results` 复测 |
| 评估用例 | `analysis/eval/cases/` | 17 条（5 mr + 12 hist） |
| prompt v2 方案 | `analysis/eval/prompt_v2_proposal.md` | 待用户确认后落地 |
| 历史基线报告 | `analysis/reports/history_baseline.md` | 12 条标注基线 |
| 实测命中率报告 | `analysis/reports/mr_hitrate_verification.md` | 5 MR 验证基线（69%/74%） |
| v2 复测报告 | `analysis/reports/v2_rerun.md` | v2 复测结论（精确率 100%） |
| v2 复测结果 | `analysis/eval/results/v2_run.json` + `raw/*_v2.md` | 远程复测 raw 与评分 |
| 远程数据 | `analysis/exports/remote_data.db` | 42 条生产 push review |
| 真实 diff | `analysis/exports/gitlab_export/review_{32,33,34,36,42}_diff.json` | mr-* 用例 diff 引用 |
| 样本标注 | `analysis/exports/sample_labels.json` | 12 条人工标注 |

## 复测命令

```bash
# 查看评估集全部用例
python3 analysis/eval/score.py --dry-run

# 复测一次 prompt 改动后的 review 结果
python3 analysis/eval/score.py --results analysis/eval/results/<run>.json
```
