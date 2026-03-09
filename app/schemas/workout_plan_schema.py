from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.exercise_schema import ExerciseDatabaseResponse

class WorkoutPlanCreate(BaseModel):
    name: str = Field(..., description="Nombre del plan de entrenamiento")
    description: Optional[str] = Field(None, description="Descripción del plan")
    user_id: int = Field(..., description="ID del usuario")
    plan_type: Optional[str] = Field(None, description="Tipo de plan")
    private: Optional[bool] = Field(False, description="¿Es privado?")

    class Config:
        from_attributes = True

class WorkoutPlanResponse(WorkoutPlanCreate):
    id: int = Field(..., description="ID del plan de entrenamiento")
    exercises: List[ExerciseDatabaseResponse] = Field(default=[], description="Ejercicios del plan")

class WorkoutPlanExerciseAdd(BaseModel):
    exercise_id: int = Field(..., description="ID del ejercicio a agregar")
