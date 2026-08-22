"""Recipe generation with real dish structures, not generic ingredient bowls."""

from nutrition import FOODS, normalize_food, calculate

PROTEINS = ["鸡胸肉", "鸡腿肉", "牛肉", "猪里脊", "虾仁", "三文鱼", "鳕鱼", "金枪鱼", "鸡蛋", "豆腐", "毛豆", "鹰嘴豆"]
CARBS = ["米饭", "糙米饭", "藜麦", "燕麦", "红薯", "紫薯", "土豆", "玉米", "全麦面包", "荞麦面", "南瓜"]
VEGETABLES = ["西红柿", "西兰花", "菠菜", "生菜", "黄瓜", "胡萝卜", "蘑菇", "芦笋", "彩椒", "洋葱", "卷心菜", "菜花", "秋葵", "海带", "木耳"]
DEFAULT_GRAMS = {
    "鸡胸肉": 150, "牛肉": 150, "虾仁": 160, "三文鱼": 150, "鸡蛋": 100,
    "豆腐": 180, "米饭": 150, "燕麦": 45, "红薯": 180, "土豆": 180,
    "玉米": 150, "西红柿": 200, "西兰花": 180, "菠菜": 150,
    "生菜": 150, "黄瓜": 180, "胡萝卜": 120, "蘑菇": 150, "橄榄油": 5,
    "鸡腿肉": 150, "猪里脊": 150, "鳕鱼": 180, "金枪鱼": 150,
    "毛豆": 150, "鹰嘴豆": 150, "糙米饭": 150, "藜麦": 150,
    "全麦面包": 80, "荞麦面": 180, "南瓜": 220, "紫薯": 180,
    "芦笋": 160, "彩椒": 150, "洋葱": 100, "卷心菜": 180,
    "菜花": 180, "秋葵": 160, "海带": 120, "木耳": 100,
}


def _supported(names):
    result = []
    for raw in names:
        name = normalize_food(raw)
        if name in FOODS and name not in result:
            result.append(name)
    return result


def _portion(items, target_kcal, preferences):
    portions = [{"name": name, "grams": DEFAULT_GRAMS[name]} for name in items]
    if "少油" not in preferences:
        portions.append({"name": "橄榄油", "grams": 5})
    current = calculate(portions)["totals"]["kcal"]
    adjustable = next((x for x in items if x in CARBS), items[0])
    delta = target_kcal - current
    for item in portions:
        if item["name"] == adjustable:
            item["grams"] = round(min(350, max(60, item["grams"] + delta / (FOODS[adjustable]["kcal"] / 100))))
    return portions, calculate(portions)


def _recipe(title, style, items, target_kcal, preferences, seasonings, steps, tip):
    portions, nutrition = _portion(items, target_kcal, preferences)
    gram_map = {x["name"]: x["grams"] for x in portions}
    formatted_steps = [step.format(**gram_map) for step in steps]
    return {
        "name": title,
        "style": style,
        "description": tip,
        "estimated_minutes": 25,
        "preferences": preferences,
        "ingredients": nutrition["items"],
        "seasonings": seasonings,
        "steps": formatted_steps,
        "nutrition": nutrition["totals"],
        "nutrition_source": nutrition["source"],
        "chef_tip": tip,
    }


