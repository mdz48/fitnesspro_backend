from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import APIRouter, status, Form, HTTPException
from app.schemas.user_schema import UserCreate, UserUpdate, LoginResponse, UserResponse
from app.schemas.daily_content_schema import UserDailyContentResponse
from app.core.dependencies import UserServiceDep, ExerciseServiceDep, RecipeServiceDep

user_router = APIRouter()

MEXICO_CITY_TIMEZONE = "America/Mexico_City"
WEEKDAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _get_mexico_city_now() -> datetime:
    """Obtiene fecha/hora de Mexico City con fallback cuando falta tzdata."""
    try:
        return datetime.now(ZoneInfo(MEXICO_CITY_TIMEZONE))
    except ZoneInfoNotFoundError:
        mexico_city_fixed = timezone(timedelta(hours=-6), name="America/Mexico_City")
        return datetime.now(mexico_city_fixed)


def _resolve_current_day() -> str:
    mexico_now = _get_mexico_city_now()
    return WEEKDAYS_ES[mexico_now.weekday()]


@user_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, service: UserServiceDep):
    return service.create_user(user)


@user_router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, service: UserServiceDep):
    return service.get_user_by_id(user_id)


@user_router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, service: UserServiceDep):
    return service.update_user(user_id, user)


@user_router.post("/login", response_model=LoginResponse)
def login_user(email: str = Form(...), password: str = Form(...), service: UserServiceDep = None):
    return service.login_user(email, password)


@user_router.post("/login/google", response_model=LoginResponse)
def login_google_user(id_token: str = Form(...), service: UserServiceDep = None):
    return service.login_google_user(id_token)


@user_router.get("/users", response_model=list[UserResponse])
def read_users(service: UserServiceDep = None):
    return service.get_all_users()


@user_router.get("/users/{user_id}/daily-content", response_model=UserDailyContentResponse)
async def read_user_daily_content(
    user_id: int,
    user_service: UserServiceDep,
    exercise_service: ExerciseServiceDep,
    recipe_service: RecipeServiceDep,
):
    # Reutilizamos la validación existente para mantener consistencia de errores 404.
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    selected_day = _resolve_current_day()
    exercises = await exercise_service.get_exercises_by_user_and_day(user_id, selected_day)
    recipes = recipe_service.get_recipes_by_user_and_day(user_id, selected_day)

    return UserDailyContentResponse(
        user_id=user_id,
        user_name=user.name,
        user_lastname=user.lastname,
        day=selected_day,
        timezone=MEXICO_CITY_TIMEZONE,
        exercises=exercises,
        recipes=recipes,
    )