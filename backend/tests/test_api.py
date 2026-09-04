import os
import tempfile
from datetime import date

TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False); TMP.close()
os.environ["DATABASE_URL"] = f"sqlite:///{TMP.name}"
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def login(name="测试用户"):
    response = client.post("/api/auth/mock-login", json={"nickname": name, "mock_openid": name})
    return {"X-User-Id": str(response.json()["data"]["user_id"])}

def setup_module():
    with TestClient(app): pass

def test_profile_and_daily_weight_upsert():
    h=login("资料用户")
    r=client.put("/api/users/me/profile",headers=h,json={"age":25,"height_cm":170,"current_weight_kg":65,"target_weight_kg":60,"goal_type":"减脂"})
    data = r.json()["data"]
    assert data["profile_completed"] is True
    assert data["protein_target_g"] == 105
    assert data["carb_target_g"] == 190
    assert data["fat_target_g"] == 50
    dashboard = client.get("/api/dashboard/today", headers=h).json()["data"]
    assert dashboard["daily_calorie_target"] == 1635
    assert dashboard["nutrition"]["protein"]["target"] == 105
    assert dashboard["nutrition"]["carb"]["target"] == 190
    client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":65})
    r=client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":64.5})
    assert r.json()["data"]["weight_kg"] == 64.5

def test_meal_uses_ingredient_nutrition():
    h=login("营养用户"); foods=client.get("/api/ingredients").json()["data"]; chicken=next(x for x in foods if x["name"]=="鸡胸肉")
    r=client.post("/api/meals",headers=h,json={"meal_type":"午餐","name":"鸡胸","ingredients":[{"ingredient_id":chicken["id"],"amount_g":200}]})
    assert r.json()["data"]["nutrition"]["calories_kcal"] == 266
    assert r.json()["data"]["nutrition"]["protein_g"] == 49.2

def test_recipe_generation_depends_on_ingredients():
    h=login("食谱用户")
    chicken = client.post("/api/recipes/generate", headers=h, json={
        "ingredients": ["鸡胸肉", "西兰花", "鸡蛋"],
        "meal_type": "午餐",
        "target_calories": 500,
        "preference": "高蛋白,少油"
    }).json()["data"]
    beef = client.post("/api/recipes/generate", headers=h, json={
        "ingredients": ["牛肉", "土豆", "番茄"],
        "meal_type": "午餐",
        "target_calories": 500,
        "preference": "高蛋白,少油"
    }).json()["data"]
    assert len(chicken) >= 4
    assert len(beef) >= 4
    assert chicken[0]["name"] != beef[0]["name"]
    assert any("鸡胸肉" in item["name"] or "西兰花" in item["name"] for item in chicken)
    assert any("牛肉" in item["name"] or "土豆" in item["name"] for item in beef)

def test_workout_complete_and_dashboard():
    h=login("训练用户"); client.put("/api/users/me/profile",headers=h,json={"current_weight_kg":70})
    exercise=client.get("/api/exercises").json()["data"][0]
    session=client.post("/api/workouts/sessions",headers=h,json={"title":"胸部训练","duration_min":30}).json()["data"]
    client.post(f"/api/workouts/sessions/{session['id']}/sets",headers=h,json={"exercise_id":exercise["id"],"set_no":1,"reps":10,"completed":True})
    done=client.post(f"/api/workouts/sessions/{session['id']}/complete",headers=h).json()["data"]
    assert done["calories_kcal"] == 220.5
    dashboard = client.get("/api/dashboard/today",headers=h).json()["data"]
    assert dashboard["workout_duration_min"] == 30
    assert dashboard["daily_calorie_target"] == dashboard["base_calorie_target"] + done["calories_kcal"]
    assert dashboard["remaining_calories_kcal"] == dashboard["daily_calorie_target"]

def test_cardio_session_uses_profile_and_updates_dashboard():
    h=login("有氧用户")
    client.put("/api/users/me/profile",headers=h,json={"height_cm":170,"current_weight_kg":70,"goal_type":"减脂"})
    done=client.post("/api/workouts/cardio",headers=h,json={"mode":"快走","duration_min":30}).json()["data"]
    assert done["title"] == "快走30分钟"
    assert done["duration_min"] == 30
    assert done["calories_kcal"] == 158
    dashboard=client.get("/api/dashboard/today",headers=h).json()["data"]
    assert dashboard["workout_duration_min"] == 30
    assert dashboard["workout_calories_kcal"] == done["calories_kcal"]
    assert dashboard["daily_calorie_target"] == dashboard["base_calorie_target"] + done["calories_kcal"]

