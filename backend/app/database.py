from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

