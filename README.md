# Coherence

Coherence is a personal memory agent that uses a LangGraph-powered chat pipeline plus async reflection to build and maintain long-term user memory. It logs memories manually and from conversation, retrieves them with hybrid dense+sparse search (RRF + reranking), and applies structured mutations via a background queue so personalization stays consistent across sessions.

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
- **Graph-based RAG** – A LangGraph chat pipeline (analysis → retrieval → response) decides when to query the user's memory store and injects retrieved memories into the prompt, using dense + sparse embeddings, **Reciprocal Rank Fusion (RRF)**, and cross-encoder reranking for high-precision matches
- **Conversation summarization** – Extract durable facts, preferences, and events with deduplication
- **Memory Space** – Browse, inspect, and trace memories back to conversations

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL (SQLAlchemy async)
- Qdrant (vector database for embeddings)
- OpenAI (GPT-4o mini for chat, text-embedding-3-small for **dense** embeddings)
- LangGraph (chat + retrieval + reflection graph)
- FastEmbed SPLADE (`prithivida/Splade_PP_en_v1`) for **sparse** text embeddings
- Jina cross-encoder reranker (`jinaai/jina-reranker-v1-turbo-en`)
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

The app is a full-stack SPA with a three‑layer architecture. The React frontend talks only to the FastAPI backend over REST; the backend owns all access to PostgreSQL, Qdrant, OpenAI, and the async reflection/mutation pipeline.

```
User -> Frontend (React SPA)
      -> Backend (FastAPI: routers + services + LangGraph chat/reflect pipeline)
          -> PostgreSQL (users, conversations, memories, memory_mutation_queue)
          -> Qdrant (vector embeddings, semantic search, payload filters)
          -> OpenAI (chat, analysis, reflection, embeddings)
```

**Request flow** – The browser sends requests to `/api/*` (auth, chat, memory). The backend validates the JWT cookie, then runs the LangGraph chat pipeline (query analysis → optional retrieval → response) and, in parallel, kicks off an async reflection step that can enqueue memory mutations. Chat and summarization use the LLM; memory search uses embeddings + Qdrant; mutations are applied later by the background worker.

**Why two stores** – PostgreSQL holds structured, queryable data (users, memory metadata, content, tags, conversations, messages). Qdrant holds only vector embeddings and a `user_id` for filtering. Semantic search runs in Qdrant; the backend then joins back to PostgreSQL for full memory records.

**How chat uses memories** – When you send a message, the chat endpoint runs a LangGraph. A **query analysis** node decides whether personal memories would help and, if so, produces a `retrieval_query`. A **retrieve_memories** node embeds this query (and, when helpful, also the raw user message), performs a hybrid dense+sparse search in Qdrant (scoped to your `user_id`) using **Reciprocal Rank Fusion (RRF)** over the two modalities, then reranks the candidates with a Jina cross-encoder before returning the top matches. Those memories are formatted into a memory context block and injected into the system prompt before the assistant responds, so personalization is driven by the graph-controlled retrieval flow rather than OpenAI tool calls.

**User isolation** – Each user has their own Qdrant collection (`user_{user_id}_memories`). All memory search is filtered by `user_id` so one user never sees another’s data.

### Mermaid LangGraph + async reflection diagram

```mermaid
graph LR
  subgraph ChatGraph
    START((START)) --> QA[query_analysis]
    QA --> RM[retrieve_memories]
    QA --> RESP[respond]
    RM --> RE[retrieval_evaluation]
    RE --> QA
    RE --> RESP
    RESP --> END((END))
  end

  subgraph ReflectionAndMutation["Async reflection + mutation queue"]
    RESP --> REFLECT[reflection_model with structured output]
    REFLECT --> ENQ[enqueue_memory_action]
    ENQ --> QUEUE[(memory_mutation_queue)]
    QUEUE --> WORKER[run_mutation_worker]
    WORKER --> APPLY[apply_memory_action]
    APPLY --> DB[(PostgreSQL memories)]
    APPLY --> VEC[(Qdrant vectors)]
  end
```

### Three-layer architecture

- **Presentation layer (frontend)** – React SPA (Vite + Tailwind + Radix) handles routing, UI, and state; it only talks to the backend via `/api/*` and never directly touches the databases or OpenAI.
- **Application layer (backend services)** – FastAPI routers and service modules (`llm_service`, `memory_service`, `db_service`, `qdrant_service`) implement all business logic: auth, chat graph, reflection, memory CRUD, and semantic retrieval.
- **Data & infrastructure layer** – PostgreSQL stores relational data and the `memory_mutation_queue`, Qdrant stores dense+sparse embeddings with payload filters, and OpenAI provides chat, analysis, and reflection models used by the graph.

