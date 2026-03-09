#!/bin/bash
# =============================================================================
# 微信公众号草稿箱 Skill 部署脚本
# 依赖: ssh, scp, rsync, npm, python3
# =============================================================================

set -euo pipefail

echo "🚀 微信公众号草稿箱 Skill 部署"
echo "=================================="
echo ""

REMOTE_HOST="${REMOTE_HOST:-__FILL_ME_SERVER_HOST__}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/home/node/.openclaw/skills/wechat-mp-skill}"

if [[ "$REMOTE_HOST" == "__FILL_ME_SERVER_HOST__" ]]; then
  echo "❌ 请先设置 REMOTE_HOST 环境变量"
  exit 1
fi

echo "📦 步骤 1: 检查本地配置"
if [[ ! -f "config.yaml" ]]; then
  echo "⚠️ 未找到 config.yaml，自动从模板创建"
  cp config.yaml.template config.yaml
  echo "   已生成 config.yaml，请先填入真实 AppID / AppSecret 后再重新执行"
  exit 1
fi

if [[ -f "scripts/package-lock.json" ]]; then
  echo "   安装 Node.js 依赖..."
  (cd scripts && npm ci)
fi

echo "✅ 本地检查完成"
echo ""

echo "📤 步骤 2: 上传到服务器"
rsync -av \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.cache' \
  -e "ssh -p $REMOTE_PORT" \
  ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

echo "✅ 上传完成"
echo ""

echo "🔧 步骤 3: 在服务器上安装依赖"
ssh -p "$REMOTE_PORT" "${REMOTE_USER}@${REMOTE_HOST}" "
  set -e
  cd ${REMOTE_DIR}
  python3 -m pip install -r requirements.txt
  if [ -f scripts/package-lock.json ]; then
    cd scripts
    npm ci
  fi
"

echo ""
echo "=================================="
echo "✅ 部署完成!"
echo "=================================="
echo ""
echo "📋 下一步:"
echo "   1. ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
echo "   2. cd $REMOTE_DIR"
echo "   3. python3 wechat_mp.py test"
echo "   4. 在 OpenClaw 中加载该 skill 并发送“公众号帮助”进行联调"
