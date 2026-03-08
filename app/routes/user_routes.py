from fastapi import APIRouter, status, Form
from app.schemas.user_schema import UserCreate, LoginResponse, UserResponse
from app.core.dependencies import UserServiceDep

user_router = APIRouter()


@user_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, service: UserServiceDep):
    return service.create_user(user)


@user_router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, service: UserServiceDep):
    return service.get_user_by_id(user_id)


@user_router.post("/login", response_model=LoginResponse)
def login_user(email: str = Form(...), password: str = Form(...), service: UserServiceDep = None):
    return service.login_user(email, password)


@user_router.get("/users", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 10, service: UserServiceDep = None):
    return service.get_all_users(skip, limit)