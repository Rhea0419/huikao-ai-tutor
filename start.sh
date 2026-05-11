#!/bin/bash
# 北京会考AI学习管家 — 启动脚本
cd "$(dirname "$0")"

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import streamlit" 2>/dev/null || {
    echo "📦 安装依赖中..."
    python3 -m pip install -r requirements.txt -q
}

echo "🚀 启动服务..."
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
python3 -m streamlit run app.py \
    --server.port 8503 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.address 0.0.0.0

echo "✅ 服务已启动: http://localhost:8503"
