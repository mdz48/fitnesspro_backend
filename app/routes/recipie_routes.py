from app.shared.config.database import get_db
from sqlalchemy.orm import Session
from app.schemas.recipie_schema import RecipeCreate, RecipeResponse
from fastapi import APIRouter, Depends, status
from app.services.recipie_service import RecipieService

recipie_router = APIRouter()


@recipie_router.post("/recipes/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Crea una nueva receta"""
    return RecipieService.create_recipe(db, recipe)


@recipie_router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Obtiene una receta por ID"""
    return RecipieService.get_recipe_by_id(db, recipe_id)


@recipie_router.get("/recipes/", response_model=list[RecipeResponse])
def read_recipes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Obtiene una lista paginada de recetas"""
    return RecipieService.get_all_recipes(db, skip, limit)


@recipie_router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Elimina una receta"""
    RecipieService.delete_recipe(db, recipe_id)
    return


@recipie_router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Actualiza una receta existente"""
    return RecipieService.update_recipe(db, recipe_id, recipe)


@recipie_router.get("/recipies/{user_id}/", response_model=list[RecipeResponse])
def read_recipes_by_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las recetas de un usuario"""
    return RecipieService.get_recipes_by_user(db, user_id)


@recipie_router.post("/recipies/{recipie_id}/lists/{list_id}", status_code=status.HTTP_201_CREATED)
def add_recipie_to_list(recipie_id: int, list_id: int, db: Session = Depends(get_db)):
    """Añade una receta a una lista"""
    return RecipieService.add_recipe_to_list(db, recipie_id, list_id)


@recipie_router.get("/lists/{list_id}/recipies", response_model=list[RecipeResponse])
def get_recipies_by_list(list_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las recetas de una lista"""
    return RecipieService.get_recipes_by_list(db, list_id)