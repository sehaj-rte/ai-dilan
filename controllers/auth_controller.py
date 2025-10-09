from typing import Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from models.user import UserCreate, UserLogin
from services.user_service import create_user, authenticate_user, get_user_by_id, get_user_by_email
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from config.database import get_db

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def register_user(db: Session, user_data: UserCreate) -> Dict[str, Any]:
    """Register a new user"""
    try:
        # Create user in database
        result = create_user(db, user_data)
        
        if not result["success"]:
            return result
        
        user = result["user"]
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active
            },
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(db: Session, user_data: UserLogin) -> Dict[str, Any]:
    """Login user"""
    try:
        # Authenticate user
        user = authenticate_user(db, user_data.email, user_data.password)
        
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        
        if not user.is_active:
            return {"success": False, "error": "Account is deactivated"}
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active
            },
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def verify_token(db: Session, token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            return {"success": False, "error": "Invalid token"}
        
        # Find user in database
        user = get_user_by_id(db, user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        if not user.is_active:
            return {"success": False, "error": "Account is deactivated"}
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active
            }
        }
    except JWTError:
        return {"success": False, "error": "Invalid token"}
    except Exception as e:
        return {"success": False, "error": str(e)}
