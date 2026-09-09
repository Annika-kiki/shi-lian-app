from datetime import UTC, date, datetime, timedelta
from calendar import monthrange
import hmac
import re
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.config.settings import settings
from backend.database.session import get_db
from backend.models.entities import *
from backend.services.ai_provider import LocalRecipeProvider
from backend.services.nutrition import nutrition_for_ingredients, recipe_payload
from backend.services.auth import InvalidSession, create_session_token, verify_session_token
from backend.services.wechat import exchange_login_code

router = APIRouter(prefix="/api")
BUSINESS_TIMEZONE = ZoneInfo("Asia/Shanghai")


def business_date(now: datetime | None = None) -> date:
    instant = now or datetime.now(UTC)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=UTC)
    return instant.astimezone(BUSINESS_TIMEZONE).date()

def ok(data=None, message="ok"): return {"code": 0, "message": message, "data": data if data is not None else {}}
def current_user(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "登录状态无效，请重新登录")
    try:
        user_id, session_nonce = verify_session_token(authorization[7:], settings.session_secret)
    except InvalidSession as exc:
        raise HTTPException(401, "登录状态无效或已过期，请重新登录") from exc
    user = db.get(User, user_id)
    if not user or not hmac.compare_digest(user.session_nonce, session_nonce):
        raise HTTPException(401, "用户不存在或登录状态已失效")
    return user

def round_to_five(value: float) -> int:
    return max(0, round(value / 5) * 5)

def profile_targets(p):
    weight = p.current_weight_kg or 56.5
    height = p.height_cm or 165
    age = p.age or 21
    goal = p.goal_type or "保持健康"
    gender = (p.gender or "").lower()
    is_male = p.gender == "男" or gender == "male"
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + (5 if is_male else -161)
    activity_calories = max(1200, bmr * 1.35)
    daily_factor = 0.85 if goal == "减脂" else 1.1 if goal == "增肌" else 1
    daily = round_to_five(min(3500, max(1200, activity_calories * daily_factor)))
    protein_factor = 1.8 if goal == "增肌" else 1.6 if goal == "减脂" else 1.2
    fat_factor = 0.9 if goal == "增肌" else 0.8
    protein = round_to_five(weight * protein_factor)
    fat = round_to_five(weight * fat_factor)
    carb = round_to_five(max(80, (daily - (protein * 4) - (fat * 9)) / 4))
    return {
        "daily_calorie_target": daily,
        "protein_target_g": protein,
        "carb_target_g": carb,
        "fat_target_g": fat,
    }

def apply_profile_targets(p):
    for key, value in profile_targets(p).items():
        setattr(p, key, value)

def profile_dict(p):
    apply_profile_targets(p)
    return {k: getattr(p, k) for k in ("gender","age","height_cm","current_weight_kg","target_weight_kg","goal_type","daily_calorie_target","protein_target_g","carb_target_g","fat_target_g","profile_completed")}

def issue_session(openid: str, db: Session, nickname: str | None = None, avatar: str | None = None):
    user = db.query(User).filter_by(openid=openid).first()
    if not user:
        user = User(openid=openid, nickname=nickname, avatar=avatar)
        db.add(user); db.flush(); db.add(UserProfile(user_id=user.id))
    elif nickname is not None:
        user.nickname, user.avatar = nickname, avatar
    db.commit()
    return ok({"user_id": user.id, "access_token": create_session_token(user.id, user.session_nonce, settings.session_secret, settings.session_ttl_seconds), "token_type": "Bearer", "expires_in": settings.session_ttl_seconds})

class LoginIn(BaseModel): nickname: str = Field(default="食练周期用户", max_length=64); avatar: str | None = Field(None, max_length=512); mock_openid: str | None = Field(None, max_length=128)
class WechatLoginIn(BaseModel): code: str = Field(min_length=1, max_length=128)
class ProfileIn(BaseModel):
    nickname: str | None = Field(None, min_length=1, max_length=64); gender: Literal["男", "女"] | None = None; age: int | None = Field(None, ge=14, le=120); height_cm: float | None = Field(None, ge=50, le=260); current_weight_kg: float | None = Field(None, gt=0, le=500); target_weight_kg: float | None = Field(None, gt=0, le=500); goal_type: Literal["增肌", "减脂", "保持健康", "提升运动水平"] = "保持健康"; daily_calorie_target: float | None = Field(None, gt=0, le=10000); protein_target_g: float | None = Field(None, ge=0, le=1000); carb_target_g: float | None = Field(None, ge=0, le=2000); fat_target_g: float | None = Field(None, ge=0, le=1000)
