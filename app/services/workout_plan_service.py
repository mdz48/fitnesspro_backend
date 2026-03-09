from sqlalchemy.orm import Session
from app.repositories.workout_plan_repository import WorkoutPlanRepository
from app.schemas.workout_plan_schema import WorkoutPlanCreate

class WorkoutPlanService:
    def __init__(self):
        self.repository = WorkoutPlanRepository()

    def get_user_plans(self, db: Session, user_id: int):
        return self.repository.get_user_workout_plans(db, user_id)

    def get_plan(self, db: Session, plan_id: int):
        return self.repository.get_workout_plan(db, plan_id)

    def create_plan(self, db: Session, plan_data: WorkoutPlanCreate):
        plan_dict = plan_data.dict()
        user_id = plan_dict.get('user_id')
        return self.repository.create_workout_plan(db, plan_dict, user_id)

    def add_exercise(self, db: Session, plan_id: int, exercise_id: int):
        return self.repository.add_exercise_to_plan(db, plan_id, exercise_id)

    def remove_exercise(self, db: Session, plan_id: int, exercise_id: int):
        return self.repository.remove_exercise_from_plan(db, plan_id, exercise_id)

    def delete_plan(self, db: Session, plan_id: int):
        return self.repository.delete_workout_plan(db, plan_id)

workout_plan_service = WorkoutPlanService()
