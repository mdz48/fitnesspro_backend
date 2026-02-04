"""
Rutas para ejercicios (proxy a ExerciseDB API)
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from app.services.exercise_service import ExerciseService
from app.services.cache_service import cache
from app.schemas.exercise_schema import ExerciseListResponse, ExerciseDetailResponse

exercise_router = APIRouter()


@exercise_router.get("/exercises", response_model=ExerciseListResponse)
async def get_exercises(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Número máximo de resultados"),
    offset: Optional[int] = Query(None, ge=0, description="Número de resultados a saltar")
):
    """
    Obtiene todos los ejercicios disponibles con paginación
    """
    service = ExerciseService()
    try:
        exercises = await service.get_all_exercises(limit=limit, offset=offset)
        return exercises
    finally:
        await service.close()


@exercise_router.get("/exercises/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(exercise_id: str):
    """
    Obtiene un ejercicio específico por su ID
    """
    service = ExerciseService()
    try:
        exercise = await service.get_exercise_by_id(exercise_id)
        return exercise
    finally:
        await service.close()


@exercise_router.get("/exercises/bodypart/{bodypart}", response_model=ExerciseListResponse)
async def get_exercises_by_bodypart(bodypart: str):
    """
    Obtiene ejercicios filtrados por parte del cuerpo
    
    Ejemplos: back, chest, legs, shoulders, arms, etc.
    """
    service = ExerciseService()
    try:
        exercises = await service.get_exercises_by_bodypart(bodypart)
        return exercises
    finally:
        await service.close()


@exercise_router.get("/exercises/target/{target}", response_model=ExerciseListResponse)
async def get_exercises_by_target(target: str):
    """
    Obtiene ejercicios filtrados por músculo objetivo
    """
    service = ExerciseService()
    try:
        exercises = await service.get_exercises_by_target(target)
        return exercises
    finally:
        await service.close()


@exercise_router.get("/exercises/equipment/{equipment}", response_model=ExerciseListResponse)
async def get_exercises_by_equipment(equipment: str):
    """
    Obtiene ejercicios filtrados por tipo de equipo
    
    Ejemplos: barbell, dumbbell, bodyweight, cable, machine, etc.
    """
    service = ExerciseService()
    try:
        exercises = await service.get_exercises_by_equipment(equipment)
        return exercises
    finally:
        await service.close()


@exercise_router.get("/exercises/metadata/bodyparts", response_model=List[str])
async def get_body_parts():
    """
    Obtiene la lista de todas las partes del cuerpo disponibles
    """
    service = ExerciseService()
    try:
        bodyparts = await service.get_body_parts()
        return bodyparts
    finally:
        await service.close()


@exercise_router.get("/exercises/metadata/targets", response_model=List[str])
async def get_target_muscles():
    """
    Obtiene la lista de todos los músculos objetivo disponibles
    """
    service = ExerciseService()
    try:
        targets = await service.get_target_muscles()
        return targets
    finally:
        await service.close()


@exercise_router.get("/exercises/metadata/equipment", response_model=List[str])
async def get_equipment_list():
    """
    Obtiene la lista de todos los equipos disponibles
    """
    service = ExerciseService()
    try:
        equipment = await service.get_equipment_list()
        return equipment
    finally:
        await service.close()


@exercise_router.get("/cache/stats")
async def get_cache_stats():
    """
    Obtiene estadísticas del caché (número de entradas)
    """
    return {
        "cache_entries": cache.size(),
        "ttl_seconds": 3600,
        "status": "active"
    }


@exercise_router.delete("/cache/clear")
async def clear_cache():
    """
    Limpia todo el caché de ejercicios
    """
    cache.clear()
    return {"message": "Caché limpiado exitosamente"}


@exercise_router.delete("/cache/expired")
async def clear_expired_cache():
    """
    Limpia solo las entradas expiradas del caché
    """
    deleted = cache.clear_expired()
    return {
        "message": f"{deleted} entradas expiradas eliminadas",
        "deleted_count": deleted
    }
