from app.shared.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class RecipieList(Base):
    __tablename__ = "recipie_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("lists.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    recipie_id = Column(Integer, ForeignKey("recipies.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)