import re
from datetime import date, datetime, timedelta
from calendar import monthrange
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.config.settings import settings
from backend.database.session import get_db
from backend.models.entities import *
from backend.services.ai_provider import LocalRecipeProvider
from backend.services.nutrition import nutrition_for_ingredients, recipe_payload

router = APIRouter(prefix="/api")

def ok(data=None, message="ok"): return {"code": 0, "message": message, "data": data if data is not None else {}}
def current_user(x_user_id: int | None = Header(None), db: Session = Depends(get_db)):
    if not x_user_id: raise HTTPException(401, "缺少 X-User-Id；请先调用 mock-login")
    user = db.get(User, x_user_id)
    if not user: raise HTTPException(401, "用户不存在")
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

class LoginIn(BaseModel): nickname: str = Field(default="食练周期用户", max_length=64); avatar: str | None = None; mock_openid: str | None = None
class ProfileIn(BaseModel):
    gender: str | None = None; age: int | None = Field(None, ge=1, le=120); height_cm: float | None = Field(None, ge=50, le=260); current_weight_kg: float | None = Field(None, gt=0, le=500); target_weight_kg: float | None = Field(None, gt=0, le=500); goal_type: str = "保持健康"; daily_calorie_target: float | None = Field(None, gt=0); protein_target_g: float | None = Field(None, ge=0); carb_target_g: float | None = Field(None, ge=0); fat_target_g: float | None = Field(None, ge=0)
class WeightIn(BaseModel): record_date: date = Field(default_factory=date.today); weight_kg: float = Field(gt=0, le=500)
class RecipeGenerateIn(BaseModel): ingredients: list[str] = Field(min_length=1); meal_type: str; target_calories: int = Field(500, ge=100, le=2000); preference: str | None = None; recipe_round: int = Field(0, ge=0)
class MealIngredientIn(BaseModel): ingredient_id: int; amount_g: float = Field(gt=0, le=3000)
class MealIn(BaseModel): record_date: date = Field(default_factory=date.today); meal_type: str; name: str | None = None; recipe_id: int | None = None; ingredients: list[MealIngredientIn] = Field(default_factory=list); note: str | None = None
class SessionIn(BaseModel): workout_date: date = Field(default_factory=date.today); title: str = Field(min_length=1,max_length=100); duration_min: int | None = Field(None, ge=0, le=1440)
class CardioSessionIn(BaseModel): workout_date: date = Field(default_factory=date.today); mode: str | None = Field(default=None, max_length=50); duration_min: int | None = Field(None, ge=1, le=360); detail: str | None = Field(None, max_length=255)
class SessionUpdateIn(BaseModel): title: str | None = None; duration_min: int | None = Field(None, ge=0, le=1440); workout_date: date | None = None
class SetIn(BaseModel): exercise_id: int; set_no: int = Field(ge=1); weight_kg: float | None = Field(None, ge=0); reps: int | None = Field(None, ge=0); completed: bool = False
class SetUpdateIn(BaseModel): weight_kg: float | None = Field(None, ge=0); reps: int | None = Field(None, ge=0); completed: bool | None = None

@router.post("/auth/mock-login")
def mock_login(body: LoginIn, db: Session = Depends(get_db)):
    openid = body.mock_openid or f"mock_{body.nickname}"
    user = db.query(User).filter_by(openid=openid).first()
    if not user:
        user = User(openid=openid, nickname=body.nickname, avatar=body.avatar); db.add(user); db.flush(); db.add(UserProfile(user_id=user.id))
    else: user.nickname, user.avatar = body.nickname, body.avatar
    db.commit(); return ok({"user_id": user.id, "access_token": f"mock-user-{user.id}", "token_type": "Use X-User-Id header"})
