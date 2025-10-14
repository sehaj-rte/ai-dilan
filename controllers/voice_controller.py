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

def get_elevenlabs_voices() -> Dict[str, Any]:
    """Get list of ElevenLabs voices"""
    try:
        # Use the elevenlabs_service which has the API key configured
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(elevenlabs_service.get_voices())
        loop.close()
        
        if not result["success"]:
            print(f"DEBUG: ElevenLabs service error: {result.get('error')}")
            return result
        
        voices = result.get("voices", [])
        print(f"DEBUG: Found {len(voices)} voices from ElevenLabs service")
        
        # Format voices for frontend (ElevenLabs API format)
        formatted_voices = []
        for voice in voices:
            formatted_voices.append({
                "id": voice.get("voice_id"),
                "name": voice.get("name"),
                "gender": voice.get("labels", {}).get("gender", "unknown"),
                "age": voice.get("labels", {}).get("age", "unknown"),
                "accent": voice.get("labels", {}).get("accent", "unknown"),
                "description": voice.get("labels", {}).get("description", ""),
                "use_case": voice.get("labels", {}).get("use case", ""),
                "preview_url": voice.get("preview_url"),
                "category": voice.get("category", "premade")
            })
        
        return {
            "success": True,
            "voices": formatted_voices,
            "total": len(formatted_voices)
        }
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return {"success": False, "error": str(e)}
