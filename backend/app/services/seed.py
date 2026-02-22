from app.entities.book import Book
from app.entities.sentence import Sentence
from app.services.seed_data_part1 import BOOKS_PART1
from app.services.seed_data_part2 import BOOKS_PART2
from app.services.seed_data_part3 import BOOKS_PART3


ALL_BOOKS = BOOKS_PART1 + BOOKS_PART2 + BOOKS_PART3


async def seed_all():
    """导入所有种子数据"""
    existing = await Book.all().count()
    if existing > 0:
        print(f"数据库已有 {existing} 本书，跳过导入")
        return

    for book_data in ALL_BOOKS:
        book = await Book.create(
            title=book_data["title"],
            author=book_data["author"],
            sentence_count=len(book_data["sentences"]),
            sort_order=book_data["sort_order"],
        )
        for s in book_data["sentences"]:
            await Sentence.create(
                book_id=book.id,
                text=s["text"],
                context_before=s["context_before"],
                context_after=s["context_after"],
                chapter=s["chapter"],
                ai_explanation=s["ai_explanation"],
                counter_quote=s["counter_quote"],
                counter_source=s["counter_source"],
                similar_quotes=s.get("similar_quotes", []),
                opposite_quotes=s.get("opposite_quotes", []),
                sort_order=s["sort_order"],
            )
        print(f"已导入《{book_data['title']}》{len(book_data['sentences'])} 句")

    print(f"种子数据导入完成，共 {len(ALL_BOOKS)} 本书")
