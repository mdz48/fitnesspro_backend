from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date
from typing import Literal
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr | None = None
    name: str | None = "Mdz"
    lastname: str | None = "C"
    birthdate: date | None = None
    weight: float | None = None
    height: float | None = None
    gender: str | None = None
    target_weight: float | None = None
    membership: Literal["gratuito", "premium", "admin"] | None = "gratuito"
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    email: EmailStr | None = "1@1.com"
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
    target_weight: float | None = None
    membership: Literal["gratuito", "free", "premium", "admin"] | None = None

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: int
    age: int | None = 25

class LoginResponse(UserResponse):
    access_token: str
    token_type: str


class FcmTokenRegisterRequest(BaseModel):
    fcm_token: str


class FcmTokenRegisterResponse(BaseModel):
    id: int
    user_id: int
    fcm_token: str
    is_active: bool
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    total_tokens: int

    model_config = ConfigDict(from_attributes=True)