def _templates(selected, target, preferences):
    protein = next((x for x in selected if x in PROTEINS), "鸡蛋")
    carb = next((x for x in selected if x in CARBS), None)
    veg = [x for x in selected if x in VEGETABLES]
    first_veg = veg[0] if veg else "西兰花"
    second_veg = veg[1] if len(veg) > 1 else ("蘑菇" if first_veg != "蘑菇" else "胡萝卜")
    base_items = list(dict.fromkeys([protein, first_veg, second_veg] + ([carb] if carb else [])))

    options = []
    if protein in ("鸡胸肉", "鸡腿肉", "牛肉", "猪里脊"):
        options.append(_recipe(
            f"黑椒蒜香{protein}配焦香{first_veg}", "煎烤",
            base_items, target, preferences,
            ["生抽 1 勺", "蒜末 1 瓣", "黑胡椒", "少量蜂蜜或代糖", "柠檬汁/醋 1 茶匙"],
            [f"{protein}逆纹切片，用生抽、蒜末、黑胡椒和少量蜂蜜腌 10 分钟。",
             f"平底锅烧热，将{protein}铺开煎至两面焦香后盛出，不要反复翻动。",
             f"原锅下{first_veg}和{second_veg}，加一小勺水焖 2 分钟，再大火收干。",
             f"食材回锅，沿锅边淋柠檬汁或醋；{('配上'+carb+'装盘。') if carb else '收汁后装盘。'}"],
            "先煎出焦香，再用酸味收尾；比水煮鸡胸更香，也不需要很多油。"))
        options.append(_recipe(
            f"韩式微辣{protein}拌饭", "韩式拌饭",
            base_items, target, preferences,
            ["韩式辣酱 1 茶匙", "生抽 1 茶匙", "米醋 1 茶匙", "蒜末", "熟芝麻"],
            [f"把{protein}切小块，用生抽、蒜末和半勺辣酱抓匀。",
             f"{first_veg}和{second_veg}分别快速炒熟，保留一点脆度。",
             f"{protein}煎至边缘微焦，加入剩余辣酱和米醋裹匀。",
             f"将所有食材铺在{carb or '蔬菜底'}上，撒熟芝麻；吃前拌匀。"],
            "辣酱只用少量，靠米醋提亮味道，口感比普通健身餐丰富。"))
    elif protein in ("虾仁", "三文鱼", "鳕鱼", "金枪鱼"):
        options.append(_recipe(
            f"柠檬香草{protein}暖沙拉", "地中海风",
            base_items, target, preferences,
            ["柠檬汁 1 勺", "蒜末", "黑胡椒", "欧芹/香菜", "盐少许"],
            [f"{protein}擦干，加黑胡椒、蒜末和少许盐腌 8 分钟。",
             f"{first_veg}与{second_veg}煎至边缘上色，盛入盘中。",
             f"{protein}煎熟后离火，挤入柠檬汁并撒香草。",
             f"与{carb or '蔬菜'}组合装盘，把锅里的柠檬汁淋在表面。"],
            "把柠檬放在离火后加入，香气更清新，也不会发苦。"))
    else:
        options.append(_recipe(
            f"日式照烧{protein}蔬菜卷", "日式",
            base_items, target, preferences,
            ["生抽 1 勺", "米醋 1 茶匙", "蜂蜜/代糖少许", "姜末", "熟芝麻"],
            [f"生抽、米醋、姜末和少量蜂蜜调成轻照烧汁。",
             f"{protein}煎至定型，倒入一半酱汁，小火裹匀。",
             f"{first_veg}和{second_veg}快速炒熟，保持脆嫩。",
             f"用蔬菜包裹{protein}，或与{carb or '蔬菜'}一起装盘，淋剩余酱汁。"],
            "酸甜咸平衡的轻照烧汁，能让豆腐或鸡蛋也有完整菜品感。"))

    options.append(_recipe(
        f"番茄香料{protein}焖菜", "一锅料理",
        list(dict.fromkeys([protein, "西红柿", second_veg] + ([carb] if carb else []))),
        target, preferences,
        ["蒜末", "生抽 1 茶匙", "黑胡椒", "辣椒粉/孜然粉可选"],
        [f"{protein}先煎至表面上色，盛出备用。",
         "西红柿切丁炒至出汁，加蒜末、黑胡椒和喜欢的香料。",
         f"加入{second_veg}与半碗水，小火焖至酱汁浓稠。",
         f"放回{protein}吸收酱汁；{('最后加入'+carb+'焖热。') if carb else '大火收汁后装盘。'}"],
        "番茄自然形成浓郁酱汁，少油也不会干柴，适合一次多做两份。"))
    return options[:3]


def generate_recipe(ingredients, target_kcal=500, preferences=None):
    if not isinstance(ingredients, list) or not ingredients:
        raise ValueError("请至少输入一种食材")
    if not isinstance(target_kcal, (int, float)) or not 250 <= target_kcal <= 1000:
        raise ValueError("目标热量应在 250–1000 kcal 之间")
    preferences = preferences or []
    selected = _supported(ingredients)
    unsupported = [str(x).strip() for x in ingredients if normalize_food(x) not in FOODS]
    if not selected:
        raise ValueError("输入的食材都不在当前营养数据库中")
    recipes = _templates(selected, target_kcal, preferences)
    return {
        "recipes": recipes,
        "recipe": recipes[0],
        "warnings": (["暂未识别：" + "、".join(unsupported)] if unsupported else []),
    }
