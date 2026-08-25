# prompt v2 修订方案：提升精确率 69% → 85%+ 且不降检出率

> 目标文件：`conf/prompt_templates.yml` 的 `code_review_prompt`（45-88 行）与 `agentic_code_review_prompt`（1-43 行）
> 依据基线：`analysis/reports/mr_hitrate_verification.md`（精确率 69%、检出率 74%）、`analysis/reports/history_baseline.md`（校准 6/12 loose、结构完整率 100%）
> 复测底座：`analysis/eval/score.py` + `analysis/eval/cases/{mr-*,hist-*}.json`

---

## 一、问题诊断

基于 5 条真实 diff 验证（29 条问题，20 TP / 9 FP，7 FN）与 12 条历史标注，当前 `code_review_prompt` 存在 5 类导致误报/漏报的机制：

### 1. 无证据约束 → 推测性误报（最大 FP 源）
当前 prompt 只要求"列出问题并给建议"，**未要求每条问题引用 diff 中具体文件+函数/行号+代码片段，也未明确禁止基于提交信息/外部文档/猜测**。
- 证据：review 36 的 6 条 FP 中 **4 条来自文档臆测**（"删除接口用 GET""下载接口无 token""接口路径不一致""vite.config.js 注释错误"），均非 diff 代码证据。
- 证据：review 33 的 FP"接口实现类未同步（diff 为空）"——**实际 diff 有 +280 行完整实现**，前提错误。
- 证据：review 34 的 FP"潜在 nil 指针目标风险"——diff 中字段已初始化为 `&model.ModelAsset{}`，且与 review 12 对同一类改动的判断相反，属推测性担忧（0% 命中）。

### 2. 无占位实现检测 → 核心功能占位漏报（最大 FN 源）
当前 prompt 未要求检查新增文件中的"待实现/TODO"占位代码，导致核心功能缺失被漏报，且占位代码被误当正常代码。
- 证据：review 36 **漏报增删改查全部占位未实现**（`handleAdd/View/Edit/Delete` 均为 `ElMessage.info('待实现')`），ground_truth 判定为 **high-value 核心缺陷**（mr-36.json 中 `fn: true`）。

### 3. 无严重度分级 → 凑数项与真实缺陷同权，分数失真
当前 prompt 只有 5 维度分数，**无每条问题的严重度标注，也无分数与严重度/问题数的挂钩规则**。
- 证据：history_baseline 分数校准 **6/12 loose、1/12 off**；review 36（63 分）实际命中率仅 14%，review 34（88 分）命中率 0%——**分数与质量倒挂**（history_baseline 系统性模式 1）。

### 4. 无凑数抑制 → 对低风险提交强挑细节
当前 prompt 未提示"低风险/纯样式提交可主动说明无实质问题"。
- 证据：history_baseline 误报约 11% 集中在"纯样式/前端提交被强挑毛病"（review 20 的颜色注入、review 33/27 的多余空行、命名、日志拼接等琐碎凑数）。

### 5. 自由格式问题列表 → 定位信息缺失
当前 prompt 的问题列表无统一结构约束，部分问题**缺文件/行号定位**，与 `score.py` 的 `match_finding`（依赖 `文件:符号`）自动匹配不兼容，导致落 needs_review 或 FP。
- 证据：`eval_schema.md` 判定口径要求"同文件 + 同函数/行号近似"，而 history_baseline 中 id=5"多数问题未给出具体文件行号，泛称迁移脚本"。

---

## 二、修订设计

**原则**：保留 `code_review_prompt` 现有键名结构（`system_prompt`/`user_prompt`）、`{{ style }}` 变量、5 维度评分框架（40/30/20/5/5）与输出正则 `总分:XX分`；新增证据约束、占位检测、严重度分级、凑数抑制、分数校准。**不破坏结构强项（问题+评分明细+总分三要素 100%）**。

### 2.1 完整修订版 YAML（可直接粘贴替换）

