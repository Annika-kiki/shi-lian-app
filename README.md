# 练食记

微信小程序「练食记」的 UI 素材与后端 MVP。后端提供饮食记录、食谱、训练、体重和统计接口；本地不依赖付费服务。

## 快速启动

需要 Python 3.10+。在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

首次启动自动创建 SQLite 数据库 `shi_lian.db` 并写入动作、食材和三份基础食谱；也可执行 `python -m backend.database.seed`。接口文档：<http://127.0.0.1:8001/docs>，健康检查：`GET /health`。将 `DATABASE_URL` 换为 SQLAlchemy 兼容的 MySQL URL 即可迁移数据库。

## 本地登录与鉴权

调用 `POST /api/auth/mock-login`，如 `{"nickname":"小练","mock_openid":"dev-xiaolian"}`；响应中的 `user_id` 用于后续 Header：`X-User-Id: <user_id>`。微信登录环境变量 `WECHAT_APP_ID`、`WECHAT_APP_SECRET` 已预留，真实 code 换取流程待小程序凭据配置后接入，仓库不会保存密钥。

## 测试

```bash
pytest backend/tests -q
```

覆盖资料更新、同日体重更新、食材克数营养计算、训练完成 MET 消耗和首页汇总。

## API 概览

所有业务响应均为 `{ "code": 0, "message": "ok", "data": ... }`，个人资源按 `X-User-Id` 隔离。

| 模块 | 接口 |
| --- | --- |
| 认证/用户 | `POST /api/auth/mock-login`、`POST /api/auth/wechat-login`、`GET /api/users/me`、`PUT /api/users/me/profile`、`POST/GET /api/users/me/weights` |
| 首页/统计 | `GET /api/dashboard/today`、`GET /api/stats/calendar`、`GET /api/stats/monthly`、`GET /api/stats/body-trend` |
| 饮食 | 食材、食谱、规则生成、餐食 CRUD、食谱收藏 |
| 训练 | 动作、动作收藏、推荐训练、session/set 创建更新和完成 |

完成训练时，具备时长和训练组则以 `MET × 3.5 × 体重 / 200 × 时长` 计算消耗；否则返回 0 并标识为估算。餐食营养均由食材每 100g 数据及实际克数计算。

## 前端对接顺序

1. `mock-login` 后保存 `user_id` 并携带 `X-User-Id`。
2. 资料、体重接口完成建档。
3. 首页、食材搜索、食谱详情和餐食记录打通饮食闭环。
4. 动作列表、推荐训练、session/set 与完成接口。
5. 日历、月统计和身体趋势。