@router.post("/auth/wechat-login")
def wechat_login():
    if not settings.wechat_app_id or not settings.wechat_app_secret: raise HTTPException(501, "微信登录尚未配置：请设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
    raise HTTPException(501, "微信 code 换取服务接口已预留，MVP 请使用 mock-login")
@router.get("/users/me")
def me(user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.get(UserProfile,user.id); created_date=(user.created_at+timedelta(hours=8)).date() if user.created_at else date.today(); return ok({"id":user.id,"openid":user.openid,"nickname":user.nickname,"avatar":user.avatar,"created_at":user.created_at,"created_date":created_date,"profile":profile_dict(p)})
@router.put("/users/me/profile")
def update_profile(body: ProfileIn, user=Depends(current_user), db: Session=Depends(get_db)):
    p=db.get(UserProfile,user.id)
    if not p:
        p=UserProfile(user_id=user.id); db.add(p)
    for k,v in body.model_dump().items(): setattr(p,k,v)
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
    since=date.today()-timedelta(days=days-1); r=db.query(WeightRecord).filter(WeightRecord.user_id==user.id,WeightRecord.record_date>=since).order_by(WeightRecord.record_date).all(); return ok([{"date":x.record_date,"weight_kg":x.weight_kg} for x in r])

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
def generate(body:RecipeGenerateIn,db:Session=Depends(get_db)): return ok(LocalRecipeProvider().generate(db,body.ingredients,body.target_calories,body.preference,body.recipe_round))
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
def meals(date_:date=Query(default_factory=date.today,alias="date"),user=Depends(current_user),db:Session=Depends(get_db)):
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
CARDIO_MET = {
    "快走": 4.3,
    "坡度走": 5.3,
    "爬坡": 6.5,
    "椭圆机": 5.0,
    "骑行": 6.0,
    "慢跑": 7.0,
    "跑步": 8.0,
    "划船机": 7.0,
    "风阻单车": 7.5,
    "跳绳": 10.0,
    "游泳": 8.0,
    "蛙泳": 10.3,
    "自由泳": 8.3,
}

CARDIO_MODE_ALIASES = [
    ("蛙泳", "蛙泳"),
    ("自由泳", "自由泳"),
    ("游泳", "游泳"),
    ("爬坡", "爬坡"),
    ("坡度", "爬坡"),
    ("快走", "快走"),
    ("椭圆", "椭圆机"),
    ("骑行", "骑行"),
    ("单车", "骑行"),
    ("慢跑", "慢跑"),
    ("跑步", "跑步"),
    ("划船", "划船机"),
    ("跳绳", "跳绳"),
]

def detect_cardio_mode(text: str, fallback: str | None = None) -> str:
    for keyword, mode in CARDIO_MODE_ALIASES:
        if keyword in text:
            return mode
    return (fallback or "快走").strip() or "快走"

def format_cardio_number(value: float) -> str:
    return f"{value:g}"

def parse_cardio_segments(detail: str | None, mode: str | None, duration_min: int | None):
    text=(detail or "").strip()
    fallback_mode=detect_cardio_mode(text,mode)
    incline_pattern=re.compile(r"(?:爬坡|坡度走)?\s*坡度\s*(\d+(?:\.\d+)?)\s*(?:速度|时速)\s*(\d+(?:\.\d+)?)\s*(?:公里/小时|km/h|kmh)?\s*(\d+(?:\.\d+)?)\s*分钟")
    segments=[]
    for match in incline_pattern.finditer(text):
        incline=float(match.group(1)); speed=float(match.group(2)); minutes=round(float(match.group(3)))
        segments.append({
            "mode":"爬坡",
            "duration_min":minutes,
            "incline_percent":incline,
            "speed_kmh":speed,
            "label":f"坡度{format_cardio_number(incline)}速度{format_cardio_number(speed)} {minutes}分钟"
        })
    if segments:
        return segments

    mode_names="蛙泳|自由泳|游泳|快走|坡度走|爬坡|椭圆机|椭圆|骑行|慢跑|跑步|划船机|划船|风阻单车|跳绳"
    normal_pattern=re.compile(rf"({mode_names})\s*(\d+(?:\.\d+)?)\s*分钟")
    for match in normal_pattern.finditer(text):
        raw_mode=match.group(1)
        cardio_mode=detect_cardio_mode(raw_mode,mode)
        minutes=round(float(match.group(2)))
        segments.append({"mode":cardio_mode,"duration_min":minutes,"label":f"{cardio_mode}{minutes}分钟"})
    if segments:
        return segments

    if duration_min:
        return [{"mode":fallback_mode,"duration_min":duration_min,"label":f"{fallback_mode}{duration_min}分钟"}]

    duration_match=re.search(r"(\d+(?:\.\d+)?)\s*分钟",text)
    if duration_match:
        minutes=round(float(duration_match.group(1)))
        return [{"mode":fallback_mode,"duration_min":minutes,"label":f"{fallback_mode}{minutes}分钟"}]

    raise HTTPException(422,"请输入有氧方式和时间，例如：蛙泳40分钟，或：坡度10速度5.5 10分钟")

def cardio_segment_met(segment) -> float:
    speed=segment.get("speed_kmh")
    incline=segment.get("incline_percent")
    if speed is not None and incline is not None:
        meters_per_min=speed*1000/60
        vo2=0.1*meters_per_min+1.8*meters_per_min*(incline/100)+3.5
        return max(3.0, vo2/3.5)
    return CARDIO_MET.get(segment["mode"], 5.0)

def estimate_cardio_calories(profile, mode: str, duration_min: int, speed_kmh: float | None = None, incline_percent: float | None = None) -> float:
    weight = profile.current_weight_kg or 60
    height = profile.height_cm or 165
    met = cardio_segment_met({"mode":mode,"speed_kmh":speed_kmh,"incline_percent":incline_percent})
    height_factor = min(1.1, max(0.95, height / 170))
    return round(met * 3.5 * weight / 200 * duration_min * height_factor, 1)

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
    if not profile:
        profile=UserProfile(user_id=user.id); db.add(profile); db.flush()
    goal_code=GOAL_ALIASES.get(profile.goal_type, "shaping")
    goal=db.get(TrainingGoal,goal_code)
    display_goal_name = "增肌" if profile.goal_type == "增肌" else goal.name
    display_description = "提高肌肉量和训练容量，优先安排复合动作与中高次数抗阻训练。" if profile.goal_type == "增肌" else goal.description
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
                          "primary_muscle":exercise_item.primary_muscle,
                          "equipment":exercise_item.equipment,
                          "difficulty":exercise_item.difficulty,
                          "thumbnail_url":exercise_item.thumbnail_url,
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
    return ok({"title":f"{display_goal_name}推荐训练","estimated_duration_min":50,
               "goal":{"code":goal.code,"name":display_goal_name,"description":display_description},
               "level":level,"principles":{"resistance":goal.resistance_principle,
               "cardio":goal.cardio_principle},"exercises":exercises,"cardio":cardio_data,
               "safety_note":"计划仅供一般健康成年人参考；如有疾病、伤病、孕期或运动中出现疼痛，请先咨询专业人员。"})
@router.post("/workouts/sessions")
def create_session(body:SessionIn,user=Depends(current_user),db:Session=Depends(get_db)):
    x=WorkoutSession(user_id=user.id,**body.model_dump());db.add(x);db.commit();return ok(session_data(db,x))
@router.post("/workouts/cardio")
def create_cardio_session(body:CardioSessionIn,user=Depends(current_user),db:Session=Depends(get_db)):
    profile=db.get(UserProfile,user.id)
    if not profile:
        profile=UserProfile(user_id=user.id); db.add(profile); db.flush()
    segments=parse_cardio_segments(body.detail,body.mode,body.duration_min)
    duration=sum(segment["duration_min"] for segment in segments)
    calories=round(sum(estimate_cardio_calories(profile,segment["mode"],segment["duration_min"],segment.get("speed_kmh"),segment.get("incline_percent")) for segment in segments),1)
    title=segments[0]["label"] if len(segments)==1 else " + ".join(segment["label"] for segment in segments)
    x=WorkoutSession(user_id=user.id,workout_date=body.workout_date,title=title,
                     duration_min=duration,calories_kcal=calories,
                     status="已完成",completed_at=datetime.utcnow())
    db.add(x);db.commit();return ok({**session_data(db,x),"cardio_segments":segments})
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
    x.status="已完成";x.completed_at=datetime.utcnow();db.commit();return ok({**session_data(db,x),"calorie_estimated":estimated})

@router.get("/dashboard/today")
def dashboard(user=Depends(current_user),db:Session=Depends(get_db)):
    today=date.today(); p=db.get(UserProfile,user.id); meals=db.query(MealRecord).filter_by(user_id=user.id,record_date=today).all(); ws=db.query(WorkoutSession).filter_by(user_id=user.id,workout_date=today,status="已完成").all()
    if not p:
        p=UserProfile(user_id=user.id); db.add(p)
    apply_profile_targets(p)
    nutrients={k:round(sum(getattr(m,k) for m in meals),1) for k in ("calories_kcal","protein_g","carb_g","fat_g")}; duration=sum(w.duration_min or 0 for w in ws); burned=round(sum(w.calories_kcal for w in ws),1)
    daily_budget=round(p.daily_calorie_target+burned,1)
    active_dates={d for (d,) in db.query(MealRecord.record_date).filter_by(user_id=user.id).distinct()} | {d for (d,) in db.query(WorkoutSession.workout_date).filter_by(user_id=user.id).distinct()}
    streak=0; cursor=today
    while cursor in active_dates: streak+=1;cursor-=timedelta(days=1)
    return ok({"date":today,"base_calorie_target":p.daily_calorie_target,"daily_calorie_target":daily_budget,"intake_calories_kcal":nutrients["calories_kcal"],"remaining_calories_kcal":round(daily_budget-nutrients["calories_kcal"],1),"nutrition":{"protein":{"consumed":nutrients["protein_g"],"target":p.protein_target_g},"carb":{"consumed":nutrients["carb_g"],"target":p.carb_target_g},"fat":{"consumed":nutrients["fat_g"],"target":p.fat_target_g}},"workout_duration_min":duration,"workout_calories_kcal":burned,"streak_days":streak})
@router.get("/stats/calendar")
def calendar(year:int,month:int,user=Depends(current_user),db:Session=Depends(get_db)):
    start=date(year,month,1); end=date(year,month,monthrange(year,month)[1]); today=date.today(); login_date=(user.created_at+timedelta(hours=8)).date() if user.created_at else today
    visible_start=max(start,login_date); visible_end=min(end,today)
    if visible_start>visible_end: return ok([])
    xs=db.query(WorkoutSession).filter(WorkoutSession.user_id==user.id,WorkoutSession.workout_date.between(visible_start,visible_end),WorkoutSession.status=="已完成").all()
    meals=db.query(MealRecord).filter(MealRecord.user_id==user.id,MealRecord.record_date.between(visible_start,visible_end)).all()
    out={}
    cursor=visible_start
    while cursor<=visible_end:
        out[str(cursor)]={"date":cursor,"sessions":0,"duration_min":0,"calories_kcal":0,"meal_count":0,"intake_calories_kcal":0,"status":"休息日"}
        cursor+=timedelta(days=1)
    for x in xs:
        item=out[str(x.workout_date)]; item["sessions"]+=1; item["duration_min"]+=x.duration_min or 0; item["calories_kcal"]=round(item["calories_kcal"]+(x.calories_kcal or 0),1); item["status"]="训练日"
    for m in meals:
        item=out[str(m.record_date)]; item["meal_count"]+=1; item["intake_calories_kcal"]=round(item["intake_calories_kcal"]+(m.calories_kcal or 0),1)
    return ok(list(out.values()))
@router.get("/stats/monthly")
def monthly(year:int,month:int,user=Depends(current_user),db:Session=Depends(get_db)):
    start=date(year,month,1);end=date(year,month,monthrange(year,month)[1]); xs=db.query(WorkoutSession).filter(WorkoutSession.user_id==user.id,WorkoutSession.workout_date.between(start,end),WorkoutSession.status=="已完成").all(); parts=[]
    for x in xs:
        for s in db.query(WorkoutSet).filter_by(session_id=x.id): parts.append(db.get(Exercise,s.exercise_id).body_part)
    return ok({"workout_count":len(xs),"total_duration_min":sum(x.duration_min or 0 for x in xs),"total_calories_kcal":round(sum(x.calories_kcal for x in xs),1),"most_trained_body_part":max(set(parts),key=parts.count) if parts else None})
@router.get("/stats/body-trend")
def body_trend(days:int=Query(30,ge=1,le=366),user=Depends(current_user),db:Session=Depends(get_db)):
    since=date.today()-timedelta(days=days-1); xs=db.query(WeightRecord).filter(WeightRecord.user_id==user.id,WeightRecord.record_date>=since).order_by(WeightRecord.record_date).all();p=db.get(UserProfile,user.id); current=xs[-1].weight_kg if xs else p.current_weight_kg;return ok({"weights":[{"date":x.record_date,"weight_kg":x.weight_kg} for x in xs],"current_weight_kg":current,"target_difference_kg":round((current-p.target_weight_kg),1) if current and p.target_weight_kg else None,"period_change_kg":round(xs[-1].weight_kg-xs[0].weight_kg,1) if len(xs)>1 else 0})
