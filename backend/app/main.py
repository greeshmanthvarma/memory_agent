from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from pydantic import BaseModel
from openai import OpenAI
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Memory Agent API",
    description="FastAPI application for Memory Agent",
    version="1.0.0"
)

# Configure CORS - allow origins from environment variable or default to "*"
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Memory Agent API"}