class DeleteAccountIn(BaseModel): confirmation: str = Field(pattern="^DELETE$")
class WeightIn(BaseModel): record_date: date = Field(default_factory=business_date); weight_kg: float = Field(gt=0, le=500)
class RecipeGenerateIn(BaseModel): ingredients: list[str] = Field(min_length=1, max_length=50); meal_type: Literal["早餐", "午餐", "晚餐"]; target_calories: int = Field(500, ge=100, le=2000); preference: str | None = Field(None, max_length=255); recipe_round: int = Field(0, ge=0, le=1000)
class MealIngredientIn(BaseModel): ingredient_id: int; amount_g: float = Field(gt=0, le=3000)
class MealIn(BaseModel): record_date: date = Field(default_factory=business_date); meal_type: Literal["早餐", "午餐", "晚餐"]; name: str | None = Field(None, max_length=100); recipe_id: int | None = Field(None, ge=1); ingredients: list[MealIngredientIn] = Field(default_factory=list, max_length=50); note: str | None = Field(None, max_length=255)
class SessionIn(BaseModel): workout_date: date = Field(default_factory=business_date); title: str = Field(min_length=1,max_length=100); duration_min: int | None = Field(None, ge=0, le=1440)
class CardioSessionIn(BaseModel): workout_date: date = Field(default_factory=business_date); mode: str | None = Field(default=None, max_length=50); duration_min: int | None = Field(None, ge=1, le=360); detail: str | None = Field(None, max_length=255)
class QuickLogIn(BaseModel): text: str = Field(min_length=1,max_length=255); record_date: date = Field(default_factory=business_date)
class SessionUpdateIn(BaseModel): title: str | None = Field(None, min_length=1, max_length=100); duration_min: int | None = Field(None, ge=0, le=1440); workout_date: date | None = None
class SetIn(BaseModel): exercise_id: int; set_no: int = Field(ge=1); weight_kg: float | None = Field(None, ge=0); reps: int | None = Field(None, ge=0); completed: bool = False
class SetUpdateIn(BaseModel): weight_kg: float | None = Field(None, ge=0); reps: int | None = Field(None, ge=0); completed: bool | None = None

@router.post("/auth/mock-login")
def mock_login(body: LoginIn, db: Session = Depends(get_db)):
    if settings.app_env != "development":
        raise HTTPException(404, "接口不存在")
    openid = body.mock_openid or f"mock_{body.nickname}"
    return issue_session(openid, db, body.nickname, body.avatar)
