"""Clase que representa un plan de recetas"""

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.shared.config.database import Base

recipe_plan_recipes = Table(
    'recipe_plan_recipes',
    Base.metadata,
    Column('recipe_plan_id', Integer, ForeignKey('recipe_plans.id'), primary_key=True),
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True)
)

class RecipePlan(Base):
    __tablename__ = "recipe_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="recipe_plans")
    recipes = relationship("Recipe", secondary=recipe_plan_recipes, back_populates="recipe_plans")
    private = Column(Boolean, nullable=True, default=False)