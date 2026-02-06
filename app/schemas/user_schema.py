from pydantic import BaseModel, ConfigDict, EmailStr

class UserBase(BaseModel):
    email: EmailStr | None = "1@1.com"
    name: str | None = "Usuario"
    lastname: str | None = "Prueba"
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str | None = "1"

class UserResponse(UserBase):
    id: int

class LoginResponse(UserResponse):
    access_token: str
    token_type: str