import unittest
from nutrition import calculate, normalize_food
from recipe_engine import generate_recipe
from training_engine import generate_plan, list_exercises


class NutritionTests(unittest.TestCase):
    def test_alias(self):
        self.assertEqual(normalize_food("番茄"), "西红柿")

    def test_calculation(self):
        result = calculate([{"name": "鸡胸肉", "grams": 100}])
        self.assertEqual(result["totals"]["kcal"], 133.0)
        self.assertEqual(result["totals"]["protein"], 24.6)

    def test_expanded_database(self):
        from nutrition import FOODS
        self.assertGreaterEqual(len(FOODS), 50)
        self.assertIn("藜麦", FOODS)


class RecipeTests(unittest.TestCase):
    def test_structured_recipe(self):
        result = generate_recipe(["鸡胸肉", "番茄", "西兰花", "米饭"], 500, ["高蛋白", "少油"])
        recipe = result["recipe"]
        self.assertGreaterEqual(len(result["recipes"]), 2)
        self.assertTrue(recipe["name"])
        self.assertGreaterEqual(len(recipe["steps"]), 3)
        self.assertGreater(recipe["nutrition"]["protein"], 20)
        self.assertLess(abs(recipe["nutrition"]["kcal"] - 500), 80)

    def test_unknown_food_warning(self):
        result = generate_recipe(["鸡胸肉", "火龙果"], 450)
        self.assertTrue(result["warnings"])

    def test_invalid_target(self):
        with self.assertRaises(ValueError):
            generate_recipe(["鸡蛋"], 100)


class TrainingTests(unittest.TestCase):
    def test_exercise_database(self):
        self.assertGreaterEqual(len(list_exercises()), 12)
        self.assertTrue(list_exercises(muscle="胸"))
        self.assertGreaterEqual(
            sum(bool(item["illustration"]) for item in list_exercises()), 8)

    def test_plan_structure(self):
        plan = generate_plan("减脂", "新手", 3)
        self.assertEqual(len(plan["sessions"]), 3)
        self.assertTrue(all(session["exercises"] for session in plan["sessions"]))


if __name__ == "__main__":
    unittest.main()
