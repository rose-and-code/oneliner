import json
from pathlib import Path
import re
import ssl
from uuid import UUID

import aiohttp
from loguru import logger

from app.config import settings
from app.services.book import _books
from app.services.book import get_sentence_by_id

SOUL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "SOUL.md"
SPROUT_SKILL_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "agent"
    / "skills"
    / "garden-sprout"
    / "SKILL.md"
)
REPLY_SKILL_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "agent"
    / "skills"
    / "garden-reply"
    / "SKILL.md"
)

MAX_HOOK_LEN = 30
MAX_BODY_LEN = 100
MAX_SPROUT_LEN = 60
MAX_DWELL_SECONDS = 120
MIN_UNIQUE_SENTENCES_FOR_LLM = 2


def _load_file(path: Path) -> str:
    """Load a text file, return empty string if not found."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _find_book_info(sentence: dict) -> tuple[str, str]:
    """从句子数据中查找所属书名和作者。"""
    for b in _books:
        if b["id"] == sentence.get("book_id"):
            return b["title"], b["author"]
    return "", ""


def _get_llm_config() -> tuple[str, str, str, bool] | None:
    """返回 (base_url, api_key, model, skip_ssl)，无可用配置则返回 None。"""
    provider = settings.llm_provider.lower()
    if provider == "openclaw":
        if settings.openclaw_api_key:
            return (
                settings.openclaw_base_url,
                settings.openclaw_api_key,
                settings.openclaw_model,
                True,
            )
        logger.warning("OpenClaw API 未配置，尝试 ARK 降级")  # noqa: RUF001
    if settings.ark_api_key:
        return (
            settings.ark_base_url,
            settings.ark_api_key,
            settings.ark_chat_model,
            False,
        )
    logger.warning("ARK API 未配置，使用降级方案")  # noqa: RUF001
    return None


async def _call_llm(system_prompt: str, user_prompt: str) -> dict | None:
    """用 aiohttp 直接调 OpenAI 兼容 API，解析 JSON 返回。"""
    cfg = _get_llm_config()
    if not cfg:
        return None
    base_url, api_key, model, skip_ssl = cfg
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 300,
    }
    ssl_ctx = False if skip_ssl else ssl.create_default_context()
    logger.info("LLM 请求 -> {} model={}", url, model)
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                ssl=ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp,
        ):
            body = await resp.json()
        content = body["choices"][0]["message"]["content"].strip()
        logger.info("LLM 原始返回: {}", content[:200])
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        parsed = json.loads(content)
        if parsed.get("text") == "null" or parsed.get("hook") == "null":
            return None
        return parsed
    except json.JSONDecodeError:
        try:
            content = _fix_json(content)
            return json.loads(content)
        except Exception:
            logger.warning(
                "LLM JSON 解析失败 ({}): {}", settings.llm_provider, content[:200]
            )
            return None
    except Exception as e:
        logger.warning("LLM 调用失败 ({}): {}", settings.llm_provider, e)
        return None


def _fix_json(raw: str) -> str:
    """Attempt to fix common LLM JSON issues like unescaped quotes in values."""
    return re.sub(
        r'(?<=: )"([^"]*)"([^",}\]\n]+)"',
        lambda m: '"'
        + m.group(1).replace('"', '\\"')
        + m.group(2).replace('"', '\\"')
        + '"',
        raw,
    )


def _truncate(result: dict) -> dict:
    """Truncate text fields to hard character limits."""
    if result.get("hook") and len(result["hook"]) > MAX_HOOK_LEN:
        result["hook"] = result["hook"][:MAX_HOOK_LEN]
    if result.get("body") and len(result["body"]) > MAX_BODY_LEN:
        result["body"] = result["body"][:MAX_BODY_LEN]
    if result.get("text") and len(result["text"]) > MAX_SPROUT_LEN:
        result["text"] = result["text"][:MAX_SPROUT_LEN]
    return result


def _normalize_rec(result: dict) -> dict:
    """Ensure rec field has valid structure or remove it."""
    rec = result.get("rec")
    if not rec or not isinstance(rec, dict):
        result.pop("rec", None)
        return result
    if not rec.get("quote") or not rec.get("book"):
        result.pop("rec", None)
    return result


def _has_enough_data(user_context: dict) -> bool:
    """Check if there's enough diverse data to generate a meaningful reply."""
    events = user_context.get("events", [])
    favorites = user_context.get("favorites", [])
    event_sids = {
        e.get("sentence_id")
        for e in events
        if e.get("sentence_id") and e.get("sentence_text")
    }
    fav_sids = {f.get("sentence_id") for f in favorites}
    all_sids = event_sids | fav_sids
    return len(all_sids) >= MIN_UNIQUE_SENTENCES_FOR_LLM


