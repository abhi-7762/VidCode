"""
Placeholder task stubs for Phase 1.
Real implementations added in Phase 2–5.
"""
from app.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.generate_script")
def generate_script(self, project_id: str):
    """Phase 2: Calls Gemini to generate a script from the project prompt."""
    self.update_state(state="PROGRESS", meta={"progress": 0, "step": "starting"})
    # TODO: implement in Phase 2
    return {"status": "not_implemented", "project_id": project_id}

