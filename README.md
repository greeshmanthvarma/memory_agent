# Coherence

Coherence is a personal memory agent that uses a LangGraph-powered chat pipeline plus async reflection to build and maintain long-term user memory. It logs memories manually and from conversation, retrieves them with hybrid dense+sparse search (RRF + reranking), and applies structured mutations via a background queue so personalization stays consistent across sessions.

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4.1-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-vector%20DB-7C3AED)](https://qdrant.tech/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o%20mini-412991?logo=openai)](https://openai.com/)

**[Project site (UI showcase)](https://coherence-agent.vercel.app)** — _Interactive demo currently offline; run locally for full functionality._

## Features

- **Persistent memory** – Explicit (user-created) and implicit (extracted from chat) memories stored long-term in PostgreSQL and Qdrant
- **Hybrid retrieval** – Dense (OpenAI `text-embedding-3-small`) + sparse (`qdrant/bm25`) embeddings fused with **Reciprocal Rank Fusion (RRF)**, then reranked with a **Jina cross-encoder** for high-precision matches
- **Graph-based RAG** – A LangGraph chat pipeline (query analysis → retrieval → evaluation/retry → response) decides when to query the memory store and injects retrieved memories into the system prompt
- **Retrieval retry** – If the reranker's top score falls below a relevance threshold (or retrieval returns nothing), the graph retries with a rephrased query (up to 2 attempts)
- **Async reflection + mutation queue** – After each chat turn, a reflection model runs in the background and enqueues a structured `create / update / merge / none` mutation; a long-running worker applies it without blocking the response
- **Memory versioning** – Updated or merged memories carry a `superseded_by_id` pointer so the full history is preserved; superseded memories are excluded from future searches
- **Memory change dialog** – Users can review the before/after of any mutation directly in the chat UI
- **Conversation summarization** – Extract durable facts, preferences, and events from a conversation with deduplication
- **Memory Space** – Browse, inspect, edit, delete, and trace memories back to their source conversations

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL (SQLAlchemy async)
- Qdrant (vector database — dense + sparse vectors, payload filters, `cloud_inference=True`)
- OpenAI (GPT-4o mini for chat/analysis/reflection, `text-embedding-3-small` for **dense** embeddings)
- LangGraph (chat + retrieval + retry + reflection graph)
- **Sparse embeddings** – `qdrant/bm25` via Qdrant Cloud inference (free tier); local FastEmbed SPLADE (`prithivida/Splade_PP_en_v1`) available for local dev, disabled in prod via `DISABLE_LOCAL_SPLADE=true`
- **Cross-encoder reranker** – Jina AI `jina-reranker-v1-base-en` (REST API)
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

**Request flow** – The browser sends requests to `/api/*` (auth, chat, memory). The backend validates the JWT cookie, then runs the LangGraph chat pipeline (query analysis → retrieval → evaluation/retry → response). After the response is returned, an async reflection step runs in the background and can enqueue a memory mutation. The mutation worker applies it later.

**Why two stores** – PostgreSQL holds structured, queryable data (users, memory metadata, content, tags, `superseded_by_id`, conversations, messages, `memory_mutation_queue`). Qdrant holds dense + sparse vector embeddings plus a payload (`user_id`, `is_superseded`) for filtering. Semantic search runs in Qdrant; the backend joins back to PostgreSQL for full memory records.

**How chat uses memories** – When you send a message, the chat endpoint runs a LangGraph graph. A **query_analysis** node decides whether personal memories would help and produces a `retrieval_query`. A **retrieve_memories** node embeds that query, issues two Qdrant prefetch queries (dense + sparse), fuses the ranked candidates with **RRF**, then reranks them with the **Jina cross-encoder**. A **retrieval_evaluation** node checks the top reranker score against a relevance threshold (`MIN_RERANK_SCORE = 0.03`); if the score is too low or retrieval returned nothing, the graph loops back to **query_analysis** with retry feedback for a rephrased query (up to 2 retries via `decide_retry`). The final memories are injected into the system prompt before the assistant responds.

After the response is returned, an async **reflection** pass runs in the background. The reflection model decides whether to `create`, `update`, `merge`, or `none` a memory mutation, then enqueues a structured job in `memory_mutation_queue`. A long-running background worker claims and applies the mutation to both PostgreSQL and Qdrant. Updated or merged memories carry a `superseded_by_id` pointer and are marked `is_superseded=True` in the Qdrant payload so they are excluded from future searches. Users can review the before/after of any mutation via the **memory change dialog** in the chat UI.

**User isolation** – Each user gets their own Qdrant collection (`user_{user_id}_memories`). Payload indexes on `user_id` and `is_superseded` are created idempotently on collection creation and before each filtered search so they work correctly on Qdrant Cloud.

### LangGraph + async reflection diagram

```mermaid
graph TD
  subgraph ChatGraph["Chat graph"]
    S((__start__)) --> QA[query_analysis]
    QA -->|personal / ambiguous| RM[retrieve_memories]
    QA -->|general_knowledge| RESP[respond]
    RM --> RE[retrieval_evaluation]
    RE -->|retry| QA
    RE -->|respond| RESP
    RESP --> E((__end__))
  end

  subgraph MutationWorkflow["Async mutation workflow"]
    RESP -.->|after response| RF[reflection_model]
    RF -->|create / update / merge| EQ[enqueue_memory_action]
    RF -->|none| SK((__end__))
    EQ --> MQ[(memory_mutation_queue)]
    MQ --> WK[run_mutation_worker]
    WK --> AM[apply_memory_action]
    AM --> PG[(PostgreSQL)]
    AM --> QD[(Qdrant)]
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

Memories are indexed in Qdrant with both **dense embeddings** (OpenAI `text-embedding-3-small`) and **sparse BM25 embeddings** (`qdrant/bm25` via Qdrant Cloud inference — free tier). At retrieval time, the backend issues two Qdrant prefetch queries (dense + sparse) and combines them with **Reciprocal Rank Fusion (RRF)** to get a strong candidate set across both modalities. Those candidates are then passed through the **Jina cross-encoder reranker** (`jina-reranker-v1-base-en` via Jina REST API). A **retrieval_evaluation** node checks the top reranker score against `MIN_RERANK_SCORE = 0.03`; if the score is too low or no memories were found, the graph retries with a rephrased query (up to 2 attempts via `decide_retry`). Only the highest-scoring memories above the threshold are injected into the prompt.

For local development, sparse embeddings fall back to the local FastEmbed SPLADE model (`prithivida/Splade_PP_en_v1`). Set `DISABLE_LOCAL_SPLADE=true` in production to skip the model download and rely solely on Qdrant Cloud inference.

## Deployment

- Frontend deployed on Vercel (SPA + serverless API proxy) — [project site](https://coherence-agent.vercel.app) serves the UI showcase
- Backend was deployed on AWS Elastic Beanstalk (currently offline)
- PostgreSQL hosted on Neon (TLS, asyncpg)
- Qdrant Cloud for vector search

The frontend never talks directly to databases or OpenAI; all access is mediated by the backend.

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Qdrant (local or Qdrant Cloud)
- OpenAI API key
- Jina API key (for reranking — free tier available at [jina.ai](https://jina.ai))

## Environment Variables

**Backend** (create `backend/.env`):

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
QDRANT_URL=http://localhost:6333
# Qdrant Cloud: set QDRANT_API_KEY (from cluster API Keys dashboard)
QDRANT_API_KEY=your_qdrant_api_key
OPENAI_API_KEY=your_openai_api_key
JINA_API_KEY=your_jina_api_key
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:5173
# Production (HTTPS): COOKIE_SECURE=true
# Disable local SPLADE model in production (uses Qdrant Cloud inference instead):
# DISABLE_LOCAL_SPLADE=true
# Optional: DB_ECHO=true to log SQL (default: false)
```

- **Neon (or any URL with query params)**: The app strips the query string from `DATABASE_URL` and sets `ssl=True` in `connect_args` so asyncpg does not receive unsupported params (e.g. `channel_binding`).
- **Qdrant**: Payload indexes on `user_id` (integer) and `is_superseded` (bool) are created idempotently on collection creation and before filtered search so they work on Qdrant Cloud.

**Frontend** – None for local development. The Vite dev server proxies `/api` to the backend. The Vercel deployment hosts the UI showcase; API requests are proxied to the backend when it is running (no backend URL in the repo).

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

To browse the UI without running locally, visit the [project site](https://coherence-agent.vercel.app) above. For the full interactive experience, follow the setup steps in this README.

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
- `GET /related` - Semantic search (query param `query`)
- `GET /mutation-queue` - Latest mutation job for current user (status, payload, before/after)
- `GET /{id}` - Get memory by ID (includes `superseded_by_id`)
- `PATCH /{id}` - Update memory content, category, tags, or importance
- `DELETE /{id}` - Delete memory

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
│   │   │   ├── AlertDialog.jsx
│   │   │   ├── LogMemoryDialog.jsx
│   │   │   ├── ViewMemoryChangesDialog.jsx
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
- ~~**Edit / delete memories**~~ ✓ – Users can update or remove memories from Memory Space.
- ~~**Memory change dialog**~~ ✓ – Review the before/after of each mutation (update/merge) in the chat UI.
- **Export memories** – Export memories (e.g. JSON or markdown) for backup or portability.
- ~~**Stronger dedup**~~ ✓ – Exact match, hybrid dense+sparse semantic similarity (RRF, threshold 0.9), and LLM-based merge via reflection all work in concert.
- **Google Calendar** – Sync events (meetings, reminders, occasions) into memories so the agent can reference past and upcoming events in conversation (OAuth2 + Calendar API).

