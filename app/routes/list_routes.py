from app.shared.config.database import get_db
from sqlalchemy.orm import Session
from app.schemas.list_schema import ListCreate, ListResponse
from fastapi import APIRouter, Depends, status
from app.services.list_service import ListService

list_routes = APIRouter()


@list_routes.post("/lists/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(list_item: ListCreate, db: Session = Depends(get_db)):
    """Crea una nueva lista"""
    return ListService.create_list(db, list_item)


@list_routes.get("/lists/{list_id}", response_model=ListResponse)
def get_list(list_id: int, db: Session = Depends(get_db)):
    """Obtiene una lista por ID"""
    return ListService.get_list_by_id(db, list_id)


@list_routes.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, db: Session = Depends(get_db)):
    """Elimina una lista"""
    ListService.delete_list(db, list_id)
    return


@list_routes.put("/lists/{list_id}", response_model=ListResponse)
def update_list(list_id: int, list_item: ListCreate, db: Session = Depends(get_db)):
    """Actualiza una lista existente"""
    return ListService.update_list(db, list_id, list_item)


@list_routes.get("/lists/", response_model=list[ListResponse])
def get_all_lists(db: Session = Depends(get_db)):
    """Obtiene todas las listas"""
    return ListService.get_all_lists(db)


@list_routes.get("/lists/user/{user_id}", response_model=list[ListResponse])
def get_lists_by_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las listas de un usuario"""
    return ListService.get_lists_by_user(db, user_id)


@list_routes.get("/lists/{list_id}/recipies", response_model=list[ListResponse])
def get_recipies_in_list(list_id: int, db: Session = Depends(get_db)):
    """Obtiene todas las recetas de una lista"""
    return ListService.get_recipes_in_list(db, list_id)

