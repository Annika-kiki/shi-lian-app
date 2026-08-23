"""Stable local recipe provider; replace LocalRecipeProvider with an LLM implementation later."""
from backend.services.nutrition import recipe_payload


class LocalRecipeProvider:
    def generate(self, db, ingredient_names: list[str], target_calories: int, preference: str | None):
        from backend.models.entities import Recipe
        recipes = db.query(Recipe).all()
        lowered = set(" ".join(ingredient_names).lower())
        scored = []
        for recipe in recipes:
            item = recipe_payload(db, recipe)
            names = " ".join(x["name"] for x in item["ingredients"]).lower()
            score = sum(name.lower() in names for name in ingredient_names) * 100
            score -= abs(item["nutrition"]["calories_kcal"] - target_calories)
            if preference and preference in recipe.tags: score += 30
            scored.append((score, item))
        result = [x[1] for x in sorted(scored, key=lambda x: x[0], reverse=True)[:3]]
        # Seeded database always has three recipes; retain a predictable response if expanded later.
        return result
