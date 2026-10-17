# 2026-10-17 小程序集成排查报告

## 来源与保护

远程仓库 Annika-kiki/shi-lian-app 的所有远程分支已枚举。组员最新提交为 main 的 8c30d1e（2026-10-17 21:35 +0800）；本地已验证快照为 codex/food-quick-log 的 6d66ce7。实际本地 miniprogram-2 与该快照 109 个文件逐字节一致。

原 miniprogram-2 与 shi-lian-app-main 两目录已完整归档，含 Git 元数据和未提交文件；逐文件 SHA-256 与压缩包内容校验通过。所有排查、数据库测试与修复均在独立目录进行；原目录内容校验未发生变化。私有备份、会话数据和环境文件不在提交范围。

## 可复现问题

1. main 根目录 project.config.json 未指定 miniprogramRoot，根 app.json 的 15 个页面、60 个页面文件全部不存在。导入根目录首先会遇到项目结构错误。
2. main/frontend 是可定位完整页面的旧入口，但 utils/api.js 优先请求 10.31.102.222:8001，再回退到 localhost/127.0.0.1；它使用 mock-login 和 X-User-Id，并将单独 userId 缓存视为已登录。另一台电脑或已部署 Bearer 后端均不兼容。隔离模拟明确捕获该请求及模拟生产 401，不能当作真实云端返回。
3. 根 utils/api.js 虽写了正确云环境与服务名，仍发送 X-User-Id、调用 mock-login，且没有 wx.cloud.init。嵌套 utils/utils/api.js 又是重复旧副本，不能把它当作有效修复入口。
4. 组员首页调用 parseFood、quickLogFull，但其 frontend/utils/api.js 没有导出这两个函数。实际执行首页 saveQuickLog 可复现 TypeError: parseFood is not a function。
5. 首页把营养数据当成顶层 protein_g/carbs_g/fat_g，而已部署后端在 nutrition.protein/carb/fat 下返回 consumed/target，造成营养显示错误。自定义底部导航把首页、记录、我的错误指向饮食页。
6. main 后端已经回退到 X-User-Id 认证并移除云登录。对其代码使用隔离 SQLite 的 TestClient 验证：POST /api/auth/cloud-login 返回 404；GET /api/users/me 仅带 Bearer 返回 401，message 为“缺少 X-User-Id；请先调用 mock-login”。这不是对生产服务的测试。main/main.py 还删除了既有生产配置校验、TrustedHost、限流和 food 挂载，且新增假 mock 路由只返回固定用户 1。未采纳这些回退，也未改动生产后端。
7. 当前真实部署的 /api/food/parse 返回 404，不能只补一个前端函数就声称新版食品解析可用。

## 选择与整合

采用本地/6d66ce7 的安全认证、隐私同意、压缩资源和所有非首页页面作为基础，保留组员首页卡片/进度布局与新增“解析—确认—记录”意图。补齐 API 导出、营养结构、餐次选择、同餐热量合计、正确组件导航、取消不写入、双击合并和错误展示；保留运动快速记录及本地昵称称呼。

兼容当前生产版本：解析接口仅在 404 时回退到现有食材库，以数据库每100g营养值换算；只接受一种已收录食材与明确克数（0<g<=3000），不进行未知食物固定估算；确认保存使用既有 /api/meals 的 ingredient_id/amount_g 合同。503/401 等错误不伪装成解析成功。新服务存在 food/parse 时仍保留原有确认记录接口。

增加仓库根项目配置，固定真正入口为 releases/miniprogram-2；排除未引用的导航栏组件和嵌套 styles 副本，其余文件不删除。后端保持 6d66ce7 的既有 Bearer、云注入身份校验及生产保护规则，没有本次后端代码变更。

## 验证结果

- 隔离虚拟环境中的后端 pytest：108 passed，1 条已有依赖弃用警告。
- test_frontend_auth.js 入口更新为运行 cloud 与 release 两套检查，并正确传播失败退出码；避免旧测试桩缺少 user_id、报错却以0退出的问题。
- 新发布版检查通过：隐私未同意零请求、旧/跨环境缓存不跳过登录、并发登录合并、并发401合并重登、最多一次重试、档案字段、食物端点、404兼容换算及既有 meals 合同。
- 首页检查通过：嵌套营养值、同餐多条热量、导航事件、取消不保存、重复点击一次保存、餐次、运动记录、错误提示。
- 发布目录所有 JS/JSON、页面/模块/组件/图片/样式引用及事件绑定检查通过，无本地请求/mock凭据。预计有效文件104个，未压缩原始体积约742 KiB，最大图片52,709字节。最终上传包尺寸以开发者工具为准。
- 开发者工具成功打开独立修正版，默认协议未勾选，无启动自动登录。
- 本次重新用 wx.cloud.callContainer 诊断调用：cloud-login、users/me、dashboard/today、insights/today 均200且code=0；登录返回user_id/access_token存在，仅输出布尔结果；Bearer来自该次登录的闭包，未打印/写入诊断文件。dashboard确认包含nutrition。
- 真实 food/parse：404；真实 ingredients?q=鸡胸肉：200/code=0，返回1条且含 id/name/aliases/calories_kcal_per_100g/protein_g/carb_g/fat_g/unit，支持兼容换算。
- 上述真实调用为独立项目控制台诊断，不等于完整按钮流程端到端通过。

未验证：组员自己的开发者权限/微信账号/网络；所有真机机型；真实档案、饮食和运动写入（刻意不改生产数据）；食品解析新端点的生产部署与未知食品识别；微信审核结果。未运行容器构建、全部迁移和 npm audit。未自动上传、审核、发布或部署。

## 导入与后续

将 releases/miniprogram-2 或仓库根目录导入微信开发者工具，AppID使用已有项目的 wx26dfe00bf5f3258b。组员需具有该AppID开发者权限，不能使用测试AppID调用生产云环境。首先编译；未勾选协议时应无登录/业务请求；自主同意后登录。食材输入示例：鸡胸肉150g。

待确认的新分支：codex/team-cloud-integration-20261017，基于6d66ce7。保留组员main原始提交，不强推、不自动合并main、不将远程回退后端纳入本次修复。逐文件变更清单在 TEAM_INTEGRATION_FILES_20261017.txt。提交和推送必须另获用户确认。
