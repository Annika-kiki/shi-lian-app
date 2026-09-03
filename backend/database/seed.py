from backend.database.session import Base, engine, SessionLocal
from backend.database.catalog import (CARDIO_PRESCRIPTIONS, EXERCISES,
    GOAL_EXERCISE_PRESCRIPTIONS, INGREDIENTS, RECIPES, TRAINING_GOALS)
from backend.models.entities import (CardioPrescription, Exercise,
    GoalExercisePrescription, Ingredient, Recipe, RecipeIngredient, RecipeStep,
    TrainingGoal)


def init_db():
    """Idempotently upgrade catalog data without deleting user records."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for name, aliases, kcal, protein, carb, fat in INGREDIENTS:
            item = db.query(Ingredient).filter_by(name=name).first()
            values = dict(aliases=aliases, calories_kcal=kcal, protein_g=protein, carb_g=carb, fat_g=fat)
            if item:
                for key, value in values.items(): setattr(item, key, value)
            else:
                db.add(Ingredient(name=name, **values))
        db.flush()
        ingredients = {x.name: x for x in db.query(Ingredient).all()}

        for name, description, minutes, tags, parts, steps in RECIPES:
            recipe = db.query(Recipe).filter_by(name=name).first()
            if not recipe:
                recipe = Recipe(name=name); db.add(recipe); db.flush()
            recipe.description, recipe.minutes, recipe.tags = description, minutes, tags
            db.query(RecipeIngredient).filter_by(recipe_id=recipe.id).delete()
            db.query(RecipeStep).filter_by(recipe_id=recipe.id).delete()
            db.add_all([RecipeIngredient(recipe_id=recipe.id, ingredient_id=ingredients[n].id, amount_g=g) for n, g in parts])
            db.add_all([RecipeStep(recipe_id=recipe.id, order_no=i + 1, content=step) for i, step in enumerate(steps)])

        for name, part, primary, secondary, equipment, difficulty, image, steps, caution, met in EXERCISES:
            exercise = db.query(Exercise).filter_by(name=name).first()
            values = dict(body_part=part, primary_muscle=primary, secondary_muscle=secondary,
                          equipment=equipment, difficulty=difficulty,
                          thumbnail_url=f"/images/exercises/{image}", steps=steps, cautions=caution, met=met)
            if exercise:
                for key, value in values.items(): setattr(exercise, key, value)
            else:
                db.add(Exercise(name=name, **values))
        db.flush()
        exercises = {x.name: x for x in db.query(Exercise).all()}

        for code, name, description, resistance, cardio in TRAINING_GOALS:
            goal = db.get(TrainingGoal, code)
            values = dict(name=name, description=description,
                          resistance_principle=resistance, cardio_principle=cardio, active=True)
            if goal:
                for key, value in values.items(): setattr(goal, key, value)
            else:
                db.add(TrainingGoal(code=code, **values))
        db.flush()

        for row in GOAL_EXERCISE_PRESCRIPTIONS:
            (goal_code, exercise_name, priority, pattern, sets_min, sets_max,
             reps_min, reps_max, duration, rest, rir_min, rir_max, notes) = row
            exercise_id = exercises[exercise_name].id
            item = db.query(GoalExercisePrescription).filter_by(
                goal_code=goal_code, exercise_id=exercise_id).first()
            values = dict(priority=priority, movement_pattern=pattern, sets_min=sets_min,
                          sets_max=sets_max, reps_min=reps_min, reps_max=reps_max,
                          duration_seconds=duration, rest_seconds=rest, rir_min=rir_min,
                          rir_max=rir_max, notes=notes)
            if item:
                for key, value in values.items(): setattr(item, key, value)
            else:
                db.add(GoalExercisePrescription(goal_code=goal_code,
                                                exercise_id=exercise_id, **values))

        for row in CARDIO_PRESCRIPTIONS:
            (goal_code, level, modes, sessions_min, sessions_max, minutes_min,
             minutes_max, method, intensity_min, intensity_max, work, rest, notes) = row
            item = db.query(CardioPrescription).filter_by(goal_code=goal_code, level=level).first()
            values = dict(modes=modes, sessions_min=sessions_min, sessions_max=sessions_max,
                          minutes_min=minutes_min, minutes_max=minutes_max,
                          intensity_method=method, intensity_min=intensity_min,
                          intensity_max=intensity_max, interval_work_seconds=work,
                          interval_rest_seconds=rest, notes=notes)
            if item:
                for key, value in values.items(): setattr(item, key, value)
            else:
                db.add(CardioPrescription(goal_code=goal_code, level=level, **values))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__": init_db()
