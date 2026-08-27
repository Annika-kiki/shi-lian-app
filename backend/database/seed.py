from backend.database.session import Base, engine, SessionLocal
from backend.models.entities import Exercise, Ingredient, Recipe, RecipeIngredient, RecipeStep


FOODS = [
    ("鸡胸肉", "鸡胸,鸡肉", 133, 24.6, 0, 5.0),
    ("西兰花", "花椰菜", 36, 4.1, 4.3, 0.6),
    ("糙米饭", "糙米", 116, 2.6, 25.9, 0.9),
    ("鸡蛋", "蛋", 144, 13.3, 2.8, 8.8),
    ("燕麦", "燕麦片", 367, 15, 61, 7),
    ("香蕉", "", 93, 1.4, 22, 0.2),
    ("三文鱼", "鲑鱼", 208, 20, 0, 13),
    ("红薯", "地瓜", 86, 1.6, 20.1, 0.1),
    ("橄榄油", "", 884, 0, 0, 100),
    ("生菜", "", 15, 1.4, 2.9, 0.2),
]


EXTRA_FOODS = [
    ("鸡腿肉", "鸡腿,鸡肉", 177, 18.0, 0, 11.0),
    ("牛肉", "瘦牛肉", 250, 26.0, 0, 15.0),
    ("三文鱼", "鲑鱼", 208, 20.0, 0, 13.0),
    ("虾仁", "虾,海虾", 99, 24.0, 0, 0.3),
    ("北豆腐", "豆腐,老豆腐", 80, 8.0, 2.0, 4.0),
    ("嫩豆腐", "内酯豆腐,绢豆腐", 56, 5.3, 2.0, 3.0),
    ("金枪鱼", "吞拿鱼", 132, 29.0, 0.0, 1.0),
    ("无糖酸奶", "酸奶", 62, 3.5, 4.7, 2.5),
    ("牛奶", "纯牛奶", 52, 3.2, 5.0, 1.5),
    ("糙米饭", "糙米", 111, 2.6, 23.0, 0.9),
    ("杂粮饭", "杂粮", 118, 3.0, 24.0, 0.9),
    ("荞麦面", "荞麦", 99, 3.4, 21.4, 1.0),
    ("全麦面包", "全麦吐司", 247, 13.0, 41.0, 4.2),
    ("南瓜", "贝贝南瓜", 26, 1.0, 6.5, 0.1),
    ("土豆", "马铃薯", 77, 2.0, 17.0, 0.1),
    ("玉米", "甜玉米", 106, 3.4, 21.0, 1.2),
    ("菠菜", "", 23, 2.9, 3.6, 0.4),
    ("生菜", "", 15, 1.4, 2.9, 0.2),
    ("番茄", "西红柿", 18, 0.9, 3.9, 0.2),
    ("黄瓜", "", 16, 0.7, 3.6, 0.1),
    ("胡萝卜", "", 41, 0.9, 9.6, 0.2),
    ("香菇", "蘑菇", 34, 2.2, 6.8, 0.5),
    ("金针菇", "", 37, 2.7, 7.8, 0.3),
    ("洋葱", "", 40, 1.1, 9.3, 0.1),
    ("菜花", "花菜", 25, 2.0, 4.9, 0.3),
    ("青椒", "彩椒", 22, 0.9, 4.6, 0.2),
    ("茄子", "", 25, 1.0, 5.7, 0.2),
    ("芹菜", "", 16, 0.7, 3.0, 0.2),
    ("白菜", "", 12, 1.1, 2.2, 0.2),
    ("芦笋", "", 20, 2.2, 3.9, 0.1),
    ("小白菜", "", 13, 1.5, 1.7, 0.2),
    ("娃娃菜", "", 12, 1.0, 2.0, 0.1),
    ("秋葵", "", 33, 2.0, 7.0, 0.2),
    ("西葫芦", "", 17, 1.2, 3.1, 0.1),
    ("橄榄油", "", 884, 0, 0, 100),
    ("芝麻油", "", 899, 0, 0, 100),
    ("花生油", "", 884, 0, 0, 100),
    ("菜籽油", "", 884, 0, 0, 100),
]

RECIPES = [
    {
        "name": "香煎鸡胸糙米碗",
        "description": "高蛋白快手午餐",
        "minutes": 20,
        "tags": "高蛋白,少油",
        "ingredients": [("鸡胸肉", 180), ("糙米饭", 180), ("西兰花", 150), ("橄榄油", 5)],
        "steps": [
            "糙米饭加热备用。",
            "鸡胸肉煎熟后切片。",
            "西兰花焯水后与鸡胸肉一起装碗即可。",
        ],
    },
    {
        "name": "香蕉燕麦鸡蛋碗",
        "description": "适合早餐的饱腹组合",
        "minutes": 10,
        "tags": "高蛋白,15分钟内",
        "ingredients": [("燕麦", 50), ("香蕉", 100), ("鸡蛋", 100)],
        "steps": [
            "燕麦用热水泡软。",
            "鸡蛋煮熟切块。",
            "与香蕉一起装碗。",
        ],
    },
    {
        "name": "三文鱼红薯沙拉",
        "description": "优质脂肪与复合碳水",
        "minutes": 25,
        "tags": "少油,高蛋白",
        "ingredients": [("三文鱼", 150), ("红薯", 200), ("生菜", 100), ("橄榄油", 5)],
        "steps": [
            "红薯蒸熟切块。",
            "三文鱼煎至熟透。",
            "和生菜混合，淋少量橄榄油。",
        ],
    },
]


