"""
Servicio para la lógica de negocio de recetas
"""
from fastapi import HTTPException
from app.models.Recipe import Recipe
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate
from app.repositories.recipe_repository import RecipeRepository


class RecipeService:
    """Servicio para gestionar recetas con DI"""
    
    def __init__(self, repository: RecipeRepository):
        """
        Inicializa el servicio con sus dependencias
        
        Args:
            repository: Repositorio de recetas
        """
        self.repository = repository
    
    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        """
        Crea una nueva receta
        
        Args:
            recipe_data: Datos de la receta a crear
            
        Returns:
            Receta creada
        """
        new_recipe = Recipe(**recipe_data.dict())
        return self.repository.create(new_recipe)
    
    def get_recipe_by_id(self, recipe_id: int) -> Recipe:
        """
        Obtiene una receta por ID
        
        Args:
            recipe_id: ID de la receta
            
        Returns:
            Receta encontrada
            
        Raises:
            HTTPException: Si la receta no existe
        """
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return recipe
    
    def get_all_recipes(self, skip: int = 0, limit: int = 10) -> list[Recipe]:
        """
        Obtiene una lista paginada de recetas
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de recetas
        """
        return self.repository.get_all(skip, limit)
    
    def delete_recipe(self, recipe_id: int) -> None:
        """
        Elimina una receta
        
        Args:
            recipe_id: ID de la receta a eliminar
            
        Raises:
            HTTPException: Si la receta no existe
        """
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        self.repository.delete(recipe)
    
    def update_recipe(self, recipe_id: int, recipe_data: RecipeUpdate) -> Recipe:
        """
        Actualiza una receta existente
        
        Args:
            recipe_id: ID de la receta a actualizar
            recipe_data: Nuevos datos de la receta
            
        Returns:
            Receta actualizada
            
        Raises:
            HTTPException: Si la receta no existe
        """
        recipe = self.repository.get_by_id(recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Actualizar solo campos no nulos (para soporte parcial con Form)
        for key, value in recipe_data.dict().items():
            if value is not None:
                setattr(recipe, key, value)
        
        return self.repository.update(recipe)
    
    def get_recipes_by_user(self, user_id: int) -> list[Recipe]:
        """
        Obtiene todas las recetas de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de recetas del usuario
        """
        return self.repository.get_by_user(user_id)
