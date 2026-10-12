#!/usr/bin/env bash
# web-sales 真实客户端 IP 还原：生成 Nginx 用的 Cloudflare 网段片段。
#
# 背景：站点接入 Cloudflare 橙云代理后，到达源站的请求对端全部是 Cloudflare 的 IP，
# 于是访问日志里只有 Cloudflare 的地址，按 IP 做的排查与风控都会失真。
# 本脚本生成 real_ip 配置，让 Nginx 用 CF-Connecting-IP 把 $remote_addr 还原成真实客户端 IP。
#
# ---------------------------------------------------------------- 重要：职责边界
# 「只允许 Cloudflare 回源」（也就是让别人直连源站 IP 打不进来）**不要**用 Nginx 的
# allow/deny 白名单来做：
#   allow/deny 判断的是 $remote_addr，而 real_ip 模块已经把它替换成了真实客户端 IP，
#   于是「allow Cloudflare 网段」永远匹配不上，CF 回源的正常请求会全部 403，全站挂掉。
# 正确做法是让防火墙（或云安全组）在 TCP 层只放行 Cloudflare 网段 —— 见：
#   deploy/cloudflare-firewall.sh   （本机 ufw，一键配置）
#   或云厂商控制台的安全组入站规则
# 那个层面判断的是「连接从哪来」，与 real_ip 的改写互不干扰。
# ---------------------------------------------------------------------------
#
# Cloudflare 网段会变动，建议每月重跑一次（或加进 crontab）。
#
# 用法（在服务器上以 root 执行）：
#   sudo bash /opt/web-sales/deploy/nginx/cloudflare-ips.sh
#   sudo bash /opt/web-sales/deploy/nginx/cloudflare-ips.sh --reload   # 生成后直接重载 Nginx
#
# 生成：/etc/nginx/cloudflare-realip.conf
# 前置：web-sales.conf 中对应的 include 行已取消注释（见 deploy/DEPLOY.md 5.2）

set -euo pipefail

OUT_FILE="${OUT_FILE:-/etc/nginx/cloudflare-realip.conf}"

CF_IPS_V4_URL="https://www.cloudflare.com/ips-v4"
CF_IPS_V6_URL="https://www.cloudflare.com/ips-v6"

RELOAD=0
for arg in "$@"; do
  case "$arg" in
    --reload) RELOAD=1 ;;
    *) echo "未知参数：$arg（可选：--reload）" >&2; exit 1 ;;
  esac
done

log() { printf '\033[36m[cloudflare]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[cloudflare][error]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "请用 root 执行：sudo bash $0"
command -v curl >/dev/null 2>&1 || die "缺少 curl，请先安装：apt install -y curl"

fetch() {
  # -f 让 HTTP 错误码直接失败，避免把错误页面当成网段写进配置
  curl -fsSL --max-time 20 "$1" | grep -Ev '^[[:space:]]*$'
}

log "拉取 Cloudflare 官方网段"
V4="$(fetch "$CF_IPS_V4_URL")" || die "IPv4 网段拉取失败（未改动任何文件）"
V6="$(fetch "$CF_IPS_V6_URL")" || die "IPv6 网段拉取失败（未改动任何文件）"

[[ -n "$V4" ]] || die "IPv4 网段为空，已放弃写入以保护现有配置"
# 兜底校验：首行必须是 CIDR，防止把非预期内容写进 Nginx 配置
# 用参数展开取首行而非 head，避免 head 提前退出触发 SIGPIPE 造成误判
FIRST_LINE="${V4%%$'\n'*}"
[[ "$FIRST_LINE" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}/[0-9]{1,2}$ ]] \
  || die "IPv4 网段格式异常，已放弃写入"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

{
  echo "# 由 deploy/nginx/cloudflare-ips.sh 自动生成，请勿手工编辑"
  echo "# 用途：把 Cloudflare 回源请求的 \$remote_addr 还原为真实客户端 IP"
  echo "# 注意：不要与 allow/deny 白名单混用，原因见脚本头部注释"
  while IFS= read -r cidr; do echo "set_real_ip_from ${cidr};"; done <<< "$V4"
  while IFS= read -r cidr; do echo "set_real_ip_from ${cidr};"; done <<< "$V6"
  echo "real_ip_header CF-Connecting-IP;"
} > "$TMP_FILE"

V4_COUNT="$(printf '%s\n' "$V4" | wc -l | tr -d ' ')"
V6_COUNT="$(printf '%s\n' "$V6" | wc -l | tr -d ' ')"

# 先在临时文件写完整，再一次性落盘，避免留下半成品配置
mv "$TMP_FILE" "$OUT_FILE"
chmod 644 "$OUT_FILE"

log "已写入 $OUT_FILE（IPv4 ${V4_COUNT} 段，IPv6 ${V6_COUNT} 段）"
log "提醒：需 web-sales.conf 中对应的 include 行已取消注释才会生效"

if [[ "$RELOAD" -eq 1 ]]; then
  nginx -t || die "Nginx 配置校验失败，未执行 reload（请检查 include 路径）"
  systemctl reload nginx
  log "Nginx 已重载"
else
  log "下一步：sudo nginx -t && sudo systemctl reload nginx"
fi
