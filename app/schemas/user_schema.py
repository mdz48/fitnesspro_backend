from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date
from typing import Literal

class UserBase(BaseModel):
    email: EmailStr | None = "1@1.com"
    name: str | None = "Usuario"
    lastname: str | None = "Prueba"
    birthdate: date | None = date(2000, 1, 1)
    weight: float | None = 70.0
    height: float | None = 1.75
    gender: str | None = "hombre"
    membership: Literal["gratuito", "premium", "admin"] | None = "gratuito"
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str | None = "1"


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    lastname: str | None = None
    password: str | None = None
    birthdate: date | None = None
    weight: float | None = None
    height: float | None = None
    gender: str | None = None
    membership: Literal["gratuito", "free", "premium", "admin"] | None = None

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: int
    age: int | None = 25

class LoginResponse(UserResponse):
    access_token: str
    token_type: str