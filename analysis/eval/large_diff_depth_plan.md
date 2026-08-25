# 大 diff 审查深度方案（Issue #5）

> 状态：research 完成（2026-08-25）｜产出：本文档
> 目标：让大 diff（>100 行增删）也能保持审查深度，消除 mr-36 / mr-42 式漏报
> 关联：`analysis/eval/prompt_v2_proposal.md`（prompt 层）｜本方案是**链路层**兜底

## 1. 根因确认（阅读代码后）

`biz/queue/worker.py:_review_with_strategy` → `str(changes)`（diff 数组直接转字符串）→
`biz/utils/code_reviewer.py:80`：

```python
tokens_count = count_tokens(changes_text)
if tokens_count > review_max_tokens:            # REVIEW_MAX_TOKENS=10000
    changes_text = truncate_text_by_tokens(changes_text, review_max_tokens)  # 取前 10000 token
```

**核心缺陷：超长时无条件截断，只保留 diff 开头。**

对照两个漏报案例验证：
- **mr-36**（+309/-40，12KB）：`TagCategory.vue` diff 顺序「模板→script→样式」。占位的 `handleAdd/View/Edit/Delete`（`ElMessage.info('待实现')`）在 script 中后段，被前 10000 token 硬切截掉 → LLM 只看到"空文件+临时路由" → high-value FN。
- **mr-42**（+458/-367，68KB）：远超 10000 token，前段全是 `FusionAlgoContextLoader` 删除/新增块；被删旧逻辑的迁移正确性在 diff_only 下**无旧代码上下文** → medium FN 系统性盲区。

项目内无任何现成分块/增量处理（`biz/` 仅 `token_util.py` 的 count/truncate）。

## 2. 决策点结论

### 2.1 分块策略：文件级为主、hunk 为辅、token 预算兜底

- **主单位 = 文件**：每个文件的完整 diff 作为一个原子 chunk（保留文件内函数/变量逻辑）。
- **超长文件降级 = hunk**：单文件 diff 超 `CHUNK_MAX_TOKENS`（建议 6000）时，文件内按 hunk 切，重叠 `50` 行（避免函数边界被切开）。
- **成本上限**：`CHUNK_MAX_CHUNKS`（建议 8），超限退化为「优先级排序 + 只审高风险 chunk」或切 agentic。
- **跨文件关联兜底（关键）**：
  - 「必查点」共享注入：占位命中清单 + deleted 行清单注入**每个 chunk** 的 prompt 顶部（全局必查项）。
  - 汇总层契约检查：汇总 prompt 注入「新增/删除文件清单」，要求 LLM 做一次跨文件接口契约/调用方核验。

```python
def chunk_diff(changes):
    chunks = []
    for f in changes:                          # 文件级原子性
        if count_tokens(f["diff"]) <= CHUNK_MAX_TOKENS:
            chunks.append(f)
        else:                                  # 超长文件按 hunk 切
            for hunk in split_into_hunks(f["diff"], overlap_lines=50):
                chunks.append(hunk)
        if len(chunks) > CHUNK_MAX_CHUNKS:     # 成本上限
            return chunks, {"truncated": True}
    return chunks, {"truncated": False}
```

### 2.2 占位/空实现检测：前置确定性规则（不依赖 LLM，强烈建议）

放在 `filter_changes` 之后、`_review_with_strategy` 之前，扫描 diff 的 `+` 行（剔除 `+++` 文件头）。

| 类别 | 正则/模式（针对 `+` 行） | 适用 | 注入 |
|------|------|------|------|
| 中文占位注释 | `待实现\|待完成\|占位\|后续实现\|暂未实现` | 全部 | 高 |
| 调试残留 | `console\.(log\|debug\|info)\|System\.out\.println\|print_r\|var_dump` | 前后端 | 高 |
| UI 占位提示 | `ElMessage\.info\s*\(\s*['"](待\|新增\|查看\|编辑\|删除)[^'"]*待实现` | Vue | 高 |
| 硬编码占位返回 | `return\s+(null\|0\|""\|None)\s*//?\s*(TODO\|占位\|待)` | 全部 | 高 |
| 显式 TODO/FIXME | `TODO\|FIXME\|XXX\|HACK` | 全部 | 高 |
| 未实现方法/异常 | `NotSupported\|NotImplementedError\|throw new NotImplemented` | 后端 | 高 |
| 空函数体 | `func\w*\([^)]*\)\s*\{\s*\}\s*\n` | 全部 | 高 |
| 空 catch 吞噬 | `catch\s*\([^)]*\)\s*\{\s*\}` | 后端 | 中 |

命中后生成「必查点」注入 prompt 顶部，**要求 LLM 判断是否属本次 MR 应交付功能**（标记 `suggest_high`，非强制 `high`，避免误伤合理延期 TODO）。

