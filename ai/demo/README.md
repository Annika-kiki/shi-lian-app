# 食练周期 — AI 饮食与训练最小可演示版

这是 Day 3–7 中 C 线的可运行交付：

- 输入现有食材、目标热量和饮食偏好
- 程序生成多种真实菜式、调味方案和结构化食谱
- 营养数据由本地数据库按克数计算，不让 AI 猜热量
- 提供网页演示和 JSON API
- 提供动作数据库、动作说明、原创虚影轨迹肌肉高亮图和个性化周训练计划
- 只使用 Python 标准库，无需安装依赖或配置 API Key

## 运行

```bash
python3 server.py
```

浏览器打开 <http://127.0.0.1:8000>。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## API

`POST /api/recipes/generate`

请求示例：

```json
{
  "ingredients": ["鸡胸肉", "西红柿", "鸡蛋", "西兰花"],
  "target_kcal": 500,
  "preferences": ["高蛋白", "少油"]
}
```

返回值包含菜名、食材克数、步骤、营养合计及营养计算来源。