EXTRA_RECIPES = [
    {
        "name": "番茄鸡胸荞麦面",
        "description": "酸甜清爽的高蛋白主食碗",
        "minutes": 18,
        "tags": "高蛋白,均衡",
        "ingredients": [("鸡胸肉", 150), ("番茄", 200), ("荞麦面", 120), ("橄榄油", 3)],
        "steps": [
            "荞麦面先煮熟过凉。",
            "鸡胸肉煎熟切片，番茄炒出汁。",
            "把面和鸡胸肉拌入番茄酱汁即可。",
        ],
    },
    {
        "name": "三文鱼烤盘蔬菜",
        "description": "烤箱一盘搞定的低脂晚餐",
        "minutes": 25,
        "tags": "低脂,少油",
        "ingredients": [("三文鱼", 140), ("菜花", 180), ("胡萝卜", 120), ("橄榄油", 4)],
        "steps": [
            "三文鱼和蔬菜切好后平铺在烤盘里。",
            "撒盐、黑胡椒和少量橄榄油。",
            "烤至表面微焦后直接出炉。",
        ],
    },
    {
        "name": "虾仁蒸蛋碗",
        "description": "嫩滑又快手的蒸制搭配",
        "minutes": 15,
        "tags": "快手,清爽",
        "ingredients": [("虾仁", 120), ("鸡蛋", 120), ("白菜", 120), ("芝麻油", 2)],
        "steps": [
            "鸡蛋打散加温水，先蒸到半凝固。",
            "放入虾仁和白菜继续蒸熟。",
            "出锅后淋少量芝麻油即可。",
        ],
    },
    {
        "name": "牛肉土豆焖锅",
        "description": "更有饱足感的焖煮主菜",
        "minutes": 28,
        "tags": "饱足,高蛋白",
        "ingredients": [("牛肉", 140), ("土豆", 160), ("洋葱", 80), ("花生油", 4)],
        "steps": [
            "牛肉先煎香，土豆和洋葱切块备用。",
            "加入少量热水，小火焖煮到土豆软糯。",
            "收汁后出锅，风味更浓郁。",
        ],
    },
    {
        "name": "豆腐菌菇汤",
        "description": "适合夜间补一碗的清汤",
        "minutes": 20,
        "tags": "清爽,少油",
        "ingredients": [("北豆腐", 180), ("香菇", 120), ("金针菇", 100), ("芝麻油", 2)],
        "steps": [
            "香菇和金针菇先煮出鲜味。",
            "加入豆腐块，小火煮几分钟。",
            "最后淋少量芝麻油，清汤就完成了。",
        ],
    },
]

