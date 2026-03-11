from datetime import UTC
from datetime import datetime
from datetime import timedelta
from uuid import UUID

from app.entities.event import UserEvent
from app.entities.favorite import Favorite
from app.entities.sprout import Sprout
from app.entities.user import User
from app.services.book import _books
from app.services.book import get_sentence_by_id

MIN_FAVORITES_FOR_SPROUT = 5
SPROUT_COOLDOWN_HOURS = 12

SPROUT_INITIAL_COOLDOWN_SECONDS = 30
SPROUT_ACTIVE_COOLDOWN_SECONDS = 120
SPROUT_STABLE_COOLDOWN_SECONDS = 180
SPROUT_LONG_COOLDOWN_SECONDS = 300
MIN_EVENTS_FOR_SPROUT = 2
SPROUT_LIST_LIMIT = 20


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


async def get_unshown_sprout(user_id: UUID) -> Sprout | None:
    """获取最新的未展示冒芽"""
    return (
        await Sprout.filter(user_id=user_id, shown=False)
        .order_by("-created_at")
        .first()
    )


async def mark_sprout_shown(sprout_id: UUID, user_id: UUID):
    """标记冒芽已展示，并重置 has_unread_sprout"""
    await Sprout.filter(id=sprout_id, user_id=user_id).update(shown=True)
    has_more = await Sprout.filter(user_id=user_id, shown=False).exists()
    if not has_more:
        await User.filter(id=user_id).update(has_unread_sprout=False)


async def should_generate_sprout_on_favorite(user_id: UUID) -> bool:
    """判断收藏触发时是否应该生成冒芽（低频，12小时冷却）"""
    fav_count = await Favorite.filter(user_id=user_id, is_cancelled=False).count()
    if fav_count < MIN_FAVORITES_FOR_SPROUT:
        return False
    unshown = await Sprout.filter(user_id=user_id, shown=False).exists()
    if unshown:
        return False
    cutoff = datetime.now(UTC) - timedelta(hours=SPROUT_COOLDOWN_HOURS)
    recent = await Sprout.filter(user_id=user_id, created_at__gte=cutoff).exists()
    return not recent


async def should_generate_sprout_on_event(user_id: UUID) -> bool:
    """判断行为事件触发时是否应该生成冒芽（高频，衰减冷却）"""
    unshown = await Sprout.filter(user_id=user_id, shown=False).exists()
    if unshown:
        return False
    event_count = await UserEvent.filter(user_id=user_id).count()
    if event_count < MIN_EVENTS_FOR_SPROUT:
        return False

    sprout_count = await Sprout.filter(user_id=user_id).count()
    if sprout_count == 0:
        cutoff = datetime.now(UTC) - timedelta(seconds=SPROUT_INITIAL_COOLDOWN_SECONDS)
        return await UserEvent.filter(user_id=user_id, created_at__gte=cutoff).exists()

    last_sprout = await Sprout.filter(user_id=user_id).order_by("-created_at").first()
    if not last_sprout:
        return True
    elapsed = (datetime.now(UTC) - last_sprout.created_at).total_seconds()

    cooldown = SPROUT_LONG_COOLDOWN_SECONDS
    if sprout_count <= 2:
        cooldown = SPROUT_ACTIVE_COOLDOWN_SECONDS
    elif sprout_count <= 5:
        cooldown = SPROUT_STABLE_COOLDOWN_SECONDS
    return elapsed >= cooldown


