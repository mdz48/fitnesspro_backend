from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.recipe_schema import RecipeResponse

class RecipePlanCreate(BaseModel):
    name: str = Field(..., description="Nombre del plan de recetas")
    description: Optional[str] = Field(None, description="Descripción del plan")
    user_id: int = Field(..., description="ID del usuario")
    private: Optional[bool] = Field(False, description="¿Es privado?")

    class Config:
        from_attributes = True

class RecipePlanResponse(RecipePlanCreate):
    id: int = Field(..., description="ID del plan de recetas")
    recipes: List[RecipeResponse] = Field(default=[], description="Recetas del plan")

class RecipePlanRecipeAdd(BaseModel):
    recipe_id: int = Field(..., description="ID de la receta a agregar")
