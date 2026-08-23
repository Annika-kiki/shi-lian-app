from backend.models.entities import Ingredient, Recipe, RecipeIngredient, RecipeStep


def nutrition_for_ingredients(rows):
    totals = {"calories_kcal": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0}
    for ingredient, amount in rows:
        factor = amount / 100
        totals["calories_kcal"] += ingredient.calories_kcal * factor
        totals["protein_g"] += ingredient.protein_g * factor
        totals["carb_g"] += ingredient.carb_g * factor
        totals["fat_g"] += ingredient.fat_g * factor
    return {key: round(value, 1) for key, value in totals.items()}


def recipe_payload(db, recipe: Recipe):
    links = db.query(RecipeIngredient).filter_by(recipe_id=recipe.id).all()
    ingredients = []
    for link in links:
        item = db.get(Ingredient, link.ingredient_id)
        ingredients.append({"id": item.id, "name": item.name, "amount_g": link.amount_g, "note": link.note})
    nutrition = nutrition_for_ingredients([(db.get(Ingredient, link.ingredient_id), link.amount_g) for link in links])
    steps = [x.content for x in db.query(RecipeStep).filter_by(recipe_id=recipe.id).order_by(RecipeStep.order_no)]
    return {"id": recipe.id, "name": recipe.name, "description": recipe.description, "minutes": recipe.minutes,
            "tags": recipe.tags.split(",") if recipe.tags else [], "cover_url": recipe.cover_url, "is_system": recipe.is_system,
            "ingredients": ingredients, "steps": steps, "nutrition": nutrition}
