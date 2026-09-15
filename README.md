# 食练周期

「食练周期」是一个把饮食记录、减脂餐生成、训练计划、有氧消耗和周期报告放在一起的微信小程序项目。

## 目录结构

```text
shi-lian-app/
├─ frontend/              微信小程序前端，微信开发者工具导入这个目录
│  ├─ pages/              首页、饮食、训练、报告、我的等页面
│  ├─ components/         小程序公共组件
│  ├─ images/             小程序正在使用的动作图片
│  ├─ styles/             公共样式
│  └─ utils/              前端接口、导航、用户与模拟数据工具
├─ backend/               FastAPI 后端
│  ├─ api/                接口路由
│  ├─ database/           数据库连接、种子数据、动作/食材目录
│  ├─ models/             数据表模型
│  ├─ services/           食谱生成、营养计算等服务
│  └─ tests/              后端自动化测试
├─ ai/demo/               早期 AI/算法原型，供参考和二次整合
├─ docs/ui-reference/     UI 截图和设计参考图
├─ .env.example           后端环境变量示例
└─ README.md
```

已清理的历史文件：

- 旧版重复组件 `frontend/bottom-nav`、`frontend/navigation-bar` 已删除；现在统一使用 `frontend/components/`。
- 旧版重复动作图 `frontend/assets/exercises` 已删除；现在统一使用 `frontend/images/exercises`。
- 根目录和 `ui/` 下的截图已整理到 `docs/ui-reference/`。

## 本地启动

需要 Python 3.10+。在仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Windows PowerShell 可用：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

健康检查：`GET http://127.0.0.1:8001/health`

接口文档：`http://127.0.0.1:8001/docs`

首次启动会自动创建 SQLite 数据库 `shi_lian.db` 并写入食材、食谱、动作和训练目标数据。真实部署时可把 `.env` 中的 `DATABASE_URL` 换成 SQLAlchemy 兼容的 MySQL 或其他数据库地址。

## 小程序联调

1. 先启动后端，确认 `http://127.0.0.1:8001/health` 正常。
2. 用微信开发者工具导入 `frontend` 目录。
3. 开发阶段在微信开发者工具里关闭“校验合法域名”。
4. 模拟器默认访问 `http://127.0.0.1:8001`。
5. 真机调试时，把接口地址换成电脑在同一局域网里的 IP：

```js
wx.setStorageSync("apiBaseUrl", "http://192.168.x.x:8001")
```

小程序会自动使用本地 mock 登录并缓存 `apiUserId`。如果要切换测试用户，清除微信开发者工具里的 `apiUserId` 和 `apiMockOpenid` 缓存即可。

## 后端测试

```bash
pytest backend/tests -q
```

测试覆盖：

- 用户资料、身高体重和营养目标计算
- 食材克数与餐食营养计算
- 食谱生成严格使用用户已有食材
- 有氧输入解析和热量消耗估算
- 首页今日评分、快速记录和周/月报告
- 日历记录从登录日开始统计，未训练日期显示休息日

## API 概览

所有业务响应统一为：

```json
{ "code": 0, "message": "ok", "data": {} }
```

个人数据通过请求头 `X-User-Id` 隔离。

| 模块 | 主要接口 |
| --- | --- |
| 认证/用户 | `POST /api/auth/mock-login`、`POST /api/auth/wechat-login`、`GET /api/users/me`、`PUT /api/users/me/profile` |
| 首页/报告 | `GET /api/dashboard/today`、`GET /api/insights/today`、`GET /api/reports/summary` |
| 饮食 | `GET /api/ingredients`、`POST /api/recipes/generate`、`POST /api/meals`、`GET /api/meals`、`POST /api/quick-log` |
| 训练 | `GET /api/exercises`、`GET /api/training-goals`、`GET /api/workouts/recommendation`、`POST /api/workouts/cardio` |
| 记录统计 | `GET /api/stats/calendar`、`GET /api/stats/monthly`、`GET /api/stats/body-trend` |

## 数据说明

- 食材、菜谱、训练动作、训练目标和有氧处方由后端种子数据统一写入。
- 用户每日可摄入热量会结合资料中的身高、体重、目标和当天训练消耗动态计算。
- 训练消耗优先使用有氧解析结果；力量训练完成时，按 `MET × 3.5 × 体重 / 200 × 时长` 估算。
- 菜谱生成必须只使用用户输入的已有食材；调料只允许基础家用调料。

## 协作约定

- 小程序功能代码放在 `frontend/`。
- 后端接口和数据逻辑放在 `backend/`。
- 原型或实验代码放在 `ai/demo/`，正式功能落地后再整合进 `backend/` 或 `frontend/`。
- 设计截图、竞品截图、页面参考图统一放在 `docs/ui-reference/`。
- 不提交 `.env`、本地数据库、运行日志、微信开发者工具个人配置和临时分析文件。
