from typing import Dict, Any, List
from datetime import datetime
from models.chat import ChatRequest, ChatMessage
from controllers.expert_controller import ask_expert, get_expert
import uuid

# Simple in-memory chat storage (replace with database in production)
chat_history_db = {}

def send_message(chat_data: ChatRequest) -> Dict[str, Any]:
    """Send a message to an expert"""
    try:
        # Verify expert exists
        expert_result = get_expert(chat_data.expert_id)
        if not expert_result["success"]:
            return {"success": False, "error": "Expert not found"}
        
        expert = expert_result["expert"]
        
        # Get AI response from expert
        response_result = ask_expert(chat_data.expert_id, chat_data.message)
        if not response_result["success"]:
            return {"success": False, "error": "Failed to get expert response"}
        
        # Create message record
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        message = {
            "id": message_id,
            "user_id": chat_data.user_id or "anonymous",
            "expert_id": chat_data.expert_id,
            "message": chat_data.message,
            "response": response_result["response"]["answer"],
            "message_type": chat_data.message_type,
            "confidence": response_result["response"]["confidence"],
            "timestamp": timestamp.isoformat()
        }
        
        # Store in chat history
        chat_key = f"{chat_data.expert_id}_{chat_data.user_id or 'anonymous'}"
        if chat_key not in chat_history_db:
            chat_history_db[chat_key] = []
        chat_history_db[chat_key].append(message)
        
        return {
            "success": True,
            "response": {
                "message_id": message_id,
                "expert_id": chat_data.expert_id,
                "expert_name": expert["name"],
                "response": response_result["response"]["answer"],
                "response_type": "text",
                "confidence": response_result["response"]["confidence"],
                "timestamp": timestamp.isoformat()
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_chat_history(expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """Get chat history for an expert"""
    try:
        chat_key = f"{expert_id}_{user_id or 'anonymous'}"
        messages = chat_history_db.get(chat_key, [])
        
        return {
            "success": True,
            "history": {
                "expert_id": expert_id,
                "messages": messages,
                "total_messages": len(messages)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def clear_chat_history(expert_id: str, user_id: str = None) -> Dict[str, Any]:
    """Clear chat history for an expert"""
    try:
        chat_key = f"{expert_id}_{user_id or 'anonymous'}"
        if chat_key in chat_history_db:
            del chat_history_db[chat_key]
        
        return {"success": True, "message": "Chat history cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_recent_conversations(user_id: str = None, limit: int = 10) -> Dict[str, Any]:
    """Get recent conversations for a user"""
    try:
        user_key = user_id or "anonymous"
        recent_chats = []
        
        for chat_key, messages in chat_history_db.items():
            if chat_key.endswith(f"_{user_key}") and messages:
                expert_id = chat_key.replace(f"_{user_key}", "")
                last_message = messages[-1]
                
                recent_chats.append({
                    "expert_id": expert_id,
                    "last_message": last_message["message"],
                    "last_response": last_message["response"],
                    "timestamp": last_message["timestamp"],
                    "message_count": len(messages)
                })
        
        # Sort by timestamp (most recent first)
        recent_chats.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "success": True,
            "conversations": recent_chats[:limit]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
