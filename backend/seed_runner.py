import asyncio

from tortoise import Tortoise

from app.config import TORTOISE_ORM
from app.services.seed import seed_all


async def main():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await seed_all()
    await Tortoise.close_connections()


asyncio.run(main())
