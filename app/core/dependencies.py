"""
Funciones de dependencias para inyección
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.shared.config.database import get_db
from app.core.security_service import SecurityService
from app.repositories.user_repository import UserRepository
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.progression_repository import ProgressionRepository
from app.services.user_service import UserService
from app.services.recipe_service import RecipeService
from app.services.exercise_service import ExerciseService
from app.services.progression_service import ProgressionService
from app.services.external_api_service import ExternalAPIClient
from app.shared.config.external_api_config import EXERCISEDB_BASE_URL


# === Dependencias de Repositorios ===

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Inyecta el repositorio de usuarios"""
    return UserRepository(db)


def get_recipe_repository(db: Session = Depends(get_db)) -> RecipeRepository:
    """Inyecta el repositorio de recetas"""
    return RecipeRepository(db)


def get_exercise_repository(db: Session = Depends(get_db)) -> ExerciseRepository:
    """Inyecta el repositorio de ejercicios"""
    return ExerciseRepository(db)


def get_progression_repository(db: Session = Depends(get_db)) -> ProgressionRepository:
    """Inyecta el repositorio de progresión de peso"""
    return ProgressionRepository(db)


# === Dependencias de Servicios Core ===

def get_security_service() -> SecurityService:
    """Inyecta el servicio de seguridad"""
    return SecurityService()


def get_api_client() -> ExternalAPIClient:
    """Inyecta el cliente de API externa"""
    return ExternalAPIClient(EXERCISEDB_BASE_URL)


# === Dependencias de Servicios de Negocio ===

def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
    security: SecurityService = Depends(get_security_service)
) -> UserService:
    """Inyecta el servicio de usuarios"""
    return UserService(repository, security)


def get_recipe_service(
    repository: RecipeRepository = Depends(get_recipe_repository)
) -> RecipeService:
    """Inyecta el servicio de recetas"""
    return RecipeService(repository)


def get_exercise_service(
    api_client: ExternalAPIClient = Depends(get_api_client),
    repository: ExerciseRepository = Depends(get_exercise_repository)
) -> ExerciseService:
    """Inyecta el servicio de ejercicios"""
    return ExerciseService(api_client, repository)


def get_progression_service(
    repository: ProgressionRepository = Depends(get_progression_repository),
    user_repository: UserRepository = Depends(get_user_repository)
) -> ProgressionService:
    """Inyecta el servicio de progresión de peso"""
    return ProgressionService(repository, user_repository)


# === Type Aliases para anotaciones ===

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
RecipeServiceDep = Annotated[RecipeService, Depends(get_recipe_service)]
ExerciseServiceDep = Annotated[ExerciseService, Depends(get_exercise_service)]
ProgressionServiceDep = Annotated[ProgressionService, Depends(get_progression_service)]
