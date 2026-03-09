"""
Rutas para ejercicios (proxy a ExerciseDB API)
"""
from fastapi import APIRouter, Query, UploadFile, File, Form, HTTPException
from typing import List, Optional
from app.core.dependencies import ExerciseServiceDep
from app.schemas.exercise_schema import ExerciseListResponse, ExerciseDetailResponse, ExerciseDatabaseCreate, ExerciseDatabaseUpdate, ExerciseDatabaseResponse
from app.services.cache_service import cache
from app.shared.config.s3_files import upload_file_to_s3

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

@exercise_router.post("/exercises/local")
async def create_exercise( 
    service: ExerciseServiceDep,
    name: str = Form(...),
    description: str = Form(...),
    user_id: int = Form(...),
    scheduled_days: Optional[List[str]] = Form(None),
    bodyparts: Optional[List[str]] = Form(None),
    equipment: Optional[List[str]] = Form(None),
    target_muscles: Optional[List[str]] = Form(None),
    secondary_muscles: Optional[List[str]] = Form(None),
    exercise_type: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    difficulty: str = Form("Facil"),
    image: Optional[UploadFile] = File(None),
    ):
        image_url = ""
        if image and image.filename:
            if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4')):
                raise HTTPException(status_code=400, detail="Only jpg, jpeg, png, gif or mp4 files are allowed")
            
            image_url = upload_file_to_s3(image)
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        def parse_form_list(items: Optional[List[str]]) -> Optional[List[str]]:
            if not items:
                return []
            result = set()
            for item in items:
                for s in item.split(","):
                    val = s.strip()
                    if val:
                        result.add(val)
            return list(result)

        exercise_data = ExerciseDatabaseCreate(
            name=name,
            description=description,
            user_id=user_id,
            scheduled_days=parse_form_list(scheduled_days),
            bodyparts=parse_form_list(bodyparts),
            equipments=parse_form_list(equipment),
            targetMuscles=parse_form_list(target_muscles),
            secondaryMuscles=parse_form_list(secondary_muscles),
            exercise_type=exercise_type,
            instructions=instructions,
            difficulty=difficulty.capitalize(),
            image_url=image_url
        )
        return await service.create_exercise(exercise_data)


@exercise_router.get("/exercises/local/user/{user_id}")
async def get_exercises_by_user(user_id: int, service: ExerciseServiceDep):
    return await service.get_exercises_by_user(user_id)

@exercise_router.put("/exercises/local/{exercise_id}")
async def update_exercise(
    exercise_id: int, 
    service: ExerciseServiceDep,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    scheduled_days: Optional[List[str]] = Form(None),
    bodyparts: Optional[List[str]] = Form(None),
    equipment: Optional[List[str]] = Form(None),
    target_muscles: Optional[List[str]] = Form(None),
    secondary_muscles: Optional[List[str]] = Form(None),
    exercise_type: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    ):
        existing_exercise = await service.get_exercises_from_db()
        image_url = None
        if image and image.filename:
            if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4')):
                raise HTTPException(status_code=400, detail="Only jpg, jpeg, png, gif or mp4 files are allowed")
            
            image_url = upload_file_to_s3(image)
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image to S3")
        
        def parse_form_list(items: Optional[List[str]]) -> Optional[List[str]]:
            if items is None:
                return None
            result = set()
            for item in items:
                for s in item.split(","):
                    val = s.strip()
                    if val:
                        result.add(val)
            return list(result)

        exercise_data = ExerciseDatabaseUpdate(
            id=exercise_id,
            name=name,
            description=description,
            user_id=user_id,
            scheduled_days=parse_form_list(scheduled_days),
            bodyparts=parse_form_list(bodyparts),
            equipments=parse_form_list(equipment),
            targetMuscles=parse_form_list(target_muscles),
            secondaryMuscles=parse_form_list(secondary_muscles),
            exercise_type=exercise_type,
            instructions=instructions,
            difficulty=difficulty.capitalize() if difficulty else None,
            image_url=image_url
        )
        return await service.update_exercise(exercise_id, exercise_data)

@exercise_router.delete("/exercises/local/{exercise_id}")
async def delete_exercise(exercise_id: int, service: ExerciseServiceDep):
    return await service.delete_exercise(exercise_id)

@exercise_router.get("/exercises/local")
async def get_exercises_from_db(service: ExerciseServiceDep):
    return await service.get_exercises_from_db()

@exercise_router.get("/exercises/local/bodypart/{bodypart}")
async def get_exercises_from_db_by_bodypart(bodypart: str, service: ExerciseServiceDep):
    return await service.get_exercises_from_db_by_bodypart(bodypart)

@exercise_router.get("/exercises/local/target/{target}")
async def get_exercises_from_db_by_target(target: str, service: ExerciseServiceDep):
    return await service.get_exercises_from_db_by_target(target)

@exercise_router.get("/exercises/local/equipment/{equipment}")
async def get_exercises_from_db_by_equipment(equipment: str, service: ExerciseServiceDep):
    return await service.get_exercises_from_db_by_equipment(equipment)

@exercise_router.get("/exercises/local/difficulty/{difficulty}")
async def get_exercises_from_db_by_difficulty(difficulty: str, service: ExerciseServiceDep):
    return await service.get_exercises_from_db_by_difficulty(difficulty)

@exercise_router.get("/exercises/local/type/{exercise_type}")
async def get_exercises_from_db_by_type(exercise_type: str, service: ExerciseServiceDep):
    return await service.get_exercises_from_db_by_type(exercise_type)

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