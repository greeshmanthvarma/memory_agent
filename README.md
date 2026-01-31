# Coherence

Coherence is a personal memory agent that persists context across conversations. Log memories manually, extract them from chat, and surface them when relevant—powered by semantic search and RAG (Retrieval-Augmented Generation).

## Features

- **Persistent memory**: Store explicit memories (manually logged) and implicit memories (extracted from conversations)
- **Semantic search**: Memories are embedded and retrieved by meaning, not exact keyword match
- **Context-aware chat**: The AI uses your memories to personalize responses via function calling
- **Conversation summarization**: Extract durable facts, preferences, and events from chat into long-term memory
- **Duplicate detection**: Deduplication by exact match and semantic similarity (facts and preferences; events are always stored)
- **Memory Space**: Browse memories in bubble or list view, view details and linked conversations

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL (SQLAlchemy async)
- Qdrant (vector database for embeddings)
- OpenAI (GPT-4 for chat, text-embedding-3-small for embeddings)
- JWT authentication (httpOnly cookies)
- Argon2 password hashing

**Frontend**
- React 19
- Vite
- React Router
- Tailwind CSS
- Radix UI
- Motion (animations)
- Sonner (toasts)

## Architecture

```
User -> Frontend (React) -> Backend (FastAPI) -> PostgreSQL (users, memories, conversations, messages)
                                        |
                                        +-> Qdrant (vector embeddings, semantic search)
                                        |
                                        +-> OpenAI (chat, embeddings, summarization)
```

- Each user has a dedicated Qdrant collection (`user_{id}_memories`) for their memory embeddings
- Memories are stored in PostgreSQL (metadata, content, tags) and Qdrant (embeddings, user_id)
- Chat uses a `search_memories` tool that queries Qdrant by semantic similarity and injects relevant memories into the prompt

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Qdrant (local or cloud)
- OpenAI API key

## Environment Variables

**Backend** (create `backend/.env`):

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:5173
```

**Frontend**: No environment variables required for local development. The Vite dev server proxies `/api` to the backend.

## Installation

### Backend

```bash
cd backend
uv sync
# or: pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Application

1. Start PostgreSQL and Qdrant (e.g. via Docker):

```bash
# PostgreSQL (example)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# Qdrant
docker run -d -p 6333:6333 qdrant/qdrant
```

2. Start the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

3. Start the frontend:

```bash
cd frontend
npm run dev
```

4. Open http://localhost:5173

## API Overview

**Auth** (`/api/auth`)
- `POST /register` - Create account
- `POST /login` - Sign in
- `GET /me` - Current user (requires auth)
- `POST /logout` - Sign out
- `POST /update-profile` - Update username or profile picture

**Chat** (`/api/chat`)
- `POST /` - Send message, get AI response (uses memories via tool)
- `POST /conversation` - Create conversation
- `POST /conversation/summarize` - Summarize messages and optionally create implicit memory
- `GET /conversation/all` - List user's conversations
- `GET /conversation/{id}` - Get conversation
- `GET /conversation/{id}/messages` - Get messages
- `PUT /conversation/{id}` - Update title
- `DELETE /conversation/{id}` - Delete conversation

**Memory** (`/api/memory`)
- `POST /create` - Create explicit or implicit memory
- `GET /` - List user's memories
- `GET /related` - Semantic search (query param `q`)
- `GET /{id}` - Get memory by ID

## Project Structure

```
memory agent/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, startup
│   │   ├── database.py       # Async SQLAlchemy engine, session
│   │   ├── db_models.py      # SQLAlchemy models
│   │   ├── models.py         # Pydantic schemas
│   │   ├── middleware/
│   │   │   └── auth.py       # JWT cookie auth
│   │   ├── routers/
│   │   │   ├── authRoutes.py
│   │   │   ├── chatRoutes.py
│   │   │   └── memoryRoutes.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── db_service.py
│   │       ├── embedding_service.py
│   │       ├── llm_service.py
│   │       ├── memory_service.py
│   │       ├── qdrant_service.py
│   │       └── tools.py      # search_memories tool for chat
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── AuthContext.jsx
│   │   ├── ThemeContext.jsx
│   │   ├── components/
│   │   │   ├── app-sidebar.jsx
│   │   │   ├── memory/
│   │   │   │   ├── MemoryBubble.jsx
│   │   │   │   ├── MemoryDialog.jsx
│   │   │   │   ├── MemoryList.jsx
│   │   │   │   └── MemoryBubblesGrid.jsx
│   │   │   └── ...
│   │   └── pages/
│   │       ├── LandingPage.jsx
│   │       ├── ChatPage.jsx
│   │       ├── MemorySpacePage.jsx
│   │       ├── LoginPage.jsx
│   │       └── RegisterPage.jsx
│   └── vite.config.js
└── README.md
```

## Build for Production

**Frontend**

```bash
cd frontend
npm run build
```

Serves static files from `frontend/dist`. Point your web server to this directory and ensure `/api` is proxied to the backend.

**Backend**

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Set `CORS_ORIGINS` to your frontend URL. For production, use `secure=True` for cookies when serving over HTTPS.
