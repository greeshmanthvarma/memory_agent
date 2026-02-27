from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from pydantic import BaseModel
from openai import OpenAI
import os
import asyncio
from app.database import AsyncSessionLocal
from app.routers.memoryRoutes import memory_router
from app.routers.authRoutes import auth_router
from app.routers.chatRoutes import chat_router
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Memory Agent API",
    description="FastAPI application for Memory Agent",
    version="1.0.0"
)


cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return 500 with error detail in JSON so the client always sees the real error."""
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )

app.include_router(memory_router)
app.include_router(auth_router)
app.include_router(chat_router)

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database will be initialized on startup
from app.database import engine, Base
from app.services.llm_service import run_mutation_worker
from app.services.qdrant_service import ensure_all_collection_indexes
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


@app.on_event("startup")
async def startup_event():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Checkpointer: run setup once so LangGraph checkpoint tables exist.
    # It expects a plain postgresql:// URI, not postgresql+asyncpg:// (SQLAlchemy driver).
    conn_string = os.getenv("DATABASE_URL")
    if conn_string:
        checkpointer_conn = conn_string.replace("postgresql+asyncpg://", "postgresql://", 1)
        try:
            async with AsyncPostgresSaver.from_conn_string(checkpointer_conn) as checkpointer:
                await checkpointer.setup()
            logger.info("LangGraph checkpointer setup completed")
        except Exception as e:
            logger.warning("Checkpointer setup failed (chat checkpointing may fail): %s", e)

    # Qdrant: ensure user_id and is_superseded indexes on all existing collections
    try:
        ensure_all_collection_indexes()
        logger.info("Qdrant indexes ensured")
    except Exception as e:
        logger.warning("Qdrant ensure indexes failed: %s", e)

    app.state.mutation_worker_task = asyncio.create_task(run_mutation_worker())


@app.on_event("shutdown")
async def shutdown_event():
    task = getattr(app.state, "mutation_worker_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error stopping mutation worker: %s", e)
    await engine.dispose()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Memory Agent API"}


@app.get("/health")
async def health():
    """Health check for load balancers and monitoring"""
    return {"status": "ok"}

# async def db_ping():
#     while True:
#         await asyncio.sleep(300)
#         try:
#             async with AsyncSessionLocal() as db:
#                 await db.execute(text("SELECT 1"))
#         except Exception as e:
#             logger.warning(f"Database connection failed: {str(e)}")
#             continue
