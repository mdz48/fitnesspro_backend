from app.shared.config.database import get_db
from sqlalchemy.orm import Session
from app.schemas.list_schema import ListBase, ListCreate, ListResponse
from fastapi import APIRouter, Depends, status, HTTPException
from app.models.List import List
from app.models.RecipieList import RecipieList

list_routes = APIRouter()

@list_routes.post("/lists/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(list_item: ListCreate, db: Session = Depends(get_db)):
    new_list = List(**list_item.dict())
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    return new_list

@list_routes.get("/lists/{list_id}", response_model=ListResponse)
def get_list(list_id: int, db: Session = Depends(get_db)):
    list_item = db.query(List).filter(List.id == list_id).first()
    if not list_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return list_item

@list_routes.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, db: Session = Depends(get_db)):
    list_item = db.query(List).filter(List.id == list_id).first()
    if not list_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    db.delete(list_item)
    db.commit()
    return

@list_routes.put("/lists/{list_id}", response_model=ListResponse)
def update_list(list_id: int, list_item: ListCreate, db: Session = Depends(get_db)):
    existing_list = db.query(List).filter(List.id == list_id).first()
    if not existing_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    for key, value in list_item.dict().items():
        setattr(existing_list, key, value)
    db.commit()
    db.refresh(existing_list)
    return existing_list

@list_routes.get("/lists/", response_model=list[ListResponse])
def get_all_lists(db: Session = Depends(get_db)):
    lists = db.query(List).all()
    return lists

@list_routes.get("/lists/user/{user_id}", response_model=list[ListResponse])
def get_lists_by_user(user_id: int, db: Session = Depends(get_db)):
    lists = db.query(List).filter(List.user_id == user_id).all()
    return lists

@list_routes.get("/lists/{list_id}/recipies", response_model=list[ListResponse])
def get_recipies_in_list(list_id: int, db: Session = Depends(get_db)):
    list_item = db.query(List).filter(List.id == list_id).first()
    if not list_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    recipies = list_item.recipies 
    return recipies

