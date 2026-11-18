from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    workspace_name: Optional[str] = "Personal Workspace"


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    workspace_name: str
    created_at: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
