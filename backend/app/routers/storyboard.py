from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.storyboard import (
    StoryboardGenerateRequest,
    StoryboardSceneUpdate,
    PromptRegenerateRequest,
)
from app.services.storyboard_service import StoryboardService

router = APIRouter(prefix="/storyboards", tags=["Storyboards & Cinematography"])


def get_storyboard_service() -> StoryboardService:
    return StoryboardService()


@router.post("/generate", status_code=201)
async def generate_storyboard(
    request: StoryboardGenerateRequest,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """
    Generate a complete storyboard from an existing script.
    Extracts characters, sets up camera angles & lighting,
    and crafts video diffusion prompts.
    """
    try:
        storyboard = await service.generate(request)
        return storyboard
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Storyboard generation failed: {str(e)}"
        )


@router.get("/{storyboard_id}")
async def get_storyboard(
    storyboard_id: str,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """Retrieve a storyboard by ID."""
    storyboard = await service.get_by_id(storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found")
    return storyboard


@router.get("/project/{project_id}")
async def get_storyboard_by_project(
    project_id: str,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """Retrieve storyboard associated with a project."""
    storyboard = await service.get_by_project(project_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="No storyboard found for this project")
    return storyboard


@router.patch("/{storyboard_id}/scenes/{scene_number}")
async def update_scene(
    storyboard_id: str,
    scene_number: int,
    updates: StoryboardSceneUpdate,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """Manually update an individual scene's prompts, camera specs, or descriptions."""
    updated = await service.update_scene(storyboard_id, scene_number, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Storyboard or scene not found")
    return updated


@router.post("/{storyboard_id}/scenes/{scene_number}/regenerate-prompt")
async def regenerate_scene_prompt(
    storyboard_id: str,
    scene_number: int,
    request: Optional[PromptRegenerateRequest] = None,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """Use Gemini to regenerate the generative prompt for a single scene with director feedback."""
    guidance = request.additional_guidance if request else None
    try:
        updated = await service.regenerate_scene_prompt(storyboard_id, scene_number, guidance)
        if not updated:
            raise HTTPException(status_code=404, detail="Storyboard or scene not found")
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene regeneration failed: {str(e)}")
