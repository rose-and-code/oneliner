# OneLiner 后端代码审查

## 1. Entity 没有 BaseEntity，代码重复严重

每个 Entity 都在重复同样的样板代码：

```python
# user.py / book.py / sentence.py / bookmark.py 全部在重复：
from uuid import uuid4
from tortoise import fields
from tortoise.models import Model

class XXX(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
```

4 个 Entity，`id` / `created_at` / `updated_at` 重复了 4 遍。应该抽取 `BaseEntity`：

```python
class BaseEntity(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True
```

子类只需声明业务字段 + `table` 名即可。

---

## 2. "Bookmark" 命名不当——前端概念泄露到后端

`Bookmark` 是前端/浏览器语境下的术语（"书签"），用在这里不能一眼看出是"收藏"。后端领域模型应该使用更贴近业务的命名：

- Entity: `Bookmark` → `Favorite` 或 `Collection`
- Route: `/api/bookmarks/` → `/api/favorites/`
- Service: `bookmark.py` → `favorite.py`
- 字段: `is_bookmarked` → `is_favorited`

命名应该反映业务领域而非照搬前端 UI 组件的称呼。

---

## 3. `dev_mode` 和 `/dev-login` 是有害设计

当前实现：

```python
# config.py
dev_mode: bool = True

# routes/auth.py
@router.post("/dev-login", response_model=TokenResponse)
async def dev_login_endpoint():
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail="仅开发环境可用")
    token, user = await dev_login()

# login 里还有 fallback 到 dev_login
except ValueError:
    if not settings.dev_mode:
        raise
    token, user = await dev_login()
```

问题：
- `dev_mode = True` 让本地环境永远走不到真实的微信登录流程，本地开发和线上行为不一致
- `/dev-login` 是一个不应该存在的 API，生产环境忘了关 `dev_mode` 就是一个安全漏洞
- 正确做法：本地开发用微信开发者工具的正常 `wx.login` 流程，后端不需要专门的开发模式降级

应该直接删除 `dev_mode` 配置、`/dev-login` 路由、以及 login 中的 fallback 逻辑。

---

## 4. 滥用 REST 语义——只用 GET / POST

当前有两个 `/me` 路由：

```python
@router.get("/me", ...)     # 获取用户信息
@router.put("/me", ...)     # 更新用户信息
```

项目约定只使用 `GET` 和 `POST`，不使用 `PUT` / `DELETE` 等 REST 语义。应改为：

```python
@router.get("/me", ...)          # 获取
@router.post("/me/update", ...) # 更新
```

所有写操作统一用 `POST` + 动作路径，简洁明确。

---

## 5. 列表接口缺少分页——直接返回全量数据

两个列表接口都返回全量数据，没有分页：

```python
# sentences.py
@router.get("/all", response_model=list[BookWithSentencesResponse])

# bookmarks.py
@router.get("/list", response_model=list[BookmarkListItem])
```

当数据量增长，这两个接口会：
- 一次性查询全表
- 返回巨大的 JSON 响应
- 前端内存爆炸

应统一使用分页，响应格式：

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool
```

---

## 6. `wechat_login` 直接调用微信 API——缺少抽象层

```python
# services/auth.py
async def wechat_login(code: str) -> tuple[str, User]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={...},
        )
```

问题：
- 业务逻辑和第三方 HTTP 调用混在一起
- 以后要调用微信其他接口（获取手机号、发送模板消息等），会到处散落 `httpx.AsyncClient` + 微信 URL 拼接
- 无法 mock 测试

应抽象出 `WechatClient`：

```python
# clients/wechat.py
class WechatClient:
    def __init__(self, appid: str, secret: str):
        ...

    async def code2session(self, code: str) -> str:
        """code 换 openid"""
        ...

    async def get_phone_number(self, code: str) -> str:
        """获取手机号"""
        ...
```

所有微信 API 调用收束到一个入口。

---

## 7. Seed 机制的存在本身就是架构错误

这个项目的核心数据——书和句子——是**静态的、只读的、编辑时确定的**。它们不会被用户创建、不会被运行时修改、不会有并发写入。这种数据根本不需要数据库。

但当前架构是：

```
Python dict (seed_data_part1/2/3.py)
    ↓ seed_runner.py
PostgreSQL (books / sentences 表)
    ↓ ORM 查询
