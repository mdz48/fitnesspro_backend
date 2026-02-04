from pydantic import BaseModel, ConfigDict, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: str
    lastname: str
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

class LoginResponse(UserResponse):
    access_token: str
    token_type: str