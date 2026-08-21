# AI 代码审查仪表盘

面向 GitLab 的 AI 代码审查与工作日报工具。仪表盘把审查记录、Token 消耗和日报数据汇总展示。

## 审查（Review）

**审查记录**：
一次 AI 代码审查产生的记录，包含项目、作者、分支、时间、提交信息、得分、代码变更行数、Token 消耗。
_Avoid_: 提交记录、review log

**MR 审查**：
针对合并请求（Merge Request）的审查记录。
_Avoid_: MR 数据、合并请求审查

**Push 审查**：
针对代码推送的审查记录。
_Avoid_: Push 数据、推送审查

**审查统计**：
仪表盘中统计审查记录的分区，包含 MR 审查与 Push 审查两个子页。不用"提交统计"称呼本概念。
_Avoid_: 提交统计

## Token（Token）

**Token 统计**：
仪表盘独立页面，聚合展示 MR 与 Push 审查的 Token 消耗，并列出日报 Token。
_Avoid_: Token 消耗、tokens 统计

**审查 Token**：
审查记录附带的三类 Token 用量（Prompt / Completion / 总计），可按项目、作者、时间聚合。
_Avoid_: 审查 token 消耗

**日报**：
按周期生成的 AI 工作日报记录，仅含生成时间与三类 Token 用量，无项目、作者维度。
_Avoid_: 日报记录、daily report