async def generate_sprout(user_context: dict) -> dict | None:
    """生成冒芽：先尝试 LLM，失败则降级到模板。"""
    if not _has_enough_data(user_context):
        return None

    soul = _load_file(SOUL_PATH)
    skill = _load_file(SPROUT_SKILL_PATH)
    system_prompt = f"{soul}\n\n---\n\n{skill}"
    user_prompt = _build_user_prompt(user_context)

    result = await _call_llm(system_prompt, user_prompt)
    if result and result.get("text"):
        return _truncate(result)
    return _generate_sprout_fallback(user_context)


async def analyze_events_and_generate_reply(
    user_id: UUID, user_context: dict
) -> dict | None:
    """分析行为事件，生成花灵回复。先尝试 LLM，失败则降级。"""
    if not _has_enough_data(user_context):
        return _generate_reply_fallback(user_id, user_context)

    soul = _load_file(SOUL_PATH)
    skill = _load_file(REPLY_SKILL_PATH)
    system_prompt = f"{soul}\n\n---\n\n{skill}"
    user_prompt = _build_user_prompt(user_context)

    result = await _call_llm(system_prompt, user_prompt)
    if result and result.get("hook") and result.get("body"):
        if "reaction_options" not in result or not result["reaction_options"]:
            result["reaction_options"] = ["确实", "才不是"]
        return _normalize_rec(_truncate(result))
    return _generate_reply_fallback(user_id, user_context)


