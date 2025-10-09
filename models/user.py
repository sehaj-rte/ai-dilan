from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# User Models (using Pydantic for validation, not classes for logic)

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
