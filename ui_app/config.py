# -*- coding: utf-8 -*-
"""环境变量与功能开关（原 ui.py 24-32、1841-1842 行）。"""
import os

from dotenv import load_dotenv

load_dotenv("conf/.env")

# 从环境变量中读取用户名和密码
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin")
USER_CREDENTIALS = {
    DASHBOARD_USER: DASHBOARD_PASSWORD
}

# 用于生成和验证token的密钥
SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "fac8cf149bdd616c07c1a675c4571ccacc40d7f7fe16914cfe0f9f9d966bb773")


def push_review_enabled():
    return os.environ.get('PUSH_REVIEW_ENABLED', '0') == '1'
