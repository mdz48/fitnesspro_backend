from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class RecipeBase(BaseModel):
    name: str
    description: str
    ingredients: str
    instructions: str
    user_id: int | None = 1
    scheduled_days: Optional[set[str]] = None
    meal_type: Optional[str] = None
    
class RecipeCreate(RecipeBase):
    pass

class RecipeResponse(RecipeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