```yaml
code_review_prompt:
  system_prompt: |-
    你是一位资深的软件开发工程师，专注于代码的规范性、功能性、安全性和稳定性。本次任务是对员工的代码进行审查，具体要求如下：

    ### 代码审查目标：
    1. 功能实现的正确性与健壮性（40分）： 确保代码逻辑正确，能够处理各种边界情况和异常输入。
    2. 安全性与潜在风险（30分）：检查代码是否存在安全漏洞（如SQL注入、XSS攻击等），并评估其潜在风险。
    3. 是否符合最佳实践（20分）：评估代码是否遵循行业最佳实践，包括代码结构、命名规范、注释清晰度等。
    4. 性能与资源利用效率（5分）：分析代码的性能表现，评估是否存在资源浪费或性能瓶颈。
    5. Commits信息的清晰性与准确性（5分）：检查提交信息是否清晰、准确，是否便于后续维护和协作。

    ### 证据约束（强制）：
    - 每条问题必须定位到 diff 中的具体证据：文件路径 + 函数名/行号 + 关键代码片段。
    - 无法在 diff 中定位到具体代码的问题，一律不得列为问题。
    - 严禁基于提交信息(commit message)、外部文档、或猜测提出"可能性"问题；提出前请确认代码里确实存在该写法。

    ### 占位实现检测（强制）：
    - 检查新增/修改文件中是否存在未实现的占位代码，如："待实现"、"TODO"、"FIXME"、`ElMessage.info('待实现')`、空函数体、抛 NotSupported/未定义方法等。
    - 占位代码意味着核心功能缺失，必须作为【高】级问题报告，并给出具体占位位置。

    ### 严重度分级：
    每个问题必须标注严重度等级，三者必选其一：
    - 【高】：安全漏洞 / 数据一致性 / 核心功能缺失（含占位未实现）/ 会导致崩溃或数据损坏。
    - 【中】：健壮性 / 资源控制 / 边界条件 / 接口契约。
    - 【低】：命名 / 注释 / 代码风格 / 日志细节。

    ### 凑数抑制：
    - 若 diff 为纯样式/纯前端/低风险改动且未发现实质问题，请主动说明"未发现实质问题"，禁止为凑问题数强挑细节。
    - 琐碎问题（【低】级）每类至多报告 1 条，且必须附带真实代码证据。

    ### 分数校准（与严重度挂钩）：
    - 存在 1 个以上【高】级问题：总分不得超过 70 分。
    - 存在【中】级问题但无【高】级：总分不得超过 85 分。
    - 5 个维度分数必须与上述严重度约束一致，且与问题数量/严重度成正比。

    ### 输出格式:
    请以Markdown格式输出代码审查报告，并包含以下内容：
    1. 问题描述和优化建议(如果有)：每条问题以"-【高/中/低】[文件:函数/行号] 问题描述 - 影响 - 建议"的格式列出。
    2. 评分明细：为每个评分标准提供具体分数，并说明扣分依据（与严重度对齐）。
    3. 总分：格式为"总分:XX分"（例如：总分:80分），确保可通过正则表达式 r"总分[:：]\s*(\d+)分?"） 解析出总分。

    ### 特别说明：
    整个评论要保持{{ style }}风格
    {% if style == 'professional' %}
    评论时请使用标准的工程术语，保持专业严谨。
    {% elif style == 'sarcastic' %}
    评论时请大胆使用讽刺性语言，但要确保技术指正准确。
    {% elif style == 'gentle' %}
    评论时请多用"建议"、"可以考虑"等温和措辞。
    {% elif style == 'humorous' %}
    评论时请：
    1. 在技术点评中加入适当幽默元素
    2. 合理使用相关Emoji（但不要过度）：
       - 🐛 表示bug
       - 💥 表示严重问题
       - 🎯 表示改进建议
       - 🔍 表示需要仔细检查
    {% endif %}

  user_prompt: |-
    以下是某位员工向 GitLab 代码库提交的代码，请以{{ style }}风格审查以下代码。

    代码变更内容：
    {diffs_text}

    提交历史(commits)：
    {commits_text}
```

### 2.2 设计要点与证据映射

| 修订点 | 位置 | 直击的基线缺陷 | 对应证据 |
|--------|------|---------------|---------|
| 证据约束 | "### 证据约束" | FP 主因：文档/commit/猜测臆测 | review 36 的 4 条文档 FP、review 33"实现未同步"、review 34 nil 指针 |
| 占位检测 | "### 占位实现检测" | FN 主因：核心功能占位漏报 | review 36 增删改查全占位（唯一 high-value FN） |
| 严重度分级 | "### 严重度分级" | 凑数项与真实缺陷同权、分数失真 | eval_schema 的 high/medium/trivial 对齐；history_baseline 6/12 loose |
| 分数校准 | "### 分数校准" | 分数与质量倒挂、校准偏松 | review 34（88 分 0% 命中）、review 36（63 分 14% 命中） |
| 凑数抑制 | "### 凑数抑制" | 对低风险提交强挑细节 | review 20 颜色注入、review 33/27 空行/命名 |
| 结构前缀 | "输出格式" 第 1 条 | 自由格式缺定位、自动匹配难 | 与 score.py `match_finding`（文件:符号）兼容 |

---

## 三、风险与回滚

### 3.1 潜在风险

| 风险 | 对强项的影响 | 缓解 |
|------|-------------|------|
| **证据约束过严**可能抑制真实但不明显（需跨文件推断）的缺陷 → 检出率下降 | 主要针对 review 42 的旧逻辑迁移正确性、review 33 的线程池/静默降级等需全局判断的场景 | 证据约束只禁止"无代码依据的推测"，不禁止基于 diff 内代码的合理推断；在占位检测中保留对核心功能缺失的强调，确保 review 36 类 FN 仍被捕获 |
| **占位检测误放大**：把"合理延期 TODO"也标为【高】→ 高-value 误报 | 增加 FP | prompt 明确占位=核心功能缺失，且要求确认占位是否属本次 MR 应交付的功能；可与严重度分级联查 |
| **严重度/校准规则执行漂移**：高/中/低判断不一致 → 分数失真 | 校准分数若被滥用反而扭曲 | 分级定义与 eval_schema 保持一致、含示例；校准规则明确数值上限 |
| **结构强项被破坏**：若误删三要素或改动 `总分:XX分` 正则 | 结构完整率 100% 回落 | 修订版完整保留输出三要素与总分正则，仅新增问题条目前缀与证据字段 |

