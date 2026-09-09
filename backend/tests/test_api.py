import os
from datetime import UTC, datetime
import tempfile
from types import SimpleNamespace

TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False); TMP.close()
os.environ["DATABASE_URL"] = f"sqlite:///{TMP.name}"
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.router import business_date

client = TestClient(app)

def login(name="测试用户"):
    response = client.post("/api/auth/mock-login", json={"nickname": name, "mock_openid": name})
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}

def setup_module():
    with TestClient(app): pass


def test_business_date_uses_china_timezone():
    assert business_date(datetime(2026, 9, 4, 16, 30, tzinfo=UTC)).isoformat() == "2026-09-05"

def test_user_id_header_cannot_impersonate_user():
    response = client.post("/api/auth/mock-login", json={"nickname": "隔离用户", "mock_openid": "isolated"})
    user_id = response.json()["data"]["user_id"]
    assert client.get("/api/users/me", headers={"X-User-Id": str(user_id)}).status_code == 401

def test_tampered_session_token_is_rejected():
    headers = login("令牌用户")
    headers["Authorization"] += "tampered"
    assert client.get("/api/users/me", headers=headers).status_code == 401


def test_session_is_bound_to_the_current_account_nonce():
    from backend.database.session import SessionLocal
    from backend.models.entities import User

    headers = login("会话换代用户")
    with SessionLocal() as db:
        user = db.query(User).filter_by(openid="会话换代用户").one()
        user.session_nonce = "rotated-session-nonce"
        db.commit()

    assert client.get("/api/users/me", headers=headers).status_code == 401

def test_mock_login_is_disabled_in_production(monkeypatch):
    import backend.api.router as api_router

    monkeypatch.setattr(api_router, "settings", SimpleNamespace(app_env="production"))
    response = client.post("/api/auth/mock-login", json={"nickname": "不应登录"})
    assert response.status_code == 404


def test_mock_login_is_disabled_in_staging(monkeypatch):
    import backend.api.router as api_router

    monkeypatch.setattr(api_router, "settings", SimpleNamespace(app_env="staging"))
    response = client.post("/api/auth/mock-login", json={"nickname": "不应登录"})
    assert response.status_code == 404

def test_private_recipe_generation_requires_login():
    response = client.post("/api/recipes/generate", json={
        "ingredients": ["鸡蛋"], "meal_type": "早餐", "target_calories": 300,
    })
    assert response.status_code == 401

def test_users_cannot_read_each_others_workouts():
    owner = login("训练记录所有者")
    stranger = login("其他用户")
    session = client.post("/api/workouts/sessions", headers=owner, json={
        "title": "私人训练", "duration_min": 30,
    }).json()["data"]
    response = client.get(f"/api/workouts/sessions/{session['id']}", headers=stranger)
    assert response.status_code == 404

