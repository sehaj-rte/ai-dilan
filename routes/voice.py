from fastapi import APIRouter, HTTPException, status, UploadFile, File
from controllers.voice_controller import transcribe_voice, synthesize_voice, get_elevenlabs_voices

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
def get_elevenlabs_voices_endpoint():
    """Get list of ElevenLabs voices"""
    result = get_elevenlabs_voices()
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result
