from app.shared.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey

class RecipeList(Base):
    __tablename__ = "recipe_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("lists.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)