from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# asyncpg does not accept URL query params like sslmode/channel_binding; it uses ssl=True. Strip entire query string and pass ssl in connect_args for Neon.
_original_url = os.getenv("DATABASE_URL") or ""
_connect_args = {}
if "neon.tech" in _original_url or "sslmode=require" in _original_url:
    _connect_args["ssl"] = True
    _url = urlparse(_original_url)
    # Remove query string so SQLAlchemy/asyncpg don't get sslmode, channel_binding, etc.
    DATABASE_URL = urlunparse(_url._replace(query=""))

engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    future=True,
    connect_args=_connect_args,
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

