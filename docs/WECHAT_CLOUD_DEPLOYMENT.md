# 微信云托管部署（2026-10-12）

本路线与传统服务器备案路线并行。此部署分支基于 GitHub main 的 1224958，保留该分支的产品功能，补齐后端部署与身份校验。云端是否成功须以实际构建、迁移和小程序验收结果为准。

## 本次先部署 staging

当前已确认测试数据库 `shi_lian_staging` 及业务账号 `shi_lian_app`、迁移账号 `sl_migrator`。选择 GitHub 分支 `codex/wechat-cloud-deploy-20261012`，端口 8001，Dockerfile 路径 `Dockerfile`，构建根目录为仓库根目录。环境变量参考 `deploy/wechat/env.staging.example`。此模式信任微信注入的身份头，必须关闭服务公网访问。先迁移空数据库及写入参考数据，再发布业务版本。不能仅填写端口就点击发布。正式库仍需独立准备。

本分支未改变组员的前端页面；小程序调用适配仍须独立同步和验收。

## 控制台设置

1. 使用小程序 `wx26dfe00bf5f3258b` 登录微信云托管，确认目标环境及服务。已有体验版配置为 `prod-d4g1s6f9gaef2c320` / `flask-3xwi`，不能据此推断服务目前健康或其数据库可用于正式版。正式版使用独立环境、数据库和会话密钥。
2. 为正式环境创建 `shi_lian_production` MySQL 数据库。业务账户为 `shi_lian_app`，只授予业务所需的数据读写权限；另建迁移账户执行建表与迁移。不要使用容器本地 SQLite 存储用户记录。
3. 新建服务版本，选择本地代码 ZIP 上传，构建目录为 ZIP 根目录，Dockerfile 路径 `Dockerfile`，监听端口 **8001**，健康检查路径 `/health`。版本初次部署保留零流量，数据库迁移完成后再验证及切流量。关闭公网访问，通过微信 `wx.cloud.callContainer` 调用。
4. 参考 `deploy/wechat/env.production.example` 在控制台填写环境变量。`ALLOWED_HOSTS` 填实际网关传入的服务主机名（无协议和路径），`CORS_ORIGINS` 填该服务的 HTTPS origin。必要时从平台服务日志确认 Host；不可用 `*` 替代。会话密钥在本地安全终端生成，例如 `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`，仅保存到平台环境变量。
5. 正式服务保持 `AUTH_MODE=wechat_api`，需要小程序 AppSecret。小程序仍通过云托管发送 `wx.login` 得到的 code，后端验证 code 后签发会话。现有体验版使用 `AUTH_MODE=cloud_headers`，不需要 AppSecret，但必须关闭公网访问并校验 AppID 和环境 ID；本次不改变其认证方式。

`DATABASE_URL` 与 `MYSQL_*` 二选一，前者优先。使用平台自动注入的 MySQL 变量时，必须检查用户名与数据库名，不能依赖默认 root 或默认 `tcb` 数据库。密码及密钥不放入 ZIP、GitHub 或聊天。

## 迁移与发布

在能够访问同一 MySQL 内网的受控任务或平台终端中，临时注入迁移账户连接信息，然后顺序执行：

```sh
python -m alembic upgrade head
python -m backend.database.seed
python -m alembic check
```

迁移账户仅用于此任务，不能作为业务服务的长期凭据。不要在 Docker 构建时执行迁移，也不要在每个业务副本启动时并行迁移。已有库应先备份并核对结构，不要直接 stamp。应用部署模式不自动建表，迁移前健康检查失败是可能的，不能因此切换成 development。

迁移完成后启动版本，确认 `/health` 的数据库检查通过。首次先配置一个实例及较小最大实例数，在控制台设置费用告警与入口限流。云托管收费以控制台为准。

在 `frontend/config/env.js` 的 `CLOUD_SERVICES.release` 同时填正式环境 ID 和服务名，正式小程序即可通过云托管访问。未填写时继续使用原有 HTTPS 域名；只填其中一个会拒绝请求。不要把体验版环境直接填入正式版。开发版仍走本地后端，云端验收使用体验版，正式服务验收前需要把体验版的目标临时指向待验收正式服务，并把该条配置的 `authMode` 改为 `wechat_api`，验收完成后恢复原体验环境及其 `cloud_headers` 模式。

验收项目：真实微信登录、档案保存、饮食记录、训练记录、用户数据隔离、注销账户、容器重启后记录仍存在。通过后再切服务流量及准备小程序上传。上传小程序、提交审核、正式发布是独立步骤，后端部署不会自动完成这些动作。

## 官方参考

- [小程序调用云托管](https://docs.cloudbase.net/run/develop/access/mini)
- [微信云托管介绍及私有协议](https://developer.cloud.tencent.com/article/1866155)
- [端口与部署常见问题](https://cloud.tencent.com/document/product/1243/59521)
