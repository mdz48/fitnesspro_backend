from pydantic import BaseModel, Field
from typing import List
from app.schemas.exercise_schema import ExerciseDatabaseResponse
from app.schemas.recipe_schema import RecipeResponse


class UserDailyContentResponse(BaseModel):
    user_id: int = Field(..., description="ID del usuario")
    user_name : str = Field(..., description="Nombre del usuario")
    user_lastname : str = Field(..., description="Apellido del usuario")
    day: str = Field(..., description="Día aplicado para el filtro")
    timezone: str = Field(..., description="Zona horaria usada para resolver el día")
    exercises: List[ExerciseDatabaseResponse] = Field(default=[], description="Ejercicios del usuario para el día")
    recipes: List[RecipeResponse] = Field(default=[], description="Recetas del usuario para el día")
