# 5 条真实 MR review 命中率验证

> 方法：将 5 条历史 review 报告与 GitLab API 导出的真实 diff（JSON）逐条对照，判定每个问题为真阳性 TP / 假阳性 FP，并识别 diff 中未被报告的漏报 FN。
> 数据：`analysis/exports/gitlab_export/review_{32,33,34,36,42}_diff.json` + `analysis/exports/samples/review_{id}.md`
> 日期：2026-08-25

## 逐条分析

### review 32 (eagle_v2, `internal/data-process/subscriber/utils/util.go`, +76/-8)

**diff 摘要**：上传下载功能下移至 system-本地模块，`EnsureHostNetwork` 相关逻辑；含 `copier.Copy(hostNetwork, network)`、新增中文错误消息、`EnsureNetwork` 逐条查询。

**报告问题清单判定**（报告 4 条问题）：
1. EnsureHostNetwork SOURCE 缺陷（复制 SOURCE 未用本次 source 参数）→ **TP (high-value)**：diff 中 `copier.Copy(hostNetwork, network)` 确会覆盖 SOURCE。
2. 错误消息语言不一致（新增中文）→ **TP (medium)**：新增中文错误消息属实。
3. 注释错别字（"确保网络接记录存在"）→ **TP (trivial)**：diff 确有错别字。
4. N+1 查询（Ensure 函数逐条查询）→ **TP (medium)**：部分推测但基本属实。

**命中率**：TP=4 / FP=0 / FN=1（NETID 硬编码 "00" 限制多网络支持，minor）
**报告内命中率**：4/4 = **100%**

---

### review 33 (etl_station, RuoYi-Vue-Plus badger-fusion 压测接口, +430/-59)

**diff 摘要**：`FusionAlgoInstanceController` +18、`IFusionAlgoInstanceService` +24、`FusionAlgoInstanceServiceImpl` +300/-38（benchmarkFetchTdb 实现）、前端 `algorithm.ts` +14、`TdbBenchmarkDialog.vue` +74/-20。

**报告问题清单判定**（报告 9 条问题）：
1. "接口实现类未同步（diff 为空）" → **FP**：实际 diff 有 +280 行完整实现，前提错误。
2. Controller 入参缺校验/类型安全（`Map<String,Object>` 强转）→ **TP (high-value)**：diff 中 `(List<String>) params.get("instanceIds")` 无校验、无 DTO，DoS/异常输入风险真实。
3. 前端防重复提交不严 → **TP (medium)**。
4. mode 访问不安全 → **FP**：基于"实现未同步"的错误前提推测，ServiceImpl 明确返回 mode。
5. 接口方法重载冗余 → **TP (trivial)**。
6. Map 作为 Controller 入参 → **TP (trivial)**。
7. 前端 any/复杂模板 → **TP (trivial)**。
8. 多余空行 → **TP (trivial)**。
9. 提交信息笼统 → **TP (trivial)**。

**漏报 FN（diff 中真实存在但未提）**：
- `System.out.println` 调试残留；
- 时间解析失败静默降级（为 0 时间戳）；
- `ForkJoinPool.commonPool` 无线程池/资源控制。

**命中率**：TP=7 / FP=2 / FN=3
**报告内命中率**：7/9 = **78%**

---

### review 34 (eagle_v2, `internal/spacemap/service/spacemap_asset_sync.go`, +3/-3)

**diff 摘要**：copier.Copy 指针层级修正（5 行小变更）。

**报告问题清单判定**（报告 1 条问题 + 1 条正面）：
1. "潜在 nil 指针目标风险" → **FP**：diff 中字段先初始化为 `&model.ModelAsset{}` 等，非 nil，一级指针安全；且与 review 12 对同一类改动的判断相反，属推测性担忧。

**命中率**：TP=0 / FP=1 / FN=0
**报告内命中率**：0/1 = **0%**

---

### review 36 (five_knowledge, `src/views/customer_communication/TagCategory.vue` +308/-40, `src/router/index.js` +1/-20)

**diff 摘要**：标签分类管理页面完整实现（树形结构 + 列表 + 分页 + 增删改查占位）。

**报告问题清单判定**（报告 7 条问题）：
1. "TagCategory.vue 空文件致功能不可用" → **FP（重大误报）**：diff 显示 +308/-20 完整实现，并非空文件。
2. "删除接口用 GET" → **FP**：基于外部文档，diff 内删除为占位（`ElMessage.info('待实现')`），无此接口。
3. "下载接口无 token" → **FP**：基于文档既有风险，不在本次 diff 范围。
4. "接口路径不一致" → **FP**：基于文档推断，无代码证据。
5. "临时路由清理不彻底" → **TP (trivial)**：路由删除属实。
6. "vite.config.js 注释错误" → **FP**：不在 diff 中。
7. "Commits 类型不匹配" → **FP**：基于 commit message 而非代码 diff。