> 这是 mr-36 漏报的**确定性**解法：纯文本正则，零 LLM 成本、零漏检（只要占位文本符合模式）。

### 2.3 重构/删除迁移验证：deleted 行签名注入

**核心认知**：GitLab `merge_requests/{iid}/changes` 本身就是 base→head 比较，diff 已含全部删除行——不需要额外 merge-base 调用。

- **方案 A（推荐）**：提取 `-` 行（非 `---`、非注释）的函数/方法签名（`(?:public|private|protected|func|def|const)\s+\w+`），注入 prompt 顶部作为**迁移核验必查项**：
  ```
  【本次重构被删除的逻辑（旧实现）】：
  - FusionAlgoContextLoader.load(): 原逻辑删除了 xxx
  请核验：该函数/字段在被删后，其调用方是否已迁移正确？
  ```
- **方案 B（增强，配合 agentic）**：用 `repository/commits/{sha}/diff` 拉取被删文件旧版本（`/raw?ref=<merge_base>`），仅对 deleted 行对应文件注入旧函数体（单文件 2-5k token，可控）。
- **退化路径**：deleted 行过多时只做「调用方检查提示」（方案 A），命中后再由 agentic 深挖。

### 2.4 与 agentic 的关系：大 diff 首选 agentic，分块是其兜底

| 维度 | diff_only + 分块 | agentic（可读全仓库） |
|------|------|------|
| 深度 | 仅 diff 上下文；跨文件靠注入兜底 | 可 `read_file`/`rg` 探查任意文件，迁移验证天然可做 |
| 成本 | N 次调用，token ≈ diff 总量 | 迭代上下文膨胀快（cap 80k）；有软降级兜底 |
| 稳定性 | 高（纯调用） | 中（工具失败/空转会 degrade，已有软降级） |
| 大 diff | 需额外注入清单 | 天然擅长（prompt_v2 已内置 rg 搜占位） |

## 3. 综合推荐方案：三层自动路由

| 条件（增删行数） | 策略 | 理由 |
|------|------|------|
| ≤ 100 行 | 现有 diff_only（单次） | 无截断问题，最省成本 |
| 100–300 行 | diff_only + 分块 + 确定性注入 | 中 diff 保深度，成本可控 |
| > 300 行且仓库可解析/可同步 | **agentic** | 深度需求最高，agentic 天然胜任；失败退化到分块 |
| > 300 行但仓库不可用 | diff_only + 分块 + deleted 注入 | agentic 兜底 |

阈值建议：`DIFF_AGENTIC_THRESHOLD=300`、`CHUNK_THRESHOLD=100`。

## 4. 分阶段实现步骤

- **阶段 1（零 LLM 成本，必做）**：确定性占位/删除检测层（2.2 + 2.3 方案 A）。
  在 `_review_with_strategy` 前扫描 `+`/`-` 行生成「必查点」清单，注入 prompt 顶部。
  **直接消除 mr-36 的 high-value FN**（占位必然命中）。
- **阶段 2（中成本）**：分块引擎。
  新增 `biz/utils/diff_chunker.py`（文件级 + hunk 切分 + token 预算 + 重叠）。
  改造 `CodeReviewer.review_and_strip_code`：超阈值分块多次调用 + 汇总去重。
- **阶段 3（更高成本）**：阈值自动切 agentic。
  `_review_with_strategy` 增加路由，复用现有 `AgenticReviewer`；失败自动落阶段 2。

## 5. 预计收益（对照漏报点）

| 漏报点 | 现状 | 方案生效点 | 预期 |
|------|------|------|------|
| mr-36 增删改查占位（high-value FN） | 截断切掉占位函数 | 阶段 1 正则必然命中 + 注入 | **确定性消除** |
| mr-42 被删逻辑迁移正确性（medium FN） | 无旧上下文 | 阶段 1 deleted 注入 + 阶段 3 agentic | **显著改善** |
| mr-36 空文件误判（FP） | 截断只看到开头 | 阶段 2 分块保留完整文件 | **消除** |
| mr-33 线程池/静默降级（FN） | 截断 | 阶段 2/3 | 改善 |

## 6. 权衡与风险

1. **深度 vs 成本**：阶段 1 是纯增益（零 LLM 成本修复最大 FN），**必做**。阶段 2/3 必须设 `CHUNK_MAX_CHUNKS` 上限 + agentic 软降级，防止超大型 MR 成本失控。
2. **不要用纯 token 硬切**（现状缺陷的根源）；分块必须以文件/hunk 为逻辑单元 + 全局必查点注入保跨文件关联。
3. **agentic 是「大 diff 首选」而非「分块对立面」**：两者层级关系——agentic 深度最高，分块+注入是其稳定兜底。
4. TODO/FIXME 注入用 `suggest_high` 而非强制 `high`，避免误伤合理延期项。
