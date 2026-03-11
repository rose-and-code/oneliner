from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "openid" VARCHAR(128) NOT NULL UNIQUE,
    "nickname" VARCHAR(64) NOT NULL DEFAULT '',
    "avatar_url" VARCHAR(512) NOT NULL DEFAULT '',
    "has_unread_sprout" BOOL NOT NULL DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_users_openid_333a8f" ON "users" ("openid");
CREATE TABLE IF NOT EXISTS "favorites" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL,
    "sentence_id" UUID NOT NULL,
    "is_cancelled" BOOL NOT NULL DEFAULT False,
    CONSTRAINT "uid_favorites_user_id_6b4bae" UNIQUE ("user_id", "sentence_id")
);
CREATE INDEX IF NOT EXISTS "idx_favorites_user_id_8e4c6c" ON "favorites" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_favorites_sentenc_87c061" ON "favorites" ("sentence_id");
CREATE TABLE IF NOT EXISTS "user_event" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL,
    "event_type" VARCHAR(32) NOT NULL,
    "sentence_id" UUID,
    "book_id" UUID,
    "duration_ms" INT,
    "meta" JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_user_event_user_id_53d168" ON "user_event" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_user_event_event_t_b656d2" ON "user_event" ("event_type");
COMMENT ON TABLE "user_event" IS '用户行为事件：停留、展开上下文、翻面等';
CREATE TABLE IF NOT EXISTS "sprout" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL,
    "text" VARCHAR(500) NOT NULL,
    "hook" VARCHAR(100) NOT NULL DEFAULT '',
    "target_sentence_id" UUID,
    "reaction_options" JSONB NOT NULL,
    "reaction" VARCHAR(20),
    "shown" BOOL NOT NULL DEFAULT False,
    "rec" JSONB
);
CREATE INDEX IF NOT EXISTS "idx_sprout_user_id_7b46b4" ON "sprout" ("user_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztWm1vozgQ/isRn3rSXkVISNLV6aSkm9XmtG1W23TvtJsVcsAkqMRkwe6Lev3vZxsIb4"
    "aDvDRpyxcC45nYfsaMnxn8KC0dA9re6bUHXel941FCYAnpTUL+riGB1SqSMgEGM5srEqrB"
    "JWDmYRfomApNYHuQigzo6a61wpaDqBQR22ZCR6eKFppHIoKsXwRq2JlDvOAD+fGTii1kwH"
    "vohY+rG820oG0kxmkZrG8u1/DDisuur0cfPnJN1t1M0x2bLFGkvXrACwet1QmxjFNmw9rm"
    "EEEXYGjEpsFGGUw3FPkjpgLsErgeqhEJDGgCYjMwpD9MgnSGQYP3xC7tP6UK8OgOYtBaCD"
    "MsHp/8WUVz5lKJdXX+qf/1pNX5jc/S8fDc5Y0cEemJGwIMfFOOawSk7kI2bQ3gLKAfaAu2"
    "llAMatIyBa4RmJ6GN5uAHAoilKMVFsIcwrcZphKdgzFG9kPgwQKMJ6OL4dWkf/GFzWTpeb"
    "9sDlF/MmQtCpc+pKQnvksc+n74b836Txp/jyafGuyx8X18OUw7bq03+S6xMQGCHQ05dxow"
    "YostlIbAUM3IsWRlbOjYpGXt2IM6Nhh85FdnBZEo+p0vgCv2Z2SR8iUFbD+xb0vfLcG9Zk"
    "M0xwv62FR6Bc771v/Kgx/VSnnkMmhS/LanBIjI0m/4fQUY4za7AbLMayBtsWMkgey0S+DY"
    "aefCyJqSKIJbuqu4GnHtKjgmrV4ikmpTKQEl1crFkrclwVwATyOIhS3NW7kOEYTtgePYEC"
    "AxrEL7FLoz+gf7grcq+SvPbgbj8edEbB6MJilgry8GQxoEON5UycJcPLqcUJAZhzRvYuSH"
    "CWZAv7kDrqFlWhzFydPNNi2VZVoCEJhziNg82awCSv0R3DquP7AM3V63FVJuM9DaA+3+wf"
    "m85u8SHkQYIh2yx581Id9kydaE/K3ztpqQv1LHZgh5LHKWDX8xk13GwKwXd8zMt4l4EWDx"
    "/aUCaCmzNwic5Wk6oAjYNhQgV8gO06Y1MTwaYshqrcNburhFzDBqLKSGPKDAtd7/cUNpSr"
    "qq0puSjtLqTkmv19anpA1bgF17M3Y1O1Nimk0qUWVVZ/rq2ZS0ZLlJJbqq0qspy0xT5lYy"
    "teqovW6o0zVNKjnrdhR6P2ufSSlnH2gIdcm5Zrg1EaoZbu3YmuHuj6jxndifcQaz/MJo0m"
    "pfhdG9FutbZQqjrfy6aCtTFj14shDg9YyBZDdrkFL6m4qgxUzeIGAGoZOiPWtLLwvaCGEx"
    "ZimrFG6WT8iPDjE6Ivrzu9Jsd9u9Vqfdoyp8KGtJtwBUP32KY7eEGGRB++tqfClGLdRP7/"
    "SWjhv/NmzLKwPbZl+BIo48I5aNLeSdsm73RJMZBIlNPox1Jxf9f9Jh8PzzeJBeqOwPBseT"
    "rF75n5YEmerV+qNTfpoafZiqTw3VKVzN9A/N9OsU7pU6tk7htmWDGN4LXoH85C3Uf77zLL"
    "vM21RZLnOiRZbzT7SwttSJFppOVIEw1H+JR4KapQBsFgDYzAKIgUs5jrZhCiy2foOJHQ3q"
    "nFFpDh+AILvLT1REtseRtLD+jj1pEXmhSkSI22wUFQ6QWSfCglImKij5QUHJxARv4dwJMC"
    "z8+Lu2qb/6ptekXi0Y6Fu//0cVRF9bdaIPXUtfSILqRNDyrqg6ASKdo6lO5NYdhbu5oNwY"
    "rLeDnuffSbExvxhxC12v4sYSM3mZhF1R1TI7i6rmby2sLXWen74aFUAM1F8mgHsh7LRHHJ"
    "zBKbunxEyen1fWG0vhxvL0Hw0O7zc="
)
