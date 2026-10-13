# 饮食快速记录

沿用现有 FastAPI/Uvicorn 容器，Flask 通过 a2wsgi 挂载于 `/api/food`；不另建服务。现有 Dockerfile 监听 `0.0.0.0:8001`，云托管容器端口配置为 8001。`/__tcb_probe__` 返回纯文本 ok；`/health` 检查数据库。

安装：`python -m pip install -r backend/requirements-dev.txt`。
本地启动：`python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001`。
数据库配置继续使用 DATABASE_URL 或 MYSQL_ADDRESS、MYSQL_USERNAME、MYSQL_PASSWORD、MYSQL_DATABASE。不要提交 .env。

迁移：先备份、核对目标数据库，再运行 `python -m alembic upgrade heads`。0003 不删除数据；同名表结构不兼容会停止。重复升级不会重建表。本任务0003直接依赖已提交0001；若工作区还有未提交0002，形成独立迁移分支，upgrade heads会同时应用它。已有0002会处理旧训练组重复数据，部署前须审查。只升级本功能可使用 `python -m alembic upgrade food_quick_log@head`。
导入：`python -m backend.database.import_foods /path/common_foods_356.xlsx --dry-run`，确认后移除 `--dry-run`。工作表 common_foods_356；按名称更新，重复名称或无效行导致整个导入回滚。空宏量营养保持 NULL，解析不完整营养时返回400，不伪造数值。多进程目录缓存最长60秒后刷新，导入进程会立即清理自身缓存。

`POST /api/food/parse` 接收 text；只从 foods 计算已匹配营养，无 AI。未匹配营养是固定占位值。
`GET /api/food/search?q=鸡胸` 返回最多10条。
`POST /api/quick-log` 携带现有 `Authorization: Bearer <token>`；X-User-Id 不作为认证来源，任意客户端ID不会获得访问权限。传入确认字段时保存 meals，同时事务性写入 meal_records 供现有报表汇总；旧 text-only 饮食/运动记录仍保留。确认数据来自用户提交，可修改占位数据；此端点不宣称这些确认值是食物库原值。日期按上海时区，创建时间为UTC。

微信调用：`wx.cloud.callContainer({config:{env:'prod-d4gls6f9gaef2c320'},path:'/api/food/parse',method:'POST',header:{'X-WX-SERVICE':'flask-3xwi','Content-Type':'application/json'},data:{text:'150g鸡胸肉'}})`。确认保存须增加 Authorization。

部署仍需用户在云托管配置数据库、现有微信登录密钥、SESSION_SECRET、允许主机等，核对项目 Settings 中部署数据库命名要求。现有 production 配置使用 wechat_api；不切换到未经验证的客户端身份头。云托管最小实例数设为1。构建并发布镜像、执行迁移和正式导入、验证登录和请求链路均需后续部署授权。本任务不执行这些生产操作。

测试：`DATABASE_URL=sqlite:////tmp/food-tests.db python -m pytest backend/tests`。生产 MySQL 的迁移和 InnoDB/utf8mb4 验证还需在隔离 MySQL 环境执行；SQLite通过不等同于MySQL通过。
