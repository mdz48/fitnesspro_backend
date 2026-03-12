from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class RecipeBase(BaseModel):
    name: str
    description: str
    ingredients: str
    instructions: Optional[str] = None
    user_id: int | None = 1
    scheduled_days: Optional[set[str]] = None
    meal_type: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    
class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[str] = None
    user_id: Optional[int] = None
    scheduled_days: Optional[set[str]] = None
    meal_type: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class RecipeResponse(RecipeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
