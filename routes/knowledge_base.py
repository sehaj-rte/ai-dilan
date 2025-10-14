from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from config.database import get_db
from dependencies.auth import get_current_user_required
from controllers.knowledge_base_controller import (
    upload_file as upload_file_controller,
    get_files as get_files_controller,
    get_file_by_id as get_file_by_id_controller,
    delete_file as delete_file_controller,
    get_file_stats as get_file_stats_controller
)

class YouTubeTranscribeRequest(BaseModel):
    youtube_url: str
    folder: str = "Uncategorized"
    custom_name: str = None

class RenameFolderRequest(BaseModel):
    old_name: str
    new_name: str

class MoveFileRequest(BaseModel):
    folder_name: str

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...), 
    folder: str = Form("Uncategorized"),
    custom_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Upload file to knowledge base"""
    user_id = current_user_id
    
    result = await upload_file_controller(file, db, user_id, folder, custom_name)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/files", response_model=dict)
def get_files(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Get all uploaded files"""
    result = get_files_controller(db, current_user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/files/{file_id}", response_model=dict)
def get_file(file_id: str, db: Session = Depends(get_db)):
    """Get file by ID"""
    result = get_file_by_id_controller(file_id, db)
    
    if not result["success"]:
        if "not found" in result["error"].lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
    
    return result

@router.delete("/files/{file_id}", response_model=dict)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Delete file from knowledge base"""
    user_id = current_user_id
    
    result = await delete_file_controller(file_id, db, user_id)
    
    if not result["success"]:
        if "not found" in result["error"].lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
    
    return result

@router.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(get_db)):
    """Get file statistics"""
    result = get_file_stats_controller(db)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/documents/selection", response_model=dict)
def get_documents_for_selection(db: Session = Depends(get_db)):
    """Get documents in a format suitable for expert creation selection"""
    # TODO: Get user_id from authentication token
    user_id = None  # Set to None for now since auth is not implemented
    
    result = get_files_controller(db, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # Transform to selection format
    documents = []
    for file_data in result["files"]:
        # Only include successfully processed files
        if file_data.get("processing_status") == "completed":
            documents.append({
                "id": file_data["id"],
                "name": file_data["name"],
                "document_type": file_data.get("document_type", "unknown"),
                "size": file_data["size"],
                "word_count": file_data.get("word_count"),
                "description": file_data.get("description"),
                "tags": file_data.get("tags", []),
                "created_at": file_data["created_at"],
                "preview": file_data.get("extracted_text_preview", "")[:200] + "..." if file_data.get("extracted_text_preview") else ""
            })
    
    return {
        "success": True,
        "documents": documents,
        "total": len(documents)
    }

@router.get("/documents/{document_id}/details", response_model=dict)
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific document"""
    result = get_file_by_id_controller(document_id, db)
    
    if not result["success"]:
        if "not found" in result["error"].lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
    
    file_data = result["file"]
    
    # Transform to detailed format
    document_details = {
        "id": file_data["id"],
        "name": file_data["name"],
        "document_type": file_data.get("document_type", "unknown"),
        "size": file_data["size"],
        "word_count": file_data.get("word_count"),
        "page_count": file_data.get("page_count"),
        "language": file_data.get("language"),
        "has_images": file_data.get("has_images", False),
        "has_tables": file_data.get("has_tables", False),
        "created_at": file_data["created_at"],
        "updated_at": file_data.get("updated_at"),
        "extracted_text": file_data.get("extracted_text"),
        "extracted_text_preview": file_data.get("extracted_text_preview"),
        "processing_status": file_data.get("processing_status", "unknown"),
        "metadata": {
            "file_type": file_data.get("type"),
            "s3_key": file_data.get("s3_key"),
            "url": file_data.get("url")
        }
    }
    
    return {
        "success": True,
        "document": document_details
    }

@router.post("/transcribe-audio", response_model=dict)
async def transcribe_audio(
    file: UploadFile = File(...),
    folder: str = Form("Uncategorized"),
    custom_name: str = Form(None),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Transcribe audio using ElevenLabs Speech-to-Text API and save to knowledge base"""
    from controllers.knowledge_base_controller import transcribe_and_save_audio
    
    user_id = current_user_id
    
    result = await transcribe_and_save_audio(file, db, user_id, folder, custom_name)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/transcribe-youtube", response_model=dict)
async def transcribe_youtube(
    request: YouTubeTranscribeRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Download audio from YouTube video and transcribe using ElevenLabs"""
    from controllers.knowledge_base_controller import transcribe_youtube_video
    
    user_id = current_user_id
    
    result = await transcribe_youtube_video(request.youtube_url, db, user_id, request.folder, request.custom_name)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

# Folder Management Endpoints

@router.get("/folders", response_model=dict)
def get_folders(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Get all folders with file counts"""
    from services.file_service import FileService
    
    user_id = current_user_id
    
    file_service = FileService(db)
    result = file_service.get_folders(user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/folders", response_model=dict)
def create_folder(
    folder_name: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Create a new folder"""
    from services.file_service import FileService
    
    user_id = current_user_id
    
    file_service = FileService(db)
    result = file_service.create_folder(folder_name, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/folders/rename", response_model=dict)
def rename_folder(
    request: RenameFolderRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Rename a folder"""
    from services.file_service import FileService
    
    user_id = current_user_id
    
    file_service = FileService(db)
    result = file_service.rename_folder(request.old_name, request.new_name, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.delete("/folders/{folder_name}", response_model=dict)
def delete_folder(
    folder_name: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_required)
):
    """Delete a folder (moves all files to Uncategorized)"""
    from services.file_service import FileService
    
    user_id = current_user_id
    
    file_service = FileService(db)
    result = file_service.delete_folder(folder_name, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.put("/files/{file_id}/move", response_model=dict)
def move_file(file_id: str, request: MoveFileRequest, db: Session = Depends(get_db)):
    """Move a file to a different folder"""
    from services.file_service import FileService
    
    file_service = FileService(db)
    result = file_service.move_file_to_folder(file_id, request.folder_name)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result
