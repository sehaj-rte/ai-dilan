from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from sqlalchemy.orm import Session
from config.database import get_db
from controllers.knowledge_base_controller import (
    upload_file as upload_file_controller,
    get_files as get_files_controller,
    get_file_by_id as get_file_by_id_controller,
    delete_file as delete_file_controller,
    get_file_stats as get_file_stats_controller
)

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload file to knowledge base"""
    # TODO: Get user_id from authentication token
    user_id = None  # Set to None for now since auth is not implemented
    
    result = await upload_file_controller(file, db, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/files", response_model=dict)
def get_files(db: Session = Depends(get_db)):
    """Get all uploaded files"""
    result = get_files_controller(db)
    
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
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete file from knowledge base"""
    # TODO: Get user_id from authentication token
    user_id = None  # Set to None for now since auth is not implemented
    
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
