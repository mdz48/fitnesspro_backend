from app.schemas.recipe_schema import RecipeCreate, RecipeResponse
from app.core.dependencies import RecipeServiceDep
from fastapi import APIRouter, status, File, UploadFile, Form, HTTPException
from app.shared.config.s3_files import upload_file_to_s3
from typing import Optional

recipe_router = APIRouter()


@recipe_router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    service: RecipeServiceDep,
    name: str = Form(...),
    description: str = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    user_id: Optional[int] = Form(1),
    scheduled_days: Optional[str] = Form(None),
    meal_type: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    image_url = None
    if image and image.filename:
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only jpg, jpeg or png files are allowed")
        
        image_url = upload_file_to_s3(image)
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

    days_set = None
    if scheduled_days:
        days_set = set(d.strip() for d in scheduled_days.split(","))

    recipe_data = RecipeCreate(
        name=name,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        user_id=user_id,
        scheduled_days=days_set,
        meal_type=meal_type,
        image_url=image_url
    )
    return service.create_recipe(recipe_data)


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