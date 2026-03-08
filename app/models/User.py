from datetime import date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, Date, Enum, Float
from sqlalchemy.orm import relationship
from app.shared.config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    birthdate = Column(Date, nullable=False)
    
    @hybrid_property
    def age(self):
        if self.birthdate:
            today = date.today()
            return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return None
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    gender = Column(Enum("hombre", "mujer", "otro"), nullable=False)

    exercises = relationship("Exercise", back_populates="user")