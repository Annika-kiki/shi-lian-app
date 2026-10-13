from datetime import UTC, datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from backend.models.food import ConfirmedMeal
from backend.models.entities import MealRecord
from backend.services.food import numeric

FIELDS = ('food_name', 'meal_type', 'quantity_g', 'kcal', 'protein_g', 'carbs_g', 'fat_g')

def save_confirmed(db, user, body):
    try:
        for name, limit in [('text',1000), ('food_name',64), ('meal_type',16)]:
            value = body.get(name)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f'{name}必须为非空字符串，最多{limit}字符')
        for name in FIELDS[2:]:
            value = numeric(body.get(name), name, name == 'quantity_g')
            if value > 3.4e38: raise ValueError(f'{name}超出数据库范围')
        if isinstance(user.id, bool) or not isinstance(user.id, int) or user.id <= 0:
            raise ValueError('用户ID无效')
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    now = datetime.now(UTC)
    day = now.astimezone(ZoneInfo('Asia/Shanghai')).date()
    row = ConfirmedMeal(user_id=user.id, raw_text=body['text'], record_date=day,
                        created_at=now.replace(tzinfo=None), **{k:body[k] for k in FIELDS})
    # Keep existing dashboard and report aggregation in sync in the same transaction.
    legacy = MealRecord(user_id=user.id, record_date=day, meal_type=row.meal_type,
                        name=row.food_name, note=row.raw_text[:255], calories_kcal=row.kcal,
                        protein_g=row.protein_g, carb_g=row.carbs_g, fat_g=row.fat_g)
    try:
        db.add_all([row, legacy])
        db.flush()
        result = {'code':0, 'data':{'id':row.id, 'created_at':now.isoformat().replace('+00:00','Z')}}
        db.commit()
        return result
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(503, '保存失败，请稍后重试') from exc
