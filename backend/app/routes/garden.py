from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from pydantic import BaseModel

from app.entities.user import User
from app.services.garden import create_agent_reply
from app.services.garden import create_sprout
from app.services.garden import get_garden_status
from app.services.garden import get_notification_payload
from app.services.garden import get_reply_list
from app.services.garden import get_unshown_sprout
from app.services.garden import get_user_context
from app.services.garden import mark_reply_read
from app.services.garden import mark_sprout_shown
from app.services.garden import should_generate_sprout
from app.services.garden import submit_reaction
from app.types.schemas import AgentReplyListResponse
from app.types.schemas import AgentReplyResponse
from app.types.schemas import CheckReplyResponse
from app.types.schemas import ReactionRequest
from app.utils.deps import current_user

router = APIRouter(prefix="/api/garden", tags=["garden"])

CurrentUser = Annotated[User, Depends(current_user)]


class SproutResponse(BaseModel):
    id: UUID
    text: str
    target_sentence_id: UUID | None
    created_at: datetime


class SproutShownRequest(BaseModel):
    sprout_id: UUID


class InternalSproutRequest(BaseModel):
    user_id: UUID
    text: str
    target_sentence_id: UUID | None = None


class InternalReplyRequest(BaseModel):
    user_id: UUID
    hook: str
    body: str
    target_sentence_id: UUID | None = None
    reaction_options: list[str] | None = None


@router.get("/status")
async def garden_status(user: CurrentUser):
    return await get_garden_status(user.id)


@router.get("/sprout")
async def get_sprout(user: CurrentUser, response: Response):
    sprout = await get_unshown_sprout(user.id)
    if not sprout:
        response.status_code = 204
        return None
    return SproutResponse(
        id=sprout.id,
        text=sprout.text,
        target_sentence_id=sprout.target_sentence_id,
        created_at=sprout.created_at,
    )


@router.post("/sprout/shown")
async def sprout_shown(req: SproutShownRequest, user: CurrentUser):
    await mark_sprout_shown(req.sprout_id)
    return {"ok": True}


@router.get("/check", response_model=CheckReplyResponse)
async def check_reply(user: CurrentUser):
    payload = await get_notification_payload(user.id)
    return payload


@router.get("/replies", response_model=AgentReplyListResponse)
async def list_replies(user: CurrentUser, limit: int = 20):
    limit = min(limit, 50)
    replies = await get_reply_list(user.id, limit)
    return AgentReplyListResponse(
        items=[
            AgentReplyResponse(
                id=r.id,
                hook=r.hook,
                body=r.body,
                target_sentence_id=r.target_sentence_id,
                reaction_options=r.reaction_options,
                reaction=r.reaction,
                created_at=r.created_at,
            )
            for r in replies
        ]
    )


@router.post("/replies/{reply_id}/react")
async def react_to_reply(reply_id: UUID, req: ReactionRequest, user: CurrentUser):
    ok = await submit_reaction(reply_id, user.id, req.reaction)
    if not ok:
        return {"ok": False}
    return {"ok": True}


@router.post("/replies/{reply_id}/read")
async def read_reply(reply_id: UUID, user: CurrentUser):
    await mark_reply_read(reply_id, user.id)
    return {"ok": True}


@router.get("/context")
async def user_context(user: CurrentUser):
    return await get_user_context(user.id)


@router.post("/internal/sprout")
async def internal_create_sprout(req: InternalSproutRequest):
    sprout = await create_sprout(req.user_id, req.text, req.target_sentence_id)
    return {"id": str(sprout.id)}


@router.post("/internal/reply")
async def internal_create_reply(req: InternalReplyRequest):
    reply = await create_agent_reply(
        req.user_id,
        req.hook,
        req.body,
        req.target_sentence_id,
        req.reaction_options,
    )
    return {"id": str(reply.id)}


@router.get("/internal/should-sprout/{user_id}")
async def internal_should_sprout(user_id: UUID):
    should = await should_generate_sprout(user_id)
    return {"should_generate": should}


@router.get("/internal/context/{user_id}")
async def internal_user_context(user_id: UUID):
    return await get_user_context(user_id)
