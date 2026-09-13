# 微信云托管部署运行手册

本手册只描述配置，不授权开通资源、生成密钥、创建版本或切换流量。所有金额以负责人在开通页面看到的实时价格为准。

## 当前环境记录

- 2026-09-05 通过官方 Flask 快速模板初始化首个环境 `prod-d4g1s6f9gaef2c320`。
- 自动创建示例服务 `flask-3xwi`、HTTPS 域名和 MySQL。后续配置截图曾意外包含初始 root 密码，因此该密码必须先重置，且不得用于业务服务。
- 环境 ID 的 `prod-` 前缀是平台自动生成名称。完成真实部署、隔离和验收前，本项目把它视为 staging 候选，而不是正式生产环境。
- 当前域名仍指向官方 Flask 计数器示例，不得写入小程序体验版或正式版配置。

## 服务配置

| 项目 | 建议值 |
| --- | --- |
| 构建目录 | 仓库根目录 |
| Dockerfile | `Dockerfile` |
| 监听端口 | `8001` |
| 健康检查 | `GET /health`，期望 HTTP 200 |
| 日志 | 标准输出，不采集请求体、令牌或密钥 |
| 发布模式 | 手工灰度；禁止选择自动全量切换 |
| 初始流量 | staging 验证完成前不切换现有流量；仅通过版本定向方式验证新版本 |
| 扩缩容 | 首版选择低成本模式，最小实例数 0；最大实例数和费用告警按开通页报价确认 |

监听端口必须同时与 Dockerfile 的 `EXPOSE 8001`、Uvicorn 启动端口和健康检查一致。官方文档指出端口不一致会导致就绪检查失败。

## 环境变量

staging 和 production 分别配置，禁止复制数据库连接串或 `SESSION_SECRET`：

- `APP_ENV=staging` 或 `production`
- `MYSQL_ADDRESS`、`MYSQL_USERNAME`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`（staging 固定为 `shi_lian_staging`，production 固定为独立的 `shi_lian_production`；禁止使用 `root`）
- `CORS_ORIGINS=`（小程序私有链路不使用浏览器 CORS，保持空值；禁止填写 `*`）
- `ALLOWED_HOSTS=实际服务主机名`（不含协议和路径）
- `WECHAT_APP_ID=wx26dfe00bf5f3258b`
- `AUTH_MODE=cloud_headers`
- `WECHAT_CLOUD_ENV_ID`（必须与调用环境完全一致）
- `WECHAT_APP_SECRET` 不用于云托管模式；只有未来切换自建后端和 `wechat_api` 模式时才需要
- `SESSION_SECRET`（每个环境独立，至少32字符）
- `SESSION_TTL_SECONDS=604800`
- `SENSITIVE_RATE_LIMIT_PER_MINUTE=30`
- `DB_POOL_SIZE=2`、`DB_MAX_OVERFLOW=3`、`DB_POOL_TIMEOUT_SECONDS=10`、`DB_POOL_RECYCLE_SECONDS=300`

测试阶段把服务最大实例数设为 1，因此数据库连接上限为每实例最多 5 条。提高最大实例数前，必须按数据库连接容量重新核算 `实例数 × (DB_POOL_SIZE + DB_MAX_OVERFLOW)`。

## 首次 staging 顺序

1. 负责人确认报价、协议和资源开通。
2. 创建独立 staging 环境、数据库和密钥配置。
3. 优先使用模板已注入的 MySQL 内网地址验证连接；只有无法连通时才配置“对接 VPC”。“公网出口”是容器主动访问互联网的出口，不是小程序访问入口，本项目不需要，保持关闭。外网数据库直连只允许临时调试且用后立即关闭。
4. 从经负责人确认推送的固定 Git 提交构建仓库根目录 `Dockerfile`，发布模式选择“手工灰度”。创建失败时保留旧版本，不切换现有流量。
5. 通过版本定向方式检查 FastAPI `/health`、启动日志和数据库连通性；确认健康后关闭公网访问，仅保留小程序 `wx.cloud.callContainer` 调用。公网访问未关闭时不得启用 `cloud_headers` 登录。
6. 使用独立迁移账号执行 `sh scripts/migrate_staging.sh`；脚本拒绝 production、非 `shi_lian_staging` 数据库和非 `shi_lian_migrator` 账号。运行时应用账号只授予业务表必要权限，不使用 `root`。
7. 配置小程序体验版，使用两个真实微信账号验证云身份隔离、注销和核心业务回归。
8. 执行一次加密逻辑备份和隔离恢复演练。

平台配置依据：[部署方式](https://docs.cloudbase.net/run/deploy/deploy/introduce)、[手工灰度](https://docs.cloudbase.net/run/deploy/deploy/gray-release)、[容器端口](https://docs.cloudbase.net/run/deploy/configuring/environment/containers)、[小程序调用云托管](https://docs.cloudbase.net/run/develop/access/mini)、[服务公网开关](https://docs.cloudbase.net/run/deploy/service-setting)、[MySQL 集成](https://docs.cloudbase.net/run/develop/resource-integration/mysql)。

注意区分两个开关：服务设置中的“公网访问”是入站域名，完成健康检查后应关闭；版本配置中的“公网出口”是容器出站能力，本项目不需要。`wx.cloud.callContainer` 不依赖公网访问。

## production 提升

production 使用同一已验证 Git 提交重新构建，单独配置数据库和会话密钥。先完成迁移、种子、健康检查和零流量冒烟，再由负责人确认流量切换。不得把 staging 数据复制为正式用户数据。

## 回滚

保留上一稳定容器版本。应用异常时由负责人确认后把流量切回上一版本；数据库结构优先采用向前修复。涉及生产数据恢复时必须另行确认，并先在隔离数据库验证备份。
