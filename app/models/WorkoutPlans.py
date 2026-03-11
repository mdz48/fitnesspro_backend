"""
Clase que representa un plan de entrenamiento.
"""
from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.Enums import ExerciseTypeEnum

workout_plan_exercises = Table(
    'workout_plan_exercises',
    Base.metadata,
    Column('workout_plan_id', Integer, ForeignKey('workout_plans.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('exercises.id'), primary_key=True)
)

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="workout_plans")
    exercises = relationship("Exercise", secondary=workout_plan_exercises, back_populates="workout_plans")
    plan_type = Column(Enum(ExerciseTypeEnum), nullable=True)
    private = Column(Boolean, nullable=True, default=False)
