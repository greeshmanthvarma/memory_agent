from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from pydantic import BaseModel
from openai import OpenAI
import os
from app.routers.memoryRoutes import memory_router
from app.routers.authRoutes import auth_router
from app.routers.chatRoutes import chat_router

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


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Memory Agent API"}


@app.get("/health")
async def health():
    """Health check for load balancers and monitoring"""
    return {"status": "ok"}

