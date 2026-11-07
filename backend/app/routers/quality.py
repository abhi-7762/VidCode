from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.models.quality import (
    ValidationResult,
    VisualQualityCheck,
    CostEstimate,
    SpliceSceneRequest,
)
from app.services.validator_service import ValidatorService
from app.services.visual_check_service import VisualCheckService
from app.services.cost_service import CostService
from app.services.version_service import VersionService

router = APIRouter(prefix="/quality", tags=["Quality & Optimization"])


def get_validator_service() -> ValidatorService:
    return ValidatorService()


def get_visual_check_service() -> VisualCheckService:
    return VisualCheckService()


def get_cost_service() -> CostService:
    return CostService()


def get_version_service() -> VersionService:
    return VersionService()


@router.get("/validate/{project_id}", response_model=ValidationResult)
async def validate_project_video(
    project_id: str,
    service: ValidatorService = Depends(get_validator_service),
):
    """
    Performs technical inspection of the project's rendered master video:
    - Codec verification (H.264/AAC)
    - Frame rate and duration check
    - Resolution and bitrate health
    - Container integrity and stream detection
    """
    return service.validate_project_output(project_id)


@router.post("/visual-audit/{storyboard_id}", response_model=VisualQualityCheck)
async def visual_audit(
    storyboard_id: str,
    service: VisualCheckService = Depends(get_visual_check_service),
):
    """
    Gemini-powered cinematic audit:
    - Overall aesthetic scoring (0-10)
    - Character consistency across scene prompts
    - Cinematography and lighting continuity
    - Specific prompt enhancement recommendations
    """
    return await service.audit_storyboard(storyboard_id)


@router.get("/cost-estimate/{project_id}", response_model=CostEstimate)
async def estimate_costs(
    project_id: str,
    service: CostService = Depends(get_cost_service),
):
    """
    Calculates estimated API consumption and dollar expenses:
    - Gemini LLM tokens (script & storyboard)
    - Video diffusion rendering (Runway / Luma)
    - Voiceover generation (Edge-TTS free vs ElevenLabs)
    - Actionable cost-reduction recommendations
    """
    return await service.calculate_project_cost(project_id)


@router.get("/versions/{project_id}")
async def list_versions(
    project_id: str,
    service: VersionService = Depends(get_version_service),
):
    """List all render versions (v1, v2...) recorded for a project."""
    versions = await service.list_versions(project_id)
    return {
        "project_id": project_id,
        "total_versions": len(versions),
        "versions": versions,
    }


@router.post("/versions/{project_id}/activate/{version_number}")
async def activate_version(
    project_id: str,
    version_number: int,
    service: VersionService = Depends(get_version_service),
):
    """Roll back or set a specific video version as active."""
    return await service.activate_version(project_id, version_number)


@router.post("/splice-scene")
async def splice_scene(
    request: SpliceSceneRequest,
    service: VersionService = Depends(get_version_service),
):
    """
    One-click targeted scene replacement:
    Regenerates only the requested scene clip, re-stitches the master video
    with FFmpeg, and automatically registers a new version without regenerating everything.
    """
    try:
        return await service.splice_scene_and_rerender(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene splicing failed: {str(e)}")
