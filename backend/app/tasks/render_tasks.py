"""
Phase 5 Celery tasks — async final video rendering and FFmpeg assembly.
"""
import asyncio
from app.celery_app import celery_app
from app.models.production import StartRenderRequest, ProductionSettings


@celery_app.task(bind=True, name="tasks.final_render", max_retries=2)
def final_render(self, project_id: str, storyboard_id: str, settings_dict: dict = None):
    """
    Celery task that executes the complete video production pipeline:
    Voice generation -> Subtitles -> FFmpeg video editing -> Master MP4.
    """
    try:
        self.update_state(state="PROGRESS", meta={"progress": 10, "step": "Initializing video production..."})

        from app.services.production_service import ProductionService

        prod_settings = ProductionSettings(**settings_dict) if settings_dict else ProductionSettings()
        request = StartRenderRequest(
            project_id=project_id,
            storyboard_id=storyboard_id,
            settings=prod_settings,
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            service = ProductionService()
            self.update_state(state="PROGRESS", meta={"progress": 30, "step": "Running production pipeline..."})
            job = loop.run_until_complete(service.create_render_job(request))
        finally:
            loop.close()

        self.update_state(state="PROGRESS", meta={"progress": 100, "step": "Render complete."})

        return {
            "status": "completed",
            "job_id": job.get("_id"),
            "project_id": project_id,
            "output_video_url": job.get("output_video_url"),
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=20)
