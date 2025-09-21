from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_reset_on_return='commit',
    connect_args={
        "command_timeout": 60,
    }
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()