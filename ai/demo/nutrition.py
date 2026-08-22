"""Small, auditable nutrition database and calculator.

Values are approximate nutrients per 100 g edible portion. In production,
replace this table with a licensed/authoritative food composition dataset.
"""

FOODS = {
    "鸡胸肉": {"kcal": 133, "protein": 24.6, "carbs": 0.0, "fat": 3.3},
    "鸡蛋": {"kcal": 144, "protein": 13.3, "carbs": 2.8, "fat": 8.8},
    "西红柿": {"kcal": 15, "protein": 0.9, "carbs": 3.3, "fat": 0.2},
    "西兰花": {"kcal": 36, "protein": 4.1, "carbs": 4.3, "fat": 0.6},
    "牛肉": {"kcal": 125, "protein": 19.9, "carbs": 0.0, "fat": 4.2},
    "虾仁": {"kcal": 93, "protein": 18.6, "carbs": 2.8, "fat": 0.8},
    "三文鱼": {"kcal": 139, "protein": 17.2, "carbs": 0.0, "fat": 7.8},
    "豆腐": {"kcal": 84, "protein": 6.6, "carbs": 3.4, "fat": 5.3},
    "米饭": {"kcal": 116, "protein": 2.6, "carbs": 25.9, "fat": 0.3},
    "燕麦": {"kcal": 338, "protein": 10.1, "carbs": 61.6, "fat": 6.1},
    "红薯": {"kcal": 61, "protein": 0.7, "carbs": 15.3, "fat": 0.2},
    "土豆": {"kcal": 81, "protein": 2.6, "carbs": 17.8, "fat": 0.2},
    "玉米": {"kcal": 112, "protein": 4.0, "carbs": 22.8, "fat": 1.2},
    "菠菜": {"kcal": 28, "protein": 2.6, "carbs": 4.5, "fat": 0.3},
    "生菜": {"kcal": 12, "protein": 1.3, "carbs": 2.1, "fat": 0.3},
    "黄瓜": {"kcal": 16, "protein": 0.8, "carbs": 2.9, "fat": 0.2},
    "胡萝卜": {"kcal": 32, "protein": 1.0, "carbs": 7.7, "fat": 0.2},
    "蘑菇": {"kcal": 20, "protein": 2.7, "carbs": 4.1, "fat": 0.1},
    "牛奶": {"kcal": 54, "protein": 3.0, "carbs": 3.4, "fat": 3.2},
    "酸奶": {"kcal": 72, "protein": 2.5, "carbs": 9.3, "fat": 2.7},
    "香蕉": {"kcal": 93, "protein": 1.4, "carbs": 22.0, "fat": 0.2},
    "橄榄油": {"kcal": 899, "protein": 0.0, "carbs": 0.0, "fat": 99.9},
    "鸡腿肉": {"kcal": 181, "protein": 16.0, "carbs": 0.0, "fat": 13.0},
    "猪里脊": {"kcal": 155, "protein": 20.2, "carbs": 0.7, "fat": 7.9},
    "鳕鱼": {"kcal": 88, "protein": 20.4, "carbs": 0.0, "fat": 0.5},
    "金枪鱼": {"kcal": 99, "protein": 23.5, "carbs": 0.0, "fat": 0.6},
    "毛豆": {"kcal": 131, "protein": 13.1, "carbs": 10.5, "fat": 5.0},
    "鹰嘴豆": {"kcal": 164, "protein": 8.9, "carbs": 27.4, "fat": 2.6},
    "黑豆": {"kcal": 337, "protein": 21.6, "carbs": 62.4, "fat": 1.4},
    "藜麦": {"kcal": 120, "protein": 4.4, "carbs": 21.3, "fat": 1.9},
    "糙米饭": {"kcal": 111, "protein": 2.6, "carbs": 23.0, "fat": 0.9},
    "全麦面包": {"kcal": 246, "protein": 9.9, "carbs": 46.0, "fat": 3.4},
    "荞麦面": {"kcal": 99, "protein": 5.1, "carbs": 21.4, "fat": 0.1},
    "南瓜": {"kcal": 23, "protein": 0.7, "carbs": 5.3, "fat": 0.1},
    "紫薯": {"kcal": 82, "protein": 1.9, "carbs": 17.6, "fat": 0.2},
    "芦笋": {"kcal": 22, "protein": 2.4, "carbs": 4.1, "fat": 0.2},
    "彩椒": {"kcal": 26, "protein": 1.0, "carbs": 6.0, "fat": 0.2},
    "洋葱": {"kcal": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1},
    "卷心菜": {"kcal": 24, "protein": 1.5, "carbs": 4.6, "fat": 0.2},
    "菜花": {"kcal": 24, "protein": 2.1, "carbs": 4.6, "fat": 0.2},
    "秋葵": {"kcal": 25, "protein": 1.8, "carbs": 6.2, "fat": 0.2},
    "海带": {"kcal": 13, "protein": 1.2, "carbs": 2.1, "fat": 0.1},
    "木耳": {"kcal": 27, "protein": 1.5, "carbs": 6.0, "fat": 0.2},
    "牛油果": {"kcal": 171, "protein": 2.0, "carbs": 7.4, "fat": 15.3},
    "苹果": {"kcal": 53, "protein": 0.4, "carbs": 13.7, "fat": 0.2},
    "蓝莓": {"kcal": 57, "protein": 0.7, "carbs": 14.5, "fat": 0.3},
    "草莓": {"kcal": 32, "protein": 1.0, "carbs": 7.1, "fat": 0.2},
    "橙子": {"kcal": 48, "protein": 0.8, "carbs": 11.1, "fat": 0.2},
    "无糖豆浆": {"kcal": 31, "protein": 3.0, "carbs": 1.2, "fat": 1.6},
    "希腊酸奶": {"kcal": 73, "protein": 9.0, "carbs": 4.0, "fat": 2.0},
    "低脂牛奶": {"kcal": 43, "protein": 3.4, "carbs": 5.0, "fat": 1.0},
    "杏仁": {"kcal": 578, "protein": 21.3, "carbs": 20.0, "fat": 50.6},
    "花生酱": {"kcal": 600, "protein": 25.0, "carbs": 20.0, "fat": 50.0},
    "芝麻油": {"kcal": 898, "protein": 0.0, "carbs": 0.0, "fat": 99.8},
}

