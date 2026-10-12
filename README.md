# web-sales · 临时链接授权下单平台

主系统统一维护商品与权限、生成**临时链接**；外部下单用户凭链接进入 H5 子系统，
无需注册即可浏览被授权的商品并提交订单；订单回到主系统统一查看与流转。

核心链路：

```
权限模板（可见商品集合） → 临时链接（有效期 / 次数 / 一次性） → 子系统凭 token 下单 → 主系统流转订单
```

---

## 目录结构

```
web-sales/
├── backend/                  FastAPI 后端（分层：api / services / schemas / models / core）
│   ├── app/
│   │   ├── api/admin/        后台接口（JWT 鉴权）
│   │   ├── api/portal/       子系统接口（链接 token 即凭证）
│   │   ├── services/         业务规则（链接校验、授权解析、下单、导出）
│   │   ├── models/           SQLAlchemy 2.0 声明式模型
│   │   └── seed.py           默认管理员与演示商品
│   ├── alembic/              数据库迁移
│   └── requirements.txt
├── frontend-admin/           主系统 PC 后台（Vue3 + TDesign Vue Next + Tailwind）
├── frontend-portal/          子系统 H5（Vue3 + TDesign Mobile Vue + Tailwind）
├── deploy/                   裸机部署产物（MySQL 调优 / Nginx / systemd / swap / 发布脚本 / Cloudflare 源站防护）
└── README.md
```

---

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3.11+ · FastAPI · Uvicorn · SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| 数据库 | MySQL 8（utf8mb4，PyMySQL 驱动）；本地开发可直接用 SQLite |
| 鉴权 | 主系统 JWT（PyJWT）+ bcrypt；子系统不鉴权，以链接 token 为凭证 |
| 导出 | openpyxl 只写模式 + 流式响应 |
| 主系统前端 | Vue 3 · TypeScript · Vite 5 · TDesign Vue Next · Pinia · Vue Router · Tailwind CSS · axios |
| 子系统前端 | Vue 3 · TypeScript · Vite 5 · TDesign Mobile Vue · Pinia · Vue Router · Tailwind CSS |

---

## 快速开始

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # 按需修改 DATABASE_URL / JWT_SECRET / PUBLIC_BASE_URL
python -m alembic upgrade head     # 建表
python -m app.seed                 # 写入默认管理员与演示商品
python -m uvicorn app.main:app --reload --port 8000
```

- 接口文档：<http://127.0.0.1:8000/api/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>
- 默认管理员：`admin` / `admin123`（见 `app/seed.py`，**上线前务必修改**）

本地开发若不想装 MySQL，把 `DATABASE_URL` 换成 SQLite 即可：

```ini
DATABASE_URL=sqlite:///./web_sales.db
```

### 2. 主系统后台

```bash
cd frontend-admin
npm install
npm run dev            # http://127.0.0.1:5173
```

### 3. 子系统 H5

```bash
cd frontend-portal
npm install
npm run dev            # http://127.0.0.1:5174/#/order?t=<token>
```

两个前端的开发服务器都把 `/api` 代理到 `http://127.0.0.1:8000`，本地联调无需额外配置。

---

## 核心机制

### 链接状态：运行期推导，不用定时任务

数据库只持久化三种显式状态（`active` / `disabled` / `voided`），其余状态在查询时实时推导：

| 展示状态 | 判定条件 |
| --- | --- |
| 未使用 | `active` 且 `used_count = 0` 且未过期未耗尽 |
| 使用中 | `active` 且 `used_count > 0` 且未过期未耗尽 |
| 已过期 | `expire_at` 已过（`NULL` 表示永久） |
| 次数耗尽 | `max_uses` 非空且 `used_count >= max_uses`，或一次性链接已下单 |
| 已禁用 | `disabled`（管理员手动禁用） |
| 已作废 | `voided`（不可再变更状态） |

这样避免了定时任务与状态不同步的问题，也省掉了 2C2G 机器上的常驻开销。

### 次数扣减：条件行级更新保证原子性

下单时用一条带条件的 `UPDATE` 抢占次数，依据 `rowcount` 判断成功与否，
从根上杜绝并发下的超发：

```sql
UPDATE temp_link
   SET used_count = used_count + 1
 WHERE id = :id
   AND status = 'active'
   AND (max_uses IS NULL OR used_count < max_uses)
   AND (expire_at IS NULL OR expire_at > NOW())
   AND (is_single_use = 0 OR used_count = 0)   -- 一次性链接只允许抢占一次
```

实测：并发 20 次提交「限 5 次」链接恰好成功 5 次、其余返回 `1003`；
并发 15 次提交一次性链接恰好成功 1 次。越权商品被拒时不会消耗链接次数。

### 授权校验：只信服务端

子系统下单只提交 `token` 与 `product_id / quantity`。
服务端重新执行 `token → 权限模板 → 可见商品集合` 的推导并逐项校验，
绝不信任前端传来的商品范围，因此改请求体也无法越权下单。

### 金额与历史一致性

订单落库时对商品名称与单价做**快照**（`order_item.product_name` / `price`），
商品后续改价或下架都不会影响历史订单金额；金额统一用 `Decimal`，不使用浮点。

---

## 接口约定

统一响应体：

```json
{ "code": 0, "message": "ok", "data": {} }
```

`code` 非 0 表示业务失败。子系统链路的关键错误码会额外带上 `reason`，
供 H5 渲染对应的失效文案：

| code | reason | 含义 |
| --- | --- | --- |
| 1001 | `LINK_NOT_FOUND` | 链接不存在 |
| 1002 | `LINK_EXPIRED` | 链接已过期 |
| 1003 | `LINK_EXHAUSTED` | 次数已用尽（含一次性链接） |
| 1004 | `LINK_DISABLED` | 链接已被禁用 |
| 1005 | `LINK_VOIDED` | 链接已作废 |
| 1101 | — | 商品不在本链接授权范围内 |
| 1104 | — | 提交过于频繁（进程内滑动窗口限流） |

主要路由：

- 后台：`/api/admin/auth/login`、`/api/admin/products`、`/api/admin/permission-templates`、
  `/api/admin/temp-links`、`/api/admin/orders`、`/api/admin/exports/{orders,products}`
- 子系统：`/api/portal/catalog?t=<token>`、`/api/portal/orders`

---

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | 数据库连接串（MySQL 或 SQLite） |
| `JWT_SECRET` | JWT 签名密钥，生产必须替换 |
| `JWT_EXPIRE_MINUTES` | 后台登录态有效期（分钟） |
| `PUBLIC_BASE_URL` | 子系统对外访问地址，用于拼完整临时链接；路径前缀方案下需带 `/portal` |
| `CORS_ORIGINS` | 允许的跨域来源，逗号分隔 |
| `PORTAL_RATE_LIMIT_PER_MINUTE` | 同一 token 每分钟允许的提交次数 |

---

## 部署

面向 2 核 2G 裸机（Ubuntu 22.04 / CentOS 7+）的完整步骤见 **[deploy/DEPLOY.md](deploy/DEPLOY.md)**，
包含 MySQL 调优、swap、Nginx、systemd、发布脚本与上线检查清单。

日常发布在本地执行：

```bash
SERVER=root@your-domain.com bash deploy/deploy.sh
```

前端一律在本地构建、只上传 `dist` 产物，不在服务器上跑 Vite。

---

## 页面一览

**主系统（PC 后台）**：登录 · 商品管理 · 权限模板管理 · 临时链接管理 · 订单管理

**子系统（H5）**：授权商品浏览与选品 · 收货信息填写 · 下单结果与失效提示
