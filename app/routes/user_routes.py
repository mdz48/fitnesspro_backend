from fastapi import APIRouter, Depends, status, Form
from sqlalchemy.orm import Session
from app.shared.config.database import get_db
from app.schemas.user_schema import UserCreate, LoginResponse, UserResponse
from app.services.user_service import UserService

user_router = APIRouter()


@user_router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Crea un nuevo usuario"""
    return UserService.create_user(db, user)


@user_router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por ID"""
    return UserService.get_user_by_id(db, user_id)


@user_router.post("/login", response_model=LoginResponse)
def login_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Autentica un usuario y retorna un token de acceso"""
    return UserService.login_user(db, email, password)


@user_router.get("/users/", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Obtiene una lista paginada de usuarios"""
    return UserService.get_all_users(db, skip, limit)