def _build_user_prompt(user_context: dict) -> str:
    """构建用户上下文 prompt。过滤无效数据，限制 dwell 时间。"""
    parts = []

    events = user_context.get("events", [])
    valid_events = [e for e in events if e.get("sentence_text")]
    if valid_events:
        parts.append("最近行为：\n")  # noqa: RUF001
        for e in valid_events[:15]:
            line = f"- [{e['event_type']}] 「{e['sentence_text'][:30]}」"
            if e.get("book_title"):
                line += f" —— {e.get('book_author', '')}《{e['book_title']}》"
            if e["event_type"] == "dwell" and e.get("duration_ms"):
                capped = min(e["duration_ms"] // 1000, MAX_DWELL_SECONDS)
                if capped >= 10:
                    line += "（停了一会儿）"  # noqa: RUF001
            if e.get("opposite_quote"):
                oq = e["opposite_quote"]
                line += f" → 翻面：「{oq['text'][:20]}」{oq.get('book_author', '')}"  # noqa: RUF001
            parts.append(line)

    favorites = user_context.get("favorites", [])
    if favorites:
        parts.append("\n收藏：\n")  # noqa: RUF001
        for f in favorites[:10]:
            line = f"- 「{f['text'][:30]}」—— {f.get('book_author', '')}《{f.get('book_title', '')}》"
            parts.append(line)

    if not parts:
        return "暂无数据"

    return "\n".join(parts)


def _generate_sprout_fallback(user_context: dict) -> dict | None:
    """降级：基于规则模板生成冒芽。"""
    favorites = user_context.get("favorites", [])
    if len(favorites) < 3:
        return None

    cross_book = _detect_cross_book_link(favorites)
    if cross_book:
        return cross_book

    theme_counts: dict[str, list[str]] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            if t not in theme_counts:
                theme_counts[t] = []
            theme_counts[t].append(fav.get("book_author", ""))

    sorted_themes = sorted(theme_counts.items(), key=lambda x: -len(x[1]))

    if len(sorted_themes) >= 1 and len(set(sorted_themes[0][1])) >= 2:
        authors = list(set(sorted_themes[0][1]))[:2]
        return {
            "text": f"诶，{authors[0]}和{authors[1]}被你翻到一起了，挺有意思的",  # noqa: RUF001
            "target_sentence_id": favorites[0].get("sentence_id"),
        }

    return None


def _detect_cross_book_link(favorites: list[dict]) -> dict | None:
    """检测跨书收藏联系。"""
    if len(favorites) < 3:
        return None
    by_theme: dict[str, list[dict]] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            if t not in by_theme:
                by_theme[t] = []
            by_theme[t].append(fav)
    for _theme, fav_list in sorted(by_theme.items(), key=lambda x: -len(x[1])):
        authors = list({f["book_author"] for f in fav_list if f.get("book_author")})
        if len(authors) >= 2:
            f1 = next(f for f in fav_list if f.get("book_author") == authors[0])
            return {
                "text": f"你有没有发现呢，{authors[0]}和{authors[1]}在你的收藏里说了差不多的事",  # noqa: RUF001
                "target_sentence_id": f1.get("sentence_id"),
            }
    return None


def _generate_reply_fallback(_user_id: UUID, user_context: dict) -> dict | None:
    """降级：从行为中检测模式，生成模板回复。"""
    events = user_context.get("events", [])
    favorites = user_context.get("favorites", [])
    if len(events) < 3:
        return None
    return _detect_pattern(events, favorites)


def _detect_pattern(events: list[dict], favorites: list[dict]) -> dict | None:
    """检测行为模式，按优先级返回。"""
    flip_dwell = _detect_flip_then_dwell(events)
    if flip_dwell:
        return flip_dwell

    cross_book = _detect_cross_book_favorites(favorites)
    if cross_book:
        return cross_book

    return None


def _detect_flip_then_dwell(events: list[dict]) -> dict | None:
    """检测翻面后停留。"""
    for i, e in enumerate(events[:20]):
        if e["event_type"] != "dwell" or e.get("duration_ms", 0) < 10000:
            continue
        if e.get("duration_ms", 0) > MAX_DWELL_SECONDS * 1000:
            continue
        sid = e.get("sentence_id")
        if not sid:
            continue
        for j in range(i + 1, min(i + 5, len(events))):
            if (
                events[j]["event_type"] == "flip"
                and events[j].get("sentence_id") == sid
            ):
                sentence = get_sentence_by_id(str(sid))
                if not sentence:
                    break
                oq = sentence.get("opposite_quotes", [])
                if not oq:
                    break
                _, book_author = _find_book_info(sentence)
                oq_author = oq[0].get("book_author", "")
                return {
                    "hook": "诶，你翻面之后在那停了一会儿",  # noqa: RUF001
                    "body": f"{book_author}那页你翻了面，{oq_author}那句你看得更久",  # noqa: RUF001
                    "target_sentence_id": sid,
                    "reaction_options": ["确实在想", "随手翻的"],
                }
    return None


def _detect_cross_book_favorites(favorites: list[dict]) -> dict | None:
    """检测收藏中跨作者联系。"""
    if len(favorites) < 4:
        return None

    by_theme: dict[str, list[dict]] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            if t not in by_theme:
                by_theme[t] = []
            by_theme[t].append(fav)

    for theme, fav_list in sorted(by_theme.items(), key=lambda x: -len(x[1])):
        authors = list({f["book_author"] for f in fav_list if f.get("book_author")})
        if len(authors) < 2 or len(fav_list) < 3:
            continue
        a1, a2 = authors[0], authors[1]
        return {
            "hook": "你有没有发现呢，你收的几句话有个共同点",  # noqa: RUF001
            "body": f"{a1}和{a2}在你的收藏里都在讲「{theme}」，角度不太一样",  # noqa: RUF001
            "target_sentence_id": None,
            "reaction_options": ["被说中了", "巧合吧"],
        }

    return None