JSON API 响应
```

整个链路是：**把静态数据写进数据库，再从数据库读出来**。Seed 机制的存在不是设计问题，而是它在弥补一个根本不该存在的决策——用数据库存储静态内容。

正确做法：书和句子用 JSON 文件存储在代码仓库中，服务启动时加载到内存，直接返回。省掉数据库、ORM 查询、seed 脚本、migration 这一整条链路。数据库只用来存真正的动态数据（用户、收藏）。

```
data/books.json          ← 静态数据，跟代码一起版本管理
    ↓ 启动时加载到内存
JSON API 响应            ← 零数据库开销
```

附带的好处：
- 删掉 `seed_runner.py`、`seed.py`、`seed_data_part1/2/3.py` 共 5 个文件
- 删掉 `books` 和 `sentences` 两张表及其 Entity 和 Migration
- 不再需要 `sentence_count` 这种冗余字段（内存里直接 `len()` ）
- 新增/修改书和句子只需编辑 JSON 文件，不需要跑 seed 或写 migration
- 本地开发不依赖数据库里是否已经 seed 过

---

## 8. 环境配置文件未实际使用

`config.py` 声明了加载 `.env.dev`：

```python
model_config = {"env_file": ".env.dev", "env_file_encoding": "utf-8"}
```

但项目中没有 `.env.dev`、`.env.stage`、`.env.prod` 任何环境文件（gitignore 也没有排除它们）。也没有文档说明需要创建什么环境文件、包含哪些变量。

同时 `database_url` 硬编码了本地用户名：

```python
database_url: str = "postgres://rosewei@localhost:5432/oneliner"
```

这意味着换一台机器就跑不起来。

---

## 9. 后端完全没有 Lint / Format 配置

`pyproject.toml` 中没有任何代码质量工具的配置：

- 没有 Ruff（lint + format）
- 没有 Black（format）
- 没有 mypy（类型检查）
- 没有 pre-commit hooks
- `devDependencies` 也没有安装任何检查工具

一个 Python 后端项目最基本的应该有：

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM"]

[tool.ruff.format]
quote-style = "double"
```

并且在 CI 和 pre-commit 中执行。

---

## 10. N+1 查询——你在写 PHP 吗？

`get_all_books_with_sentences` 和 `get_user_bookmarks` 都是经典的 N+1 灾难：

```python
# sentence.py — 查 N 本书，每本书再查一次 sentences
for book in books:
    sentences = await Sentence.filter(book_id=book.id).order_by("sort_order")

# bookmark.py — 查 N 个收藏，每个再查 sentence，再查 book
for bm in bookmarks:
    sentence = await Sentence.filter(id=bm.sentence_id).first()
    book = await Book.filter(id=sentence.book_id).first()
```

6 本书 + 100 条句子 = 7 次查询。看起来还行？等到 50 本书、2000 条句子、每个用户 500 个收藏的时候，每个请求打 500+ 次数据库，服务直接趴下。

这是 Tortoise ORM 最基础的用法。`prefetch_related` 和 `select_related` 存在就是为了解决这个问题：

```python
# sentence.py — 1 次查询全部搞定
books = await Book.all().order_by("sort_order").prefetch_related(
    Prefetch("sentences", queryset=Sentence.all().order_by("sort_order"))
)
```

bookmark.py 更简单——用一次 `IN` 查询批量拿 sentence_ids 和 book_ids，而不是循环里一条条查。

这不是优化，这是纠错。

---

## 11. `generate_schemas=True` 在生产环境——你想自动 DDL 吗？

```python
# main.py
async with RegisterTortoise(app, config=TORTOISE_ORM, generate_schemas=True):
    yield
```

每次服务启动自动建表。你已经用了 Aerich 做迁移管理，`generate_schemas=True` 会绕过迁移直接改表结构。两套建表机制并存，迁移历史随时可能和实际表结构不一致。

生产环境只用 `aerich upgrade`，`generate_schemas` 只在单元测试或本地开发的 seed 脚本里用。主应用里应该是 `generate_schemas=False`。

---

## 12. `decode_token` 吃掉了所有异常

```python
# jwt.py
def decode_token(token: str) -> str | None:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return payload.get("sub")
```

如果 token 过期、签名错误、格式损坏，`jwt.decode` 会抛 `ExpiredSignatureError`、`InvalidTokenError` 等异常——但这个函数没有 catch，异常会直接冒泡到 `deps.py` 的 `current_user`，那里也没有 catch，最终变成 500 Internal Server Error。

用户拿着过期 token 请求，看到的不是 401 "请重新登录"，而是 500 "服务器内部错误"。

