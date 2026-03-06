"""
Modelo de ejercicio
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    scheduled_days = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    
    user = relationship("User", back_populates="exercises")