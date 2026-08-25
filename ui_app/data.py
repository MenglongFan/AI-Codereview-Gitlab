# -*- coding: utf-8 -*-
"""数据获取与格式化（原 ui.py 140-165、1888-1901、1966-1982 行）。"""
import datetime
import math

import pandas as pd

from biz.service.review_service import ReviewService
from ui_app.config import push_review_enabled


# 获取数据函数
def get_data(service_func, authors=None, project_names=None, updated_at_gte=None, updated_at_lte=None, columns=None):
    df = service_func(authors=authors, project_names=project_names, updated_at_gte=updated_at_gte,
                      updated_at_lte=updated_at_lte)

    if df.empty:
        return pd.DataFrame(columns=columns)

    if "updated_at" in df.columns:
        df["updated_at"] = df["updated_at"].apply(
            lambda ts: datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(ts, (int, float)) else ts
        )

    def format_delta(row):
        if not math.isnan(row['additions']) and not math.isnan(row['deletions']):
            return f"+{int(row['additions'])}  -{int(row['deletions'])}"
        else:
            return ""

    if "additions" in df.columns and "deletions" in df.columns:
        df["delta"] = df.apply(format_delta, axis=1)
    else:
        df["delta"] = ""

    data = df[columns]
    return data


# ============ 共享筛选数据（合并 MR + Push 基础记录） ============
def _load_combined_base(start_datetime, end_datetime):
    """合并 MR（+ Push）基础记录，用于构建共享筛选的作者/项目选项。"""
    frames = []
    funcs = [ReviewService().get_mr_review_logs]
    if push_review_enabled():
        funcs.append(ReviewService().get_push_review_logs)
    for func in funcs:
        df = get_data(func, updated_at_gte=start_datetime, updated_at_lte=end_datetime,
                      columns=["author", "project_name"])
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["author", "project_name"])
    return pd.concat(frames, ignore_index=True)


# ============ Token 统计数据 ============
# Token 统计页所需的审查记录列
TOKEN_COLUMNS = ["project_name", "author", "updated_at", "prompt_tokens", "completion_tokens", "total_tokens"]


def load_review_tokens(authors=None, project_names=None, updated_at_gte=None, updated_at_lte=None):
    """合并 MR + Push 的审查 token 数据（纯合并，不做来源区分）。"""
    funcs = [ReviewService().get_mr_review_logs]
    if push_review_enabled():
        funcs.append(ReviewService().get_push_review_logs)

    frames = []
    for func in funcs:
        df = get_data(func, authors=authors, project_names=project_names,
                      updated_at_gte=updated_at_gte, updated_at_lte=updated_at_lte,
                      columns=TOKEN_COLUMNS)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame(columns=TOKEN_COLUMNS)
    return pd.concat(frames, ignore_index=True)
