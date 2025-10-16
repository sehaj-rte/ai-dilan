from typing import Dict, Any
from fastapi import UploadFile
from services.openai_service import transcribe_audio, generate_speech
from services.elevenlabs_service import elevenlabs_service
import base64
import io
import asyncio

def transcribe_voice(audio_file: UploadFile) -> Dict[str, Any]:
    """Transcribe voice to text"""
    try:
        # Check file type
        if not audio_file.content_type.startswith("audio/"):
            return {"success": False, "error": "File must be an audio file"}
        
        # Read audio file
        audio_content = audio_file.file.read()
        
        # Create a file-like object for OpenAI
        audio_io = io.BytesIO(audio_content)
        audio_io.name = audio_file.filename
        
        # Transcribe using OpenAI Whisper
        transcription = transcribe_audio(audio_io)
        
        if not transcription:
            return {"success": False, "error": "Failed to transcribe audio"}
        
        return {
            "success": True,
            "transcription": {
                "text": transcription,
                "filename": audio_file.filename,
                "content_type": audio_file.content_type
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def synthesize_voice(text: str, voice: str = "alloy") -> Dict[str, Any]:
    """Convert text to speech"""
    try:
        # Generate speech using OpenAI TTS
        audio_content = generate_speech(text, voice)
        
        if not audio_content:
            return {"success": False, "error": "Failed to generate speech"}
        
        # Convert to base64 for JSON response
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        return {
            "success": True,
            "audio": {
                "content": audio_base64,
                "format": "mp3",
                "voice": voice,
                "text": text
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_voice_info(voice_id: str) -> Dict[str, Any]:
    """Get information about a voice"""
    voices = {
        "alloy": {"name": "Alloy", "gender": "neutral", "description": "Balanced and clear"},
        "echo": {"name": "Echo", "gender": "male", "description": "Deep and resonant"},
        "fable": {"name": "Fable", "gender": "neutral", "description": "Warm and expressive"},
        "onyx": {"name": "Onyx", "gender": "male", "description": "Strong and confident"},
        "nova": {"name": "Nova", "gender": "female", "description": "Bright and energetic"},
        "shimmer": {"name": "Shimmer", "gender": "female", "description": "Soft and melodic"}
    }
    
    voice_info = voices.get(voice_id)
    if not voice_info:
        return {"success": False, "error": "Voice not found"}
    
    return {
        "success": True,
        "voice": {
            "id": voice_id,
            **voice_info
        }
    }

def get_elevenlabs_voices(search: str = None, 
                         voice_type: str = None, 
                         category: str = None,
                         page_size: int = 50,
                         next_page_token: str = None,
                         sort: str = None,
                         sort_direction: str = None) -> Dict[str, Any]:
    """Get list of ElevenLabs voices with advanced filtering and pagination"""
    try:
        # Use the elevenlabs_service which has the API key configured
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_service.get_voices(
            search=search,
            voice_type=voice_type,
            category=category,
            page_size=page_size,
            next_page_token=next_page_token,
            sort=sort,
            sort_direction=sort_direction
        ))
        loop.close()
        
        if not result["success"]:
            print(f"DEBUG: ElevenLabs service error: {result.get('error')}")
            return result
        
        voices = result.get("voices", [])
        print(f"DEBUG: Found {len(voices)} voices from ElevenLabs service")
        
        # Format voices for frontend with enhanced information
        formatted_voices = []
        for voice in voices:
            labels = voice.get("labels", {})
            
            # Extract voice characteristics
            voice_data = {
                "voice_id": voice.get("voice_id"),
                "name": voice.get("name"),
                "category": voice.get("category", "premade"),
                "description": voice.get("description"),
                "preview_url": voice.get("preview_url"),
                "available_for_tiers": voice.get("available_for_tiers", []),
                "is_owner": voice.get("is_owner", False),
                "is_legacy": voice.get("is_legacy", False),
                "is_mixed": voice.get("is_mixed", False),
                "created_at_unix": voice.get("created_at_unix"),
                "favorited_at_unix": voice.get("favorited_at_unix"),
                
                # Voice characteristics from labels
                "gender": labels.get("gender", "unknown"),
                "age": labels.get("age", "unknown"),
                "accent": labels.get("accent", "unknown"),
                "use_case": labels.get("use case", ""),
                "descriptive": labels.get("descriptive", ""),
                
                # Voice settings if available
                "settings": voice.get("settings"),
                
                # Sharing information if available
                "sharing": voice.get("sharing"),
                
                # Sample information
                "samples": voice.get("samples", []),
                
                # Fine tuning information
                "fine_tuning": voice.get("fine_tuning"),
                
                # Verification status
                "voice_verification": voice.get("voice_verification"),
                
                # High quality model IDs
                "high_quality_base_model_ids": voice.get("high_quality_base_model_ids", []),
                
                # Verified languages
                "verified_languages": voice.get("verified_languages", [])
            }
            
            formatted_voices.append(voice_data)
        
        return {
            "success": True,
            "voices": formatted_voices,
            "total_count": result.get("total_count", len(formatted_voices)),
            "has_more": result.get("has_more", False),
            "next_page_token": result.get("next_page_token")
        }
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return {"success": False, "error": str(e)}

def get_voice_details(voice_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific voice"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_service.get_voice_details(voice_id))
        loop.close()
        
        if not result["success"]:
            print(f"DEBUG: ElevenLabs voice details error: {result.get('error')}")
            return result
        
        voice = result.get("voice", {})
        print(f"DEBUG: Retrieved details for voice: {voice.get('name', 'Unknown')}")
        
        return {
            "success": True,
            "voice": voice
        }
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return {"success": False, "error": str(e)}

def synthesize_elevenlabs_voice(text: str, voice_id: str, settings: dict = None) -> Dict[str, Any]:
    """Convert text to speech using ElevenLabs"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_service.synthesize_speech(text, voice_id, settings))
        loop.close()
        
        if not result["success"]:
            print(f"DEBUG: ElevenLabs synthesis error: {result.get('error')}")
            return result
        
        # Convert audio data to base64 for JSON response
        audio_data = result.get("audio_data")
        if audio_data:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return {
                "success": True,
                "audio": {
                    "content": audio_base64,
                    "format": "mp3",
                    "voice_id": voice_id,
                    "text": text
                }
            }
        else:
            return {"success": False, "error": "No audio data received"}
            
    except Exception as e:
        print(f"DEBUG: Exception occurred in synthesize_elevenlabs_voice: {str(e)}")
        return {"success": False, "error": str(e)}