## Key design decisions

### Async reflection

Reflection (turning conversations into long‑term memories) runs asynchronously using LangGraph nodes and a dedicated reflection model. The chat response is returned immediately, while a separate reflection pass decides whether to **create/update/merge/skip** a memory based on the conversation turn (and, optionally, retrieved context). This keeps the main chat path fast and resilient to occasional reflection failures while still building rich long‑term state in the background.

### Mutation queue

Instead of mutating memories inline during the request, the reflection node enqueues a structured mutation job into a `memory_mutation_queue` table. A long‑running background worker polls this queue, claims jobs with row‑level locks, and applies mutations to PostgreSQL and Qdrant in a single transactional flow. This design avoids race conditions between concurrent chats, keeps writes idempotent/retriable, and ensures memory history (including superseded chains) remains consistent.

### Structured outputs over generic tool calling

For reflection, the model uses `with_structured_output(ReflectionOutput, method="function_calling")` rather than emitting free‑form tool calls. The schema forces the model to pick a single action (`none | create | update | merge`), provide normalized fields like `memory_category`, `tags`, and `target_memory_ids`, and return a single `memory_content` string. This reduces prompt fragility, makes validation and logging trivial on the backend, and allows the mutation worker to operate over strongly‑typed payloads instead of brittle, model‑generated tool call JSON.

### Hybrid dense+sparse retrieval, Reciprocal Rank Fusion (RRF), and reranking

Memories are indexed in Qdrant with both **dense embeddings** (OpenAI `text-embedding-3-small`) and **sparse SPLADE embeddings** (`prithivida/Splade_PP_en_v1`). At retrieval time, the backend issues two prefetches (dense + sparse) and combines them with **Reciprocal Rank Fusion (RRF)** to get a strong candidate set across both modalities. Those candidates are then passed through a **Jina cross-encoder reranker** (`jinaai/jina-reranker-v1-turbo-en`), and only the highest-scoring matches above a relevance threshold are returned to the graph. This stack improves recall and precision compared to using only dense embeddings or naive vector similarity.

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
- `POST /` - Send message, get AI response (runs LangGraph with query analysis, retrieval, and reflection over your memories)
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
│   │   ├── main.py           # FastAPI app, CORS, global 500 handler, startup (incl. mutation worker)
│   │   ├── database.py       # Async SQLAlchemy engine, session; strips URL query for Neon/asyncpg
│   │   ├── db_models.py      # SQLAlchemy models (incl. memory_mutation_queue)
│   │   ├── models.py         # Pydantic schemas
│   │   ├── state_models.py   # LangGraph state + structured outputs for analysis and reflection
│   │   ├── middleware/
│   │   │   └── auth.py       # JWT cookie auth
│   │   ├── routers/
│   │   │   ├── authRoutes.py
│   │   │   ├── chatRoutes.py
│   │   │   └── memoryRoutes.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── db_service.py           # DB helpers + memory_mutation_queue helpers
│   │       ├── embedding_service.py
│   │       ├── llm_service.py          # LangGraph chat + retrieval + reflection + mutation worker
│   │       ├── memory_service.py       # Memory CRUD + dedup + Qdrant integration
│   │       ├── qdrant_service.py       # Qdrant client, search, and payload indexing
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

- ~~**Streaming chat**~~ ✓ – Stream LLM tokens as they’re generated so responses appear incrementally and avoid long proxy timeouts.
- **Edit / delete memories** – Let users update or remove memories from Memory Space.
- **Export memories** – Export memories (e.g. JSON or markdown) for backup or portability.
- **Stronger dedup** – Tune similarity thresholds and add merge/merge-prompt for near-duplicate facts and preferences.

### Phase 2 (integrations)

- **Google Calendar** – Sync events (meetings, reminders, occasions) into memories so the agent can reference past and upcoming events in conversation (OAuth2 + Calendar API).
- **Google Photos** – Ingest photo metadata (dates, albums, locations) or use vision to describe photos and create memories (e.g. “Trip to X”, “Family gathering”) via Photos Library API and optional vision model.

Phase 2 adds *more tools*: the model can call Calendar and Photos when the user asks. The flow stays reactive (user asks → model uses tools → reply).

### Phase 3 (agentic)

- Phase 3 introduces an agent loop with planning, tool chaining, and recovery rather than single-turn tool calls.

