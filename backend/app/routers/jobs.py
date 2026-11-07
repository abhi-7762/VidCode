from fastapi import APIRouter, HTTPException
from app.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{task_id}")
async def get_job_status(task_id: str):
    """Poll a Celery task's status and progress."""
    result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.state,
        "progress": 0,
        "result": None,
        "error": None,
    }

    if result.state == "PROGRESS":
        info = result.info or {}
        response["progress"] = info.get("progress", 0)
        response["step"] = info.get("step", "")
    elif result.state == "SUCCESS":
        response["progress"] = 100
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["error"] = str(result.info)

    return response