async def get_user_context(user_id: UUID) -> dict:
    """获取用户收藏和行为数据，供 Agent 使用"""
    favorites = (
        await Favorite.filter(user_id=user_id, is_cancelled=False)
        .order_by("-created_at")
        .limit(50)
    )
    fav_data = []
    for fav in favorites:
        sentence = get_sentence_by_id(str(fav.sentence_id))
        if not sentence:
            continue
        book_title, book_author = _find_book_info(sentence)
        entry = {
            "text": sentence["text"],
            "book_title": book_title,
            "book_author": book_author,
            "themes": sentence.get("themes", []),
            "sentence_id": str(fav.sentence_id),
        }
        oq = sentence.get("opposite_quotes", [])
        if oq:
            entry["opposite_quote"] = {
                "text": oq[0]["text"],
                "book_title": oq[0].get("book_title", ""),
                "book_author": oq[0].get("book_author", ""),
            }
        fav_data.append(entry)

    recent_events = (
        await UserEvent.filter(user_id=user_id).order_by("-created_at").limit(100)
    )
    events_data = []
    for ev in recent_events:
        sentence = get_sentence_by_id(str(ev.sentence_id)) if ev.sentence_id else None
        entry = {
            "event_type": ev.event_type,
            "sentence_id": str(ev.sentence_id) if ev.sentence_id else "",
            "duration_ms": ev.duration_ms or 0,
        }
        if sentence:
            book_title, book_author = _find_book_info(sentence)
            entry["sentence_text"] = sentence["text"]
            entry["book_title"] = book_title
            entry["book_author"] = book_author
            entry["themes"] = sentence.get("themes", [])
            if ev.event_type == "flip":
                oq = sentence.get("opposite_quotes", [])
                if oq:
                    entry["opposite_quote"] = {
                        "text": oq[0]["text"],
                        "book_title": oq[0].get("book_title", ""),
                        "book_author": oq[0].get("book_author", ""),
                    }
        events_data.append(entry)

    return {"favorites": fav_data, "events": events_data}


def _find_book_info(sentence: dict) -> tuple[str, str]:
    """从句子数据中查找所属书名和作者。"""
    for b in _books:
        if b["id"] == sentence.get("book_id"):
            return b["title"], b["author"]
    return "", ""


async def create_sprout(
    user_id: UUID,
    text: str,
    hook: str = "",
    target_sentence_id: UUID | None = None,
    reaction_options: list[str] | None = None,
    rec: dict | None = None,
) -> Sprout:
    """写入一条冒芽，并标记用户有未读"""
    sprout = await Sprout.create(
        user_id=user_id,
        text=text,
        hook=hook or text[:25],
        target_sentence_id=target_sentence_id,
        reaction_options=reaction_options or [],
        rec=rec,
    )
    await User.filter(id=user_id).update(has_unread_sprout=True)
    return sprout


async def check_unread_sprout(user_id: UUID) -> dict | None:
    """检查用户是否有未读冒芽，返回最新一条的钩子信息"""
    sprout = (
        await Sprout.filter(user_id=user_id, shown=False)
        .order_by("-created_at")
        .first()
    )
    if not sprout:
        return None
    return {"sprout_id": str(sprout.id), "sprout_hook": sprout.hook or sprout.text[:25]}


async def get_notification_payload(user_id: UUID) -> dict:
    """获取通知载荷，用于注入到 API 响应中"""
    user = await User.filter(id=user_id).first()
    if not user or not user.has_unread_sprout:
        return {"has_unread_sprout": False}
    info = await check_unread_sprout(user_id)
    if not info:
        await User.filter(id=user_id).update(has_unread_sprout=False)
        return {"has_unread_sprout": False}
    return {
        "has_unread_sprout": True,
        "sprout_id": info["sprout_id"],
        "sprout_hook": info["sprout_hook"],
    }


async def get_sprout_list(
    user_id: UUID, limit: int = SPROUT_LIST_LIMIT
) -> list[Sprout]:
    """获取冒芽时间线"""
    return await Sprout.filter(user_id=user_id).order_by("-created_at").limit(limit)


async def submit_sprout_reaction(sprout_id: UUID, user_id: UUID, reaction: str) -> bool:
    """提交用户对冒芽的回应"""
    updated = await Sprout.filter(id=sprout_id, user_id=user_id).update(
        reaction=reaction
    )
    return updated > 0


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
    favorites = await Favorite.filter(user_id=user_id, is_cancelled=False).values_list(
        "sentence_id", flat=True
    )
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
