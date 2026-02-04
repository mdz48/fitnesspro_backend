from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.recipie_schema import RecipeResponse

class ListBase(BaseModel):
    list_name: str
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class ListCreate(ListBase):
    pass

class ListResponse(ListBase):
    id: int
    recipes: Optional[list[RecipeResponse]] = []