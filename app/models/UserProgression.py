from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.shared.config.database import Base

class WeightProgress(Base):
    __tablename__ = "user_progression"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    weight = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="weight_progress")