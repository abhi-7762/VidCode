from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.production import (
    StartRenderRequest,
    RenderJobResponse,
    VoiceInfo,
)
from app.services.production_service import ProductionService
from app.services.voice_service import VoiceService
from app.tasks.render_tasks import final_render

router = APIRouter(prefix="/production", tags=["Video Production & Rendering"])


def get_production_service() -> ProductionService:
    return ProductionService()


def get_voice_service() -> VoiceService:
    return VoiceService()


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(voice_service: VoiceService = Depends(get_voice_service)):
    """List available AI voices for voiceover narration."""
    return voice_service.get_available_voices()


@router.post("/render", status_code=201)
async def start_render(
    request: StartRenderRequest,
    service: ProductionService = Depends(get_production_service),
):
    """
    Synchronously renders the final master video:
    1. Generates voiceover
    2. Builds subtitle timings
    3. Mixes audio tracks and concatenates clips via FFmpeg
    4. Produces master MP4
    """
    try:
        job = await service.create_render_job(request)
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.post("/render-async", status_code=202)
async def start_render_async(
    request: StartRenderRequest,
):
    """
    Dispatches video rendering to a Celery background worker.
    Returns task_id to poll via /api/v1/jobs/{task_id}.
    """
    settings_dict = request.settings.model_dump() if request.settings else None
    task = final_render.delay(
        project_id=request.project_id,
        storyboard_id=request.storyboard_id,
        settings_dict=settings_dict,
    )
    return {
        "status": "queued",
        "task_id": task.id,
        "project_id": request.project_id,
        "storyboard_id": request.storyboard_id,
        "poll_url": f"/api/v1/jobs/{task.id}",
    }


@router.get("/jobs/{job_id}")
async def get_render_job(
    job_id: str,
    service: ProductionService = Depends(get_production_service),
):
    """Check status, progress, and download link for a render job."""
    job = await service.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found")
    return job


@router.get("/project/{project_id}")
async def get_project_renders(
    project_id: str,
    service: ProductionService = Depends(get_production_service),
):
    """Get all render history for a project."""
    jobs = await service.get_jobs_by_project(project_id)
    return {
        "project_id": project_id,
        "total_renders": len(jobs),
        "renders": jobs,
    }