def test_wechat_login_creates_signed_session(monkeypatch):
    import backend.api.router as api_router

    monkeypatch.setattr(api_router, "settings", SimpleNamespace(
        auth_mode="wechat_api",
        wechat_app_id="test-app-id",
        wechat_app_secret="test-secret",
        session_secret="test-session-secret",
        session_ttl_seconds=3600,
        app_env="development",
    ))
    monkeypatch.setattr(api_router, "exchange_login_code", lambda code, app_id, secret: "wx-test-openid")
    response = client.post("/api/auth/wechat-login", json={"code": "temporary-code"})
    assert response.status_code == 200
    data = response.json()["data"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert "openid" not in me.json()["data"]

def test_cloud_login_accepts_only_matching_injected_identity_headers(monkeypatch):
    import backend.api.router as api_router

    monkeypatch.setattr(api_router, "settings", SimpleNamespace(
        auth_mode="cloud_headers",
        is_deployed=True,
        wechat_app_id="wx26dfe00bf5f3258b",
        wechat_cloud_env_id="prod-d4g1s6f9gaef2c320",
        session_secret="test-session-secret",
        session_ttl_seconds=3600,
    ))
    valid_headers = {
        "X-WX-OPENID": "openid_12345678",
        "X-WX-APPID": "wx26dfe00bf5f3258b",
        "X-WX-ENV": "prod-d4g1s6f9gaef2c320",
    }
    response = client.post("/api/auth/cloud-login", headers=valid_headers)
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    assert client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    assert client.post("/api/auth/cloud-login", headers={**valid_headers, "X-WX-APPID": "wx0000000000000000"}).status_code == 401
    assert client.post("/api/auth/cloud-login", headers={**valid_headers, "X-WX-ENV": "wrong-env"}).status_code == 401
    assert client.post("/api/auth/cloud-login", headers={**valid_headers, "X-WX-OPENID": "bad"}).status_code == 401


def test_cloud_auth_mode_disables_code_exchange_login(monkeypatch):
    import backend.api.router as api_router

    monkeypatch.setattr(api_router, "settings", SimpleNamespace(auth_mode="cloud_headers"))
    assert client.post("/api/auth/wechat-login", json={"code": "temporary-code"}).status_code == 404

def test_profile_rejects_users_under_fourteen():
    headers = login("年龄限制用户")
    response = client.put("/api/users/me/profile", headers=headers, json={"age": 13})
    assert response.status_code == 422

def test_delete_account_removes_personal_data_and_invalidates_session():
    headers = login("注销用户")
    foods = client.get("/api/ingredients").json()["data"]
    client.post("/api/users/me/weights", headers=headers, json={"weight_kg": 60})
    client.post("/api/meals", headers=headers, json={
        "meal_type": "早餐",
        "name": "注销测试餐",
        "ingredients": [{"ingredient_id": foods[0]["id"], "amount_g": 100}],
    })
    session = client.post("/api/workouts/sessions", headers=headers, json={
        "title": "注销测试训练",
        "duration_min": 10,
    }).json()["data"]
    exercise = client.get("/api/exercises").json()["data"][0]
    client.post(f"/api/workouts/sessions/{session['id']}/sets", headers=headers, json={
        "exercise_id": exercise["id"], "set_no": 1, "reps": 8,
    })

    response = client.request("DELETE", "/api/users/me", headers=headers, json={"confirmation": "DELETE"})
    assert response.status_code == 200
    assert client.get("/api/users/me", headers=headers).status_code == 401

def test_profile_and_daily_weight_upsert():
    h=login("资料用户")
    r=client.put("/api/users/me/profile",headers=h,json={"nickname":"新昵称","age":25,"height_cm":170,"current_weight_kg":65,"target_weight_kg":60,"goal_type":"减脂"})
    data = r.json()["data"]
    assert data["profile_completed"] is True
    assert data["protein_target_g"] == 105
    assert data["carb_target_g"] == 190
    assert data["fat_target_g"] == 50
    assert client.get("/api/users/me", headers=h).json()["data"]["nickname"] == "新昵称"
    dashboard = client.get("/api/dashboard/today", headers=h).json()["data"]
    assert dashboard["daily_calorie_target"] == 1635
    assert dashboard["nutrition"]["protein"]["target"] == 105
    assert dashboard["nutrition"]["carb"]["target"] == 190
    client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":65})
    r=client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":64.5})
    assert r.json()["data"]["weight_kg"] == 64.5
    trend = client.get("/api/stats/body-trend", headers=h).json()["data"]
    assert trend["current_weight_kg"] == 64.5
    assert trend["target_weight_kg"] == 60


def test_calendar_rejects_invalid_month_instead_of_crashing():
    h = login("日期校验用户")
    response = client.get("/api/stats/calendar?year=2026&month=13", headers=h)
    assert response.status_code == 422


def test_database_bounded_text_fields_are_validated():
    h = login("字段边界用户")
    response = client.post("/api/meals", headers=h, json={
        "meal_type": "午餐",
        "name": "x" * 101,
        "ingredients": [],
    })
    assert response.status_code == 422
    response = client.put("/api/users/me/profile", headers=h, json={"gender": "未知"})
    assert response.status_code == 422
    response = client.put("/api/users/me/profile", headers=h, json={"nickname": "   "})
    assert response.status_code == 422

def test_meal_uses_ingredient_nutrition():
    h=login("营养用户"); foods=client.get("/api/ingredients").json()["data"]; chicken=next(x for x in foods if x["name"]=="鸡胸肉")
    r=client.post("/api/meals",headers=h,json={"meal_type":"午餐","name":"鸡胸","ingredients":[{"ingredient_id":chicken["id"],"amount_g":200}]})
    assert r.json()["data"]["nutrition"]["calories_kcal"] == 266
    assert r.json()["data"]["nutrition"]["protein_g"] == 49.2

def test_recipe_generation_depends_on_ingredients():
    from backend.database.session import SessionLocal
    from backend.models.entities import Recipe

    h=login("食谱用户")
    with SessionLocal() as db:
        recipe_count_before = db.query(Recipe).count()
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
    assert all(str(item["id"]).startswith("generated-") for item in chicken + beef)
    with SessionLocal() as db:
        assert db.query(Recipe).count() == recipe_count_before

def test_workout_complete_and_dashboard():
    h=login("训练用户"); client.put("/api/users/me/profile",headers=h,json={"current_weight_kg":70})
    exercise=client.get("/api/exercises").json()["data"][0]
    session=client.post("/api/workouts/sessions",headers=h,json={"title":"胸部训练","duration_min":30}).json()["data"]
    client.post(f"/api/workouts/sessions/{session['id']}/sets",headers=h,json={"exercise_id":exercise["id"],"set_no":1,"reps":10,"completed":True})
    done=client.post(f"/api/workouts/sessions/{session['id']}/complete",headers=h).json()["data"]
    assert done["calories_kcal"] == 220.5
    assert client.get("/api/dashboard/today",headers=h).json()["data"]["workout_duration_min"] == 30
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


def test_recipe_generation_rejects_fully_unknown_ingredients():
    h = login("未知食材用户")
    response = client.post("/api/recipes/generate", headers=h, json={
        "ingredients": ["完全不存在的食材", "另一个未知食材"],
        "meal_type": "午餐",
        "target_calories": 400,
    })
    assert response.status_code == 400
    assert "食材不足" in response.json()["message"]


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

def test_first_phase_insight_quick_log_and_report():
    h=login("第一阶段联调用户")
    before=client.get("/api/insights/today",headers=h).json()["data"]
    assert before["score"] == 0

    quick_meal=client.post("/api/quick-log",headers=h,json={"text":"午餐 鸡蛋100g 燕麦50g"}).json()["data"]
    assert quick_meal["type"] == "meal"
    assert quick_meal["record"]["meal_type"] == "午餐"
    assert quick_meal["record"]["nutrition"]["calories_kcal"] > 0

    quick_cardio=client.post("/api/quick-log",headers=h,json={"text":"蛙泳40分钟"}).json()["data"]
    assert quick_cardio["title"] == "蛙泳40分钟"
    assert quick_cardio["calories_kcal"] > 0

    after=client.get("/api/insights/today",headers=h).json()["data"]
    assert after["meal_count"] == 1
    assert after["workout_count"] == 1
    assert after["diet_score"] > 0
    assert after["workout_score"] > 0

    report=client.get("/api/reports/summary?days=7",headers=h).json()["data"]
    assert report["summary"]["meal_count"] == 1
    assert report["summary"]["workout_count"] == 1
    assert len(report["trend"]) == 7
