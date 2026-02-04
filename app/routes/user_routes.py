from fastapi import APIRouter, Depends, status, HTTPException, Security, Response, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.shared.config.database import get_db
from app.schemas.user_schema import UserCreate, UserBase, LoginResponse, UserResponse
from app.models.User import User
from app.shared.config.security import get_password_hash, create_access_token, verify_password

user_router = APIRouter()

@user_router.post("/users/", response_model= UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, name=user.name, lastname=user.lastname, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@user_router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@user_router.post("/users/login")
def login_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user or not verify_password(password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user.email})
    return LoginResponse(**db_user.__dict__, access_token=access_token, token_type="bearer")

@user_router.get("/users/", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users