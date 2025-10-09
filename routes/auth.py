from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from models.user import UserCreate, UserLogin, Token, UserResponse
from controllers.auth_controller import register_user, login_user, verify_token
from config.database import get_db

router = APIRouter()

@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    result = register_user(db, user_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return {
        "success": True,
        "message": "User registered successfully",
        "user": result["user"],
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"]
    }

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    result = login_user(db, user_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    return {
        "success": True,
        "message": "Login successful",
        "user": result["user"],
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"]
    }

@router.post("/verify")
def verify_user_token(token_data: dict, db: Session = Depends(get_db)):
    """Verify JWT token"""
    token = token_data.get("token", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    result = verify_token(db, token)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    return {
        "success": True,
        "message": "Token is valid",
        "user": result["user"]
    }

@router.get("/me")
def get_current_user():
    """Get current user info (placeholder)"""
    return {
        "success": True,
        "message": "User info endpoint - implement with JWT middleware"
    }