**漏报 FN**：**增删改查全部占位未实现**（handleAdd/View/Edit/Delete 均为 `ElMessage.info('待实现')`，页面按钮可操作）——核心功能缺失未被报告。

**命中率**：TP=1 / FP=6 / FN=2
**报告内命中率**：1/7 = **14%**

---

### review 42 (etl_station, FusionAlgoContextLoader 重构, +458/-367)

**diff 摘要**：`FusionAlgoContextLoader` 大规模重构（-348）、新增 `FusionNodeConfigResolver` (+185)、`TradingPriceMockSupplier` (+118)、`FusionAlgoInstanceServiceImpl` (+35/-17)、`JsTdbDataSourceStrategy` (+3/-2)；涉及 CompletableFuture 异步、线程池。

**报告问题清单判定**（报告 8 条问题）：
1. resultId 丢失（同步/异步路径）→ **TP (high-value)**：`return finalExistingId != null ? finalExistingId : 0L` 真实存在。
2. 异步异常吞噬 + 返回 0L → **TP (high-value)**。
3. 并发合并重复 → **TP (medium)**。
4. queryKeys 日志 → **TP (medium)**。
5. 通配符导入 → **TP (trivial)**。
6. 线程名判断 → **TP (trivial)**。
7. 日期截取 → **TP (trivial)**。
8. orTimeout → **TP (medium)**。

**漏报 FN**（受文件大小限制，判定有限）：未验证被删除旧逻辑的迁移正确性（报告主要盯新增逻辑）、线程池容量/资源泄漏。

**命中率**：TP=8 / FP=0 / FN=1-2
**报告内命中率**：8/8 = **100%**

---

## 汇总表

| id | 项目 | diff 规模 | 报告问题数 | TP | FP | FN | 报告内命中率 | 主要漏报 |
|----|------|----------|-----------|----|----|----|-------------|---------|
| 32 | eagle_v2 | +76/-8 | 4 | 4 | 0 | 1 | 100% | NETID 硬编码 |
| 33 | etl_station | +430/-59 | 9 | 7 | 2 | 3 | 78% | 调试残留/静默降级/线程池 |
| 34 | eagle_v2 | +3/-3 | 1 | 0 | 1 | 0 | 0% | — |
| 36 | five_knowledge | +309/-40 | 7 | 1 | 6 | 2 | 14% | 增删改查全占位未实现 |
| 42 | etl_station | +458/-367 | 8 | 8 | 0 | 1 | 100% | 旧逻辑删除迁移正确性 |
| **合计** | | | **29** | **20** | **9** | **7** | **69%** | |

**精确率（报告问题真实命中比例）**：20/29 = **69%**
**检出问题数**：TP=20 条真实问题 + FN=7 条漏报（检出率约 74%）

## 结论

### 整体命中率基线
- **报告内命中率 69%**（29 条报告中 20 条真实命中）：约 1/3 的 review 意见不可靠。
- **检出率约 74%**：diff 中真实核心风险约 3/4 被报告命中，1/4 被漏掉。
- 高质量 review（32/42）命中率 100%，低质量 review（34/36）命中率 0-14%——**质量分化严重**。

### 误报高发场景（FP=9）
1. **基于错误前提的推测**：review 33 的"接口实现类未同步"（实际有完整实现）、review 34 的 nil 指针担忧（实际已初始化）；
2. **基于外部文档/commit message 而非代码 diff**：review 36 的 6 条 FP 中 4 条来自文档臆测；
3. **将正常/占位代码误判为缺陷**。

### 漏报高发场景（FN=7）
1. **核心功能占位未实现**（review 36：增删改查全是 `待实现`）；
2. **调试残留 / 静默降级**（review 33：System.out.println、时间解析失败静默为 0）；
3. **线程池 / 资源控制**（review 33/42）；
4. **删除/重构旧逻辑的迁移正确性**（review 42 系统性盲区）。

### 与历史基线报告的一致性
与 `analysis/reports/history_baseline.md` 的结论高度一致：
- ✅ 分数校准偏松 → review 36（63 分）实际命中率仅 14%；
- ✅ 误报集中在样式/前端/推测性技术担忧 → review 36/34 验证；
- ✅ 高分段深度不足 → review 34（88 分）0% 命中、review 42（68 分）100% 命中，分数与质量倒挂再次验证；
- ✅ 大 diff 前端实现漏报 → review 36 核心功能占位未被发现。

**实测结论**：当前系统 review 的**精确率约 69%**，主要短板是「推测性误报」与「前端/占位代码的核心漏报」，与历史基线相互印证，可作为优化方向（Prompt 工程 + 证据约束 + 前端审查增强）的数据依据。
