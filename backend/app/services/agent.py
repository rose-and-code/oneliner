import json
import logging
from pathlib import Path
from uuid import UUID

from app.entities.event import UserEvent
from app.services.book import get_sentence_by_id
from app.services.book import _books

logger = logging.getLogger(__name__)

SOUL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "SOUL.md"
SPROUT_SKILL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "skills" / "garden-sprout" / "SKILL.md"
REPLY_SKILL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "skills" / "garden-reply" / "SKILL.md"


def _load_file(path: Path) -> str:
    """Load a text file, return empty string if not found."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _find_book_for_sentence(sentence: dict) -> dict:
    """Find the book a sentence belongs to."""
    book_id = sentence.get("book_id")
    for b in _books:
        if b["id"] == book_id:
            return b
    return {}


async def generate_sprout_via_openclaw(user_context: dict) -> dict | None:
    """通过 OpenClaw SDK 调用 Garden Agent 生成冒芽（需要 Gateway 部署后启用）"""
    try:
        from openclaw_sdk import OpenClawClient
        async with await OpenClawClient.connect() as client:
            agent = client.get_agent("garden")
            prompt = f"执行 garden-sprout skill，用户上下文：{json.dumps(user_context, ensure_ascii=False)}"
            result = await agent.execute(prompt)
            return json.loads(result.content)
    except ImportError:
        logger.warning("openclaw-sdk 未安装，使用降级方案")
        return None
    except Exception as e:
        logger.warning("OpenClaw 调用失败: %s，使用降级方案", e)
        return None


async def generate_sprout_fallback(user_context: dict) -> dict | None:
    """降级方案：基于规则模板生成冒芽（不依赖 AI）"""
    favorites = user_context.get("favorites", [])
    if len(favorites) < 3:
        return None

    theme_counts: dict[str, list[str]] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            if t not in theme_counts:
                theme_counts[t] = []
            theme_counts[t].append(fav.get("book_author", ""))

    sorted_themes = sorted(theme_counts.items(), key=lambda x: -len(x[1]))

    if len(sorted_themes) >= 1 and len(set(sorted_themes[0][1])) >= 2:
        theme = sorted_themes[0][0]
        unique_authors = list(set(sorted_themes[0][1]))[:2]
        return {
            "text": f"{unique_authors[0]}和{unique_authors[1]}，都在说「{theme}」这件事，你注意到了吗。",
            "target_sentence_id": favorites[0].get("sentence_id"),
        }

    if len(sorted_themes) >= 2:
        t1 = sorted_themes[0][0]
        t2 = sorted_themes[1][0]
        return {
            "text": f"你最近种的种子，一半在想「{t1}」，一半在想「{t2}」。",
            "target_sentence_id": None,
        }

    if len(favorites) >= 5:
        return {
            "text": f"你已经种了{len(favorites)}颗种子了，花园开始有自己的形状了。",
            "target_sentence_id": None,
        }

    return None


async def generate_sprout(user_context: dict) -> dict | None:
    """生成冒芽：先尝试 OpenClaw，失败则降级到模板"""
    result = await generate_sprout_via_openclaw(user_context)
    if result:
        return result
    return await generate_sprout_fallback(user_context)


async def generate_reply_via_openclaw(user_context: dict) -> dict | None:
    """通过 OpenClaw SDK 调用 Garden Agent 生成花灵回复"""
    try:
        from openclaw_sdk import OpenClawClient
        async with await OpenClawClient.connect() as client:
            agent = client.get_agent("garden")
            prompt = f"执行 garden-reply skill，用户上下文：{json.dumps(user_context, ensure_ascii=False)}"
            result = await agent.execute(prompt)
            return json.loads(result.content)
    except ImportError:
        return None
    except Exception as e:
        logger.warning("OpenClaw reply 调用失败: %s", e)
        return None


async def analyze_events_and_generate_reply(user_id: UUID, user_context: dict) -> dict | None:
    """分析用户行为事件流，生成花灵回复。先尝试 OpenClaw，失败则降级到规则模板。"""
    result = await generate_reply_via_openclaw(user_context)
    if result:
        return result
    return await _generate_reply_fallback(user_id, user_context)


async def _generate_reply_fallback(user_id: UUID, user_context: dict) -> dict | None:
    """降级方案：从行为事件中检测模式，生成规则模板回复"""
    events = user_context.get("events", [])
    favorites = user_context.get("favorites", [])

    if len(events) < 3:
        return None

    pattern = _detect_pattern(events, favorites)
    if not pattern:
        return None

    return pattern


def _detect_pattern(events: list[dict], favorites: list[dict]) -> dict | None:
    """从行为事件和收藏中检测可触发回复的模式，按优先级返回第一个命中。"""

    long_dwell = _detect_long_dwell(events)
    if long_dwell:
        return long_dwell

    consecutive_theme = _detect_consecutive_theme(events, favorites)
    if consecutive_theme:
        return consecutive_theme

    same_theme_favorites = _detect_same_theme_favorites(favorites)
    if same_theme_favorites:
        return same_theme_favorites

    return None


def _detect_long_dwell(events: list[dict]) -> dict | None:
    """检测异常长停留：用户在某句话上停了很久"""
    dwell_events = [e for e in events if e["event_type"] == "dwell" and e.get("duration_ms", 0) > 15000]
    if not dwell_events:
        return None

    longest = max(dwell_events, key=lambda e: e.get("duration_ms", 0))
    seconds = longest["duration_ms"] // 1000
    sentence_text = longest.get("sentence_text", "")
    snippet = sentence_text[:15] + "..." if len(sentence_text) > 15 else sentence_text

    return {
        "hook": f"这句你停了{seconds}秒，比平时久。",
        "body": f"「{snippet}」这句你看了{seconds}秒。大多数句子你几秒就划过去了，这句让你停下来了。",
        "target_sentence_id": None,
        "reaction_options": ["被看到了", "没那回事"],
    }


def _detect_consecutive_theme(events: list[dict], favorites: list[dict]) -> dict | None:
    """检测连续浏览同主题内容"""
    view_events = [e for e in events if e["event_type"] in ("dwell", "context_open", "flip")]
    if len(view_events) < 3:
        return None

    recent_texts = [e.get("sentence_text", "") for e in view_events[:10]]
    recent_ids = []
    for e in view_events[:10]:
        sid = e.get("sentence_id")
        if sid:
            recent_ids.append(sid)

    theme_streak: dict[str, int] = {}
    for sid in recent_ids:
        sentence = get_sentence_by_id(str(sid)) if sid else None
        if not sentence:
            continue
        for t in sentence.get("themes", []):
            theme_streak[t] = theme_streak.get(t, 0) + 1

    if not theme_streak:
        return None

    top_theme, count = max(theme_streak.items(), key=lambda x: x[1])
    if count < 3:
        return None

    return {
        "hook": f"你连翻了{count}页都是关于{top_theme}的。",
        "body": f"最近{count}条你看过的内容里，都在围绕「{top_theme}」。不知道你有没有注意到。",
        "target_sentence_id": None,
        "reaction_options": ["确实", "才不是"],
    }


def _detect_same_theme_favorites(favorites: list[dict]) -> dict | None:
    """检测收藏中高度集中的主题"""
    if len(favorites) < 4:
        return None

    theme_counts: dict[str, int] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            theme_counts[t] = theme_counts.get(t, 0) + 1

    if not theme_counts:
        return None

    top_theme, count = max(theme_counts.items(), key=lambda x: x[1])
    total = len(favorites)
    ratio = count / total

    if ratio < 0.5 or count < 3:
        return None

    return {
        "hook": f"你收藏的{total}句话里有{count}句在讲同一件事。",
        "body": f"「{top_theme}」这个词在你的花园里反复出现。你收藏的{total}句话里，{count}句都跟它有关。",
        "target_sentence_id": None,
        "reaction_options": ["有点准", "想多了"],
    }
