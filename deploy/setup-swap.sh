#!/usr/bin/env bash
# web-sales 部署前置：为 2 核 2G 机器创建并启用 2GB swap。
#
# 为什么必须做：Alembic 迁移、pip 安装依赖、以及并发请求峰值都会短时占用大量内存，
# 没有 swap 时 Linux 的 OOM Killer 会直接杀掉 MySQL 或 Uvicorn 进程。
#
# 用法：
#   sudo bash deploy/setup-swap.sh
#
# 幂等：已存在同名 swapfile 时直接启用，不重复创建。

set -euo pipefail

SWAP_FILE="${SWAP_FILE:-/swapfile}"
SWAP_SIZE_MB="${SWAP_SIZE_MB:-2048}"
SWAPPINESS="${SWAPPINESS:-10}"

log() { printf '\033[32m[swap]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[swap][error]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请用 root 执行：sudo bash $0"

if ! command -v swapon >/dev/null 2>&1; then
  die "未找到 swapon，请先安装 util-linux"
fi

if swapon --show=NAME --noheadings 2>/dev/null | grep -qx "$SWAP_FILE"; then
  log "$SWAP_FILE 已启用，跳过"
  exit 0
fi

if [[ -f "$SWAP_FILE" ]]; then
  log "$SWAP_FILE 已存在但未启用，直接启用"
else
  # fallocate 在部分文件系统（如旧版 ext4/xfs 组合）上生成的 swap 不可用，
  # 这里用 dd 兜底，2G 大约需要十几秒。
  log "创建 ${SWAP_SIZE_MB}MB swapfile：$SWAP_FILE"
  if ! fallocate -l "${SWAP_SIZE_MB}M" "$SWAP_FILE" 2>/dev/null; then
    log "fallocate 不可用，改用 dd"
    dd if=/dev/zero of="$SWAP_FILE" bs=1M count="$SWAP_SIZE_MB" status=progress
  fi
  chmod 600 "$SWAP_FILE"
  mkswap "$SWAP_FILE" >/dev/null
fi

swapon "$SWAP_FILE"

# 持久化：重启后仍生效
if ! grep -qE "^\s*${SWAP_FILE}\s" /etc/fstab; then
  log "写入 /etc/fstab"
  printf '%s none swap sw 0 0\n' "$SWAP_FILE" >> /etc/fstab
fi

# 降低 swappiness：只有内存真的吃紧才换出，避免正常运行时拖慢响应
if ! grep -qE '^\s*vm\.swappiness' /etc/sysctl.conf; then
  printf 'vm.swappiness = %s\n' "$SWAPPINESS" >> /etc/sysctl.conf
fi
sysctl -q "vm.swappiness=$SWAPPINESS"

log "当前内存与 swap 状态："
free -h
