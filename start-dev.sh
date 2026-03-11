#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
  if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} $1"
  else
    echo -e "  ${RED}✗${NC} $1"
    return 1
  fi
}

echo ""
echo "================================"
echo "  OneLiner 本地开发环境启动"
echo "================================"
echo ""

echo "[1/4] 检查 PostgreSQL..."
pg_isready -q
check "PostgreSQL 运行中" || { echo -e "  ${RED}请先启动 PostgreSQL${NC}"; exit 1; }

echo "[2/4] 启动后端..."
if lsof -ti:8000 > /dev/null 2>&1; then
  echo -e "  ${YELLOW}⚠${NC} 端口 8000 已占用，先关闭旧进程"
  lsof -ti:8000 | xargs kill -9 2>/dev/null
  sleep 1
fi
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 2

if kill -0 $BACKEND_PID 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} 后端已启动 (PID: $BACKEND_PID) → http://localhost:8000"
else
  echo -e "  ${RED}✗${NC} 后端启动失败"
  exit 1
fi

echo "[3/4] 构建小程序..."
cd miniprogram
npm run build --silent
check "小程序构建完成 → dist/"
cd ..

echo "[4/4] 环境信息"
echo -e "  ${GREEN}✓${NC} API_BASE: http://localhost:8000 (develop)"
echo ""
echo -e "${GREEN}全部就绪${NC} 打开微信开发者工具导入 miniprogram/dist/ 即可"
echo -e "后端日志: ${YELLOW}fg${NC} 或查看终端输出"
echo ""

wait $BACKEND_PID
