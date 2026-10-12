# web-sales 裸机部署手册（Ubuntu 22.04 / 2 核 2G）

本文档面向一台全新的 Linux 裸机，从零部署「主系统后台 + 子系统 H5 + FastAPI 后端 + MySQL 8」。
目标硬件为 2 核 2G，所有取舍都围绕「不 OOM、不拖垮机器」展开。

CentOS 7+ 的差异只在包管理命令（`yum` 替代 `apt`）与 Nginx 配置目录（`/etc/nginx/conf.d/` 相同），
下面凡是与发行版相关的步骤都会标注。

---

## 0. 部署拓扑

| 组件 | 位置 | 说明 |
| --- | --- | --- |
| Nginx | 宿主机 | 静态托管两个前端 + 反向代理 `/api/` |
| Uvicorn | systemd | `127.0.0.1:8000`，2 worker |
| MySQL 8 | 宿主机 | `utf8mb4`，仅监听本机 |
| 主系统产物 | `/var/www/web-sales/admin` | `base=/` |
| 子系统产物 | `/var/www/web-sales/portal` | `base=/portal/` |
| 后端代码 | `/opt/web-sales/backend` | 含 `.venv` 与 `.env` |
| Cloudflare | 外部（可选，推荐） | 橙云代理隐藏源站 IP，回源到 80/443（见 5.2） |

对外只需暴露 80/443；接入 Cloudflare 后，80/443 还可进一步收敛为「只放行 Cloudflare 网段」，
这样别人即使知道域名也打不到源站。MySQL 与 Uvicorn 都不对公网开放。

---

## 1. 系统准备

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev build-essential \
                    nginx mysql-server git rsync curl
```

### 1.1 创建 2GB swap（**必做**）

```bash
sudo bash /opt/web-sales/deploy/setup-swap.sh
free -h          # 应能看到 2.0Gi 的 Swap
```

没有 swap 时，`pip install`、Alembic 迁移以及并发请求峰值都可能触发 OOM Killer，
直接把 MySQL 或 Uvicorn 杀掉（表现为服务莫名重启、502）。

---

## 2. 数据库初始化

```bash
sudo systemctl enable --now mysql
sudo mysql_secure_installation      # 按提示设置 root 密码、移除匿名用户
```

```sql
-- 用强密码替换下面的 CHANGE_ME，并同步写进 backend/.env
CREATE DATABASE web_sales CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'websales'@'localhost' IDENTIFIED BY 'CHANGE_ME';
GRANT ALL PRIVILEGES ON web_sales.* TO 'websales'@'localhost';
FLUSH PRIVILEGES;
```

### 2.1 应用 2C2G 调优

```bash
sudo cp deploy/mysql/2c2g-tuning.cnf /etc/mysql/mysql.conf.d/zz-web-sales.cnf
sudo systemctl restart mysql
sudo mysql -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size'"   # 期望 268435456
```

调优要点见 `deploy/mysql/2c2g-tuning.cnf` 内注释，核心是
`innodb_buffer_pool_size=256M`、关闭 `performance_schema`、`max_connections=50`。

---

## 3. 部署后端

```bash
sudo mkdir -p /opt/web-sales
# 方式一：git clone 到 /opt/web-sales
# 方式二：从本地用 deploy/deploy.sh 推送（推荐，见第 6 节）
```

首次需要手动准备虚拟环境与 `.env`：

```bash
cd /opt/web-sales/backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip wheel
.venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
vi .env       # 至少改 DATABASE_URL / JWT_SECRET / PUBLIC_BASE_URL
```

`.env` 关键项：

```ini
DATABASE_URL=mysql+pymysql://websales:CHANGE_ME@127.0.0.1:3306/web_sales?charset=utf8mb4
JWT_SECRET=<用下面的命令生成>
JWT_EXPIRE_MINUTES=720
# 必须与 Nginx 中子系统的实际访问路径一致，后端据此拼完整下单链接
PUBLIC_BASE_URL=https://your-domain.com/portal
CORS_ORIGINS=https://your-domain.com
```

生成 JWT 密钥：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

执行迁移并初始化管理员：

```bash
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.seed          # 创建默认管理员与演示商品（仅首次）
```

> 默认管理员账号见 `app/seed.py`，**上线后请立即在数据库里改密码或删除演示商品**。

---

## 4. 配置 systemd

```bash
sudo cp /opt/web-sales/deploy/systemd/web-sales-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now web-sales-api
systemctl status web-sales-api --no-pager
curl -fsS http://127.0.0.1:8000/api/health
```

单元文件要点：

- `EnvironmentFile=/opt/web-sales/backend/.env`：密钥不进单元文件；
- `--workers 2 --limit-concurrency 100`：2 核机器上再多只会让整体变慢；
- `MemoryMax=900M`：单进程组超限重启，而不是把整机拖进 OOM；
- `Restart=always` + `StartLimitBurst=5`：崩溃自愈但不会疯狂重启；
- `Requires=mysql.service`：与 MySQL 同生共死，避免数据库挂掉后接口持续 500。
  **CentOS / RHEL 下 MySQL 单元名是 `mysqld.service`，需同步修改单元文件里的两处引用。**

排查命令：

```bash
journalctl -u web-sales-api -f
journalctl -u web-sales-api -n 200 --no-pager
```

---

## 5. 配置 Nginx

```bash
sudo mkdir -p /var/www/web-sales/admin /var/www/web-sales/portal
sudo cp deploy/nginx/web-sales.conf /etc/nginx/conf.d/web-sales.conf
sudo vi /etc/nginx/conf.d/web-sales.conf      # 改 server_name 与 your-domain
sudo nginx -t && sudo systemctl reload nginx
```

路径约定：

- `/` → 主系统后台；
- `/portal/` → 子系统 H5（**必须**用 `VITE_BASE=/portal/` 构建）；
- `/api/` → 反代 `127.0.0.1:8000`。

因为子系统使用 hash 路由（`#/order?t=...`），Nginx 侧不需要任何额外的 rewrite 规则，
只需 `try_files $uri $uri/ /portal/index.html` 兜底。

