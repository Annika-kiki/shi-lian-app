from backend.database.session import Base, engine, SessionLocal
from backend.models.entities import Exercise, Ingredient, Recipe, RecipeIngredient, RecipeStep


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Ingredient).count(): return
        foods = [
            ("鸡胸肉", "鸡胸,鸡肉", 133, 24.6, 0, 5.0), ("西兰花", "花椰菜", 36, 4.1, 4.3, 0.6),
            ("糙米饭", "糙米", 116, 2.6, 25.9, 0.9), ("鸡蛋", "蛋", 144, 13.3, 2.8, 8.8),
            ("燕麦", "麦片", 367, 15, 61, 7), ("香蕉", "", 93, 1.4, 22, 0.2),
            ("三文鱼", "鲑鱼", 208, 20, 0, 13), ("红薯", "地瓜", 86, 1.6, 20.1, 0.1),
            ("橄榄油", "", 884, 0, 0, 100), ("生菜", "", 15, 1.4, 2.9, 0.2),
        ]
        db.add_all([Ingredient(name=n, aliases=a, calories_kcal=c, protein_g=p, carb_g=carb, fat_g=f) for n,a,c,p,carb,f in foods])
        db.flush(); by_name = {x.name: x for x in db.query(Ingredient).all()}
        data = [
            ("香煎鸡胸糙米碗", "高蛋白快捷午餐", 20, "高蛋白,少油", [("鸡胸肉",180),("糙米饭",180),("西兰花",150),("橄榄油",5)], ["糙米饭加热备用。","鸡胸肉煎熟后切片。","西兰花焯水，全部装碗即可。"]),
            ("香蕉燕麦鸡蛋杯", "适合早餐的饱腹组合", 10, "高蛋白,15分钟内", [("燕麦",50),("香蕉",100),("鸡蛋",100)], ["燕麦用热水泡软。","鸡蛋煮熟切块。","与香蕉一起装杯。"]),
            ("三文鱼红薯沙拉", "优质脂肪与复合碳水", 25, "少油,高蛋白", [("三文鱼",150),("红薯",200),("生菜",100),("橄榄油",5)], ["红薯蒸熟切块。","三文鱼煎至熟透。","和生菜拌匀，淋少量橄榄油。"]),
        ]
        for name, desc, mins, tags, parts, steps in data:
            recipe = Recipe(name=name, description=desc, minutes=mins, tags=tags); db.add(recipe); db.flush()
            db.add_all([RecipeIngredient(recipe_id=recipe.id, ingredient_id=by_name[n].id, amount_g=g) for n,g in parts])
            db.add_all([RecipeStep(recipe_id=recipe.id, order_no=i+1, content=s) for i,s in enumerate(steps)])
        db.add_all([
            Exercise(name="杠铃卧推", body_part="胸部", primary_muscle="胸大肌", secondary_muscle="肱三头肌", equipment="杠铃", difficulty="中级", steps="躺稳，缓慢下放，推起。", cautions="保持肩胛稳定。", met=6.0),
            Exercise(name="俯卧撑", body_part="胸部", primary_muscle="胸大肌", secondary_muscle="肱三头肌", equipment="徒手", difficulty="初级", steps="身体成直线，屈肘下放后推起。", cautions="腰背不要塌陷。", met=5.0),
            Exercise(name="高位下拉", body_part="背部", primary_muscle="背阔肌", secondary_muscle="肱二头肌", equipment="器械", difficulty="初级", steps="下拉至锁骨附近。", cautions="避免借力后仰。", met=5.0),
            Exercise(name="深蹲", body_part="腿部", primary_muscle="股四头肌", secondary_muscle="臀大肌", equipment="杠铃", difficulty="中级", steps="屈髋屈膝下蹲后站起。", cautions="膝盖方向跟随脚尖。", met=6.0),
        ])
        db.commit()
    finally: db.close()


if __name__ == "__main__": init_db()
