"""
Servicio para la lógica de negocio de listas
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.List import List
from app.models.RecipeList import RecipeList
from app.schemas.list_schema import ListCreate


class ListService:
    """Servicio para gestionar listas"""
    
    @staticmethod
    def create_list(db: Session, list_data: ListCreate) -> List:
        """
        Crea una nueva lista
        
        Args:
            db: Sesión de base de datos
            list_data: Datos de la lista a crear
            
        Returns:
            Lista creada
        """
        new_list = List(**list_data.dict())
        db.add(new_list)
        db.commit()
        db.refresh(new_list)
        return new_list
    
    @staticmethod
    def get_list_by_id(db: Session, list_id: int) -> List:
        """
        Obtiene una lista por ID
        
        Args:
            db: Sesión de base de datos
            list_id: ID de la lista
            
        Returns:
            Lista encontrada
            
        Raises:
            HTTPException: Si la lista no existe
        """
        list_item = db.query(List).filter(List.id == list_id).first()
        if not list_item:
            raise HTTPException(status_code=404, detail="List not found")
        return list_item
    
    @staticmethod
    def delete_list(db: Session, list_id: int) -> None:
        """
        Elimina una lista
        
        Args:
            db: Sesión de base de datos
            list_id: ID de la lista a eliminar
            
        Raises:
            HTTPException: Si la lista no existe
        """
        list_item = db.query(List).filter(List.id == list_id).first()
        if not list_item:
            raise HTTPException(status_code=404, detail="List not found")
        db.delete(list_item)
        db.commit()
    
    @staticmethod
    def update_list(db: Session, list_id: int, list_data: ListCreate) -> List:
        """
        Actualiza una lista existente
        
        Args:
            db: Sesión de base de datos
            list_id: ID de la lista a actualizar
            list_data: Nuevos datos de la lista
            
        Returns:
            Lista actualizada
            
        Raises:
            HTTPException: Si la lista no existe
        """
        existing_list = db.query(List).filter(List.id == list_id).first()
        if not existing_list:
            raise HTTPException(status_code=404, detail="List not found")
        
        # Actualizar campos
        for key, value in list_data.dict().items():
            setattr(existing_list, key, value)
        
        db.commit()
        db.refresh(existing_list)
        return existing_list
    
    @staticmethod
    def get_all_lists(db: Session) -> list[List]:
        """
        Obtiene todas las listas
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Lista de todas las listas
        """
        lists = db.query(List).all()
        return lists
    
    @staticmethod
    def get_lists_by_user(db: Session, user_id: int) -> list[List]:
        """
        Obtiene todas las listas de un usuario
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Lista de listas del usuario
        """
        lists = db.query(List).filter(List.user_id == user_id).all()
        return lists
    
    @staticmethod
    def get_recipes_in_list(db: Session, list_id: int) -> list:
        """
        Obtiene todas las recetas en una lista
        
        Args:
            db: Sesión de base de datos
            list_id: ID de la lista
            
        Returns:
            Lista de recetas
            
        Raises:
            HTTPException: Si la lista no existe
        """
        list_item = db.query(List).filter(List.id == list_id).first()
        if not list_item:
            raise HTTPException(status_code=404, detail="List not found")
        return list_item.recipies
