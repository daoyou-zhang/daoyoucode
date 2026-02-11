#!/bin/bash
# daoyoucode 环境设置脚本

set -e

echo "🚀 Setting up daoyoucode development environment..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

echo "✅ pnpm found: $(pnpm --version)"

# 安装后端依赖
echo "📦 Installing backend dependencies..."
cd backend
pip install -e ".[dev]"
cd ..

# 安装前端依赖
echo "📦 Installing frontend dependencies..."
cd frontend
pnpm install
cd ..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start backend: cd backend && uvicorn daoyoucode.api.main:app --reload"
echo "  2. Start TUI: cd frontend && pnpm dev:tui"
echo "  3. Start Web: cd frontend && pnpm dev:web"
