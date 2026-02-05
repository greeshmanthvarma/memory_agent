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

qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"),api_key=os.getenv("QDRANT_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database will be initialized on startup
from app.database import engine, Base


@app.on_event("startup")
async def startup_event():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    
    # app.state.db_ping_task = asyncio.create_task(db_ping())


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    

#    db_ping_task = getattr(app.state, "db_ping_task", None)
#    if db_ping_task:
#        db_ping_task.cancel()
#        try:
#            await db_ping_task
#        except asyncio.CancelledError:
#            pass
#        except Exception as e:
#            logger.warning(f"Error canceling db ping task: {str(e)}")

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
