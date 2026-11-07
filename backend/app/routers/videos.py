from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.video import (
    GenerateClipsRequest,
    RegenerateClipRequest,
    BatchClipsResponse,
)
from app.services.video_service import VideoService
from app.tasks.video_tasks import generate_video_clips

router = APIRouter(prefix="/videos", tags=["Video Generation & Clips"])


def get_video_service() -> VideoService:
    return VideoService()


@router.post("/generate", status_code=201)
async def generate_clips(
    request: GenerateClipsRequest,
    service: VideoService = Depends(get_video_service),
):
    """
    Generate video clips for scenes in a storyboard.
    Can use Mock provider (free/instant) or external AI engines (Runway, Luma).
    """
    try:
        clips = await service.generate_clips_for_storyboard(request)
        return {
            "project_id": request.project_id,
            "storyboard_id": request.storyboard_id,
            "total_clips": len(clips),
            "clips": clips,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clip generation failed: {str(e)}")


@router.post("/generate-async", status_code=202)
async def generate_clips_async(
    request: GenerateClipsRequest,
):
    """
    Asynchronously triggers clip generation using a Celery background worker.
    Returns task_id to poll via /api/v1/jobs/{task_id}.
    """
    task = generate_video_clips.delay(
        project_id=request.project_id,
        storyboard_id=request.storyboard_id,
        provider=request.provider.value,
        scene_numbers=request.scene_numbers,
    )
    return {
        "status": "queued",
        "task_id": task.id,
        "project_id": request.project_id,
        "storyboard_id": request.storyboard_id,
        "poll_url": f"/api/v1/jobs/{task.id}",
    }


@router.get("/project/{project_id}")
async def get_project_clips(
    project_id: str,
    service: VideoService = Depends(get_video_service),
):
    """List all generated video clips for a project."""
    clips = await service.get_clips_by_project(project_id)
    return {
        "project_id": project_id,
        "total_clips": len(clips),
        "clips": clips,
    }


@router.get("/clips/{clip_id}")
async def get_clip(
    clip_id: str,
    service: VideoService = Depends(get_video_service),
):
    """Retrieve details and status for a single clip."""
    clip = await service.get_clip_by_id(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    return clip


@router.post("/clips/{clip_id}/regenerate")
async def regenerate_clip(
    clip_id: str,
    request: RegenerateClipRequest,
    service: VideoService = Depends(get_video_service),
):
    """Regenerate a single scene clip with updated prompt or provider."""
    try:
        updated = await service.regenerate_clip(clip_id, request)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

