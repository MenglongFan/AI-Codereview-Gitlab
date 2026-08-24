#!/usr/bin/env bash
# 本地启动 AI 代码审查 Dashboard
# 注意：必须设置 PUSH_REVIEW_ENABLED=1，否则 Push 审查选项卡不会渲染（ui.py 默认 '0'）。
set -e
cd "$(dirname "$0")/.."

PORT="${PORT:-5002}"

if [ ! -d .venv ]; then
  echo "[setup] 创建虚拟环境并安装依赖..."
  python3 -m venv .venv
  .venv/bin/pip install -q \
    "streamlit==1.42.2" "altair==5.5.0" "pandas==2.2.3" \
    "streamlit-cookies-manager==0.2.0" "python-dotenv"
fi

# 先停掉旧实例，避免端口占用
pkill -f "streamlit run ui.py" 2>/dev/null || true
sleep 1

PUSH_REVIEW_ENABLED=1 nohup .venv/bin/streamlit run ui.py \
  --server.port="$PORT" \
  --server.address=127.0.0.1 \
  --server.headless=true \
  > log/streamlit.log 2>&1 &

echo "Dashboard 已启动: http://127.0.0.1:$PORT"
echo "日志: log/streamlit.log   停止: pkill -f 'streamlit run ui.py'"
