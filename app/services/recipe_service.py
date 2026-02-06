"""
Servicio para la lógica de negocio de recetas
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.Recipe import Recipe
from app.models.RecipeList import RecipeList
from app.schemas.recipe_schema import RecipeCreate


class RecipeService:
    """Servicio para gestionar recetas"""
    
    @staticmethod
    def create_recipe(db: Session, recipe_data: RecipeCreate) -> Recipe:
        """
        Crea una nueva receta
        
        Args:
            db: Sesión de base de datos
            recipe_data: Datos de la receta a crear
            
        Returns:
            Receta creada
        """
        new_recipe = Recipe(**recipe_data.dict())
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        return new_recipe
    
    @staticmethod
    def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe:
        """
        Obtiene una receta por ID
        
        Args:
            db: Sesión de base de datos
            recipe_id: ID de la receta
            
        Returns:
            Receta encontrada
            
        Raises:
            HTTPException: Si la receta no existe
        """
        db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if db_recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return db_recipe
    
    @staticmethod
    def get_all_recipes(db: Session, skip: int = 0, limit: int = 10) -> list[Recipe]:
        """
        Obtiene una lista paginada de recetas
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de recetas
        """
        recipes = db.query(Recipe).offset(skip).limit(limit).all()
        return recipes
    
    @staticmethod
    def delete_recipe(db: Session, recipe_id: int) -> None:
        """
        Elimina una receta
        
        Args:
            db: Sesión de base de datos
            recipe_id: ID de la receta a eliminar
            
        Raises:
            HTTPException: Si la receta no existe
        """
        db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if db_recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        db.delete(db_recipe)
        db.commit()
    
    @staticmethod
    def update_recipe(db: Session, recipe_id: int, recipe_data: RecipeCreate) -> Recipe:
        """
        Actualiza una receta existente
        
        Args:
            db: Sesión de base de datos
            recipe_id: ID de la receta a actualizar
            recipe_data: Nuevos datos de la receta
            
        Returns:
            Receta actualizada
            
        Raises:
            HTTPException: Si la receta no existe
        """
        db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if db_recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Actualizar campos
        for key, value in recipe_data.dict().items():
            setattr(db_recipe, key, value)
        
        db.commit()
        db.refresh(db_recipe)
        return db_recipe
    
    @staticmethod
    def get_recipes_by_user(db: Session, user_id: int) -> list[Recipe]:
        """
        Obtiene todas las recetas de un usuario
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Lista de recetas del usuario
        """
        recipes = db.query(Recipe).filter(Recipe.user_id == user_id).all()
        return recipes
    
    @staticmethod
    def add_recipe_to_list(db: Session, recipe_id: int, list_id: int) -> RecipeList:
        """
        Añade una receta a una lista
        
        Args:
            db: Sesión de base de datos
            recipe_id: ID de la receta
            list_id: ID de la lista
            
        Returns:
            Relación receta-lista creada
            
        Raises:
            HTTPException: Si la relación ya existe
        """
        # Verificar si la relación ya existe
        existing_relation = db.query(RecipeList).filter(
            RecipeList.recipie_id == recipe_id,
            RecipeList.list_id == list_id
        ).first()
        
        if existing_relation:
            raise HTTPException(status_code=400, detail="Recipe already in list")
        
        # Crear nueva relación
        recipie_list = RecipeList(recipie_id=recipe_id, list_id=list_id)
        db.add(recipie_list)
        db.commit()
        db.refresh(recipie_list)
        return recipie_list
    
    @staticmethod
    def get_recipes_by_list(db: Session, list_id: int) -> list[Recipe]:
        """
        Obtiene todas las recetas de una lista
        
        Args:
            db: Sesión de base de datos
            list_id: ID de la lista
            
        Returns:
            Lista de recetas
        """
        recipie_lists = db.query(RecipeList).filter(RecipeList.list_id == list_id).all()
        recipes = []
        
        for rl in recipie_lists:
            recipie = db.query(Recipe).filter(Recipe.id == rl.recipie_id).first()
            if recipie:
                recipes.append(recipie)
        
        return recipes
