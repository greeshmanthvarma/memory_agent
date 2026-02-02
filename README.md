# Coherence

Coherence is a personal memory agent that persists context across conversations. Log memories manually, extract them from chat, and surface them when relevant—powered by semantic search and RAG (Retrieval-Augmented Generation).

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4.1-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector%20DB-7C3AED)](https://qdrant.tech/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o%20mini-412991?logo=openai)](https://openai.com/)

**[Live demo](https://coherence-agent.vercel.app)** 

## Features

- **Persistent memory** – Explicit (user-created) and implicit (extracted from chat) memories stored long-term
- **Semantic retrieval** – Meaning-based search using embeddings (not keyword match)
- **Tool-based RAG** – The model calls `search_memories` only when relevant
- **Conversation summarization** – Extract durable facts, preferences, and events with deduplication
- **Memory Space** – Browse, inspect, and trace memories back to conversations

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL (SQLAlchemy async)
- Qdrant (vector database for embeddings)
- OpenAI (GPT-4o mini for chat, text-embedding-3-small for embeddings)
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

## Deployment

- Frontend deployed on Vercel (SPA + serverless API proxy)
- Backend deployed on AWS Elastic Beanstalk
- PostgreSQL hosted on Neon (TLS, asyncpg)
- Qdrant Cloud for vector search

The frontend never talks directly to databases or OpenAI; all access is mediated by the backend.

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

## What's next

- **Streaming chat** – Stream LLM tokens as they’re generated so responses appear incrementally and avoid long proxy timeouts.
- **Edit / delete memories** – Let users update or remove memories from Memory Space.
- **Export memories** – Export memories (e.g. JSON or markdown) for backup or portability.
- **Stronger dedup** – Tune similarity thresholds and add merge/merge-prompt for near-duplicate facts and preferences.

### Phase 2 (integrations)

- **Google Calendar** – Sync events (meetings, reminders, occasions) into memories so the agent can reference past and upcoming events in conversation (OAuth2 + Calendar API).
- **Google Photos** – Ingest photo metadata (dates, albums, locations) or use vision to describe photos and create memories (e.g. “Trip to X”, “Family gathering”) via Photos Library API and optional vision model.

Phase 2 adds *more tools*: the model can call Calendar and Photos when the user asks. The flow stays reactive (user asks → model uses tools → reply).

### Phase 3 (agentic)

- Phase 3 introduces an agent loop with planning, tool chaining, and recovery rather than single-turn tool calls.

