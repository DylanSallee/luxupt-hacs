"""API routes for external integrations (e.g. Home Assistant)."""

from typing import Any

from db.connection import DbSession
from fastapi import APIRouter, Depends, HTTPException, status
from logging_config import get_logger
from pydantic import BaseModel, Field

from services.job_service import get_job_processor
from web.auth import get_api_user
from web.deps import TimelapsesViewDep

logger = get_logger(__name__)

router = APIRouter(tags=["api"])

class CreateTimelapseRequest(BaseModel):
    """Request model for creating a timelapse via API."""
    camera: str = Field(..., description="Camera ID or safe name")
    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    interval: int = Field(..., description="Interval in seconds (e.g., 60 for 1 frame per minute)", ge=1)


class CreateTimelapseResponse(BaseModel):
    """Response model for creating a timelapse."""
    success: bool
    job_id: str | None = None
    message: str


@router.post(
    "/timelapses",
    response_model=CreateTimelapseResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a timelapse creation job",
    description="Start a background job to generate a timelapse for the specified camera and date.",
)
async def api_create_timelapse(
    request: CreateTimelapseRequest,
    view_service: TimelapsesViewDep,
    db: DbSession,
    user: str = Depends(get_api_user),
) -> Any:
    """Create a new timelapse job."""
    try:
        # Check if camera exists by ID first, then by safe_name
        camera_info = await view_service.get_camera_info(request.camera)
        
        if not camera_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera '{request.camera}' not found",
            )

        camera_safe_name = camera_info["safe_name"]
        camera_id = camera_info["camera_id"]

        # Check if job already exists
        if await view_service.check_job_exists(camera_safe_name, request.date, request.interval):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Job already exists for {camera_safe_name} on {request.date} at {request.interval}s interval",
            )

        # Create job in database
        title = f"{camera_safe_name}_{request.date}_{request.interval}s"
        job = await view_service.create_job(
            title=title,
            camera_safe_name=camera_safe_name,
            camera_id=camera_id,
            date_str=request.date,
            interval=request.interval,
        )
        await db.commit()

        # Start processing the job in background
        get_job_processor().start_job(job.job_id, request.date, camera_safe_name, request.interval)

        return CreateTimelapseResponse(
            success=True,
            job_id=job.job_id,
            message="Timelapse job created successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating timelapse via API", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create timelapse",
        )
