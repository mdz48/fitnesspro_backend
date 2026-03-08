"""
Rutas para ejercicios (proxy a ExerciseDB API)
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from app.core.dependencies import ExerciseServiceDep
from app.schemas.exercise_schema import ExerciseListResponse, ExerciseDetailResponse, ExerciseDatabaseCreate, ExerciseDatabaseUpdate, ExerciseDatabaseResponse
from app.services.cache_service import cache

exercise_router = APIRouter()


@exercise_router.get("/exercises/remote", response_model=ExerciseListResponse)
async def get_exercises_from_api(
    service: ExerciseServiceDep,
    limit: Optional[int] = Query(None, ge=1, le=25, description="Número máximo de resultados"),
    offset: Optional[int] = Query(None, ge=0, description="Número de resultados a saltar")
):
    return await service.get_all_exercises(limit=limit, offset=offset)


@exercise_router.get("/exercises/local")
async def get_exercises_from_db(service: ExerciseServiceDep):
    return await service.get_exercises_from_db()

@exercise_router.post("/exercises")
async def create_exercise(exercise: ExerciseDatabaseCreate, service: ExerciseServiceDep):
    return await service.create_exercise(exercise)

@exercise_router.get("/exercises/user/{user_id}")
async def get_exercises_by_user(user_id: int, service: ExerciseServiceDep):
    return await service.get_exercises_by_user(user_id)

@exercise_router.put("/exercises/{exercise_id}")
async def update_exercise(exercise_id: int, exercise: ExerciseDatabaseUpdate, service: ExerciseServiceDep):
    return await service.update_exercise(exercise_id, exercise)

@exercise_router.delete("/exercises/{exercise_id}")
async def delete_exercise(exercise_id: int, service: ExerciseServiceDep):
    return await service.delete_exercise(exercise_id)

@exercise_router.get("/exercises/local")
async def get_exercises_from_db(service: ExerciseServiceDep):
    return await service.get_exercises_from_db()


@exercise_router.get("/exercises/bodypart/{bodypart}", response_model=ExerciseListResponse)
async def get_exercises_by_bodypart(bodypart: str, service: ExerciseServiceDep):
    return await service.get_exercises_by_bodypart(bodypart)


@exercise_router.get("/exercises/target/{target}", response_model=ExerciseListResponse)
async def get_exercises_by_target(target: str, service: ExerciseServiceDep):
    return await service.get_exercises_by_target(target)


@exercise_router.get("/exercises/equipment/{equipment}", response_model=ExerciseListResponse)
async def get_exercises_by_equipment(equipment: str, service: ExerciseServiceDep):
    return await service.get_exercises_by_equipment(equipment)


@exercise_router.get("/exercises/metadata/bodyparts", response_model=List[str])
async def get_body_parts(service: ExerciseServiceDep):
    return await service.get_body_parts()


@exercise_router.get("/exercises/metadata/targets", response_model=List[str])
async def get_target_muscles(service: ExerciseServiceDep):
    return await service.get_target_muscles()


@exercise_router.get("/exercises/metadata/equipment", response_model=List[str])
async def get_equipment_list(service: ExerciseServiceDep):
    return await service.get_equipment_list()


@exercise_router.get("/exercises/{exercise_id}", response_model=ExerciseDetailResponse)
async def get_exercise(exercise_id: str, service: ExerciseServiceDep):
    return await service.get_exercise_by_id(exercise_id)


@exercise_router.get("/cache/stats")
async def get_cache_stats():
    return {
        "cache_entries": cache.size(),
        "ttl_seconds": 3600,
        "status": "active"
    }


@exercise_router.delete("/cache/clear")
async def clear_cache():
    cache.clear()
    return {"message": "Caché limpiado exitosamente"}


@exercise_router.delete("/cache/expired")
async def clear_expired_cache():
    deleted = cache.clear_expired()
    return {
        "message": f"{deleted} entradas expiradas eliminadas",
        "deleted_count": deleted
    }