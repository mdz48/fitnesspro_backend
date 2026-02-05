from app.shared.config.database import Base
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from datetime import datetime

class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    ingredients = Column(String(500), nullable=False)
    instructions = Column(String(1000), nullable=False)
    scheduled_datetime = Column(DateTime, nullable=True)  
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)