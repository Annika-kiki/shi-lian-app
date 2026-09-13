# 部署与发布

## 分支与版本

- `main`：只保存已验收、可部署的版本。
- `codex/release-readiness`：当前本地上线准备分支。
- 功能和修复通过短期分支进入发布分支。
- 上传前更新 `package.json` 版本号和 `CHANGELOG.md`。
- 未经负责人确认，不推送、合并、创建 PR 或上传微信后台。

## 后端部署

Docker 镜像只安装 `backend/requirements.txt` 中的生产依赖；本地和 CI 使用 `backend/requirements-dev.txt`。微信云托管创建版本时将监听端口明确设置为 `8001`，与 Dockerfile 的 `EXPOSE`、启动命令和健康检查保持一致。平台端口与容器真实端口不一致会导致就绪检查失败。

1. CI 执行 `sh scripts/verify.sh`。
2. 构建固定 Python 版本的不可变部署制品。
3. 在 staging 迁移任务中临时注入 `sl_migrator` 凭据并执行 `sh scripts/migrate_staging.sh`；业务服务只注入 `shi_lian_app` 凭据。两者均不得使用 root。
4. 在业务服务注入 `AUTH_MODE=cloud_headers`、AppID、云环境 ID 和独立会话密钥；不创建 AppSecret。
5. 完成健康检查、登录、权限隔离、注销和核心业务回归。
6. 负责人验收后，将同一制品提升至 production。
7. production 仅更换环境配置，不重新构建源码。

生产服务启动时不会自动建表或写入种子数据，部署必须先成功完成迁移。已有数据库首次纳入迁移管理时，应先备份并核对结构，再由负责人确认执行 `alembic stamp 0001`；不可直接假定结构一致。

CloudBase MySQL 的连接串使用 `mysql+pymysql://用户:URL编码后的密码@主机:端口/数据库名?charset=utf8mb4`。密码必须先做 URL 编码，且完整连接串只能放在平台密钥/环境变量中，不能写入仓库、截图或构建日志。首次部署顺序为：创建独立 staging 数据库 → 从受控终端执行迁移和种子 → 发布零流量 staging 版本 → 健康检查通过后再做真实登录回归。生产环境重复相同步骤，但不得复用 staging 数据库或密钥。

应用对登录和食谱生成接口提供基础的单实例限流。生产入口还必须在云网关设置独立的 IP/QPS 限流、最大实例数和费用告警；应用内限流不能替代网关级保护。

## 小程序上传

上传使用 `miniprogram-ci`。私钥路径只通过环境变量提供，不进入仓库：

```bash
WECHAT_APP_ID=wx26dfe00bf5f3258b \
MINIPROGRAM_PRIVATE_KEY_PATH=/secure/path/private.key \
RELEASE_DESCRIPTION="本次变更摘要" \
CONFIRM_WECHAT_UPLOAD=yes \
npm run upload:wechat
```

缺少负责人当次确认时不得设置 `CONFIRM_WECHAT_UPLOAD=yes`。上传成功不代表自动提交审核或发布。

`miniprogram-ci` 仅是开发/发布工具，不会进入小程序包或后端运行环境。其依赖树含有上游遗留安全告警，因此只在隔离的 CI 发布任务中安装和运行，不在生产服务器常驻。升级前必须用 staging 重新验证上传产物，禁止盲目执行 `npm audit fix` 改写依赖树。

## 回滚

- 应用回滚：将流量切回上一份已验证制品。
- 数据库回滚：优先使用向前修复迁移；涉及破坏性逆向迁移时先恢复到隔离环境验证。
- 小程序回滚：按微信后台当时提供的版本能力操作，并由负责人确认。
- 回滚后保留故障现场日志，记录时间线、影响和修复动作。
