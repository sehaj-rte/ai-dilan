from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query
from controllers.voice_controller import transcribe_voice, synthesize_voice, get_elevenlabs_voices, get_voice_details, synthesize_elevenlabs_voice
from typing import Optional

router = APIRouter()

@router.post("/transcribe", response_model=dict)
def transcribe_audio(audio_file: UploadFile = File(...)):
    """Transcribe audio to text"""
    result = transcribe_voice(audio_file)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.post("/synthesize", response_model=dict)
def synthesize_speech(voice_data: dict):
    """Convert text to speech"""
    text = voice_data.get("text", "")
    voice = voice_data.get("voice", "alloy")
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is required"
        )
    
    result = synthesize_voice(text, voice)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.get("/voices", response_model=dict)
def get_available_voices():
    """Get list of available voices"""
    return {
        "success": True,
        "voices": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "neutral"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"}
        ]
    }

@router.get("/elevenlabs-voices", response_model=dict)
def get_elevenlabs_voices_endpoint(
    search: Optional[str] = Query(None, description="Search term to filter voices"),
    voice_type: Optional[str] = Query(None, description="Voice type filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    page_size: int = Query(50, ge=1, le=100, description="Number of voices per page"),
    next_page_token: Optional[str] = Query(None, description="Token for next page"),
    sort: Optional[str] = Query(None, description="Sort field"),
    sort_direction: Optional[str] = Query(None, description="Sort direction")
):
    """Get list of ElevenLabs voices with advanced filtering and pagination"""
    result = get_elevenlabs_voices(
        search=search,
        voice_type=voice_type,
        category=category,
        page_size=page_size,
        next_page_token=next_page_token,
        sort=sort,
        sort_direction=sort_direction
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result

@router.get("/elevenlabs-voices/{voice_id}", response_model=dict)
def get_voice_details_endpoint(voice_id: str):
    """Get detailed information about a specific ElevenLabs voice"""
    result = get_voice_details(voice_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    return result

@router.post("/synthesize-elevenlabs", response_model=dict)
def synthesize_elevenlabs_speech(voice_data: dict):
    """Convert text to speech using ElevenLabs"""
    text = voice_data.get("text", "")
    voice_id = voice_data.get("voice_id", "")
    settings = voice_data.get("settings", {})
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is required"
        )
    
    if not voice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voice ID is required"
        )
    
    result = synthesize_elevenlabs_voice(text, voice_id, settings)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result
