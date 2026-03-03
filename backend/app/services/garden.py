from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID

from app.entities.agent_reply import AgentReply
from app.entities.event import UserEvent
from app.entities.favorite import Favorite
from app.entities.sprout import Sprout
from app.entities.user import User
from app.services.book import get_sentence_by_id
from app.services.book import _books


SPROUT_COOLDOWN_HOURS = 12
MIN_FAVORITES_FOR_SPROUT = 5
REPLY_LIST_LIMIT = 20


async def get_garden_status(user_id: UUID) -> dict:
    """获取花园状态：种子数、生长阶段、热门主题"""
    seed_count = await Favorite.filter(user_id=user_id, is_cancelled=False).count()
    stage = _calc_stage(seed_count)
    top_themes = await _calc_top_themes(user_id)
    has_unread = await Sprout.filter(user_id=user_id, shown=False).exists()
    return {
        "seed_count": seed_count,
        "stage": stage,
        "top_themes": top_themes,
        "has_unread_sprout": has_unread,
    }


async def get_unshown_sprout(user_id: UUID) -> Sprout:
    """获取最新的未展示冒芽"""
    return await Sprout.filter(user_id=user_id, shown=False).order_by("-created_at").first()


async def mark_sprout_shown(sprout_id: UUID):
    """标记冒芽已展示"""
    await Sprout.filter(id=sprout_id).update(shown=True)


async def should_generate_sprout(user_id: UUID) -> bool:
    """判断是否应该生成新冒芽"""
    fav_count = await Favorite.filter(user_id=user_id, is_cancelled=False).count()
    if fav_count < MIN_FAVORITES_FOR_SPROUT:
        return False

    unshown = await Sprout.filter(user_id=user_id, shown=False).exists()
    if unshown:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(hours=SPROUT_COOLDOWN_HOURS)
    recent = await Sprout.filter(user_id=user_id, created_at__gte=cutoff).exists()
    if recent:
        return False

    return True


async def get_user_context(user_id: UUID) -> dict:
    """获取用户收藏和行为数据，供 Agent 使用"""
    favorites = await Favorite.filter(user_id=user_id, is_cancelled=False).order_by("-created_at").limit(50)
    fav_data = []
    for fav in favorites:
        sentence = get_sentence_by_id(str(fav.sentence_id))
        if not sentence:
            continue
        book_title = ""
        book_author = ""
        for b in _books:
            if b["id"] == sentence.get("book_id"):
                book_title = b["title"]
                book_author = b["author"]
                break
        fav_data.append({
            "text": sentence["text"],
            "book_title": book_title,
            "book_author": book_author,
            "themes": sentence.get("themes", []),
            "sentence_id": str(fav.sentence_id),
        })

    recent_events = await UserEvent.filter(user_id=user_id).order_by("-created_at").limit(100)
    events_data = []
    for ev in recent_events:
        sentence = get_sentence_by_id(str(ev.sentence_id)) if ev.sentence_id else None
        events_data.append({
            "event_type": ev.event_type,
            "sentence_text": sentence["text"][:50] if sentence else "",
            "duration_ms": ev.duration_ms or 0,
        })

    return {"favorites": fav_data, "events": events_data}


async def create_sprout(user_id: UUID, text: str, target_sentence_id: UUID | None = None) -> Sprout:
    """写入一条冒芽"""
    return await Sprout.create(
        user_id=user_id,
        text=text,
        target_sentence_id=target_sentence_id,
    )


def _calc_stage(seed_count: int) -> str:
    if seed_count == 0:
        return "empty"
    if seed_count <= 4:
        return "seed"
    if seed_count <= 9:
        return "sprout"
    if seed_count <= 19:
        return "plant"
    return "tree"


async def _calc_top_themes(user_id: UUID) -> list[str]:
    favorites = await Favorite.filter(user_id=user_id, is_cancelled=False).values_list("sentence_id", flat=True)
    if len(favorites) < 3:
        return []
    theme_counts: dict[str, int] = {}
    for sid in favorites:
        sentence = get_sentence_by_id(str(sid))
        if not sentence:
            continue
        for t in sentence.get("themes", []):
            theme_counts[t] = theme_counts.get(t, 0) + 1
    sorted_themes = sorted(theme_counts.items(), key=lambda x: -x[1])
    return [t for t, _ in sorted_themes[:2]]


async def check_unread_reply(user_id: UUID) -> dict | None:
    """检查用户是否有未读的花灵回复，返回最新一条的钩子信息"""
    reply = await AgentReply.filter(user_id=user_id, shown=False).order_by("-created_at").first()
    if not reply:
        return None
    return {"reply_id": str(reply.id), "reply_hook": reply.hook}


async def get_notification_payload(user_id: UUID) -> dict:
    """获取通知载荷，用于注入到 API 响应中"""
    user = await User.filter(id=user_id).first()
    if not user or not user.has_unread_reply:
        return {"has_unread_reply": False}
    info = await check_unread_reply(user_id)
    if not info:
        await User.filter(id=user_id).update(has_unread_reply=False)
        return {"has_unread_reply": False}
    return {"has_unread_reply": True, "reply_id": info["reply_id"], "reply_hook": info["reply_hook"]}


async def get_reply_list(user_id: UUID, limit: int = REPLY_LIST_LIMIT) -> list[AgentReply]:
    """获取花灵回复列表"""
    return await AgentReply.filter(user_id=user_id).order_by("-created_at").limit(limit)


async def submit_reaction(reply_id: UUID, user_id: UUID, reaction: str) -> bool:
    """提交用户对花灵回复的回应"""
    updated = await AgentReply.filter(id=reply_id, user_id=user_id).update(reaction=reaction)
    return updated > 0


async def mark_reply_read(reply_id: UUID, user_id: UUID):
    """标记花灵回复已读，并重置 has_unread_reply"""
    await AgentReply.filter(id=reply_id, user_id=user_id).update(shown=True)
    has_more = await AgentReply.filter(user_id=user_id, shown=False).exists()
    if not has_more:
        await User.filter(id=user_id).update(has_unread_reply=False)


async def create_agent_reply(
    user_id: UUID,
    hook: str,
    body: str,
    target_sentence_id: UUID | None = None,
    reaction_options: list[str] | None = None,
) -> AgentReply:
    """写入一条花灵回复，并标记用户有未读"""
    reply = await AgentReply.create(
        user_id=user_id,
        hook=hook,
        body=body,
        target_sentence_id=target_sentence_id,
        reaction_options=reaction_options or ["确实", "才不是"],
    )
    await User.filter(id=user_id).update(has_unread_reply=True)
    return reply
