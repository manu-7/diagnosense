import asyncio

from app.database import Base, engine
from app.models import *  # noqa: F401,F403  - registers all models on Base.metadata


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables ensured (existing tables untouched, missing ones created).")


if __name__ == "__main__":
    asyncio.run(main())