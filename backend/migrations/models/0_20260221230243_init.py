from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "openid" VARCHAR(128) NOT NULL UNIQUE,
    "nickname" VARCHAR(64) NOT NULL,
    "avatar_url" VARCHAR(512) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_users_openid_333a8f" ON "users" ("openid");
CREATE TABLE IF NOT EXISTS "books" (
    "id" UUID NOT NULL PRIMARY KEY,
    "title" VARCHAR(128) NOT NULL,
    "author" VARCHAR(64) NOT NULL,
    "sentence_count" INT NOT NULL,
    "sort_order" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_books_title_396825" ON "books" ("title");
CREATE INDEX IF NOT EXISTS "idx_books_sort_or_5bb53d" ON "books" ("sort_order");
CREATE TABLE IF NOT EXISTS "sentences" (
    "id" UUID NOT NULL PRIMARY KEY,
    "book_id" UUID NOT NULL,
    "text" TEXT NOT NULL,
    "context_before" TEXT NOT NULL,
    "context_after" TEXT NOT NULL,
    "chapter" VARCHAR(256) NOT NULL,
    "ai_explanation" TEXT NOT NULL,
    "counter_quote" TEXT NOT NULL,
    "counter_source" VARCHAR(256) NOT NULL,
    "similar_quotes" JSONB NOT NULL,
    "opposite_quotes" JSONB NOT NULL,
    "sort_order" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_sentences_book_id_6a15ce" ON "sentences" ("book_id");
CREATE INDEX IF NOT EXISTS "idx_sentences_sort_or_e6b508" ON "sentences" ("sort_order");
CREATE TABLE IF NOT EXISTS "bookmarks" (
    "id" UUID NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL,
    "sentence_id" UUID NOT NULL,
    "cancelled" BOOL NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    CONSTRAINT "uid_bookmarks_user_id_0799c2" UNIQUE ("user_id", "sentence_id")
);
CREATE INDEX IF NOT EXISTS "idx_bookmarks_user_id_a8e8e3" ON "bookmarks" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_bookmarks_sentenc_f461aa" ON "bookmarks" ("sentence_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
