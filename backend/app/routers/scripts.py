from fastapi import APIRouter, HTTPException, Depends
from app.models.script import ScriptGenerateRequest
from app.services.script_service import ScriptService
from app.services.gemini_service import GeminiService
from pydantic import BaseModel

router = APIRouter(prefix="/scripts", tags=["Scripts & AI"])


def get_script_service() -> ScriptService:
    return ScriptService()


class ImproveRequest(BaseModel):
    feedback: str


class AnalyseRequest(BaseModel):
    prompt: str
    duration_seconds: int = 60


class StoryStructureRequest(BaseModel):
    topic: str
    duration_seconds: int = 60


# ── Generate ──────────────────────────────────────────────────────────

@router.post("/generate", status_code=201)
async def generate_script(
    request: ScriptGenerateRequest,
    service: ScriptService = Depends(get_script_service),
):
    """
    Generate a full AI video script from a user prompt.
    Uses Gemini for NLU + scriptwriting in one call.
    """
    try:
        script = await service.generate(request)
        return script
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


# ── Retrieve ──────────────────────────────────────────────────────────

@router.get("/{script_id}")
async def get_script(
    script_id: str,
    service: ScriptService = Depends(get_script_service),
):
    script = await service.get_by_id(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.get("/project/{project_id}")
async def get_script_by_project(
    project_id: str,
    service: ScriptService = Depends(get_script_service),
):
    script = await service.get_by_project(project_id)
    if not script:
        raise HTTPException(status_code=404, detail="No script found for this project")
    return script


# ── Improve ───────────────────────────────────────────────────────────

@router.post("/{script_id}/improve")
async def improve_script(
    script_id: str,
    body: ImproveRequest,
    service: ScriptService = Depends(get_script_service),
):
    """Rewrite the script using Gemini based on user feedback."""
    try:
        script = await service.improve(script_id, body.feedback)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        return script
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script improvement failed: {str(e)}")


# ── Utility endpoints ─────────────────────────────────────────────────

@router.post("/analyse-prompt")
async def analyse_prompt(body: AnalyseRequest):
    """
    Run NLU only — analyse a prompt without generating a full script.
    Useful for previewing what Gemini understands before committing.
    """
    try:
        gemini = GeminiService()
        nlu = await gemini.analyse_prompt(body.prompt, body.duration_seconds)
        return nlu.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/story-structures")
async def suggest_story_structures(body: StoryStructureRequest):
    """Get 3 narrative structure options for a topic."""
    try:
        gemini = GeminiService()
        structures = await gemini.suggest_story_structures(body.topic, body.duration_seconds)
        return {"structures": structures}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story structure generation failed: {str(e)}")

