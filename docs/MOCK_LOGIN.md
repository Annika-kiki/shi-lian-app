# mock-login 联调契约

本项目已有 POST /api/auth/mock-login，使用现有 SQLAlchemy 会话，按 users.openid 查询或创建用户。请求中的 mock_openid 对应 users.openid，不新增重复身份字段。

请求 Content-Type: application/json：
```json
{"nickname":"练食记用户","avatar":"","mock_openid":"mock_练食记用户"}
```
成功返回 code=0，data 包含真实 user_id、nickname。同时保留 access_token、token_type、expires_in，以兼容现有小程序前端。重复 mock_openid 使用同一用户ID，并更新昵称和头像。省略 nickname 时默认练食记用户；省略 mock_openid 时默认 mock_加昵称。

格式错误返回HTTP400、数据库错误回滚并返回HTTP503，响应为 `{"code":-1,"message":"错误原因"}`。

开发接口仅在 APP_ENV=development 启用。staging/production主动返回HTTP404及说明性错误，这是环境限制，不代表路由缺失。仅根据截图无法确认云托管实际运行的是当前仓库版本，也不能确认真实APP_ENV。

现有请求通过 Authorization: Bearer access_token 验证会话。X-User-Id不作为认证凭证；单凭ID会允许客户端冒充其他用户。现有 frontend/utils/api.js 已保存 accessToken并发送Bearer头，不能把成功响应缩减到仅ID而不同时调整前端。

生产登录应调用现有 /api/auth/wechat-login，配置 WECHAT_APP_ID、WECHAT_APP_SECRET和SESSION_SECRET；云托管可信头模式另有 /api/auth/cloud-login，但当前生产配置验证限制仍须单独审查。mock联调使用隔离开发服务与开发数据库，不能通过把生产APP_ENV改为development来绕过配置校验。

本次只修改本地代码并推送功能分支，不部署云服务、不写入生产数据库。若线上仍404，需核对服务镜像入口、版本和环境配置；本地修复不等于云端已经生效。
