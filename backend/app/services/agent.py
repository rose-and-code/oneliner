import json
import logging
from pathlib import Path
from uuid import UUID

from openai import AsyncOpenAI

from app.config import settings
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


def _get_client() -> AsyncOpenAI | None:
    """Get ARK API client, return None if not configured."""
    if not settings.ark_api_key:
        return None
    return AsyncOpenAI(api_key=settings.ark_api_key, base_url=settings.ark_base_url)


async def _call_llm(system_prompt: str, user_prompt: str) -> dict | None:
    """Call ARK LLM API and parse JSON response."""
    client = _get_client()
    if not client:
        logger.warning("ARK API 未配置，使用降级方案")
        return None
    try:
        resp = await client.chat.completions.create(
            model=settings.ark_chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=500,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except Exception as e:
        logger.warning("ARK API 调用失败: %s，使用降级方案", e)
        return None


async def generate_sprout(user_context: dict) -> dict | None:
    """生成冒芽：先尝试 LLM，失败则降级到模板"""
    soul = _load_file(SOUL_PATH)
    skill = _load_file(SPROUT_SKILL_PATH)
    system_prompt = f"{soul}\n\n---\n\n{skill}"
    user_prompt = f"用户上下文：\n{json.dumps(user_context, ensure_ascii=False, indent=2)}"

    result = await _call_llm(system_prompt, user_prompt)
    if result and result.get("text"):
        return result
    return await _generate_sprout_fallback(user_context)


async def analyze_events_and_generate_reply(user_id: UUID, user_context: dict) -> dict | None:
    """分析用户行为事件流，生成花灵回复。先尝试 LLM，失败则降级到规则模板。"""
    soul = _load_file(SOUL_PATH)
    skill = _load_file(REPLY_SKILL_PATH)
    system_prompt = f"{soul}\n\n---\n\n{skill}"
    user_prompt = f"用户上下文：\n{json.dumps(user_context, ensure_ascii=False, indent=2)}"

    result = await _call_llm(system_prompt, user_prompt)
    if result and result.get("hook") and result.get("body"):
        if "reaction_options" not in result or not result["reaction_options"]:
            result["reaction_options"] = ["确实", "才不是"]
        return result
    return await _generate_reply_fallback(user_id, user_context)


async def _generate_sprout_fallback(user_context: dict) -> dict | None:
    """降级方案：基于规则模板生成冒芽"""
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


async def _generate_reply_fallback(user_id: UUID, user_context: dict) -> dict | None:
    """降级方案：从行为事件中检测模式，生成规则模板回复"""
    events = user_context.get("events", [])
    favorites = user_context.get("favorites", [])

    if len(events) < 3:
        return None

    return _detect_pattern(events, favorites)


def _detect_pattern(events: list[dict], favorites: list[dict]) -> dict | None:
    """从行为事件和收藏中检测可触发回复的模式，按优先级返回第一个命中。"""
    long_dwell = _detect_long_dwell(events)
    if long_dwell:
        return long_dwell

    consecutive_theme = _detect_consecutive_theme(events)
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


def _detect_consecutive_theme(events: list[dict]) -> dict | None:
    """检测连续浏览同主题内容"""
    view_events = [e for e in events if e["event_type"] in ("dwell", "context_open", "flip")]
    if len(view_events) < 3:
        return None

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
