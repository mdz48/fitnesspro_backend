from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.shared.config.database import get_db
from app.schemas.workout_plan_schema import WorkoutPlanCreate, WorkoutPlanResponse, WorkoutPlanExerciseAdd
from app.schemas.exercise_schema import ExerciseDatabaseResponse
from app.services.workout_plan_service import workout_plan_service

workout_plan_router = APIRouter()

@workout_plan_router.get("/user/{user_id}", response_model=List[WorkoutPlanResponse])
def get_user_workout_plans(user_id: int, db: Session = Depends(get_db)):
    """Obtener todas las listas de ejercicios que tiene un usuario"""
    return workout_plan_service.get_user_plans(db, user_id)

@workout_plan_router.post("/", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def create_workout_plan(plan_data: WorkoutPlanCreate, db: Session = Depends(get_db)):
    """Crear un nuevo plan de entrenamiento"""
    return workout_plan_service.create_plan(db, plan_data)

@workout_plan_router.post("/{plan_id}/exercises", response_model=WorkoutPlanResponse)
def add_exercise_to_plan(plan_id: int, exercise_data: WorkoutPlanExerciseAdd, db: Session = Depends(get_db)):
    """Agregar un ejercicio a un plan de entrenamiento"""
    current_plan = workout_plan_service.get_plan(db, plan_id)
    if current_plan and any(ex.id == exercise_data.exercise_id for ex in current_plan.exercises):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ejercicio ya está en el plan")
    plan = workout_plan_service.add_exercise(db, plan_id, exercise_data.exercise_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan o ejercicio no encontrado")
    return plan

@workout_plan_router.get("/{plan_id}/exercises", response_model=List[ExerciseDatabaseResponse])
def get_plan_exercises(plan_id: int, db: Session = Depends(get_db)):
    """Obtener todos los ejercicios de un plan"""
    plan = workout_plan_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan.exercises

@workout_plan_router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_plan(plan_id: int, db: Session = Depends(get_db)):
    """Eliminar un plan de entrenamiento completo"""
    success = workout_plan_service.delete_plan(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return None

@workout_plan_router.delete("/{plan_id}/exercises/{exercise_id}", response_model=WorkoutPlanResponse)
def remove_exercise_from_plan(plan_id: int, exercise_id: int, db: Session = Depends(get_db)):
    """Eliminar un ejercicio específico de un plan"""
    plan = workout_plan_service.remove_exercise(db, plan_id, exercise_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan o ejercicio no encontrado")
    return plan