> 若希望两个前端各用独立域名，请启用配置文件末尾注释里的「备选方案」，
> 此时子系统 `VITE_BASE` 保持 `/`，`PUBLIC_BASE_URL` 设为 `https://portal.your-domain.com`。

### 5.1 HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 5.2 隐藏服务器 IP（Cloudflare 代理，**推荐优先做**）

这是投入产出比最高的一步安全加固：**别人拿到你的域名也解析不到源站 IP**，
端口扫描、直接打 IP、绕过域名做防护这些攻击方式全部失效。

它由两件事组成，缺一不可：

1. **Cloudflare 橙云代理**：对外 DNS 只解析 Cloudflare 的 IP，用户请求经 Cloudflare 回源；
2. **源站只接受 Cloudflare 回源**：防火墙（或云安全组）在 **TCP 层**只放行 Cloudflare 网段，
   直连源站 IP 的请求根本到不了 Nginx。

> **顺序极其重要**：先让域名在 Cloudflare 代理下能正常访问，**再**启用源站访问限制。
> 顺序反了（域名还是灰云 DNS only 就限制来源）会让所有真实用户连不上。

#### 步骤 1：接入 Cloudflare 并确认可访问

1. 域名 NS 交给 Cloudflare，添加指向源站 IP 的 A 记录；
2. 先保持**灰云（DNS only）**，按 5.1 用 certbot 把证书签好，确认 `https://your-domain.com/portal/` 能正常打开；
3. 再把 A 记录切成**橙云（Proxied）**，并把 SSL/TLS 模式设为 **Full (strict)**；
   （不要用 Flexible：源站会把自己 301 到 https，形成重定向循环）
4. 确认网站仍然正常。这一步没通过就不要继续。

> 源站证书也可以换成 Cloudflare 面板里的 Origin Certificate（15 年、无需续期），
> 好处是源站证书不会进入公共 CT 日志。但要清楚：Cloudflare 给域名签发的**边缘证书**
> 照样会写进 CT 日志，所以「用了 HTTPS 还不想让任何人知道域名」在技术上做不到，
> 能达成的目标是不让域名直接指向你的服务器。

#### 步骤 2：生成真实客户端 IP 还原配置

```bash
# 从 Cloudflare 官方地址拉取最新网段；网段会变动，建议每月重跑一次
sudo bash /opt/web-sales/deploy/nginx/cloudflare-ips.sh
```

生成 `/etc/nginx/cloudflare-realip.conf`：让 Nginx 用 `CF-Connecting-IP` 把 `$remote_addr`
还原成真实客户端 IP。不做这一步，日志与排查里看到的全是 Cloudflare 的 IP。

