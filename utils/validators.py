import re
from typing import Dict, Any, List

def validate_expert_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate expert creation data"""
    errors = []
    
    # Required fields
    if not data.get("name"):
        errors.append("Name is required")
    elif len(data["name"]) < 2:
        errors.append("Name must be at least 2 characters")
    
    if not data.get("role"):
        errors.append("Role is required")
    elif len(data["role"]) < 2:
        errors.append("Role must be at least 2 characters")
    
    # Optional fields validation
    if data.get("bio") and len(data["bio"]) > 1000:
        errors.append("Bio must be less than 1000 characters")
    
    if data.get("image_url"):
        if not is_valid_url(data["image_url"]):
            errors.append("Invalid image URL")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_content_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate content upload data"""
    errors = []
    
    if not data.get("content"):
        errors.append("Content is required")
    elif len(data["content"]) < 10:
        errors.append("Content must be at least 10 characters")
    
    valid_types = ["text", "audio", "video", "document"]
    if not data.get("content_type") or data["content_type"] not in valid_types:
        errors.append(f"Content type must be one of: {', '.join(valid_types)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_chat_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate chat message data"""
    errors = []
    
    if not data.get("message"):
        errors.append("Message is required")
    elif len(data["message"]) < 1:
        errors.append("Message cannot be empty")
    elif len(data["message"]) > 2000:
        errors.append("Message must be less than 2000 characters")
    
    valid_types = ["text", "voice"]
    if data.get("message_type") and data["message_type"] not in valid_types:
        errors.append(f"Message type must be one of: {', '.join(valid_types)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_user_registration(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user registration data"""
    errors = []
    
    # Email validation
    if not data.get("email"):
        errors.append("Email is required")
    elif not is_valid_email(data["email"]):
        errors.append("Invalid email format")
    
    # Username validation
    if not data.get("username"):
        errors.append("Username is required")
    elif len(data["username"]) < 3:
        errors.append("Username must be at least 3 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', data["username"]):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    # Password validation
    if not data.get("password"):
        errors.append("Password is required")
    elif len(data["password"]) < 6:
        errors.append("Password must be at least 6 characters")
    
    # Full name validation (optional)
    if data.get("full_name") and len(data["full_name"]) > 100:
        errors.append("Full name must be less than 100 characters")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def is_valid_email(email: str) -> bool:
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_url(url: str) -> bool:
    """Check if URL format is valid"""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    return re.match(pattern, url) is not None

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove script tags and content
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    return text.strip()

def validate_file_upload(filename: str, content_type: str, max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
    """Validate file upload"""
    errors = []
    
    if not filename:
        errors.append("Filename is required")
    
    # Check file extension
    allowed_extensions = ['.txt', '.pdf', '.doc', '.docx', '.mp3', '.wav', '.mp4', '.avi']
    if filename and not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Check content type
    allowed_types = ['text/', 'audio/', 'video/', 'application/pdf', 'application/msword']
    if content_type and not any(content_type.startswith(t) for t in allowed_types):
        errors.append("Content type not allowed")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
