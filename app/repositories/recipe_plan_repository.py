from sqlalchemy.orm import Session
from app.models.RecipePlans import RecipePlan
from app.models.Recipe import Recipe

class RecipePlanRepository:
    def get_user_recipe_plans(self, db: Session, user_id: int):
        return db.query(RecipePlan).filter(RecipePlan.user_id == user_id).all()

    def get_recipe_plan(self, db: Session, plan_id: int):
        return db.query(RecipePlan).filter(RecipePlan.id == plan_id).first()

    def create_recipe_plan(self, db: Session, plan_data: dict, user_id: int):
        new_plan = RecipePlan(**plan_data)
        new_plan.user_id = user_id
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return new_plan

    def add_recipe_to_plan(self, db: Session, plan_id: int, recipe_id: int):
        plan = db.query(RecipePlan).filter(RecipePlan.id == plan_id).first()
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

        if not plan or not recipe:
            return None

        if recipe not in plan.recipes:
            plan.recipes.append(recipe)
            db.commit()
            db.refresh(plan)

        return plan

    def remove_recipe_from_plan(self, db: Session, plan_id: int, recipe_id: int):
        plan = db.query(RecipePlan).filter(RecipePlan.id == plan_id).first()
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

        if not plan or not recipe:
            return None

        if recipe in plan.recipes:
            plan.recipes.remove(recipe)
            db.commit()
            db.refresh(plan)

        return plan

    def delete_recipe_plan(self, db: Session, plan_id: int):
        plan = db.query(RecipePlan).filter(RecipePlan.id == plan_id).first()
        if not plan:
            return False

        db.delete(plan)
        db.commit()
        return True