```python
def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
```

然后 `deps.py` 里的 `if not user_id` 分支自然走到 401。

---

## 13. `update_me` 盲写——不检查、不做 partial update

```python
# routes/auth.py
@router.put("/me", response_model=UserResponse)
async def update_me(req: UpdateProfileRequest, user: User = Depends(current_user)):
    user.nickname = req.nickname
    user.avatar_url = req.avatar_url
    await user.save()
```

两个问题：

1. **全量覆盖**：用户只想改昵称，必须同时传 `avatar_url`，否则字段被覆盖成空值。`UpdateProfileRequest` 的字段应该是 `Optional`，只更新传了的字段。

2. **无校验**：nickname 可以是空字符串、1000 个字符、全是空格——数据库层面 `max_length=64` 会截断或报错，但用户看到的又是 500。Pydantic schema 应该做前置校验。

```python
class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    
    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str | None) -> str | None:
        if v is not None and (len(v.strip()) == 0 or len(v) > 64):
            raise ValueError("昵称长度 1-64 字符")
        return v
```

---

## 14. Schema 里 `str` 满天飞——UUID 不是字符串

整个 `schemas.py` 里，所有 ID 字段都声明为 `str`：

```python
class UserResponse(BaseModel):
    id: str           # 应该是 UUID
    
class SentenceResponse(BaseModel):
    id: str           # 应该是 UUID
    book_id: str      # 应该是 UUID

class BookmarkListItem(BaseModel):
    id: str           # 应该是 UUID
    sentence_id: str  # 应该是 UUID
    created_at: str   # 应该是 datetime
```

`id: str` 意味着类型系统完全放弃了对 ID 格式的校验。任何字符串都能通过——`"hello"`、`""`、`"not-a-uuid"`。用 `UUID` 类型，Pydantic 自动做格式校验和序列化。`created_at: str` 同理，应该是 `datetime`。

service 层里到处 `str(book.id)`、`str(s.id)` 的手动转换也跟着消失。

---

## 15. `sentence_count` 冗余字段——没有维护就是错误数据

```python
# book.py
sentence_count = fields.IntField(default=0)

# seed.py
await Book.create(
    ...
    sentence_count=len(book_data["sentences"]),
)
```

`sentence_count` 在 seed 时写入，之后永远不更新。如果之后有 CRUD 操作增删句子，这个字段就是错的。

冗余字段要么有触发器/钩子保持同步，要么不要存——直接 `COUNT()` 或者在返回时计算。既然你现在只有 seed，没有增删句子的接口，这个字段纯粹是提前优化了一个不存在的问题。

---

## 16. 没有健康检查端点

整个 API 没有 `GET /health` 或 `GET /api/ping`。

部署到任何平台（K8s、ECS、Cloud Run），第一件事就是配置健康检查。没有这个端点，平台不知道服务是否活着，数据库连接断了也不知道。

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

两行代码。

---

## 总结：修复清单

| # | 问题 | 影响 |
|---|------|------|
| 1 | 抽取 `BaseEntity` | 4 个 Entity 重复样板代码 |
| 2 | Bookmark → Favorite 改名 | 前端术语泄露到后端领域模型 |
| 3 | 删除 `dev_mode` 和 `/dev-login` | 安全隐患 + 本地无法验证真实流程 |
| 4 | PUT → POST，只用 GET/POST | 统一约定 |
| 5 | 列表接口加分页 | 数据量增长后服务不可用 |
| 6 | 抽象 `WechatClient` | 可维护性、可测试性 |
| 7 | 静态数据去数据库化，改用 JSON 文件 + 内存加载 | 架构简化，删掉整条 seed 链路 |
| 8 | 补全 .env 模板和文档 | 换一台机器跑不起来 |
| 9 | 添加 Ruff lint/format | 代码质量底线 |
| 10 | N+1 查询 | 性能炸弹，数据量上来直接打爆数据库 |
| 11 | `generate_schemas=True` 移除 | 与 Aerich 迁移机制冲突 |
| 12 | `decode_token` 异常处理 | 过期 token 返回 500 而不是 401 |
| 13 | `update_me` partial update + 校验 | 防止数据被意外覆盖清空 |
| 14 | Schema UUID 类型化 | 类型安全、自动校验，消除手动 `str()` 转换 |
| 15 | `sentence_count` 冗余字段 | seed 后不更新，迟早是错误数据 |
| 16 | 健康检查端点 | 部署基础设施需要 |
