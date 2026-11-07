from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_service() -> ProjectService:
    return ProjectService()


@router.post("/", response_model=dict, status_code=201)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
):
    """Create a new video project."""
    project = await service.create(data)
    return project


@router.get("/", response_model=List[dict])
async def list_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
):
    """List all projects (paginated)."""
    return await service.list_all(skip=skip, limit=limit)


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    """Get a single project by ID."""
    project = await service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=dict)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
):
    """Update project fields."""
    project = await service.update(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    """Delete a project."""
    deleted = await service.delete(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")

