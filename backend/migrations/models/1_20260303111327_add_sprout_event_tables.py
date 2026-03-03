from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
    "text" VARCHAR(200) NOT NULL,
    "hook" VARCHAR(100) NOT NULL DEFAULT '',
    "target_sentence_id" UUID,
    "reaction_options" JSONB NOT NULL,
    "reaction" VARCHAR(20),
    "shown" BOOL NOT NULL DEFAULT False
);
CREATE INDEX IF NOT EXISTS "idx_sprout_user_id_7b46b4" ON "sprout" ("user_id");
        ALTER TABLE "users" ADD "has_unread_sprout" BOOL NOT NULL DEFAULT False;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP COLUMN "has_unread_sprout";
        DROP TABLE IF EXISTS "user_event";
        DROP TABLE IF EXISTS "sprout";"""


MODELS_STATE = (
    "eJztmm1v4kYQx78K8qtUSiMwGEhVVYIcp6O6hOoCbXUhshZ7DVbMmrN386Ao372zaxs/U5"
    "vAQRK/ITA7E+/+xh7/Z+1naWnr2HLPJi52pN9qzxJBSwxfYvbTmoRWq9DKDRTNLOHIwENY"
    "0MylDtIoGA1kuRhMOnY1x1xR0yZgJcyyuNHWwNEk89DEiPmDYZXac0wXYiI3t2A2iY4fsR"
    "v8XN2phoktPTZPU+fHFnaVPq2EbTIZfvosPPnhZqpmW2xJQu/VE13YZO3OmKmf8Rg+NscE"
    "O4hiPbIMPkt/uYHJmzEYqMPweqp6aNCxgZjFYUi/G4xonEFNHIl/tP6QSuDRbMLRmoRyFs"
    "8v3qrCNQurxA918aX37aTZ/kWs0nbp3BGDgoj0IgIRRV6o4BqC1BzMl60imgb6CUaoucTZ"
    "UOORCbi6H3oWfNkGcmAIKYdnWIA5wLcdUwnWoI+I9eRncAPj8fBycD3uXf7FV7J03R+WQN"
    "QbD/iILKxPCeuJlxIbrg/vqln/k9o/w/GXGv9Z+z66GiQTt/Ybf5f4nBCjtkrsBxXpkZMt"
    "sAZgwDNMLFvpWyY2Hlkl9qCJ9Scf5tVeYZJV/S4WyMnOZxiRyCUA20/te2XuluhRtTCZ0w"
    "X8bMjdDcn7u/dNFD/wSmTkyh+SvbGXGERianfiewmM0ZjdgCxyGUivuGPEQbZbBTi2W7kY"
    "+VCcIrqHu4qjMscqwzEe9RZJKg25AErwymUpxuIwF8hVGeFlS3VXjs0yynbfti2MSDbWzP"
    "gE3Rn8g33hLSv+iqub/mj0NVab+8NxAuzksj+AIiB4g5NJhXl4NQbIXEMadxHxww0zpN09"
    "IEdXUyO2bOf5poeW8jJpQQTNBSK+Tr4qX1J/Rve2400sJbfXYxslt+F77UF23wg9r3p3CR"
    "cTiomG+c/bSpBvc8pWgvyj67ZKkL/TxKYEeaRyFi1/kZBd1sB0FneszF9T8UJg0ftLCWiJ"
    "sA8IznRVDQEBy8IZ5Daqw2RoJQyPRhjyvdbBPZzcWcowHNwoDUVBwWu//9OG0pR1FLk7ZW"
    "252ZmybrelTVkLNxH/7M74p9GeMsNogEWpKxr3V86nrFmvN8CiKQp8GvU696yLqDpEtZVu"
    "J/DpGAZYzjttGb7PWudSItkHmkK15Vwp3EoIVQq3SmylcPcn1MSd2Ftxiln+xmg8al8bo3"
    "vdrG8W2Rht5u+LNlPbogdvFnxeP7GQ7OYcBEl/VxJaJOQDAtMZLAqOrC7dNLQhodnMElEJ"
    "bqYnyI+OGMwI/vwqN1qdVrfZbnXBRUxlbelsgOq1T1F2S0xRGtqf16OrbGqBfwLXhMA6bn"
    "RTo6c1y3Tp7d6eBYVKecZMi5rEPeOH3ZNY5iBit/qg4p1c9v5NFsOLr6N+8nTl/6B/PC3r"
    "tfeAKaNfvV4/espvVsPHU9W7Q1UjV+n9Q+v9qpF7p4mtGrnXakKKHzMugfwWLvD/eW+17L"
    "J7k+v1Au0beOX2b2Is8V4LNBVlEAb+b/HFoEYhgI0NABtpgBQ5oHHULRvh7OgP2N5BUReK"
    "SrXFBDJ6vPx2JSv2mFoXfsBjb12yclGmLkRjtqoNB+iyE9W1UHHdUFtTe2ML+yGD4cYHwe"
    "uY6gnw0bTTPeyY2kLKaKf9kdNN7TQKfY6mnc7dLsu8/WTskvkX60FfQ9/JHll+93yPHbdk"
    "DYyEvFGFqShFiqCi5FdBPpZ4DR0ujRIQffe3CXAvChOOSP1XR4oqokjIoYTQ3kTl+9itff"
    "kPEY+K0Q=="
)
