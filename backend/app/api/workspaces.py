import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserOut
from backend.app.services.workspace_service import get_workspace_service

logger = logging.getLogger("docnest.api.workspaces")
router = APIRouter(prefix="/api/workspaces", tags=["Workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    color: Optional[str] = Field(default="#F5C542", max_length=20)


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, max_length=20)


class WorkspaceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    color: str
    is_default: bool
    created_at: str
    updated_at: str
    document_count: int = 0


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(current_user: UserOut = Depends(get_current_user)):
    """List all research workspaces accessible by current user."""
    ws_svc = get_workspace_service()
    workspaces = await ws_svc.get_user_workspaces(current_user.id)
    return [WorkspaceResponse(**w) for w in workspaces]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: CreateWorkspaceRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Create a new isolated research workspace."""
    ws_svc = get_workspace_service()
    ws = await ws_svc.create_workspace(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description or "",
        color=payload.color or "#F5C542",
        is_default=False,
    )
    return WorkspaceResponse(**ws)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    """Get single workspace details by ID."""
    ws_svc = get_workspace_service()
    ws = await ws_svc.get_workspace_by_id(workspace_id, current_user.id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**ws)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    payload: UpdateWorkspaceRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Update workspace name, description, or color theme."""
    ws_svc = get_workspace_service()
    ws = await ws_svc.update_workspace(
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        color=payload.color,
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found or unauthorized")
    return WorkspaceResponse(**ws)


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    """Delete a workspace and reassign documents to default workspace."""
    ws_svc = get_workspace_service()
    success = await ws_svc.delete_workspace(workspace_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default workspace or workspace not found",
        )
    return {"success": True, "workspace_id": workspace_id, "message": "Workspace deleted successfully"}


@router.post("/{workspace_id}/documents/{document_id}")
async def assign_document(
    workspace_id: str,
    document_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    """Assign an existing document to a workspace."""
    ws_svc = get_workspace_service()
    # Verify target workspace exists
    ws = await ws_svc.get_workspace_by_id(workspace_id, current_user.id)
    if not ws:
        raise HTTPException(status_code=404, detail="Target workspace not found")

    success = await ws_svc.assign_document_to_workspace(document_id, workspace_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or update failed")

    return {"success": True, "document_id": document_id, "workspace_id": workspace_id}
