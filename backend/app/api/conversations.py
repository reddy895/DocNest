import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.auth_dependency import get_current_user
from backend.app.models.auth import UserOut
from backend.app.models.schemas import ChatSessionInfo, ChatMessageInfo, FeedbackRequest
from backend.app.services.conversation_service import get_conversation_service

logger = logging.getLogger("docnest.api.conversations")
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(default="New Research", max_length=120)
    workspace_id: Optional[str] = "Default Workspace"


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    is_pinned: Optional[bool] = None


class PaginatedConversationsResponse(BaseModel):
    items: List[ChatSessionInfo]
    total: int
    limit: int
    offset: int


class AddMessageRequest(BaseModel):
    sender: str = Field(pattern="^(user|assistant|system)$")
    text: str = Field(min_length=1)
    citations: Optional[List[Dict[str, Any]]] = None
    retrieval_trace: Optional[Dict[str, Any]] = None


@router.get("", response_model=PaginatedConversationsResponse)
async def list_conversations(
    q: Optional[str] = Query(None, description="Search keyword in titles or message text"),
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserOut = Depends(get_current_user),
):
    """List research conversations with title/message full-text search and pagination."""
    conv_service = get_conversation_service()
    sessions, total = await conv_service.get_user_sessions(
        user_id=current_user.id,
        workspace_id=workspace_id,
        search_query=q,
        limit=limit,
        offset=offset,
    )
    return PaginatedConversationsResponse(
        items=[ChatSessionInfo(**s) for s in sessions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ChatSessionInfo, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: CreateConversationRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Create a new conversational research session."""
    conv_service = get_conversation_service()
    session = await conv_service.create_session(
        user_id=current_user.id,
        title=payload.title or "New Research",
        workspace_id=payload.workspace_id or "Default Workspace",
    )
    return ChatSessionInfo(**session)


@router.get("/{session_id}", response_model=ChatSessionInfo)
async def get_conversation(
    session_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    """Get single conversation session details."""
    conv_service = get_conversation_service()
    session = await conv_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ChatSessionInfo(**session)


@router.patch("/{session_id}", response_model=ChatSessionInfo)
async def update_conversation(
    session_id: str,
    payload: UpdateConversationRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Rename or toggle pin status for a conversation."""
    conv_service = get_conversation_service()
    session = await conv_service.update_session(
        session_id=session_id,
        title=payload.title,
        is_pinned=payload.is_pinned,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ChatSessionInfo(**session)


@router.delete("/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    """Delete a conversation session and all its messages."""
    conv_service = get_conversation_service()
    success = await conv_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "session_id": session_id, "message": "Conversation deleted successfully"}


@router.get("/{session_id}/messages", response_model=List[ChatMessageInfo])
async def get_conversation_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: UserOut = Depends(get_current_user),
):
    """Retrieve full message history for a conversation."""
    conv_service = get_conversation_service()
    messages = await conv_service.get_session_messages(session_id, limit=limit)
    return [ChatMessageInfo(**m) for m in messages]


@router.post("/{session_id}/messages/{message_id}/feedback")
async def record_feedback(
    session_id: str,
    message_id: str,
    payload: FeedbackRequest,
    current_user: UserOut = Depends(get_current_user),
):
    """Record user feedback rating on a specific message."""
    conv_service = get_conversation_service()
    success = await conv_service.record_feedback(
        message_id=message_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True, "message_id": message_id, "rating": payload.rating}