@router.post("/auth/wechat-login")
def wechat_login(body: WechatLoginIn, db: Session = Depends(get_db)):
    if settings.auth_mode != "wechat_api": raise HTTPException(404, "接口不存在")
    if not settings.wechat_app_id or not settings.wechat_app_secret: raise HTTPException(501, "微信登录尚未配置：请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
    openid = exchange_login_code(body.code, settings.wechat_app_id, settings.wechat_app_secret)
    return issue_session(openid, db)

@router.post("/auth/cloud-login")
def cloud_login(
    x_wx_openid: str | None = Header(None, alias="X-WX-OPENID"),
    x_wx_appid: str | None = Header(None, alias="X-WX-APPID"),
    x_wx_env: str | None = Header(None, alias="X-WX-ENV"),
    db: Session = Depends(get_db),
):
    # These identity headers are trusted only behind WeChat Cloud Hosting. Public
    # access to this service must be disabled before staging or production use.
    if settings.auth_mode != "cloud_headers" or not settings.is_deployed:
        raise HTTPException(404, "接口不存在")
    if x_wx_appid != settings.wechat_app_id or x_wx_env != settings.wechat_cloud_env_id:
        raise HTTPException(401, "云托管身份校验失败")
    if not x_wx_openid or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", x_wx_openid):
        raise HTTPException(401, "云托管用户身份无效")
    return issue_session(x_wx_openid, db)
@router.get("/users/me")
def me(user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.get(UserProfile,user.id); return ok({"id":user.id,"nickname":user.nickname,"avatar":user.avatar,"profile":profile_dict(p)})
@router.put("/users/me/profile")
def update_profile(body: ProfileIn, user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.get(UserProfile,user.id)
    if not p:
        p=UserProfile(user_id=user.id); db.add(p)
    if body.nickname is not None:
        nickname = body.nickname.strip()
        if not nickname:
            raise HTTPException(422, "昵称不能为空")
        user.nickname = nickname
    for k,v in body.model_dump(exclude={"nickname"}).items(): setattr(p,k,v)
    apply_profile_targets(p)
    p.profile_completed=True; db.commit(); return ok(profile_dict(p))
@router.post("/users/me/weights")
def weight(body: WeightIn,user=Depends(current_user),db:Session=Depends(get_db)):
    r=db.query(WeightRecord).filter_by(user_id=user.id,record_date=body.record_date).first()
    if r: r.weight_kg=body.weight_kg
    else: r=WeightRecord(user_id=user.id,record_date=body.record_date,weight_kg=body.weight_kg); db.add(r)
    p=db.get(UserProfile,user.id)
    if not p:
        p=UserProfile(user_id=user.id); db.add(p)
    p.current_weight_kg=body.weight_kg; apply_profile_targets(p); db.commit(); return ok({"id":r.id,"record_date":r.record_date,"weight_kg":r.weight_kg})
@router.get("/users/me/weights")
def weights(days:int=Query(30,ge=1,le=366),user=Depends(current_user),db:Session=Depends(get_db)):
    since=business_date()-timedelta(days=days-1); r=db.query(WeightRecord).filter(WeightRecord.user_id==user.id,WeightRecord.record_date>=since).order_by(WeightRecord.record_date).all(); return ok([{"date":x.record_date,"weight_kg":x.weight_kg} for x in r])

@router.delete("/users/me")
def delete_account(body: DeleteAccountIn, user=Depends(current_user), db: Session=Depends(get_db)):
    session_ids = [row[0] for row in db.query(WorkoutSession.id).filter_by(user_id=user.id)]
    if session_ids:
        db.query(WorkoutSet).filter(WorkoutSet.session_id.in_(session_ids)).delete(synchronize_session=False)
    db.query(WorkoutSession).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(FavoriteExercise).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(FavoriteRecipe).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(MealRecord).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(WeightRecord).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(UserProfile).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return ok(message="账号及个人数据已删除")

@router.get("/ingredients")
def ingredients(q:str="",db:Session=Depends(get_db)):
    x=db.query(Ingredient).filter((Ingredient.name.contains(q)) | (Ingredient.aliases.contains(q))).all() if q else db.query(Ingredient).all(); return ok([{"id":i.id,"name":i.name,"aliases":i.aliases,"calories_kcal_per_100g":i.calories_kcal,"protein_g":i.protein_g,"carb_g":i.carb_g,"fat_g":i.fat_g,"unit":i.unit} for i in x])
@router.get("/recipes")
def recipes(db:Session=Depends(get_db)): return ok([recipe_payload(db,x) for x in db.query(Recipe).all()])
@router.get("/recipes/{recipe_id}")
def recipe(recipe_id:int,db:Session=Depends(get_db)):
    x=db.get(Recipe,recipe_id)
    if not x: raise HTTPException(404,"食谱不存在")
    return ok(recipe_payload(db,x))
@router.post("/recipes/generate")
def generate(body:RecipeGenerateIn,user=Depends(current_user),db:Session=Depends(get_db)): return ok(LocalRecipeProvider().generate(db,body.ingredients,body.target_calories,body.preference,body.recipe_round))
@router.post("/meals")
def create_meal(body:MealIn,user=Depends(current_user),db:Session=Depends(get_db)):
    if body.recipe_id:
        r=db.get(Recipe,body.recipe_id)
        if not r: raise HTTPException(404,"食谱不存在")
        payload=recipe_payload(db,r); n=payload["nutrition"]; name=body.name or r.name
    else:
        if not body.ingredients: raise HTTPException(422,"自定义餐食必须提供 ingredients")
        rows=[]
        for entry in body.ingredients:
            i=db.get(Ingredient,entry.ingredient_id)
            if not i: raise HTTPException(404,"食材不存在")
            rows.append((i,entry.amount_g))
        n=nutrition_for_ingredients(rows); name=body.name or "自定义餐食"
    m=MealRecord(user_id=user.id,record_date=body.record_date,meal_type=body.meal_type,recipe_id=body.recipe_id,name=name,note=body.note,**n); db.add(m);db.commit();return ok({"id":m.id,"name":m.name,"nutrition":n})
@router.get("/meals")
def meals(date_:date=Query(default_factory=business_date,alias="date"),user=Depends(current_user),db:Session=Depends(get_db)):
    x=db.query(MealRecord).filter_by(user_id=user.id,record_date=date_).all();return ok([{"id":m.id,"meal_type":m.meal_type,"name":m.name,"calories_kcal":m.calories_kcal,"protein_g":m.protein_g,"carb_g":m.carb_g,"fat_g":m.fat_g,"recipe_id":m.recipe_id,"note":m.note} for m in x])
@router.delete("/meals/{meal_id}")
def del_meal(meal_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    x=db.query(MealRecord).filter_by(id=meal_id,user_id=user.id).first()
    if not x: raise HTTPException(404,"餐食记录不存在")
    db.delete(x);db.commit();return ok()
def favorite_recipe(recipe_id,user,db,remove=False):
    if not db.get(Recipe,recipe_id): raise HTTPException(404,"食谱不存在")
    x=db.query(FavoriteRecipe).filter_by(user_id=user.id,recipe_id=recipe_id).first()
    if remove and x: db.delete(x)
    if not remove and not x: db.add(FavoriteRecipe(user_id=user.id,recipe_id=recipe_id))
    db.commit();return ok()
@router.post("/recipes/{recipe_id}/favorite")
def fav_recipe(recipe_id:int,user=Depends(current_user),db:Session=Depends(get_db)): return favorite_recipe(recipe_id,user,db)
@router.delete("/recipes/{recipe_id}/favorite")
def unfav_recipe(recipe_id:int,user=Depends(current_user),db:Session=Depends(get_db)): return favorite_recipe(recipe_id,user,db,True)

@router.get("/exercises")
def exercises(body_part:str="",equipment:str="",difficulty:str="",q:str="",db:Session=Depends(get_db)):
    query=db.query(Exercise)
    if body_part: query=query.filter(Exercise.body_part==body_part)
    if equipment: query=query.filter(Exercise.equipment==equipment)
    if difficulty: query=query.filter(Exercise.difficulty==difficulty)
    if q: query=query.filter(Exercise.name.contains(q))
    return ok([exercise_data(x) for x in query.all()])
def exercise_data(x): return {"id":x.id,"name":x.name,"body_part":x.body_part,"primary_muscle":x.primary_muscle,"secondary_muscle":x.secondary_muscle,"equipment":x.equipment,"difficulty":x.difficulty,"video_url":x.video_url,"thumbnail_url":x.thumbnail_url,"steps":x.steps,"cautions":x.cautions,"met":x.met}
@router.get("/exercises/{exercise_id}")
def exercise(exercise_id:int,db:Session=Depends(get_db)):
    x=db.get(Exercise,exercise_id)
    if not x: raise HTTPException(404,"动作不存在")
    return ok(exercise_data(x))
@router.post("/exercises/{exercise_id}/favorite")
def fav_exercise(exercise_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(Exercise,exercise_id): raise HTTPException(404,"动作不存在")
    if not db.query(FavoriteExercise).filter_by(user_id=user.id,exercise_id=exercise_id).first(): db.add(FavoriteExercise(user_id=user.id,exercise_id=exercise_id));db.commit()
    return ok()
@router.delete("/exercises/{exercise_id}/favorite")
def unfav_exercise(exercise_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    x=db.query(FavoriteExercise).filter_by(user_id=user.id,exercise_id=exercise_id).first()
    if x: db.delete(x);db.commit()
    return ok()
GOAL_ALIASES = {"塑形":"shaping", "保持健康":"shaping", "增肌":"shaping",
                "减脂":"fat_loss", "提升运动水平":"performance"}

@router.get("/training-goals")
def training_goals(db:Session=Depends(get_db)):
    goals=db.query(TrainingGoal).filter_by(active=True).order_by(TrainingGoal.code).all()
    return ok([{"code":x.code,"name":x.name,"description":x.description,
                "resistance_principle":x.resistance_principle,
                "cardio_principle":x.cardio_principle} for x in goals])

@router.get("/workouts/recommendation")
def recommendation(level:str=Query("新手",pattern="^(新手|中级|高级)$"),
                   user=Depends(current_user),db:Session=Depends(get_db)):
    profile=db.get(UserProfile,user.id)
    goal_code=GOAL_ALIASES.get(profile.goal_type, "shaping")
    goal=db.get(TrainingGoal,goal_code)
    rows=(db.query(GoalExercisePrescription,Exercise)
          .join(Exercise,GoalExercisePrescription.exercise_id==Exercise.id)
          .filter(GoalExercisePrescription.goal_code==goal_code)
          .order_by(GoalExercisePrescription.priority).all())
    cardio=db.query(CardioPrescription).filter_by(goal_code=goal_code,level=level).first()
    exercises=[]
    for prescription, exercise_item in rows:
        reps=(f"{prescription.reps_min}-{prescription.reps_max}次"
              if prescription.reps_min is not None else f"{prescription.duration_seconds}秒")
        exercises.append({"exercise_id":exercise_item.id,"name":exercise_item.name,
                          "body_part":exercise_item.body_part,
                          "movement_pattern":prescription.movement_pattern,
                          "sets":f"{prescription.sets_min}-{prescription.sets_max}组",
                          "reps":reps,"rest_seconds":prescription.rest_seconds,
                          "rir":f"{prescription.rir_min}-{prescription.rir_max}",
                          "notes":prescription.notes})
    cardio_data=None if not cardio else {
        "modes":cardio.modes.split(","),
        "sessions_per_week":f"{cardio.sessions_min}-{cardio.sessions_max}次",
        "minutes_per_session":f"{cardio.minutes_min}-{cardio.minutes_max}分钟",
        "intensity":{"method":cardio.intensity_method,
                     "range":f"{cardio.intensity_min:g}-{cardio.intensity_max:g}"},
        "interval":None if cardio.interval_work_seconds is None else {
            "work_seconds":cardio.interval_work_seconds,
            "rest_seconds":cardio.interval_rest_seconds},
        "notes":cardio.notes}
    return ok({"title":f"{goal.name}推荐训练","estimated_duration_min":50,
               "goal":{"code":goal.code,"name":goal.name,"description":goal.description},
               "level":level,"principles":{"resistance":goal.resistance_principle,
               "cardio":goal.cardio_principle},"exercises":exercises,"cardio":cardio_data,
               "safety_note":"计划仅供一般健康成年人参考；如有疾病、伤病、孕期或运动中出现疼痛，请先咨询专业人员。"})
@router.post("/workouts/sessions")
def create_session(body:SessionIn,user=Depends(current_user),db:Session=Depends(get_db)):
    x=WorkoutSession(user_id=user.id,**body.model_dump());db.add(x);db.commit();return ok(session_data(db,x))
@router.get("/workouts/sessions")
def sessions(date_:date|None=Query(None,alias="date"),user=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(WorkoutSession).filter_by(user_id=user.id)
    if date_: q=q.filter_by(workout_date=date_)
    return ok([session_data(db,x) for x in q.order_by(WorkoutSession.created_at.desc()).all()])
def owned_session(id,user,db):
    x=db.query(WorkoutSession).filter_by(id=id,user_id=user.id).first()
    if not x: raise HTTPException(404,"训练记录不存在")
    return x
def session_data(db,x):
    sets=db.query(WorkoutSet).filter_by(session_id=x.id).all()
    return {"id":x.id,"workout_date":x.workout_date,"title":x.title,"duration_min":x.duration_min,"calories_kcal":x.calories_kcal,"status":x.status,"completed_at":x.completed_at,"sets":[{"id":s.id,"exercise_id":s.exercise_id,"exercise_name":db.get(Exercise,s.exercise_id).name,"set_no":s.set_no,"weight_kg":s.weight_kg,"reps":s.reps,"completed":s.completed} for s in sets]}
@router.get("/workouts/sessions/{session_id}")
def session(session_id:int,user=Depends(current_user),db:Session=Depends(get_db)): return ok(session_data(db,owned_session(session_id,user,db)))
@router.put("/workouts/sessions/{session_id}")
def update_session(session_id:int,body:SessionUpdateIn,user=Depends(current_user),db:Session=Depends(get_db)):
    x=owned_session(session_id,user,db)
    for k,v in body.model_dump(exclude_none=True).items(): setattr(x,k,v)
    db.commit();return ok(session_data(db,x))
@router.post("/workouts/sessions/{session_id}/sets")
def add_set(session_id:int,body:SetIn,user=Depends(current_user),db:Session=Depends(get_db)):
    owned_session(session_id,user,db)
    if not db.get(Exercise,body.exercise_id): raise HTTPException(404,"动作不存在")
    x=WorkoutSet(session_id=session_id,**body.model_dump());db.add(x);db.commit();return ok({"id":x.id})
@router.put("/workouts/sets/{set_id}")
def update_set(set_id:int,body:SetUpdateIn,user=Depends(current_user),db:Session=Depends(get_db)):
    x=db.get(WorkoutSet,set_id)
    if not x or not db.query(WorkoutSession).filter_by(id=x.session_id,user_id=user.id).first(): raise HTTPException(404,"训练组不存在")
    for k,v in body.model_dump(exclude_none=True).items(): setattr(x,k,v)
    db.commit();return ok({"id":x.id,"completed":x.completed})
@router.post("/workouts/sessions/{session_id}/complete")
def complete(session_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    x=owned_session(session_id,user,db); sets=db.query(WorkoutSet).filter_by(session_id=x.id).all(); duration=x.duration_min or 0
    weight=db.get(UserProfile,user.id).current_weight_kg or 60
    if duration and sets:
        met=sum(db.get(Exercise,s.exercise_id).met for s in sets)/len(sets); x.calories_kcal=round(met*3.5*weight/200*duration,1); estimated=False
    else: x.calories_kcal=0; estimated=True
    x.status="已完成";x.completed_at=utc_now();db.commit();return ok({**session_data(db,x),"calorie_estimated":estimated})

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def target_score(value, target, tolerance=0.12):
    if not target:
        return 0
    ratio=value/target
    if 1-tolerance <= ratio <= 1+tolerance:
        return 100
    return round(clamp(100-abs(1-ratio)*120))

def protein_score(value, target):
    if not target:
        return 0
    return round(clamp(value/target*100))

def profile_for_user(db,user):
    p=db.get(UserProfile,user.id)
    if not p:
        p=UserProfile(user_id=user.id); db.add(p); db.flush()
    apply_profile_targets(p)
    return p

def day_totals(db,user,day):
    meals=db.query(MealRecord).filter_by(user_id=user.id,record_date=day).all()
    workouts=db.query(WorkoutSession).filter_by(user_id=user.id,workout_date=day,status="已完成").all()
    nutrients={k:round(sum(getattr(m,k) for m in meals),1) for k in ("calories_kcal","protein_g","carb_g","fat_g")}
    duration=sum(w.duration_min or 0 for w in workouts)
    burned=round(sum(w.calories_kcal or 0 for w in workouts),1)
    return meals,workouts,nutrients,duration,burned

def score_for_day(db,user,day):
    p=profile_for_user(db,user)
    meals,workouts,nutrients,duration,burned=day_totals(db,user,day)
    daily_budget=round((p.daily_calorie_target or 1800)+burned,1)
    calorie=target_score(nutrients["calories_kcal"],daily_budget,0.15) if meals else 0
    protein=protein_score(nutrients["protein_g"],p.protein_target_g) if meals else 0
    carb=target_score(nutrients["carb_g"],p.carb_target_g,0.2) if meals else 0
    fat=target_score(nutrients["fat_g"],p.fat_target_g,0.25) if meals else 0
    balance=round((protein+carb+fat)/3) if meals else 0
    workout=round(clamp((duration/45)*70+(burned/300)*30)) if workouts else 0
    diet=round(calorie*0.35+protein*0.35+balance*0.3) if meals else 0
    total=round(diet*0.65+workout*0.35)
    return {
        "date":day,
        "score":total,
        "diet_score":diet,
        "workout_score":workout,
        "calorie_score":calorie,
        "protein_score":protein,
        "balance_score":balance,
        "daily_calorie_target":daily_budget,
        "intake_calories_kcal":nutrients["calories_kcal"],
        "workout_calories_kcal":burned,
        "workout_duration_min":duration,
        "nutrition":{
            "protein":{"consumed":nutrients["protein_g"],"target":p.protein_target_g},
            "carb":{"consumed":nutrients["carb_g"],"target":p.carb_target_g},
            "fat":{"consumed":nutrients["fat_g"],"target":p.fat_target_g},
        },
        "meal_count":len(meals),
        "workout_count":len(workouts),
    }

def build_today_advice(score):
    advice=[]
    if score["meal_count"] == 0:
        advice.append("今天还没有饮食记录，先记录一餐，系统才能判断营养是否达标。")
    elif score["intake_calories_kcal"] < score["daily_calorie_target"]*0.65:
        advice.append("今天摄入偏低，下一餐可以补充一份主食和优质蛋白。")
    elif score["intake_calories_kcal"] > score["daily_calorie_target"]*1.1:
        advice.append("今天热量已经偏高，后续优先选择清淡蔬菜和低脂蛋白。")
    else:
        advice.append("今天热量在目标附近，继续保持稳定记录。")
    protein=score["nutrition"]["protein"]
    if protein["consumed"] < protein["target"]*0.75:
        advice.append(f"蛋白质还差约 {round(protein['target']-protein['consumed'])} g，可以优先安排鸡蛋、虾仁、豆腐或瘦肉。")
    if score["workout_count"] == 0:
        advice.append("今天还没有训练记录，哪怕 20-30 分钟快走也能让当天评分更完整。")
    elif score["workout_duration_min"] < 30:
        advice.append("训练时长偏短，如果体力允许，可以补 10-15 分钟低强度有氧。")
    else:
        advice.append("今天已经完成训练，晚餐注意补充蛋白质并保证睡眠恢复。")
    return advice[:3]

def meal_type_from_text(text):
    for label in ("早餐","午餐","晚餐","加餐"):
        if label in text:
            return label
    return "加餐"

def default_amount_for_ingredient(item):
    if item.calories_kcal > 180 and item.carb_g > item.protein_g:
        return 110
    if item.protein_g >= 10:
        return 120
    if item.fat_g >= 20:
        return 8
    return 160

def parse_quick_meal_ingredients(db,text):
    rows=[]
    seen=set()
    ingredients=db.query(Ingredient).all()
    for item in sorted(ingredients,key=lambda x:len(x.name),reverse=True):
        aliases=[x.strip() for x in (item.aliases or "").split(",") if x.strip()]
        names=[item.name]+aliases
        if any(name and name in text for name in names):
            if item.id in seen:
                continue
            seen.add(item.id)
            amount_match=re.search(rf"{re.escape(item.name)}\s*(\d+(?:\.\d+)?)\s*(?:g|克)",text)
            amount=float(amount_match.group(1)) if amount_match else default_amount_for_ingredient(item)
            rows.append((item,amount))
    return rows

@router.get("/insights/today")
def today_insight(user=Depends(current_user),db:Session=Depends(get_db)):
    score=score_for_day(db,user,date.today())
    return ok({**score,"advice":build_today_advice(score),
               "dimensions":[
                   {"label":"热量","score":score["calorie_score"]},
                   {"label":"蛋白质","score":score["protein_score"]},
                   {"label":"营养均衡","score":score["balance_score"]},
                   {"label":"训练","score":score["workout_score"]},
               ]})

@router.post("/quick-log")
def quick_log(body:QuickLogIn,user=Depends(current_user),db:Session=Depends(get_db)):
    text=body.text.strip()
    if "分钟" in text or any(keyword in text for keyword,_ in CARDIO_MODE_ALIASES):
        payload=CardioSessionIn(workout_date=body.record_date,detail=text)
        return create_cardio_session(payload,user,db)
    rows=parse_quick_meal_ingredients(db,text)
    if not rows:
        raise HTTPException(422,"没有识别到食材。可以输入：午餐 鸡蛋100g 燕麦80g，或：蛙泳40分钟")
    n=nutrition_for_ingredients(rows)
    name=text.replace(meal_type_from_text(text),"").strip() or "快速记录餐"
    m=MealRecord(user_id=user.id,record_date=body.record_date,meal_type=meal_type_from_text(text),name=name[:100],note=text,**n)
    db.add(m);db.commit();return ok({"type":"meal","record":{"id":m.id,"name":m.name,"meal_type":m.meal_type,"nutrition":n,**n}})

@router.get("/reports/summary")
def report_summary(days:int=Query(7,ge=7,le=31),user=Depends(current_user),db:Session=Depends(get_db)):
    today=date.today(); start=today-timedelta(days=days-1)
    scores=[score_for_day(db,user,start+timedelta(days=i)) for i in range(days)]
    meals=db.query(MealRecord).filter(MealRecord.user_id==user.id,MealRecord.record_date.between(start,today)).all()
    workouts=db.query(WorkoutSession).filter(WorkoutSession.user_id==user.id,WorkoutSession.workout_date.between(start,today),WorkoutSession.status=="已完成").all()
    distribution={"优秀":0,"良好":0,"一般":0,"较差":0}
    for item in scores:
        bucket="优秀" if item["score"]>=80 else "良好" if item["score"]>=60 else "一般" if item["score"]>=30 else "较差"
        distribution[bucket]+=1
    meal_groups={}
    for meal in meals:
        meal_groups.setdefault(meal.meal_type,[]).append(meal)
    meal_scores=[]
    for label,items in meal_groups.items():
        avg_cal=sum(x.calories_kcal for x in items)/len(items)
        avg_protein=sum(x.protein_g for x in items)/len(items)
        meal_scores.append({"label":label,"count":len(items),"avg_calories":round(avg_cal),"avg_protein":round(avg_protein,1),
                            "score":round(clamp(avg_protein*3+min(avg_cal,600)/8))})
    average=round(sum(x["score"] for x in scores)/len(scores)) if scores else 0
    suggestions=build_today_advice(scores[-1]) if scores else []
    if len(workouts)<3:
        suggestions.append("本周训练次数偏少，可以先安排 2-3 次抗阻训练加 1-2 次有氧。")
    if len(meals)<days*2:
        suggestions.append("饮食记录还不够完整，建议每天至少记录午餐和晚餐。")
    return ok({"range":{"start":start,"end":today,"days":days},"average_score":average,
               "trend":[{"date":x["date"],"score":x["score"],"diet_score":x["diet_score"],"workout_score":x["workout_score"]} for x in scores],
               "distribution":distribution,
               "meal_scores":meal_scores,
               "summary":{"meal_count":len(meals),"workout_count":len(workouts),
                          "workout_minutes":sum(x.duration_min or 0 for x in workouts),
                          "workout_calories":round(sum(x.calories_kcal or 0 for x in workouts),1)},
               "suggestions":suggestions[:4]})

@router.get("/dashboard/today")
def dashboard(user=Depends(current_user),db:Session=Depends(get_db)):
    today=business_date(); p=db.get(UserProfile,user.id); meals=db.query(MealRecord).filter_by(user_id=user.id,record_date=today).all(); ws=db.query(WorkoutSession).filter_by(user_id=user.id,workout_date=today,status="已完成").all()
    if not p:
        p=UserProfile(user_id=user.id); db.add(p)
    apply_profile_targets(p)
    nutrients={k:round(sum(getattr(m,k) for m in meals),1) for k in ("calories_kcal","protein_g","carb_g","fat_g")}; duration=sum(w.duration_min or 0 for w in ws); burned=round(sum(w.calories_kcal for w in ws),1)
    active_dates={d for (d,) in db.query(MealRecord.record_date).filter_by(user_id=user.id).distinct()} | {d for (d,) in db.query(WorkoutSession.workout_date).filter_by(user_id=user.id).distinct()}
    streak=0; cursor=today
    while cursor in active_dates: streak+=1;cursor-=timedelta(days=1)
    return ok({"date":today,"daily_calorie_target":p.daily_calorie_target,"intake_calories_kcal":nutrients["calories_kcal"],"remaining_calories_kcal":round(p.daily_calorie_target-nutrients["calories_kcal"],1),"nutrition":{"protein":{"consumed":nutrients["protein_g"],"target":p.protein_target_g},"carb":{"consumed":nutrients["carb_g"],"target":p.carb_target_g},"fat":{"consumed":nutrients["fat_g"],"target":p.fat_target_g}},"workout_duration_min":duration,"workout_calories_kcal":burned,"streak_days":streak})
@router.get("/stats/calendar")
def calendar(year:int=Query(ge=2000,le=2100),month:int=Query(ge=1,le=12),user=Depends(current_user),db:Session=Depends(get_db)):
    start=date(year,month,1); end=date(year,month,monthrange(year,month)[1]); xs=db.query(WorkoutSession).filter(WorkoutSession.user_id==user.id,WorkoutSession.workout_date.between(start,end)).all(); out={}
    for x in xs: out.setdefault(str(x.workout_date),{"date":x.workout_date,"sessions":0,"duration_min":0,"calories_kcal":0});out[str(x.workout_date)]["sessions"]+=1;out[str(x.workout_date)]["duration_min"]+=x.duration_min or 0;out[str(x.workout_date)]["calories_kcal"]+=x.calories_kcal
    return ok(list(out.values()))
@router.get("/stats/monthly")
def monthly(year:int=Query(ge=2000,le=2100),month:int=Query(ge=1,le=12),user=Depends(current_user),db:Session=Depends(get_db)):
    start=date(year,month,1);end=date(year,month,monthrange(year,month)[1]); xs=db.query(WorkoutSession).filter(WorkoutSession.user_id==user.id,WorkoutSession.workout_date.between(start,end),WorkoutSession.status=="已完成").all(); parts=[]
    for x in xs:
        for s in db.query(WorkoutSet).filter_by(session_id=x.id): parts.append(db.get(Exercise,s.exercise_id).body_part)
    return ok({"workout_count":len(xs),"total_duration_min":sum(x.duration_min or 0 for x in xs),"total_calories_kcal":round(sum(x.calories_kcal for x in xs),1),"most_trained_body_part":max(set(parts),key=parts.count) if parts else None})
@router.get("/stats/body-trend")
def body_trend(days:int=Query(30,ge=1,le=366),user=Depends(current_user),db:Session=Depends(get_db)):
    since=business_date()-timedelta(days=days-1); xs=db.query(WeightRecord).filter(WeightRecord.user_id==user.id,WeightRecord.record_date>=since).order_by(WeightRecord.record_date).all();p=db.get(UserProfile,user.id)
    current=xs[-1].weight_kg if xs else (p.current_weight_kg if p else None)
    target=p.target_weight_kg if p else None
    return ok({"weights":[{"date":x.record_date,"weight_kg":x.weight_kg} for x in xs],"current_weight_kg":current,"target_weight_kg":target,"target_difference_kg":round((current-target),1) if current is not None and target is not None else None,"period_change_kg":round(xs[-1].weight_kg-xs[0].weight_kg,1) if len(xs)>1 else 0})