ALIASES = {
    "番茄": "西红柿", "圣女果": "西红柿", "鸡肉": "鸡胸肉",
    "鸡胸": "鸡胸肉", "蛋": "鸡蛋", "西蓝花": "西兰花",
    "白米饭": "米饭", "米": "米饭", "红萝卜": "胡萝卜",
    "鸡腿": "鸡腿肉", "里脊肉": "猪里脊", "猪里脊肉": "猪里脊",
    "吞拿鱼": "金枪鱼", "花椰菜": "菜花",
    "包菜": "卷心菜", "圆白菜": "卷心菜", "甜椒": "彩椒",
    "牛油果果肉": "牛油果", "原味希腊酸奶": "希腊酸奶",
    "豆奶": "无糖豆浆", "全麦吐司": "全麦面包",
}


def normalize_food(name):
    cleaned = str(name).strip()
    return ALIASES.get(cleaned, cleaned)


def calculate(items):
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    details = []
    for item in items:
        name = normalize_food(item["name"])
        grams = float(item["grams"])
        if name not in FOODS:
            raise ValueError(f"营养数据库暂不支持：{name}")
        if grams <= 0 or grams > 2000:
            raise ValueError(f"{name} 的克数不合理")
        nutrients = {key: FOODS[name][key] * grams / 100 for key in totals}
        for key, value in nutrients.items():
            totals[key] += value
        details.append({"name": name, "grams": round(grams, 1),
                        "nutrition": {k: round(v, 1) for k, v in nutrients.items()}})
    return {
        "items": details,
        "totals": {k: round(v, 1) for k, v in totals.items()},
        "source": "本地食物营养表（每100g数据 × 实际克数）",
    }
