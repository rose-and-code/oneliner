import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SOUL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "SOUL.md"
SPROUT_SKILL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "skills" / "garden-sprout" / "SKILL.md"


def _load_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


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
    authors: dict[str, list[str]] = {}
    for fav in favorites:
        for t in fav.get("themes", []):
            if t not in theme_counts:
                theme_counts[t] = []
            theme_counts[t].append(fav.get("book_author", ""))
        author = fav.get("book_author", "")
        if author:
            if author not in authors:
                authors[author] = []
            authors[author].append(fav.get("text", "")[:20])

    sorted_themes = sorted(theme_counts.items(), key=lambda x: -len(x[1]))

    cross_book_authors = set()
    for fav in favorites:
        for t in fav.get("themes", []):
            if t in theme_counts and len(set(theme_counts[t])) >= 2:
                cross_book_authors.update(set(theme_counts[t]))

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
