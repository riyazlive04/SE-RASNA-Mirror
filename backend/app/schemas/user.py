from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserSignup(BaseModel):
    """Schema for user signup"""
    name: str = Field(..., min_length=1, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (min 6 characters)")
    domain: Optional[str] = Field(None, description="User's domain/organization")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user response (no password)"""
    id: int
    name: str
    email: str
    domain: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