> `deploy/deploy.sh` 只同步 `backend/` 目录，不会推 `deploy/`。若服务器上的 `deploy/`
> 来自 git clone，先 `git pull`；否则把本节用到的两个脚本推上去：
>
> ```bash
> scp deploy/nginx/cloudflare-ips.sh root@your-domain.com:/opt/web-sales/deploy/nginx/
> scp deploy/cloudflare-firewall.sh  root@your-domain.com:/opt/web-sales/deploy/
> ```

#### 步骤 3：启用还原配置

编辑 `/etc/nginx/conf.d/web-sales.conf`，取消 server 块里「真实客户端 IP 还原」那段注释：

```nginx
include /etc/nginx/cloudflare-realip.conf;
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> 用两个独立域名方案时，两个 server 块都 include 一份（都在橙云下时）。

> **不要在这里用 `allow`/`deny` 写「只放行 Cloudflare」的白名单。**
> `real_ip` 已经把 `$remote_addr` 换成了真实客户 IP，`allow <Cloudflare 网段>` 永远匹配不上，
> 结果是把 CF 回源的正常请求全部 403、全站挂掉。这件事交给步骤 4。

#### 步骤 4：让源站只接受 Cloudflare 回源（关键一步）

脚本化配置 ufw，先 dry-run 看清楚要做什么：

```bash
# 1) 只看会执行什么，不改动系统
sudo bash /opt/web-sales/deploy/cloudflare-firewall.sh --dry-run

# 2) 确认后写入规则（默认入站拒绝 + 放行 SSH + 放行 Cloudflare 到 80/443）
sudo bash /opt/web-sales/deploy/cloudflare-firewall.sh

# 3) 让规则生效（ufw 之前未启用时）
sudo ufw --force enable
```

脚本的执行顺序（这个顺序是为了不把自己锁在门外）：

1. 放行 SSH 端口；
2. 默认入站策略设为 `deny`；
3. 放行 Cloudflare 网段访问 80/443。

重复执行是幂等的，Cloudflare 网段变动后重跑即可。
回滚：`sudo bash deploy/cloudflare-firewall.sh --remove`。

#### 步骤 4b：云安全组收口（双保险，可选）

在云厂商控制台把 80/443 的入站来源也限制为 Cloudflare 网段
（即 `curl -s https://www.cloudflare.com/ips-v4` 与 `/ips-v6` 列出的地址），
**22 端口只放行你自己的 IP**。与 ufw 叠加即为双保险。

#### 步骤 5：验证

```bash
# 1) 解析结果是 Cloudflare 的 IP，而不是你的源站 IP
dig +short your-domain.com

# 2) 响应确实经过 Cloudflare
curl -sI https://your-domain.com/ | grep -i '^cf-ray'

# 3) 从外部机器直连源站 IP，应当连不上（连接超时或 connection refused，而不是返回页面）
curl -m 5 -sI -H 'Host: your-domain.com' http://<源站IP>/

# 4) 日志里应是真实客户端 IP，而不是 Cloudflare 网段
tail -n 5 /var/log/nginx/web-sales.access.log
```

#### 三个需要提前知道的坑

- **Excel 导出可能报 524**：Cloudflare（免费/Pro/Business）等待源站响应的上限约 100 秒，
  而 Nginx 侧放宽到了 120 秒，所以超大导出会先被 Cloudflare 截断。建议按时间范围分批导出并控制在 100 秒内。
- **下单限流不受影响**：节流是按链接 token 分桶的（`app/api/portal/checkout.py`），
  不依赖客户端 IP，因此接入 Cloudflare 后限流行为不变。
- **别把「只放行 Cloudflare」写成 Nginx 的 `allow`/`deny`**：`real_ip` 已经把 `$remote_addr`
  换成了真实客户 IP，白名单永远匹配不上，会把 CF 回源的正常请求全部判 403（详见步骤 3 的提示）。

**回滚**：

- 只撤防火墙：`sudo bash deploy/cloudflare-firewall.sh --remove`；
- 撤 Nginx 还原：把 `include /etc/nginx/cloudflare-realip.conf;` 注释掉，
  再 `sudo nginx -t && sudo systemctl reload nginx`。

---

## 6. 日常发布

在**本地开发机**执行（不要在生产机上构建前端）：

```bash
SERVER=root@your-domain.com bash deploy/deploy.sh
```

脚本流程：

