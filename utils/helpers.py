import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict, List

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def generate_short_id(length: int = 8) -> str:
    """Generate a short unique ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]

def hash_string(text: str) -> str:
    """Hash a string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()

def current_timestamp() -> str:
    """Get current timestamp as ISO string"""
    return datetime.now().isoformat()

def format_response(success: bool, data: Any = None, error: str = None, message: str = None) -> Dict[str, Any]:
    """Format API response"""
    response = {"success": success}
    
    if data is not None:
        response["data"] = data
    if error:
        response["error"] = error
    if message:
        response["message"] = message
    
    return response

def validate_email(email: str) -> bool:
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    import re
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)
    
    return text.strip()

def chunk_text(text: str, max_length: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with optional overlap"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, start + max_length // 2, -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else end
    
    return chunks

def calculate_similarity_score(score: float) -> str:
    """Convert similarity score to human readable format"""
    if score >= 0.9:
        return "Excellent"
    elif score >= 0.8:
        return "Very Good"
    elif score >= 0.7:
        return "Good"
    elif score >= 0.6:
        return "Fair"
    else:
        return "Poor"
