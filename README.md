# Coherence

Coherence is a personal memory agent that persists context across conversations. Log memories manually, extract them from chat, and surface them when relevant—powered by semantic search and RAG (Retrieval-Augmented Generation).

**[Live demo](https://coherence-agent.vercel.app)** 

## Features

- **Persistent memory** – Log memories manually (explicit) or have the app extract them from conversations (implicit). Both are stored long-term so the AI can refer to them later.
- **Semantic search** – Memories are embedded and retrieved by *meaning*, not exact words (e.g. “I like hiking” can surface when you ask about outdoor activities).
- **Context-aware chat** – The model can call a `search_memories` tool during a conversation; relevant memories are injected into the prompt so replies stay personalized.
- **Conversation summarization** – Summarize a chat to extract durable facts, preferences, and events into long-term memory, with deduplication.
- **Duplicate detection** – Facts and preferences are deduplicated by exact match and semantic similarity; events are stored as separate memories.
- **Memory Space** – Browse all memories in bubble or list view, open details, and see which conversations a memory came from.

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

The app is a full-stack SPA: the frontend talks only to the backend over REST; the backend owns all access to PostgreSQL, Qdrant, and OpenAI.

```
User -> Frontend (React) -> Backend (FastAPI) -> PostgreSQL (users, memories, conversations, messages)
                                        |
                                        +-> Qdrant (vector embeddings, semantic search)
                                        |
                                        +-> OpenAI (chat, embeddings, summarization)
```

**Request flow** – The browser sends requests to `/api/*` (auth, chat, memory). The backend validates the JWT cookie, then calls the right service (DB, Qdrant, or OpenAI). Chat and summarization use the LLM; memory search uses embeddings and Qdrant.

**Why two stores** – PostgreSQL holds structured, queryable data (users, memory metadata, content, tags, conversations, messages). Qdrant holds only vector embeddings and a `user_id` for filtering. Semantic search runs in Qdrant; the backend then joins back to PostgreSQL for full memory records.

**How chat uses memories** – The chat endpoint gives the model a `search_memories` tool. When the model decides it needs past context, it calls the tool with a query string. The backend embeds the query, runs a similarity search in Qdrant (scoped to the user’s collection), and returns the top matches. Those memories are added to the prompt as context, and the model generates a reply. So personalization is driven by tool use, not a fixed retrieval step.

**User isolation** – Each user has their own Qdrant collection (`user_{user_id}_memories`). All memory search is filtered by `user_id` so one user never sees another’s data.

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
# Qdrant Cloud: set QDRANT_API_KEY (from cluster API Keys in dashboard)
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:5173
# Production (HTTPS): COOKIE_SECURE=true
# Optional: DB_ECHO=true to log SQL (default: false)
```

- **Neon (or any URL with query params)**: The app strips the query string from `DATABASE_URL` and sets `ssl=True` in `connect_args` so asyncpg does not receive unsupported params (e.g. `channel_binding`).
- **Qdrant**: A payload index on `user_id` is created when needed (on collection create and before filtered search) so filters work on Qdrant Cloud.

**Frontend** – None for local development. The Vite dev server proxies `/api` to the backend. The live demo is hosted on Vercel and proxies API requests to the backend (no backend URL in the repo).

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

To try the app without running it locally, use the [live demo](https://coherence-agent.vercel.app) above.

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
│   │   ├── main.py           # FastAPI app, CORS, global 500 handler, startup
│   │   ├── database.py       # Async SQLAlchemy engine, session; strips URL query for Neon/asyncpg
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
│   ├── Procfile             # web: uvicorn app.main:app --host 0.0.0.0 --port 8000
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── api/
│   │   ├── chat.js          # Serverless proxy for POST /api/chat (60s timeout)
│   │   └── memory.js        # Serverless proxy for GET /api/memory (60s timeout)
│   ├── middleware.js        # Edge Middleware: pass-through for chat/memory list; proxy rest of /api/* to BACKEND_URL
│   ├── vercel.json          # functions (maxDuration 60), rewrites (SPA fallback to index.html)
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
