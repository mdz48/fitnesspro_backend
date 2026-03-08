"""
Modelo de ejercicio
"""
from sqlalchemy import Column, Enum, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.Enums import BodyPartEnum, EquipmentEnum, MuscleEnum, ExerciseTypeEnum
from sqlalchemy.dialects.mysql import SET

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_days = Column(SET('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'), nullable=True, default="")
    image_url = Column(String(255), nullable=True, default="")
    bodyparts = Column(SET(*[e.value for e in BodyPartEnum]), nullable=True, default="")
    equipments = Column(SET(*[e.value for e in EquipmentEnum]), nullable=True, default="")
    targetMuscles = Column(SET(*[e.value for e in MuscleEnum]), nullable=True, default="")
    secondaryMuscles = Column(SET(*[e.value for e in MuscleEnum]), nullable=True, default="")
    exercise_type = Column(Enum(ExerciseTypeEnum), nullable=True, default="")
    instructions = Column(String(1000), nullable=True, default="")
    
    user = relationship("User", back_populates="exercises")