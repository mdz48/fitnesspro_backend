from typing import List
from sqlalchemy.orm import Session
from app.models.Recipe import Recipe
from app.repositories.base_repository import BaseRepository


class RecipeRepository(BaseRepository[Recipe]):
    def __init__(self, db: Session):
        super().__init__(Recipe, db)
    
    def get_by_user(self, user_id: int) -> List[Recipe]:
        return self.db.query(Recipe).filter(Recipe.user_id == user_id).all()

    def get_by_user_and_day(self, user_id: int, day: str) -> List[Recipe]:
        return self.db.query(Recipe).filter(
            Recipe.user_id == user_id,
            Recipe.scheduled_days.contains(day)
        ).all()
    
    def search_by_name(self, name: str) -> List[Recipe]:
        return self.db.query(Recipe).filter(Recipe.name.ilike(f"%{name}%")).all()
    
    def get_except_user(self, user_id: int) -> List[Recipe]:
        return self.db.query(Recipe).filter(Recipe.user_id != user_id).all()