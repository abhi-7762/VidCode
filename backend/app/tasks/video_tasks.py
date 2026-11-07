from app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.generate_video_clips")
def generate_video_clips(self, project_id: str, storyboard_id: str):
    """Phase 4: Generates video clips from storyboard scenes."""
    self.update_state(state="PROGRESS", meta={"progress": 0, "step": "starting"})
    return {"status": "not_implemented", "project_id": project_id}

