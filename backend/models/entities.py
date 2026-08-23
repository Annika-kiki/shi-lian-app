from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.session import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="练食记用户")
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    height_cm: Mapped[float | None] = mapped_column(nullable=True)
    current_weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    target_weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    goal_type: Mapped[str] = mapped_column(String(16), default="保持健康")
    daily_calorie_target: Mapped[float] = mapped_column(default=2000)
    protein_target_g: Mapped[float] = mapped_column(default=100)
    carb_target_g: Mapped[float] = mapped_column(default=250)
    fat_target_g: Mapped[float] = mapped_column(default=60)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)


class WeightRecord(Base):
    __tablename__ = "weight_records"
    __table_args__ = (UniqueConstraint("user_id", "record_date", name="uq_weight_user_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    record_date: Mapped[date] = mapped_column(Date, index=True)
    weight_kg: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    aliases: Mapped[str] = mapped_column(String(255), default="")
    calories_kcal: Mapped[float]
    protein_g: Mapped[float]
    carb_g: Mapped[float]
    fat_g: Mapped[float]
    unit: Mapped[str] = mapped_column(String(20), default="g")


class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    minutes: Mapped[int] = mapped_column(default=15)
    tags: Mapped[str] = mapped_column(String(255), default="")
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)
    amount_g: Mapped[float]
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)


class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    order_no: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)


class MealRecord(Base):
    __tablename__ = "meal_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    record_date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(16))
    recipe_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    calories_kcal: Mapped[float]
    protein_g: Mapped[float]
    carb_g: Mapped[float]
    fat_g: Mapped[float]
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FavoriteRecipe(Base):
    __tablename__ = "favorite_recipes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    body_part: Mapped[str] = mapped_column(String(50))
    primary_muscle: Mapped[str] = mapped_column(String(100))
    secondary_muscle: Mapped[str] = mapped_column(String(100), default="")
    equipment: Mapped[str] = mapped_column(String(50), default="徒手")
    difficulty: Mapped[str] = mapped_column(String(20), default="初级")
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    steps: Mapped[str] = mapped_column(Text, default="")
    cautions: Mapped[str] = mapped_column(Text, default="")
    met: Mapped[float] = mapped_column(default=5.0)


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    workout_date: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(100))
    duration_min: Mapped[int | None] = mapped_column(nullable=True)
    calories_kcal: Mapped[float] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(16), default="进行中")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    set_no: Mapped[int]
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    reps: Mapped[int | None] = mapped_column(nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class FavoriteExercise(Base):
    __tablename__ = "favorite_exercises"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), primary_key=True)