EXERCISES = [
    {
        "name": "杠铃卧推",
        "body_part": "胸部",
        "primary_muscle": "胸大肌",
        "secondary_muscle": "肱三头肌",
        "equipment": "杠铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/barbell-bench-press.png",
        "steps": "躺稳，肩胛后收，缓慢下放到胸口上方，再推起。",
        "cautions": "保持肩胛稳定，动作全程受控。",
        "met": 6.0,
    },
    {
        "name": "俯卧撑",
        "body_part": "胸部",
        "primary_muscle": "胸大肌",
        "secondary_muscle": "肱三头肌",
        "equipment": "徒手",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/barbell-bench-press.png",
        "steps": "身体成直线，屈肘下放后推起。",
        "cautions": "腰背不要塌陷。",
        "met": 5.0,
    },
    {
        "name": "上斜哑铃卧推",
        "body_part": "胸部",
        "primary_muscle": "上胸",
        "secondary_muscle": "肱三头肌",
        "equipment": "哑铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/incline-dumbbell-press.png",
        "steps": "上斜板稳定身体，哑铃下放到胸上方，再向上推起。",
        "cautions": "双手轨迹保持一致，避免耸肩。",
        "met": 6.0,
    },
    {
        "name": "高位下拉",
        "body_part": "背部",
        "primary_muscle": "背阔肌",
        "secondary_muscle": "肱二头肌",
        "equipment": "器械",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/lat-pulldown.png",
        "steps": "下拉至锁骨附近，再控制还原。",
        "cautions": "避免借力后仰。",
        "met": 5.0,
    },
    {
        "name": "坐姿划船",
        "body_part": "背部",
        "primary_muscle": "背阔肌",
        "secondary_muscle": "菱形肌",
        "equipment": "器械",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/seated-cable-row.png",
        "steps": "挺胸坐稳，向后拉到腹部附近，再缓慢回位。",
        "cautions": "不要含胸猛拉。",
        "met": 5.0,
    },
    {
        "name": "哑铃单臂划船",
        "body_part": "背部",
        "primary_muscle": "背阔肌",
        "secondary_muscle": "斜方肌",
        "equipment": "哑铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/seated-cable-row.png",
        "steps": "一手支撑，哑铃向髋部上拉。",
        "cautions": "保持躯干稳定，避免扭转。",
        "met": 5.5,
    },
    {
        "name": "哑铃侧平举",
        "body_part": "肩部",
        "primary_muscle": "三角肌中束",
        "secondary_muscle": "斜方肌",
        "equipment": "哑铃",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/dumbbell-lateral-raise.png",
        "steps": "手臂微屈向两侧抬起，到肩高后缓慢放下。",
        "cautions": "不要用惯性甩动。",
        "met": 4.5,
    },
    {
        "name": "哑铃推举",
        "body_part": "肩部",
        "primary_muscle": "三角肌前束",
        "secondary_muscle": "肱三头肌",
        "equipment": "哑铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/dumbbell-lateral-raise.png",
        "steps": "双手托举哑铃，从肩部向上推起。",
        "cautions": "核心收紧，避免腰部后仰。",
        "met": 5.0,
    },
    {
        "name": "哑铃弯举",
        "body_part": "手臂",
        "primary_muscle": "肱二头肌",
        "secondary_muscle": "前臂",
        "equipment": "哑铃",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/barbell-bench-press.png",
        "steps": "手肘夹紧身体，弯曲手臂将哑铃卷起。",
        "cautions": "上臂保持稳定，不要甩肩。",
        "met": 4.5,
    },
    {
        "name": "窄距俯卧撑",
        "body_part": "手臂",
        "primary_muscle": "肱三头肌",
        "secondary_muscle": "胸大肌",
        "equipment": "徒手",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/barbell-bench-press.png",
        "steps": "双手间距略窄，屈肘下放后推起。",
        "cautions": "手肘不要外展太多。",
        "met": 5.0,
    },
    {
        "name": "深蹲",
        "body_part": "腿部",
        "primary_muscle": "股四头肌",
        "secondary_muscle": "臀大肌",
        "equipment": "杠铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/goblet-squat.png",
        "steps": "屈髋屈膝下蹲后站起。",
        "cautions": "膝盖方向跟随脚尖。",
        "met": 6.0,
    },
    {
        "name": "罗马尼亚硬拉",
        "body_part": "腿部",
        "primary_muscle": "腘绳肌",
        "secondary_muscle": "臀大肌",
        "equipment": "哑铃",
        "difficulty": "中级",
        "thumbnail_url": "/assets/exercises/dumbbell-romanian-deadlift.png",
        "steps": "髋部后移，下放哑铃到小腿中段，再收臀站起。",
        "cautions": "背部保持中立位。",
        "met": 6.0,
    },
    {
        "name": "平板支撑",
        "body_part": "核心",
        "primary_muscle": "腹直肌",
        "secondary_muscle": "臀肌",
        "equipment": "徒手",
        "difficulty": "初级",
        "thumbnail_url": "/assets/exercises/forearm-plank.png",
        "steps": "前臂支撑，身体保持一条直线。",
        "cautions": "不要塌腰或撅臀。",
        "met": 3.5,
    },
]


def _seed_foods(db):
    existing = {item.name for item in db.query(Ingredient).all()}
    for name, aliases, calories, protein, carb, fat in FOODS + EXTRA_FOODS:
        if name in existing:
            continue
        db.add(
            Ingredient(
                name=name,
                aliases=aliases,
                calories_kcal=calories,
                protein_g=protein,
                carb_g=carb,
                fat_g=fat,
            )
        )
        existing.add(name)


def _seed_recipes(db):
    ingredients = {item.name: item for item in db.query(Ingredient).all()}
    existing = {item.name for item in db.query(Recipe).all()}

    for recipe_data in RECIPES + EXTRA_RECIPES:
        if recipe_data["name"] in existing:
            continue
        recipe = Recipe(
            name=recipe_data["name"],
            description=recipe_data["description"],
            minutes=recipe_data["minutes"],
            tags=recipe_data["tags"],
            is_system=True,
        )
        db.add(recipe)
        db.flush()

        for ingredient_name, amount_g in recipe_data["ingredients"]:
            ingredient = ingredients.get(ingredient_name)
            if ingredient:
                db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        amount_g=amount_g,
                    )
                )

        for order_no, content in enumerate(recipe_data["steps"], start=1):
            db.add(RecipeStep(recipe_id=recipe.id, order_no=order_no, content=content))
        existing.add(recipe_data["name"])


def _seed_exercises(db):
    for exercise_data in EXERCISES:
        exercise = db.query(Exercise).filter_by(name=exercise_data["name"]).first()
        if exercise:
            continue
        db.add(Exercise(**exercise_data))


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_foods(db)
        _seed_recipes(db)
        _seed_exercises(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
