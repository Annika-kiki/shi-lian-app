"""Database-backed quick food logging; independent of legacy recipe ingredients."""
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.session import Base
from backend.models.entities import utc_now

OPTIONS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (Index("ix_foods_name", "name"), Index("ix_foods_category", "category"), OPTIONS)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    kcal_per_100g: Mapped[float] = mapped_column(Float)
    protein_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_per_100g: Mapped[float | None] = mapped_column(Float, nullable=True)
    default_quantity_g: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    unit: Mapped[str] = mapped_column(String(16), default="份", server_default="份")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class ConfirmedMeal(Base):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_date", "user_id", "record_date"), OPTIONS)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    meal_type: Mapped[str] = mapped_column(String(16))
    food_name: Mapped[str] = mapped_column(String(64))
    quantity_g: Mapped[float] = mapped_column(Float)
    kcal: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    raw_text: Mapped[str] = mapped_column(Text)
    record_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
