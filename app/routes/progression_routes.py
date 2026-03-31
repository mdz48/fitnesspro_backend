from fastapi import APIRouter, status
from app.core.dependencies import ProgressionServiceDep
from app.schemas.progression_schema import (
    WeightProgressCreate,
    WeightProgressResponse,
    WeightProgressSummary,
)

progression_router = APIRouter()


@progression_router.post("/users/{user_id}/progression", response_model=WeightProgressResponse, status_code=status.HTTP_201_CREATED)
def create_weight_progress(user_id: int, progress_data: WeightProgressCreate, service: ProgressionServiceDep):
    return service.register_weight(user_id, progress_data)


@progression_router.get("/users/{user_id}/progression", response_model=list[WeightProgressResponse])
def get_weight_progress(user_id: int, service: ProgressionServiceDep):
    return service.get_user_progress(user_id)


@progression_router.get("/users/{user_id}/progression/summary", response_model=WeightProgressSummary)
def get_weight_progress_summary(user_id: int, service: ProgressionServiceDep):
    return service.get_progress_summary(user_id)
