from app.shared.config.database import get_db
from sqlalchemy.orm import Session
from app.schemas.recipie_schema import RecipeBase, RecipeCreate, RecipeResponse
from app.models.Recipie import Recipie
from fastapi import APIRouter, Depends, status, HTTPException
from app.models.RecipieList import RecipieList

recipie_router = APIRouter()

@recipie_router.post("/recipes/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    new_recipe = Recipie(**recipe.dict())
    db.add(new_recipe)
    db.commit()
    db.refresh(new_recipe)
    return new_recipe

@recipie_router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.query(Recipie).filter(Recipie.id == recipe_id).first()
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@recipie_router.get("/recipes/", response_model=list[RecipeResponse])
def read_recipes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    recipes = db.query(Recipie).offset(skip).limit(limit).all()
    return recipes

@recipie_router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.query(Recipie).filter(Recipie.id == recipe_id).first()
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(db_recipe)
    db.commit()
    return

@recipie_router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = db.query(Recipie).filter(Recipie.id == recipe_id).first()
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    for key, value in recipe.dict().items():
        setattr(db_recipe, key, value)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


@recipie_router.get("/recipies/{user_id}/", response_model=list[RecipeResponse])
def read_recipes_by_user(user_id: int, db: Session = Depends(get_db)):
    recipes = db.query(Recipie).filter(Recipie.user_id == user_id).all()
    return recipes

# Post una recipie a una tabla relacional de recipies y listas
@recipie_router.post("/recipies/{recipie_id}/lists/{list_id}", status_code=status.HTTP_201_CREATED)
def add_recipie_to_list(recipie_id: int, list_id: int, db: Session = Depends(get_db)):
    recipie_list = RecipieList(recipie_id=recipie_id, list_id=list_id)
    #  Verificar si la relación ya existe
    existing_relation = db.query(RecipieList).filter(
        RecipieList.recipie_id == recipie_id,
        RecipieList.list_id == list_id
    ).first()
    if existing_relation:
        raise HTTPException(status_code=400, detail="Recipie already in list")
    db.add(recipie_list)
    db.commit()
    db.refresh(recipie_list)
    return recipie_list

# Get recetas de una lista a través de la tabla relacional
@recipie_router.get("/lists/{list_id}/recipies", response_model=list[RecipeResponse])
def get_recipies_by_list(list_id: int, db: Session = Depends(get_db)):
    recipie_lists = db.query(RecipieList).filter(RecipieList.list_id == list_id).all()
    recipies = []
    for rl in recipie_lists:
        recipie = db.query(Recipie).filter(Recipie.id == rl.recipie_id).first()
        if recipie:
            recipies.append(recipie)
    return recipies