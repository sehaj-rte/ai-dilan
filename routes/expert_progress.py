from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from services.expert_processing_progress_service import ExpertProcessingProgressService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/experts/{expert_id}/progress")
async def get_expert_progress(expert_id: str, db: Session = Depends(get_db)):
    """
    Get processing progress for an expert
    
    Args:
        expert_id: Expert ID to get progress for
        
    Returns:
        Progress information including stage, status, and percentage
    """
    try:
        progress_service = ExpertProcessingProgressService(db)
        progress_record = progress_service.get_progress_by_expert_id(expert_id)
        
        if not progress_record:
            return {
                "success": False,
                "error": "No progress record found for this expert",
                "expert_id": expert_id
            }
        
        return {
            "success": True,
            "progress": progress_record.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error getting progress for expert {expert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")

@router.get("/experts/progress/active")
async def get_all_active_progress(db: Session = Depends(get_db)):
    """
    Get all active (in-progress) expert processing records
    
    Returns:
        List of all active progress records
    """
    try:
        progress_service = ExpertProcessingProgressService(db)
        active_records = progress_service.get_all_active_progress()
        
        return {
            "success": True,
            "count": len(active_records),
            "progress_records": [record.to_dict() for record in active_records]
        }
        
    except Exception as e:
        logger.error(f"Error getting active progress records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get active progress: {str(e)}")

@router.delete("/experts/{expert_id}/progress")
async def delete_expert_progress(expert_id: str, db: Session = Depends(get_db)):
    """
    Delete progress record for an expert (cleanup after completion)
    
    Args:
        expert_id: Expert ID to delete progress for
        
    Returns:
        Success status
    """
    try:
        progress_service = ExpertProcessingProgressService(db)
        success = progress_service.delete_progress_record(expert_id)
        
        if not success:
            return {
                "success": False,
                "error": "No progress record found for this expert",
                "expert_id": expert_id
            }
        
        return {
            "success": True,
            "message": f"Progress record deleted for expert {expert_id}"
        }
        
    except Exception as e:
        logger.error(f"Error deleting progress for expert {expert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete progress: {str(e)}")
