import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from settings import config

from .models import Base


engine = create_async_engine(config.db.url, pool_pre_ping=True)

Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

rd = redis.Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS processing;"))
        await conn.run_sync(Base.metadata.create_all)
