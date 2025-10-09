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
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload file to knowledge base"""
    result = upload_file_controller(file, db)
    
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
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete file from knowledge base"""
    result = delete_file_controller(file_id, db)
    
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
