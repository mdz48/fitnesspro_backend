from datetime import date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, Date, Enum, Float
from sqlalchemy.orm import relationship
from app.shared.config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    lastname = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    birthdate = Column(Date, nullable=True)
    
    @hybrid_property
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    gender = Column(Enum("hombre", "mujer", "otro"), nullable=True)
    membership = Column(Enum("gratuito", "premium", "admin"), default="gratuito", nullable=False)

    exercises = relationship("Exercise", back_populates="user")
    workout_plans = relationship("WorkoutPlan", back_populates="user")
    recipe_plans = relationship("RecipePlan", back_populates="user")
