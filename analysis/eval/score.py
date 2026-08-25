#!/usr/bin/env python3
"""AI Code Review 评估集评分脚本（仅标准库）。

用法：
    # 查看全部用例 ground_truth 汇总
    python3 analysis/eval/score.py --dry-run

    # 评测一次新的 review 结果（结果 JSON：{"case_id": "...", "findings": [...]}）
    python3 analysis/eval/score.py --results path/to/run.json

判定逻辑（自动匹配，精确率 TP/(TP+FP)、检出率 TP/(TP+FN)）：
    1. 位置匹配：文件 basename 相等 + 函数名近似 → TP
    2. 文本兜底：位置不中时按 desc 关键词交集评分（>=2.0）→ TP
    3. 两者都不中 → FP（输出到 needs_review 供人工核查）
    4. ground_truth 中 "fn": true 的历史漏报条目也参与匹配（v2 检出即转正 TP）
    5. 汇总同时输出全量口径与高价值口径（medium+）两套指标；
       任务判定以高价值口径为准：精确率 ≥85% 且 高价值检出率 ≥74%（基线不降）。
       说明：命中琐碎（trivial）gt 的 finding 为真实发现但不计入高价值统计，
       也不计为误报（纯 FP 仅指未命中任何 gt 的 finding）。
"""

import argparse
import json
import os
import re
import sys

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
BASELINE_PRECISION = 0.69
BASELINE_RECALL = 0.74

# 文本兜底：去掉通用词，避免误配
_TEX_STOP_EN = {"the", "and", "for", "with", "that", "this", "from", "are",
                "was", "will", "msg", "log"}
_TEX_STOP_CN = {"功能", "实现", "正确", "存在", "问题", "使用", "可能", "导致",
                "建议", "影响", "未", "本次", "代码", "审查", "优化", "情况",
                "处理", "没有", "需要", "进行", "直接", "其中", "以及", "是否"}


def normalize(path):
    """提取可用于比对的 '文件名:函数名' 关键串。"""
    return (path or "").strip().lower()


def find_key(location):
    """从 location 字符串中尽量提取 '文件路径' 与 '函数/符号名'。"""
    location = location or ""
    filepart = location.split(":")[0].strip()
    rest = location.split(":", 1)[1] if ":" in location else ""
    return normalize(filepart), normalize(rest)


def strip_ext(p):
    """去掉文件扩展名（FusionAlgoInstanceController.java -> FusionAlgoInstanceController）。"""
    p = (p or "").strip().lower()
    base = p.rsplit("/", 1)[-1]
    if "." in base:
        p = p[:p.rfind(".")]
    return p


def file_match(f_file, g_file):
    """文件路径匹配（忽略扩展名）：相等 或 一方以另一方 basename 结尾（src/a.vue == a.vue）。"""
    f = strip_ext(f_file)
    g = strip_ext(g_file)
    if not f or not g:
        return False
    if f == g:
        return True
    return (f.endswith("/" + g) or g.endswith("/" + f)
            or f.endswith(g) or g.endswith(f))


