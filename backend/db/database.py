from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from utils.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set — cannot start without a database connection")

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_connect_args = {} if _is_sqlite else {"statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
