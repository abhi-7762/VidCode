"""
Phase 2 Celery tasks — async script generation via Gemini.
"""
import asyncio
from app.celery_app import celery_app
from app.models.script import ScriptGenerateRequest


@celery_app.task(bind=True, name="tasks.generate_script", max_retries=3)
def generate_script(self, project_id: str, prompt: str, duration_seconds: int = 60):
    """
    Async Celery task that calls GeminiService to generate a script.
    Progress is reported via task state so the frontend can poll.
    """
    try:
        self.update_state(state="PROGRESS", meta={"progress": 10, "step": "Analysing prompt..."})

        from app.services.script_service import ScriptService

        request = ScriptGenerateRequest(
            project_id=project_id,
            prompt=prompt,
            duration_seconds=duration_seconds,
        )

        self.update_state(state="PROGRESS", meta={"progress": 30, "step": "Understanding intent..."})

        # Run async service inside sync Celery task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            service = ScriptService()
            script = loop.run_until_complete(service.generate(request))
        finally:
            loop.close()

        self.update_state(state="PROGRESS", meta={"progress": 90, "step": "Saving script..."})

        return {
            "status": "completed",
            "script_id": script.get("_id"),
            "project_id": project_id,
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
