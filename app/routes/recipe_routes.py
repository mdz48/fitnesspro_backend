from app.schemas.recipe_schema import RecipeCreate, RecipeResponse
from fastapi import APIRouter, status
from app.core.dependencies import RecipeServiceDep

recipe_router = APIRouter()


@recipe_router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(recipe: RecipeCreate, service: RecipeServiceDep):
    return service.create_recipe(recipe)


@recipe_router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def read_recipe(recipe_id: int, service: RecipeServiceDep):
    return service.get_recipe_by_id(recipe_id)


@recipe_router.get("/recipes", response_model=list[RecipeResponse])
def read_recipes(skip: int = 0, limit: int = 10, service: RecipeServiceDep = None):
    return service.get_all_recipes(skip, limit)


@recipe_router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, service: RecipeServiceDep):
    service.delete_recipe(recipe_id)
    return


@recipe_router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, recipe: RecipeCreate, service: RecipeServiceDep):
    return service.update_recipe(recipe_id, recipe)


@recipe_router.get("/users/{user_id}/recipes", response_model=list[RecipeResponse])
def read_recipes_by_user(user_id: int, service: RecipeServiceDep):
    return service.get_recipes_by_user(user_id)