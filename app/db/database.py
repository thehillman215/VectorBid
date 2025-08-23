import os
from typing import AsyncGenerator

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URLs
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/vectorbid")
ASYNC_DATABASE_URL = os.environ.get("ASYNC_DATABASE_URL", "postgresql+asyncpg://localhost/vectorbid")

# Async engine for new features
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    autoflush=False, 
    autocommit=False, 
    expire_on_commit=False
)

# Sync engine for compatibility with existing code
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL.replace("+asyncpg", ""), connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

# Base with proper metadata
metadata = MetaData()
Base = declarative_base(metadata=metadata)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session for legacy compatibility"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
