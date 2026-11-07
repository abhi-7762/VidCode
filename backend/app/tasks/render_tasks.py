from app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.final_render")
def final_render(self, project_id: str):
    """Phase 5: Assembles clips, audio, and subtitles via FFmpeg."""
    self.update_state(state="PROGRESS", meta={"progress": 0, "step": "starting"})
    return {"status": "not_implemented", "project_id": project_id}

