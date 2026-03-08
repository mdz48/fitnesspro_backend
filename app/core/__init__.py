"""
Núcleo de la aplicación: configuración, dependencias y servicios core
"""
from app.core.dependencies import (
    get_user_service,
    get_recipe_service,
    get_exercise_service,
    UserServiceDep,
    RecipeServiceDep,
    ExerciseServiceDep,
)
from app.core.security_service import SecurityService

__all__ = [
    "get_user_service",
    "get_recipe_service",
    "get_exercise_service",
    "UserServiceDep",
    "RecipeServiceDep",
    "ExerciseServiceDep",
    "SecurityService",
]
