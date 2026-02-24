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


MODELS_STATE = (
    "eJztmPFP4jAUx/8Vsp+8xDMwkTOXyyWgGLkIXBTuLhqzlLVAQ9fOrVOJ4X+/ttvYVrYFFE"
    "/N8QvZvu892vd5W/u6J8NhEBH/YOgjz/haeTIocJC4yOj7FQO4bqJKgYMRUY6B8FAKGPnc"
    "AzYX4hgQHwkJIt/2sMsxo0KlASFSZLZwxHSSSAHFdwGyOJsgPlUTubkVMqYQPSI/vnVn1h"
    "gjAjPzxFCOrXSLz12lDYed0zPlKYcbWTYjgUMTb3fOp4wu3YMAwwMZI20TRJEHOIKpNOQs"
    "o3RjKZyxELgXoOVUYSJANAYBkTCMb+OA2pJBRY0kf+rfjQ3w2IxKtJhyyeJpEWaV5KxUQw"
    "51ct683DtsfFJZMp9PPGVURIyFCgQchKGKawLS9pBM2wJ8FeipsHDsoHyo2UgNLoxCD+KL"
    "50COhYRy8oTFmGN8z2NqiBxgn5J5VMESxoNOt301aHZ/ykwc378jClFz0JYWU6lzTd0LS8"
    "LE+xG+Ncs/qfzuDM4r8rZy3e+19cIt/QbXhpwTCDizKHuwAEw9bLEagxGeSWEDFz6zsNnI"
    "XWHftLDR5JO6MhfRvNXvZAq8/HomEVotBbDXWfteWDsHPFoE0QmfituaeVxSvF/NS7X4CS"
    "+tIr3IZIa2RQYixfZMXW+AMR2zHZDrvAbGC3aMLMhGfQ2OjXohRmnKUgT3YlfxrMAjm3DM"
    "Rn1Ekkc1cw2UwquQpbItFrK9Gc9S+7IURsCePQAPWisWZrIi31WTYzq6AiiYKDgySZlB1O"
    "2dgXvmYY7yOsGlrbQbHEder9AR3qhW0woXMB9RjqiN5O3trlfc9Yq7lmLXK+4KW9QrplbO"
    "dZe/VMg218DVKm65aXzJipcAS+8vG0DTwv5DcNi3bCAIEIJyyLUYIwjQgg1XC9XojUTsa6"
    "0bm7Yn66Nr9fsXmTWi1RlozeCw22qLg4uiK5zC/svo9AbvpzFsIg/b07y2MLKUNoUg8Xk3"
    "3wg7lG/Q9olC649e9Pa96fl4Ikf5bNbqX+rHh436sXBRM1kqX0qezPABK2vz7pHnyymtwC"
    "s+06VC/t2BbptfGcyjozWOdMKr8EinbNr5WLwaG0CM3D8mwFq1us5nmmq1+DONtGUBihHF"
    "vprTlP646vcKThpJiAZySEWCNxDbfL9CsM9v3yfWEooy68ymEsPb6zb/6FxPLvotfeOWf9"
    "B66+1l8Rd54Xry"
)