def test_cardio_session_parses_free_text_and_segments():
    h=login("有氧文本用户")
    client.put("/api/users/me/profile",headers=h,json={"height_cm":170,"current_weight_kg":70,"goal_type":"减脂"})
    swim=client.post("/api/workouts/cardio",headers=h,json={"detail":"蛙泳40分钟"}).json()["data"]
    assert swim["title"] == "蛙泳40分钟"
    assert swim["duration_min"] == 40
    assert swim["calories_kcal"] == 504.7
    climb=client.post("/api/workouts/cardio",headers=h,json={"detail":"爬坡坡度10速度5.5 10分钟 坡度11速度5.5 20分钟"}).json()["data"]
    assert climb["duration_min"] == 30
    assert len(climb["cardio_segments"]) == 2
    assert climb["calories_kcal"] > 200

def test_calendar_records_start_at_login_and_show_day_data():
    h=login("日历用户")
    today=date.today()
    records=client.get(f"/api/stats/calendar?year={today.year}&month={today.month}",headers=h).json()["data"]
    today_record=next(item for item in records if str(item["date"]) == str(today))
    assert today_record["status"] == "休息日"
    assert today_record["sessions"] == 0
    assert all(str(item["date"]) >= str(today) for item in records)

    foods=client.get("/api/ingredients").json()["data"]
    egg=next(x for x in foods if x["name"]=="鸡蛋")
    client.post("/api/meals",headers=h,json={"record_date":str(today),"meal_type":"早餐","name":"鸡蛋","ingredients":[{"ingredient_id":egg["id"],"amount_g":100}]})
    exercise=client.get("/api/exercises").json()["data"][0]
    session=client.post("/api/workouts/sessions",headers=h,json={"workout_date":str(today),"title":"今日训练","duration_min":20}).json()["data"]
    client.post(f"/api/workouts/sessions/{session['id']}/sets",headers=h,json={"exercise_id":exercise["id"],"set_no":1,"reps":10,"completed":True})
    client.post(f"/api/workouts/sessions/{session['id']}/complete",headers=h)

    records=client.get(f"/api/stats/calendar?year={today.year}&month={today.month}",headers=h).json()["data"]
    today_record=next(item for item in records if str(item["date"]) == str(today))
    assert today_record["status"] == "训练日"
    assert today_record["sessions"] == 1
    assert today_record["meal_count"] == 1
    assert today_record["duration_min"] == 20
def test_recipe_generation_rotates_main_ingredients_between_batches():
    h = login("澶氭牱鍖栫敤鎴?")
    request = {
        "ingredients": ["鸡蛋", "牛肉", "虾仁", "糙米饭", "西兰花", "胡萝卜"],
        "meal_type": "午餐",
        "target_calories": 500,
        "preference": "高蛋白,少油",
        "recipe_round": 0,
    }
    first = client.post("/api/recipes/generate", headers=h, json=request).json()["data"]
    request["recipe_round"] = 1
    second = client.post("/api/recipes/generate", headers=h, json=request).json()["data"]
    first_names = [item["name"] for item in first]
    second_names = [item["name"] for item in second]
    assert len(set(first_names)) >= 4
    assert len(set(second_names)) >= 4
    assert first_names != second_names


def test_recipe_generation_filters_selected_preferences():
    h = login("偏好用户")
    result = client.post("/api/recipes/generate", headers=h, json={
        "ingredients": ["鸡蛋", "牛肉", "虾仁", "糙米饭"],
        "meal_type": "午餐",
        "target_calories": 400,
        "preference": "少油,15分钟内",
        "recipe_round": 0,
    }).json()["data"]

    assert len(result) >= 4
    assert all(item["minutes"] <= 15 for item in result)
    assert all("少油" in item["tags"] for item in result)
    assert all("高蛋白" not in item["tags"] for item in result)

def test_recipe_generation_uses_only_requested_ingredients():
    h = login("严格食材用户")
    allowed = {"糙米饭", "燕麦", "红薯", "土豆", "玉米", "生菜", "胡萝卜", "荞麦面"}
    result = client.post("/api/recipes/generate", headers=h, json={
        "ingredients": list(allowed),
        "meal_type": "午餐",
        "target_calories": 400,
        "preference": "少油",
        "recipe_round": 0,
    }).json()["data"]

    assert len(result) >= 4
    for recipe in result:
        used = {ingredient["name"] for ingredient in recipe["ingredients"]}
        assert used <= allowed
        assert "鸡胸肉" not in recipe["name"]


def test_goal_driven_workout_recommendation():
    h=login("推荐用户")
    client.put("/api/users/me/profile",headers=h,json={"goal_type":"提升运动水平"})
    data=client.get("/api/workouts/recommendation?level=中级",headers=h).json()["data"]
    assert data["goal"]["code"] == "performance"
    assert data["exercises"][0]["name"] == "深蹲"
    assert data["exercises"][0]["reps"] == "3-6次"
    assert data["cardio"]["intensity"] == {"method":"RPE","range":"4-8"}
    assert data["cardio"]["interval"] == {"work_seconds":30,"rest_seconds":90}

def test_training_goal_catalog():
    goals=client.get("/api/training-goals").json()["data"]
    assert {x["name"] for x in goals} == {"塑形","减脂","提升运动水平"}
