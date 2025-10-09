from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.user_db import UserDB
from models.user import UserCreate
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user_data: UserCreate) -> Dict[str, Any]:
    """Create a new user in the database"""
    try:
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Create user instance
        db_user = UserDB(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True
        )
        
        # Add to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {"success": True, "user": db_user}
        
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            return {"success": False, "error": "Email already registered"}
        elif "username" in str(e.orig):
            return {"success": False, "error": "Username already taken"}
        else:
            return {"success": False, "error": "User already exists"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}

def get_user_by_email(db: Session, email: str) -> Optional[UserDB]:
    """Get user by email"""
    return db.query(UserDB).filter(UserDB.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[UserDB]:
    """Get user by username"""
    return db.query(UserDB).filter(UserDB.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[UserDB]:
    """Get user by ID"""
    try:
        return db.query(UserDB).filter(UserDB.id == uuid.UUID(user_id)).first()
    except ValueError:
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[UserDB]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def update_user(db: Session, user_id: str, **kwargs) -> Dict[str, Any]:
    """Update user information"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        for key, value in kwargs.items():
            if hasattr(user, key) and key != "id":
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        return {"success": True, "user": user}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Update failed: {str(e)}"}

def delete_user(db: Session, user_id: str) -> Dict[str, Any]:
    """Delete user (soft delete by setting is_active to False)"""
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        user.is_active = False
        db.commit()
        
        return {"success": True, "message": "User deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"Delete failed: {str(e)}"}
