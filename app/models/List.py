from app.shared.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class List(Base):
    __tablename__ = "lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)