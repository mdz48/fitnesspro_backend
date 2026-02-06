from app.shared.config.database import get_db
from sqlalchemy.orm import Session
from app.schemas.recipe_schema import RecipeCreate, RecipeResponse
from fastapi import APIRouter, Depends, status
from app.services.recipe_service import RecipeService

recipe_router = APIRouter()


@recipe_router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Crea una nueva receta"""
    return RecipeService.create_recipe(db, recipe)


@recipe_router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Obtiene una receta por ID"""
    return RecipeService.get_recipe_by_id(db, recipe_id)


@recipe_router.get("/recipes", response_model=list[RecipeResponse])
def read_recipes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Obtiene una lista paginada de recetas"""
    return RecipeService.get_all_recipes(db, skip, limit)


@recipe_router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Elimina una receta"""
    RecipeService.delete_recipe(db, recipe_id)
    return


@recipe_router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Actualiza una receta existente"""
    return RecipeService.update_recipe(db, recipe_id, recipe)


@recipe_router.get("/recipes/{user_id}", response_model=list[RecipeResponse])
def read_recipes_by_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las recetas de un usuario"""
    return RecipeService.get_recipes_by_user(db, user_id)


@recipe_router.post("/recipes/{recipe_id}/lists/{list_id}", status_code=status.HTTP_201_CREATED)
def add_recipe_to_list(recipe_id: int, list_id: int, db: Session = Depends(get_db)):
    """Añade una receta a una lista"""
    return RecipeService.add_recipe_to_list(db, recipe_id, list_id)

@recipe_router.get("/lists/{list_id}/recipes", response_model=list[RecipeResponse])
def get_recipes_by_list(list_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las recetas de una lista"""
    return RecipeService.get_recipes_by_list(db, list_id)