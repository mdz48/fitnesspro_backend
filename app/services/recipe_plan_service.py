from sqlalchemy.orm import Session
from app.repositories.recipe_plan_repository import RecipePlanRepository
from app.schemas.recipe_plan_schema import RecipePlanCreate

class RecipePlanService:
    def __init__(self):
        self.repository = RecipePlanRepository()

    def get_user_plans(self, db: Session, user_id: int):
        return self.repository.get_user_recipe_plans(db, user_id)

    def get_plan(self, db: Session, plan_id: int):
        return self.repository.get_recipe_plan(db, plan_id)

    def create_plan(self, db: Session, plan_data: RecipePlanCreate):
        plan_dict = plan_data.dict()
        user_id = plan_dict.get('user_id')
        return self.repository.create_recipe_plan(db, plan_dict, user_id)

    def add_recipe(self, db: Session, plan_id: int, recipe_id: int):
        return self.repository.add_recipe_to_plan(db, plan_id, recipe_id)

    def remove_recipe(self, db: Session, plan_id: int, recipe_id: int):
        return self.repository.remove_recipe_from_plan(db, plan_id, recipe_id)

    def delete_plan(self, db: Session, plan_id: int):
        return self.repository.delete_recipe_plan(db, plan_id)

recipe_plan_service = RecipePlanService()