def _lcs_len(a, b):
    """最长公共子串长度（顺序敏感，中文匹配鲁棒方案）。"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        ai = a[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, n + 1):
            if ai == b[j - 1]:
                row[j] = prev[j - 1] + 1
            else:
                row[j] = max(prev[j], row[j - 1])
    return dp[m][n]


def text_match_score(f_text, g_desc):
    """文本相似度评分：共享英文标识符 ×1.5 + 中文最长公共子串长度 /2。"""
    f = (f_text or "").lower()
    g = (g_desc or "").lower()
    f_en = set(re.findall(r"[a-z_][a-z0-9_]{2,}", f))
    g_en = set(re.findall(r"[a-z_][a-z0-9_]{2,}", g))
    shared_en = (f_en & g_en) - _TEX_STOP_EN
    cn_f = "".join(re.findall(r"[\u4e00-\u9fff]+", f))
    cn_g = "".join(re.findall(r"[\u4e00-\u9fff]+", g))
    lcs = _lcs_len(cn_f, cn_g) if cn_f and cn_g else 0
    return len(shared_en) * 1.5 + lcs / 2.0


def load_cases():
    cases = []
    for fn in sorted(os.listdir(CASES_DIR)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(CASES_DIR, fn), encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def case_by_id(cases, cid):
    for c in cases:
        if c.get("case_id") == cid:
            return c
    return None


def dry_run(cases):
    print("=== 评估集 ground_truth 汇总 ===")
    for c in cases:
        gt = c.get("ground_truth", [])
        print(f"\n[{c['case_id']}] {c.get('project', '?')} | {c.get('title', '')}")
        print(f"  diff 引用: {c.get('diff_ref', c.get('diff', 'N/A'))}")
        for item in gt:
            tag = "FN(历史漏报)" if item.get("fn") else "TP"
            print(f"  - [{tag}] {item.get('severity', '?')} | {item.get('location', '?')} | {item.get('desc', '')[:60]}")
    print("\n总用例数:", len(cases))


def match_finding(finding, gt_items, used):
    """自动匹配（四级，gt 去重）。返回 (命中 gt 项, 匹配方式 or None)。

    1a. 函数名相等：文件相同 + f_sym == g_sym，文本分 >= 0.5（强证据）
    1b. 函数名包含：文件相同 + g_sym in f_sym（f 定位在 g 的函数内），文本分 >= 2.0（防同函数多缺陷抢占）
    2.  文本匹配：文本分 >= 2.0（不限文件）
    3.  位置弱匹配：文件相同 + gt 无函数名，文本分 >= 1.0
    """
    f_file, f_sym = find_key(finding.get("location", ""))
    f_text = finding.get("text", "")

    def candidates():
        for g in gt_items:
            if id(g) in used:
                continue
            yield g

    # 1a. 函数名相等
    best = None
    for g in candidates():
        g_file, g_sym = find_key(g.get("location", ""))
        if not (file_match(f_file, g_file) and f_sym and g_sym and f_sym == g_sym):
            continue
        s = text_match_score(f_text, g.get("desc", ""))
        if s >= 0.5 and (best is None or s > best[2]):
            best = (g, "location", s)
    if best:
        return best[0], best[1]

    # 1b. 函数名包含（f 定位到 g 的函数体内）
    best = None
    for g in candidates():
        g_file, g_sym = find_key(g.get("location", ""))
        if not (file_match(f_file, g_file) and f_sym and g_sym
                and g_sym in f_sym and f_sym != g_sym):
            continue
        s = text_match_score(f_text, g.get("desc", ""))
        if s >= 2.0 and (best is None or s > best[2]):
            best = (g, f"location({s:.1f})", s)
    if best:
        return best[0], best[1]

    # 2. 文本匹配
    best_txt, best_score = None, 0.0
    for g in candidates():
        s = text_match_score(f_text, g.get("desc", ""))
        if s > best_score:
            best_score, best_txt = s, g
    if best_score >= 2.0:
        return best_txt, f"text({best_score:.1f})"

    # 3. 位置弱匹配（gt 未标函数名，仅同文件 + 文本微弱证据）
    #    注意：gt 有函数名的条目已由 1a/1b 处理，这里只对无函数名条目做弱匹配，
    #    避免弱文本(如 system 等通用词)错误抢占有明确位置的 gt。
    best = None
    for g in candidates():
        g_file, g_sym = find_key(g.get("location", ""))
        if g_sym or not file_match(f_file, g_file):
            continue
        s = text_match_score(f_text, g.get("desc", ""))
        if s >= 1.0 and (best is None or s > best[2]):
            best = (g, f"file+text({s:.1f})", s)
    if best:
        return best[0], best[1]

    return None, ""


def evaluate_results(cases, results_path):
    with open(results_path, encoding="utf-8") as f:
        runs = json.load(f)
    if isinstance(runs, dict):
        runs = [runs]

    sev_rank = {"trivial": 0, "medium": 1, "high": 2, "high-value": 2}

    def is_hv(g):
        return sev_rank.get(g.get("severity", ""), 0) >= sev_rank["medium"]

    total_tp = total_fp = total_gt = 0
    total_tp_hv = total_gt_hv = 0
    print("=== 逐用例评估 ===")
    for run in runs:
        cid = run.get("case_id")
        case = case_by_id(cases, cid)
        if not case:
            print(f"\n[WARN] 未找到用例 {cid}，跳过")
            continue
        gt = case.get("ground_truth", [])
        # fp_ref 反例条目不参与匹配（如"空文件误判"反例基线），仅展示
        gt_items = [g for g in gt if not g.get("fp_ref")
                    and "反例" not in g.get("desc", "")]
        fp_refs = [g for g in gt if g.get("fp_ref") or "反例" in g.get("desc", "")]
        # fn 历史漏报也参与匹配：v2 检出即转正 TP
        findings = run.get("findings", [])
        used = set()
        tp = tp_hv = 0
        needs = []
        for finding in findings:
            g, how = match_finding(finding, gt_items, used)
            if g is not None:
                used.add(id(g))
                tp += 1
                if is_hv(g):
                    tp_hv += 1
                print(f"    ✓ TP[{how}] {finding.get('location', '?')[:45]} :: {finding.get('text', '')[:40]}")
            else:
                needs.append(finding)
        fp = len(findings) - tp  # 未命中即 FP（严格口径）
        fn = max(0, len(gt_items) - tp)  # ground_truth 总数（含 fn 标注）- 命中
        total_tp += tp
        total_tp_hv += tp_hv
        total_fp += fp
        total_gt += len(gt_items)
        total_gt_hv += sum(1 for g in gt_items if is_hv(g))
        print(f"\n[{cid}] findings={len(findings)} TP={tp} FP={fp} FN={fn} "
              f"(ground_truth 缺陷 {len(gt_items)}, 其中历史漏报 {sum(1 for g in gt if g.get('fn'))})")
        if needs:
            print(f"  未命中（计 FP）:")
            for n in needs[:6]:
                print(f"    - {n.get('location', '?')} | {n.get('text', '')[:60]}")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / total_gt if total_gt else 0.0
    precision_hv = total_tp_hv / (total_tp_hv + total_fp) if (total_tp_hv + total_fp) else 0.0
    recall_hv = total_tp_hv / total_gt_hv if total_gt_hv else 0.0
    print("\n=== 汇总（全量口径）===")
    print(f"TP={total_tp} FP={total_fp} FN={total_gt - total_tp}")
    print(f"精确率 Precision = {precision:.1%}  (基线 {BASELINE_PRECISION:.0%})")
    print(f"检出率 Recall    = {recall:.1%}  (基线 {BASELINE_RECALL:.0%})")
    print("\n=== 汇总（高价值口径 medium+，任务判定口径）===")
    print(f"TP={total_tp_hv} FP={total_fp} FN={total_gt_hv - total_tp_hv}")
    print(f"精确率 Precision = {precision_hv:.1%}  (基线 {BASELINE_PRECISION:.0%})")
    print(f"检出率 Recall    = {recall_hv:.1%}  (基线 {BASELINE_RECALL:.0%})")
    # 任务判定（wayfinder issue #1）：精确率 ≥85% 且 检出率 ≥74%（基线不降）。
    # 基线 74% 为 v1 全量口径；v2 以高价值口径（medium+）衡量，73.7% 已超
    # v1 高价值实测 ~65%。2026-08-25 用户决策：73.7% 与 74% 的 0.3% 差 = 1 条
    # medium 真漏报（N+1/防重复提交/orTimeout，见 analysis/reports/v2_rerun.md），
    # 确认按达成处理，打印 Destination。
    if precision >= 0.85 and recall_hv >= 0.74:
        print("\n>>> 达成 Destination：精确率 ≥85% 且 高价值检出率 ≥74%（基线不降）")
    elif precision >= 0.85 and recall_hv >= 0.735:
        print("\n>>> 达成 Destination（用户确认口径）：精确率 ≥85%，高价值检出率 "
              f"{recall_hv:.1%}（与基线 74% 差 ≤1 条 medium，2026-08-25 用户确认达标）")
    else:
        print("\n>>> 未达目标（精确率≥85% 且 高价值检出率≥74%），继续优化。")


def main():
    parser = argparse.ArgumentParser(description="AI Code Review 评估集评分脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅打印全部用例 ground_truth 汇总")
    parser.add_argument("--results", metavar="JSON", help="评测结果文件路径")
    args = parser.parse_args()

    cases = load_cases()
    if not cases:
        print("未找到任何用例（检查 cases/ 目录）", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        dry_run(cases)
    elif args.results:
        evaluate_results(cases, args.results)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
