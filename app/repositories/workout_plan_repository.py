from sqlalchemy.orm import Session
from app.models.WorkoutPlans import WorkoutPlan
from app.models.Exercise import Exercise

class WorkoutPlanRepository:
    def get_user_workout_plans(self, db: Session, user_id: int):
        return db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).all()
        
    def get_workout_plan(self, db: Session, plan_id: int):
        return db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()

    def create_workout_plan(self, db: Session, plan_data: dict, user_id: int):
        new_plan = WorkoutPlan(**plan_data)
        new_plan.user_id = user_id
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return new_plan
        
    def add_exercise_to_plan(self, db: Session, plan_id: int, exercise_id: int):
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        
        if not plan or not exercise:
            return None
            
        if exercise not in plan.exercises:
            plan.exercises.append(exercise)
            db.commit()
            db.refresh(plan)
            
        return plan

    def remove_exercise_from_plan(self, db: Session, plan_id: int, exercise_id: int):
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        
        if not plan or not exercise:
            return None
            
        if exercise in plan.exercises:
            plan.exercises.remove(exercise)
            db.commit()
            db.refresh(plan)
            
        return plan

    def delete_workout_plan(self, db: Session, plan_id: int):
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        if not plan:
            return False
            
        db.delete(plan)
        db.commit()
        return True