### 3.2 用 score.py 复测验证（对比基线 69% / 74%）

1. **落地 prompt**：将修订版 YAML 写入 `conf/prompt_templates.yml`（替换 `code_review_prompt`）。
2. **对 5 条 `mr-*` diff 重跑 review**，产出结果 JSON（`location` 用 `文件:函数` 或 `文件:行号`）：
   ```json
   {"case_id": "mr-36", "findings": [
     {"location": "src/views/customer_communication/TagCategory.vue:handleDelete", "severity": "high", "text": "占位未实现"},
     {"location": "src/router/index.js", "severity": "low", "text": "临时路由清理不彻底"}
   ]}
   ```
   保存到 `analysis/eval/results/prompt-v2.json`。
3. **运行评分**：
   ```bash
   python3 analysis/eval/score.py --results analysis/eval/results/prompt-v2.json
   ```
4. **对比基线判读**：
   - 精确率升、检出率跌 → **过度保守**，需放宽证据约束中"禁止合理推断"的措辞（尤其 review 42 大重构、review 33 线程池场景）。
   - 精确率 ≥ 85% 且检出率 ≥ 74%（不下降）→ 达成目标；score.py 在两指标均 ≥ 85% 时打印 Destination。
   - 精确率仍低 → 检查是否仍产出文档/commit 臆测问题，加强"### 证据约束"措辞。
5. **hist-* 用例回归**：`hist-*` 无真实 diff ground_truth，用于报告质量评级。按 `sample_labels.json` 维度（structure_complete / specificity_issues / vague_issues / false_positive_count / missed_critical_count / actionable_ratio / score_calibration / quality_grade）对同样 commit+diff 摘要重跑新系统并人工评级，重点确认：**结构完整率仍 100%**、校准分布从 loose/off 改善为 good、false_positive_count 下降。
   - 注意：当前 `score.py` 未实现 README 提到的 `--hist` 模式，hist 回归需人工按维度核查（或后续为 score.py 补充 hist 评级能力）。

### 3.3 回滚方式（git 版本管理）

- 项目在 git 管理下。落地修订前先固化 v1 基线：
  ```bash
  git add conf/prompt_templates.yml
  git commit -m "baseline: code_review_prompt v1 (精确率 69%)"
  ```
- 落地 v2：
  ```bash
  git checkout -b feat/prompt-v2
  # 编辑 conf/prompt_templates.yml 为修订版
  git add conf/prompt_templates.yml
  git commit -m "feat: code_review_prompt v2 证据约束+占位检测+严重度分级"
  ```
- 复测不达标回滚：
  ```bash
  git checkout -- conf/prompt_templates.yml        # 或
  git revert feat/prompt-v2                         # 回到 v1
  ```
- 若需 A/B 对比，可保留 v1/v2 两版 YAML 段，用不同 `style` 或参数切换复测。

---

## 四、agentic_code_review_prompt 同步修订要点

`agentic_code_review_prompt`（1-43 行，带工具探索能力）建议同步修订以下 5 点：

1. **证据约束**：在"审查目标"前新增强制条款——"所有问题必须能在 diff 或读取到的源码中定位到具体文件+行号+代码片段；禁止基于提交信息/外部文档/猜测提出可能性问题"。
2. **占位实现检测**：利用工具探索能力主动 `rg` 搜索新增文件中 `TODO|待实现|FIXME|NotSupported|空函数体`，命中即报【高】级核心功能缺失（针对 review 36 类前端占位漏报）。
3. **严重度分级与分数校准**：为每条问题标【高/中/低】，并加"存在【高】级问题总分 ≤ 70"规则（解决校准 loose/off、分数与质量倒挂）。
4. **凑数抑制**：对纯样式/前端/低风险 diff 输出"未发现实质问题"，不凑数；琐碎问题每类至多 1 条。
5. **大重构迁移正确性**：对含大量删除/重构的 diff，提示主动检查被删旧逻辑的调用方是否迁移正确、线程池/资源控制（针对 review 42 的 FN、review 33 的 ForkJoinPool 盲区）。

---

## 附：与评估集字段的对齐说明

- 严重度分级（高/中/低）与 `eval_schema.md` 的 `high-value/medium/trivial` 一一对应，便于 `score.py` 按严重度加权统计 high-value 精确率/检出率。
- 问题条目前缀 `-【高/中/低】[文件:函数/行号]` 为 `score.py` 的 `match_finding`（按 `文件:符号` 匹配）提供标准定位串，减少 needs_review/误判。
- 分数校准规则可量化为 prompt 内硬约束，同时可作为后续 `score.py` 扩展"校准校验"（若 findings 含 high 而总分 > 70 则告警）的输入。
