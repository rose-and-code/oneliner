from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "openid" VARCHAR(128) NOT NULL UNIQUE,
    "nickname" VARCHAR(64) NOT NULL DEFAULT '',
    "avatar_url" VARCHAR(512) NOT NULL DEFAULT '',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_openid" ON "users" ("openid");
CREATE TABLE IF NOT EXISTS "favorites" (
    "id" UUID NOT NULL PRIMARY KEY,
    "user_id" UUID NOT NULL,
    "sentence_id" UUID NOT NULL,
    "is_cancelled" BOOL NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_favorites_user_id_sentence_id" UNIQUE ("user_id", "sentence_id")
);
CREATE INDEX IF NOT EXISTS "idx_favorites_user_id" ON "favorites" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_favorites_sentence_id" ON "favorites" ("sentence_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "favorites";
        DROP TABLE IF EXISTS "users";
        DROP TABLE IF EXISTS "aerich";"""
