#!/usr/bin/env python3
"""评估集复测脚本：用 prompt v2 对 mr-* 用例真实生成 review 并评分。

用法：
    # 前置：conf/.env 已配置 LLM_PROVIDER 与对应厂商 KEY（参照 conf/.env.dist）
    .venv-py311/bin/python scripts/eval-rerun.py [--output analysis/eval/results/v2_run.json]
    # 只跑单个用例：
    .venv-py311/bin/python scripts/eval-rerun.py --only mr-32

流程：
    1. 加载 conf/.env 注入环境变量
    2. 遍历 analysis/eval/cases/mr-*.json，按 diff_ref 组装 diffs_text
    3. 用 CodeReviewer（prompt v2）生成 review
    4. 解析 findings（-【高/中/低】[location] ... 格式）
    5. 写 results JSON 并调用 analysis/eval/score.py 评分
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CASES_DIR = os.path.join(ROOT, "analysis/eval/cases")
RESULTS_DIR = os.path.join(ROOT, "analysis/eval/results")
ENV_FILE = os.path.join(ROOT, "conf/.env")

SEV_MAP = {"高": "high-value", "中": "medium", "低": "trivial"}


def load_env_file(path):
    """加载 conf/.env（KEY=VALUE，跳过注释/占位符），只注入未设置的环境变量。"""
    if not os.path.exists(path):
        print(f"[WARN] {path} 不存在，仅使用系统环境变量", file=sys.stderr)
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            if not v or v.lower() in ("xxxx", "{your_...}", "sk-xxx"):
                continue
            os.environ.setdefault(k, v)


def build_diffs_text(diff_path):
    """把 GitLab diff JSON 数组组装成 diffs_text。"""
    with open(diff_path, encoding="utf-8") as f:
        changes = json.load(f)
    parts = []
    for item in changes:
        path = item.get("new_path") or item.get("old_path") or "?"
        parts.append(f"### 文件: {path}\n{item.get('diff', '')}")
    return "\n\n".join(parts)


def parse_findings(review_text):
    """从 review 文本解析 findings。

    兼容格式（v2 prompt 输出约定）：
        -【高】[file:func/line] desc - 影响 - 建议
        - **【中】 [file:line] desc**        （markdown 加粗）
        -【低】[file:func]                   （描述在下一行缩进）
    描述在下一行缩进时自动合并。
    """
    lines = review_text.splitlines()
    findings = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line.startswith("-"):
            continue
        sev_match = re.search(r"【([高中低])】", line)
        if not sev_match:
            continue
        severity = SEV_MAP[sev_match.group(1)]
        loc_matches = re.findall(r"\[([^\]\[]+)\]", line)
        location = ""
        for cand in loc_matches:
            cand = cand.strip()
            # 优先取包含文件后缀或路径分隔符/冒号的片段
            if re.search(r"[:：/\\]|\.\w{1,5}$", cand):
                location = cand
                break
        if not location and loc_matches:
            location = loc_matches[0].strip()
        text = line[1:].strip()
        text = re.sub(r"^\**\s*【[高中低]】\s*\**", "", text).strip()
        if location and f"[{location}]" in text:
            text = text.replace(f"[{location}]", "", 1).strip()
        text = re.sub(r"^\**\s*", "", text).strip()
        # 合并后续缩进描述行（含嵌套的"问题描述/影响/建议"列表项），
        # 直到空行、非缩进内容、新的顶层列表项或标题
        body = []
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip():
                break
            if nxt.startswith((" ", "\t")):
                body.append(nxt.strip())
                i += 1
            elif nxt.startswith("#"):
                break
            elif nxt.startswith("-"):
                break
            else:
                break
        if body:
            extra = " ".join(body)
            text = (text + " " + extra).strip() if text else extra
        # 清理 markdown 残留与行首符号
        text = text.replace("**", "").strip()
        text = re.sub(r"^[-—\-]\s*", "", text).strip()
        # 截断到 600 字符（保留下文关键词如 ForkJoinPool.commonPool 供文本匹配），
        # 过短截断（200）会切掉证据关键词导致误判 FP
        findings.append({"location": location, "severity": severity, "text": text[:600]})
    return findings


def main():
    parser = argparse.ArgumentParser(description="prompt v2 评估集复测")
    parser.add_argument("--output", default=os.path.join(RESULTS_DIR, "v2_run.json"),
                        help="results JSON 输出路径")
    parser.add_argument("--only", default=None, help="只跑指定用例，如 mr-32")
    parser.add_argument("--reparse", action="store_true",
                        help="跳过 LLM，用 results/raw/*.md 重新解析 findings")
    args = parser.parse_args()

    load_env_file(ENV_FILE)

    # reparse 模式：不需要 LLM，直接复用已保存的 review 原文
    if args.reparse:
        raw_dir = os.path.join(RESULTS_DIR, "raw")
        if not os.path.isdir(raw_dir):
            print(f"[FATAL] 无 raw 目录：{raw_dir}", file=sys.stderr)
            sys.exit(1)
        runs = []
        for fn in sorted(os.listdir(raw_dir)):
            if not fn.endswith("_v2.md"):
                continue
            cid = fn[: -len("_v2.md")]
            if args.only and not cid.startswith(args.only):
                continue
            with open(os.path.join(raw_dir, fn), encoding="utf-8") as f:
                review = f.read()
            findings = parse_findings(review)
            runs.append({"case_id": cid, "findings": findings})
            print(f"[{cid}] findings={len(findings)}")
        if not runs:
            print("[FATAL] raw 目录无可用 review", file=sys.stderr)
            sys.exit(1)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(runs, f, ensure_ascii=False, indent=2)
        print(f"重新解析完成，写入 {args.output}")
        subprocess.run([sys.executable,
                        os.path.join(ROOT, "analysis/eval/score.py"),
                        "--results", args.output])
        return

    from biz.llm.factory import Factory
    try:
        Factory().getClient()
    except Exception as e:
        print(f"[FATAL] LLM 客户端初始化失败：{e}", file=sys.stderr)
        print("请先在 conf/.env 配置 LLM_PROVIDER 与对应厂商 KEY（参照 conf/.env.dist）", file=sys.stderr)
        sys.exit(1)

    from biz.utils.code_reviewer import CodeReviewer

    case_files = sorted(f for f in os.listdir(CASES_DIR)
                        if f.startswith("mr-") and f.endswith(".json"))
    if args.only:
        case_files = [f for f in case_files if f.startswith(args.only)]
    if not case_files:
        print(f"[FATAL] 未找到匹配用例（--only={args.only}）", file=sys.stderr)
        sys.exit(1)

    reviewer = CodeReviewer()
    runs = []
    os.makedirs(RESULTS_DIR, exist_ok=True)
    raw_dir = os.path.join(RESULTS_DIR, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    for fn in case_files:
        cid = fn[:-5]
        with open(os.path.join(CASES_DIR, fn), encoding="utf-8") as f:
            case = json.load(f)
        diff_path = os.path.join(ROOT, case["diff_ref"])
        diffs_text = build_diffs_text(diff_path)
        print(f"\n=== [{cid}] 调用 LLM 生成 review（diff {len(diffs_text)} 字符）===")
        try:
            review = reviewer.review_and_strip_code(diffs_text, "")
        except Exception as e:
            print(f"[ERROR] {cid} 调用失败：{e}", file=sys.stderr)
            continue
        findings = parse_findings(review)
        runs.append({"case_id": cid, "findings": findings})
        print(f"  findings={len(findings)}")
        with open(os.path.join(raw_dir, f"{cid}_v2.md"), "w", encoding="utf-8") as f:
            f.write(review)

    if not runs:
        print("[FATAL] 没有任何成功结果", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入 {args.output}")

    subprocess.run([sys.executable,
                    os.path.join(ROOT, "analysis/eval/score.py"),
                    "--results", args.output])


if __name__ == "__main__":
    main()
