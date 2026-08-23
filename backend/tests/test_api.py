import os
import tempfile

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
    assert r.json()["data"]["profile_completed"] is True
    client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":65})
    r=client.post("/api/users/me/weights",headers=h,json={"record_date":"2026-08-23","weight_kg":64.5})
    assert r.json()["data"]["weight_kg"] == 64.5

def test_meal_uses_ingredient_nutrition():
    h=login("营养用户"); foods=client.get("/api/ingredients").json()["data"]; chicken=next(x for x in foods if x["name"]=="鸡胸肉")
    r=client.post("/api/meals",headers=h,json={"meal_type":"午餐","name":"鸡胸","ingredients":[{"ingredient_id":chicken["id"],"amount_g":200}]})
    assert r.json()["data"]["nutrition"]["calories_kcal"] == 266
    assert r.json()["data"]["nutrition"]["protein_g"] == 49.2

def test_workout_complete_and_dashboard():
    h=login("训练用户"); client.put("/api/users/me/profile",headers=h,json={"current_weight_kg":70})
    exercise=client.get("/api/exercises").json()["data"][0]
    session=client.post("/api/workouts/sessions",headers=h,json={"title":"胸部训练","duration_min":30}).json()["data"]
    client.post(f"/api/workouts/sessions/{session['id']}/sets",headers=h,json={"exercise_id":exercise["id"],"set_no":1,"reps":10,"completed":True})
    done=client.post(f"/api/workouts/sessions/{session['id']}/complete",headers=h).json()["data"]
    assert done["calories_kcal"] == 220.5
    assert client.get("/api/dashboard/today",headers=h).json()["data"]["workout_duration_min"] == 30
