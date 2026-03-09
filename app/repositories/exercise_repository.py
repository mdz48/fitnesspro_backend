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
        return self.db.query(Exercise).filter(Exercise.bodyparts.contains(bodypart)).all()
    
    def get_by_equipment(self, equipment: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.equipments.contains(equipment)).all()
    
    def get_by_muscle(self, muscle: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.targetMuscles.contains(muscle)).all()
    
    def get_by_name(self, name: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.name == name).all()
    
    def get_by_difficulty(self, difficulty: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.difficulty == difficulty).all()
    
    def get_by_type(self, exercise_type: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.exercise_type == exercise_type).all()
    
    def get_by_target(self, target: str) -> List[Exercise]:
        return self.db.query(Exercise).filter(Exercise.targetMuscles.contains(target)).all()