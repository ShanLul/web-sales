#!/usr/bin/env bash
# web-sales 源站防护：用 ufw 把 80/443 收敛为「只接受 Cloudflare 回源」。
#
# 这是「隐藏源站 IP」真正起作用的一层：别人即使知道域名、也直接解析到了源站 IP，
# 直连 80/443 的请求会在 TCP 层就被丢弃，连 Nginx 都到不了。
#
# 为什么不用 Nginx 的 allow/deny 来做这件事：
#   启用 real_ip 还原后，allow/deny 判断的是**已还原的真实客户端 IP**，
#   「allow Cloudflare 网段」永远匹配不上，会把 CF 回源的正常请求全部 403，全站挂掉。
#   防火墙判断的是「连接从哪来」，与 real_ip 的改写互不干扰。
#
# 用法（在服务器上以 root 执行）：
#   sudo bash deploy/cloudflare-firewall.sh --dry-run   # 只打印将要执行的命令，不改动系统
#   sudo bash deploy/cloudflare-firewall.sh             # 写入规则（ufw 已启用则立即生效）
#   sudo bash deploy/cloudflare-firewall.sh --enable    # 写入规则并启用 ufw
#   sudo bash deploy/cloudflare-firewall.sh --remove    # 删除这些规则（回滚）
#
# Cloudflare 网段会变动，变动后重跑本脚本即可（重复规则会被 ufw 跳过）。
#
# 前提：域名已经通过 Cloudflare 代理（橙云）正常访问。
# 若域名还是灰云（DNS only），启用本脚本会让所有用户连不上源站。

set -euo pipefail

SSH_PORT="${SSH_PORT:-22}"
PORTS="${PORTS:-80,443}"
DRY_RUN=0
DO_ENABLE=0
DO_REMOVE=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --enable)  DO_ENABLE=1 ;;
    --remove)  DO_REMOVE=1 ;;
    *) echo "未知参数：$arg（可选：--dry-run / --enable / --remove）" >&2; exit 1 ;;
  esac
done

CF_IPS_V4_URL="https://www.cloudflare.com/ips-v4"
CF_IPS_V6_URL="https://www.cloudflare.com/ips-v6"

log() { printf '\033[36m[firewall]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[firewall][error]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请用 root 执行：sudo bash $0"

if ! command -v ufw >/dev/null 2>&1; then
  die "未找到 ufw。可直接在云厂商控制台的安全组里限制 80/443 的入站来源为 Cloudflare 网段
      （网段列表：curl -s https://www.cloudflare.com/ips-v4 与 https://www.cloudflare.com/ips-v6），
      效果等价且不需要本脚本。"
fi

command -v curl >/dev/null 2>&1 || die "缺少 curl，请先安装：apt install -y curl"

fetch() {
  curl -fsSL --max-time 20 "$1" | grep -Ev '^[[:space:]]*$'
}

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '  [dry-run] %s\n' "$*"
    return 0
  fi
  # ufw 对重复规则会打印 Skipping，删除不存在的规则会返回非 0；
  # 这两类都不该中断脚本（set -e），因此吞掉输出并只在失败时给个提示。
  if ! "$@" >/dev/null 2>&1; then
    printf '  [warn] 未成功执行（通常可忽略）：%s\n' "$*"
  fi
  return 0
}

log "拉取 Cloudflare 官方网段"
V4="$(fetch "$CF_IPS_V4_URL")" || die "IPv4 网段拉取失败"
V6="$(fetch "$CF_IPS_V6_URL")" || die "IPv6 网段拉取失败"
[[ -n "$V4" ]] || die "IPv4 网段为空，已中止"
# 用参数展开取首行而非 head，避免 head 提前退出触发 SIGPIPE 造成误判
FIRST_LINE="${V4%%$'\n'*}"
[[ "$FIRST_LINE" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}/[0-9]{1,2}$ ]] \
  || die "IPv4 网段格式异常，已中止"

V4_COUNT="$(printf '%s\n' "$V4" | wc -l | tr -d ' ')"
V6_COUNT="$(printf '%s\n' "$V6" | wc -l | tr -d ' ')"
log "网段已就绪：IPv4 ${V4_COUNT} 段，IPv6 ${V6_COUNT} 段；目标端口 ${PORTS}"

# ---------------------------------------------------------------------------
# 回滚：删除此前写入的 Cloudflare 规则
# ---------------------------------------------------------------------------
if [[ "$DO_REMOVE" -eq 1 ]]; then
  log "开始删除 Cloudflare 相关规则"
  while IFS= read -r cidr; do
    run ufw delete allow from "$cidr" to any port "$PORTS" proto tcp
  done <<< "$V4"
  while IFS= read -r cidr; do
    run ufw delete allow from "$cidr" to any port "$PORTS" proto tcp
  done <<< "$V6"
  log "已删除。注意：默认入站策略仍为 deny，源站此时对外不可访问"
  log "如需完全恢复，请手动执行：sudo ufw allow ${SSH_PORT}/tcp && sudo ufw disable"
  exit 0
fi

# ---------------------------------------------------------------------------
# 写入规则
# ---------------------------------------------------------------------------
# 顺序要点：先把 SSH 放行、把默认入站策略设为 deny，再放行 80/443 的 Cloudflare 来源。
# 绝不先 deny 后放行 SSH，否则会把自己锁在服务器外面。
log "放行 SSH 端口 ${SSH_PORT}/tcp（避免把自己锁在门外）"
run ufw allow "${SSH_PORT}/tcp"

log "设置默认策略：入站拒绝、出站允许"
run ufw default deny incoming
run ufw default allow outgoing

log "放行 Cloudflare 网段访问 ${PORTS}"
while IFS= read -r cidr; do
  run ufw allow from "$cidr" to any port "$PORTS" proto tcp
done <<< "$V4"
while IFS= read -r cidr; do
  run ufw allow from "$cidr" to any port "$PORTS" proto tcp
done <<< "$V6"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "dry-run 结束，未改动系统。去掉 --dry-run 即真正执行。"
  exit 0
fi

if [[ "$DO_ENABLE" -eq 1 ]]; then
  log "启用 ufw"
  ufw --force enable
else
  if [[ "$(ufw status | head -n 1)" == *"inactive"* ]]; then
    log "ufw 当前未启用，规则尚未生效。确认无误后执行：sudo ufw --force enable"
    log "（或重跑本脚本并加上 --enable）"
  fi
fi

log "当前防火墙状态："
ufw status verbose | sed 's/^/  /'
log "验证：从外部机器直连源站 IP，应当连不上（超时或 connection refused）"
log "      curl -m 5 -H 'Host: your-domain.com' http://<源站IP>/"
