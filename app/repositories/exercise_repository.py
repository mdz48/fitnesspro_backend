"""
Repositorio de ejercicios
"""

from typing import List
from sqlalchemy.orm import Session
from app.models.Exercise import Exercise
from app.repositories.base_repository import BaseRepository

class ExerciseRepository(BaseRepository[Exercise]):
    def __init__(self, db: Session):
        super().__init__(Exercise, db)
    
    def get_by_user(self, user_id: int) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.user_id == user_id).all()
    
    def get_by_bodypart(self, bodypart: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.bodypart == bodypart).all()
    
    def get_by_equipment(self, equipment: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.equipment == equipment).all()
    
    def get_by_muscle(self, muscle: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.muscle == muscle).all()
    
    def get_by_name(self, name: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.name == name).all()