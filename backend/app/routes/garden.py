from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from pydantic import BaseModel

from app.entities.sprout import Sprout
from app.entities.user import User
from app.services.garden import create_sprout
from app.services.garden import get_garden_status
from app.services.garden import get_notification_payload
from app.services.garden import get_sprout_list
from app.services.garden import get_unshown_sprout
from app.services.garden import get_user_context
from app.services.garden import mark_sprout_shown
from app.services.garden import should_generate_sprout_on_favorite
from app.services.garden import submit_sprout_reaction
from app.types.schemas import ReactionRequest
from app.types.schemas import RecResponse
from app.types.schemas import SproutListResponse
from app.types.schemas import SproutResponse
from app.utils.deps import current_user

router = APIRouter(prefix="/api/garden", tags=["garden"])

CurrentUser = Annotated[User, Depends(current_user)]


def _to_sprout_response(s: Sprout) -> SproutResponse:
    """Convert a Sprout entity to SproutResponse."""
    rec = None
    if s.rec and isinstance(s.rec, dict):
        rec = RecResponse(**s.rec)
    return SproutResponse(
        id=s.id,
        text=s.text,
        hook=s.hook,
        target_sentence_id=s.target_sentence_id,
        reaction_options=s.reaction_options,
        reaction=s.reaction,
        rec=rec,
        created_at=s.created_at,
    )


class SproutShownRequest(BaseModel):
    sprout_id: UUID


class InternalSproutRequest(BaseModel):
    user_id: UUID
    text: str
    hook: str = ""
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
    return _to_sprout_response(sprout)


@router.post("/sprout/shown")
async def sprout_shown(req: SproutShownRequest, user: CurrentUser):
    await mark_sprout_shown(req.sprout_id, user.id)
    return {"ok": True}


@router.get("/sprout/check")
async def check_sprout(user: CurrentUser):
    return await get_notification_payload(user.id)


@router.get("/sprout/list", response_model=SproutListResponse)
async def list_sprouts(user: CurrentUser, limit: int = 20):
    limit = min(limit, 50)
    sprouts = await get_sprout_list(user.id, limit)
    return SproutListResponse(items=[_to_sprout_response(s) for s in sprouts])


@router.post("/sprout/{sprout_id}/react")
async def react_to_sprout(sprout_id: UUID, req: ReactionRequest, user: CurrentUser):
    ok = await submit_sprout_reaction(sprout_id, user.id, req.reaction)
    return {"ok": ok}


@router.get("/context")
async def user_context(user: CurrentUser):
    return await get_user_context(user.id)


@router.post("/internal/sprout")
async def internal_create_sprout(req: InternalSproutRequest):
    sprout = await create_sprout(
        req.user_id,
        req.text,
        hook=req.hook,
        target_sentence_id=req.target_sentence_id,
        reaction_options=req.reaction_options,
    )
    return {"id": str(sprout.id)}


@router.get("/internal/should-sprout/{user_id}")
async def internal_should_sprout(user_id: UUID):
    should = await should_generate_sprout_on_favorite(user_id)
    return {"should_generate": should}


@router.get("/internal/context/{user_id}")
async def internal_user_context(user_id: UUID):
    return await get_user_context(user_id)
