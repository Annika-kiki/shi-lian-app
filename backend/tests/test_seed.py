from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from backend.database import seed
from backend.database.session import Base
from backend.models.entities import Recipe, RecipeIngredient


def test_fresh_catalog_has_recipe_ingredients_and_is_idempotent(monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    session_factory = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(seed, 'engine', engine)
    monkeypatch.setattr(seed, 'SessionLocal', session_factory)
    seed.init_db()
    with session_factory() as db:
        recipes = db.scalars(select(Recipe)).all()
        assert len(recipes) == len(seed.RECIPES + seed.EXTRA_RECIPES)
        for recipe in recipes:
            count = db.scalar(select(func.count()).select_from(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id))
            assert count > 0, recipe.name
        initial_count = db.scalar(select(func.count()).select_from(RecipeIngredient))
    seed.init_db()
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(RecipeIngredient)) == initial_count
    engine.dispose()
