from typing import List
from sqlalchemy.orm import Session
from app.models.Recipe import Recipe
from app.repositories.base_repository import BaseRepository


class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, db: Session):
        super().__init__(Recipe, db)
    
    def get_by_user(self, user_id: int) -> List[Recipe]:
        return self.db.query(Recipe).filter(Recipe.user_id == user_id).all()