1. 本地 `npm ci && npm run build`（主系统 `base=/`，子系统 `VITE_BASE=/portal/`）；
2. `rsync` 同步后端源码（排除 `.env`、`.venv`、`*.db`、`logs/`）；
3. `rsync` 同步两个 `dist` 到 `/var/www/web-sales/`；
4. 服务器侧装依赖、`alembic upgrade head`、`chown www-data`；
5. `systemctl restart web-sales-api`、`nginx -t && reload`；
6. 健康检查 `/api/health`。

常用变体：

```bash
bash deploy/deploy.sh --skip-build      # 复用已有 dist
bash deploy/deploy.sh --backend-only    # 只发后端
```

回滚：前端产物按 `dist` 目录整体覆盖，保留上一版目录即可秒回；
后端回滚用 `git checkout <tag>` 后重跑 `deploy.sh --backend-only`。

---

## 7. 上线检查清单

- [ ] `free -h` 中 Swap 为 2.0Gi
- [ ] `JWT_SECRET` 已替换，且不是 `.env.example` 中的示例值
- [ ] `PUBLIC_BASE_URL` 与实际访问路径一致（含 `/portal`）
- [ ] 默认管理员密码已修改
- [ ] 演示商品已清理或替换为真实商品
- [ ] MySQL 未监听 0.0.0.0（`sudo ss -lntp | grep 3306`）
- [ ] Uvicorn 未监听 0.0.0.0（应为 `127.0.0.1:8000`）
- [ ] 已配置 HTTPS 与证书自动续期
- [ ] 域名解析结果是 Cloudflare 的 IP，而非源站 IP（`dig +short your-domain.com`）
- [ ] 从外部直连源站 IP 连不上（80/443 只放行 Cloudflare，见 5.2 步骤 4）
- [ ] 响应头含 `cf-ray`，Nginx 日志里是真实客户端 IP
- [ ] 云安全组（如启用）80/443 仅放行 Cloudflare 网段，22 仅放行运维 IP
- [ ] 生成一条测试链接，在手机浏览器完整走一遍下单流程
- [ ] `journalctl -u web-sales-api` 无持续报错

---

## 8. 常见问题

**502 Bad Gateway**
后端没起来。`systemctl status web-sales-api` 与 `journalctl -u web-sales-api -n 100` 看原因；
常见是 `.env` 里 `DATABASE_URL` 密码错或 MySQL 未启动。

**子系统页面白屏、assets 404**
子系统构建时没设 `VITE_BASE=/portal/`，产物引用的是 `/assets/...`。
重新构建并同步即可。

**临时链接点开提示「链接不可用」但后台看着正常**
先核对 `PUBLIC_BASE_URL` 是否少了 `/portal`；再确认链接状态
（已过期 / 次数耗尽 / 已禁用 三种都会给出对应提示）。

**MySQL 被 OOM Killer 杀掉**
swap 没配或 `innodb_buffer_pool_size` 调得过大。先执行 `setup-swap.sh`，
再把缓冲池降到 256M 以内。

**接入 Cloudflare 后导出 Excel 报 524**
Cloudflare 等待源站响应的上限约 100 秒（免费/Pro/Business），比 Nginx 的 120 秒更早超时。
按时间范围分批导出，或把导出接口放到不经 Cloudflare 的地址（见 5.2 的坑位说明）。

**配置源站防护后所有用户都连不上**
最常见原因是域名还在**灰云（DNS only）**，此时限制来源会把真实用户一起挡掉 —— 先让域名走 Cloudflare 橙云。
其次是自己被 SSH 锁在外面：从云控制台的 VNC／救援模式进去执行 `sudo ufw allow 22/tcp`（或 `sudo ufw disable`）。

**在 Nginx 里写了 `allow`/`deny` 白名单后全站 403**
`real_ip` 会把 `$remote_addr` 还原成真实客户 IP，`allow <Cloudflare 网段>` 匹配不上 CF 回源的请求。
删掉这几行 allow/deny，改用 `deploy/cloudflare-firewall.sh`（原因见 5.2 步骤 3 的提示）。

**脚本报 `$'\r': command not found`**
脚本在 Windows 下被转成了 CRLF 行尾。执行 `sed -i 's/\r$//' deploy/*.sh deploy/nginx/*.sh` 修复。

**导出 Excel 超时**
订单量很大时导出会持续较久。已在 Nginx 侧放宽到 120s；
如仍不足，建议先按时间范围筛选再导出。
