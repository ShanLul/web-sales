#!/usr/bin/env bash
# web-sales 一键发布脚本（在本地开发机执行，通过 ssh/rsync 推到服务器）
#
# 设计前提（针对 2 核 2G 服务器）：
#   * 前端构建全部在本地完成，服务器只接收 dist 产物，绝不在服务器上跑 Vite；
#   * 后端只同步源码，依赖安装与迁移在服务器上按需执行；
#   * 全程不覆盖服务器上的 .env 与数据库。
#
# 依赖：本机需有 npm、rsync、ssh；服务器需有 systemd + 已初始化好的 MySQL。
#
# 用法：
#   bash deploy/deploy.sh                 # 完整发布（前端 + 后端 + 迁移 + 重启）
#   bash deploy/deploy.sh --skip-build    # 跳过前端构建，只同步已有 dist
#   bash deploy/deploy.sh --backend-only  # 只发布后端

set -euo pipefail

# ---------------------------------------------------------------------------
# 配置：按实际环境修改，或通过同名环境变量覆盖
# ---------------------------------------------------------------------------
SERVER="${SERVER:-root@your-domain.com}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_ROOT="${REMOTE_ROOT:-/opt/web-sales}"        # 后端代码目录
REMOTE_WWW="${REMOTE_WWW:-/var/www/web-sales}"      # 前端静态产物目录
SERVICE_NAME="${SERVICE_NAME:-web-sales-api}"
PORTAL_BASE="${PORTAL_BASE:-/portal/}"              # 子系统部署路径前缀

SKIP_BUILD=0
BACKEND_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --skip-build)   SKIP_BUILD=1 ;;
    --backend-only) BACKEND_ONLY=1; SKIP_BUILD=1 ;;
    *) echo "未知参数：$arg" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

log() { printf '\033[36m[deploy]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[deploy][error]\033[0m %s\n' "$*" >&2; exit 1; }

command -v ssh   >/dev/null || die "本机缺少 ssh"
command -v rsync >/dev/null || die "本机缺少 rsync"

SSH_OPTS=(-p "$SSH_PORT" -o StrictHostKeyChecking=accept-new)
RSYNC_SSH="ssh -p $SSH_PORT -o StrictHostKeyChecking=accept-new"

remote() { ssh "${SSH_OPTS[@]}" "$SERVER" "$@"; }

# ---------------------------------------------------------------------------
# 1. 前端构建（本地）
# ---------------------------------------------------------------------------
if [[ "$SKIP_BUILD" -eq 0 ]]; then
  command -v npm >/dev/null || die "本机缺少 npm"

  log "构建主系统后台（base=/）"
  ( cd frontend-admin && npm ci && npm run build )

  log "构建子系统 H5（base=${PORTAL_BASE}）"
  # 子系统部署在路径前缀下，必须显式指定 base，否则 assets 会 404
  ( cd frontend-portal && npm ci && VITE_BASE="$PORTAL_BASE" npm run build )

  [[ -f frontend-admin/dist/index.html ]]  || die "主系统产物缺失"
  [[ -f frontend-portal/dist/index.html ]] || die "子系统产物缺失"
fi

# ---------------------------------------------------------------------------
# 2. 后端代码同步（不含 .env / .venv / 本地 sqlite / 日志）
# ---------------------------------------------------------------------------
log "同步后端源码到 $SERVER:$REMOTE_ROOT"
remote "mkdir -p '$REMOTE_ROOT/backend' '$REMOTE_WWW/admin' '$REMOTE_WWW/portal'"

rsync -az --delete \
  -e "$RSYNC_SSH" \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude '*.db' \
  --exclude 'logs/' \
  --exclude '*.log' \
  --exclude '.pytest_cache/' \
  backend/ "$SERVER:$REMOTE_ROOT/backend/"

# ---------------------------------------------------------------------------
# 3. 前端产物同步
# ---------------------------------------------------------------------------
if [[ "$BACKEND_ONLY" -eq 0 ]]; then
  log "同步主系统产物到 $REMOTE_WWW/admin"
  rsync -az --delete -e "$RSYNC_SSH" frontend-admin/dist/ "$SERVER:$REMOTE_WWW/admin/"

  log "同步子系统产物到 $REMOTE_WWW/portal"
  rsync -az --delete -e "$RSYNC_SSH" frontend-portal/dist/ "$SERVER:$REMOTE_WWW/portal/"
fi

# ---------------------------------------------------------------------------
# 4. 服务器侧：依赖、迁移、重启
# ---------------------------------------------------------------------------
log "服务器侧安装依赖并执行数据库迁移"
remote bash -s <<EOF
set -euo pipefail
cd '$REMOTE_ROOT/backend'

[[ -f .env ]] || { echo '缺少 $REMOTE_ROOT/backend/.env，请先按 .env.example 创建' >&2; exit 1; }

# 首次部署时创建虚拟环境
if [[ ! -x .venv/bin/python ]]; then
  echo '创建虚拟环境 .venv'
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip wheel >/dev/null
.venv/bin/python -m pip install -r requirements.txt

# 迁移必须串行执行，避免两个进程同时改表结构
.venv/bin/python -m alembic upgrade head

mkdir -p logs
chown -R www-data:www-data '$REMOTE_ROOT' '$REMOTE_WWW'
EOF

log "重启后端服务"
remote "systemctl restart '$SERVICE_NAME' && sleep 2 && systemctl is-active '$SERVICE_NAME'"

log "重载 Nginx"
remote "nginx -t && systemctl reload nginx"

# ---------------------------------------------------------------------------
# 5. 冒烟检查
# ---------------------------------------------------------------------------
log "健康检查"
remote "curl -fsS http://127.0.0.1:8000/api/health || { echo '健康检查失败，请查看 journalctl -u $SERVICE_NAME -n 100' >&2; exit 1; }"

log "发布完成"
log "主系统： https://<your-domain>/"
log "子系统： https://<your-domain>${PORTAL_BASE}"
