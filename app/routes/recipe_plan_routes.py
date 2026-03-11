from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.shared.config.database import get_db
from app.schemas.recipe_plan_schema import RecipePlanCreate, RecipePlanResponse, RecipePlanRecipeAdd
from app.schemas.recipe_schema import RecipeResponse
from app.services.recipe_plan_service import recipe_plan_service

recipe_plan_router = APIRouter()

@recipe_plan_router.get("/user/{user_id}", response_model=List[RecipePlanResponse])
def get_user_recipe_plans(user_id: int, db: Session = Depends(get_db)):
    """Obtener todas las listas de recetas que tiene un usuario"""
    return recipe_plan_service.get_user_plans(db, user_id)

@recipe_plan_router.post("/", response_model=RecipePlanResponse, status_code=status.HTTP_201_CREATED)
def create_recipe_plan(plan_data: RecipePlanCreate, db: Session = Depends(get_db)):
    """Crear un nuevo plan de recetas"""
    return recipe_plan_service.create_plan(db, plan_data)

@recipe_plan_router.post("/{plan_id}/recipes", response_model=RecipePlanResponse)
def add_recipe_to_plan(plan_id: int, recipe_data: RecipePlanRecipeAdd, db: Session = Depends(get_db)):
    """Agregar una receta a un plan de recetas"""
    current_plan = recipe_plan_service.get_plan(db, plan_id)
    if current_plan and any(r.id == recipe_data.recipe_id for r in current_plan.recipes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La receta ya está en el plan")
    plan = recipe_plan_service.add_recipe(db, plan_id, recipe_data.recipe_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan o receta no encontrado")
    return plan

@recipe_plan_router.get("/{plan_id}/recipes", response_model=List[RecipeResponse])
def get_plan_recipes(plan_id: int, db: Session = Depends(get_db)):
    """Obtener todas las recetas de un plan"""
    plan = recipe_plan_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan.recipes

@recipe_plan_router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe_plan(plan_id: int, db: Session = Depends(get_db)):
    """Eliminar un plan de recetas completo"""
    success = recipe_plan_service.delete_plan(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return None

@recipe_plan_router.delete("/{plan_id}/recipes/{recipe_id}", response_model=RecipePlanResponse)
def remove_recipe_from_plan(plan_id: int, recipe_id: int, db: Session = Depends(get_db)):
    """Eliminar una receta específica de un plan"""
    plan = recipe_plan_service.remove_recipe(db, plan_id, recipe_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan o receta no encontrado")
    return plan
