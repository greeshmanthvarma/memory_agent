# Deployment walkthrough

This guide walks you through deploying Coherence (Memory Agent) for the first time. No prior deployment experience assumed.

---

## What “deploy” means

Right now your app runs on your machine (localhost). **Deployment** means putting each part of the app on servers that are reachable on the internet so anyone (or just you) can use it via a URL.

---

## What you need to deploy

Your app has four pieces:

| Piece | What it is | Where it can run |
|-------|------------|-------------------|
| **Frontend** | React app (HTML/JS/CSS) built by Vite | Any static hosting (Vercel, Netlify, or same server as backend) |
| **Backend** | FastAPI app (Python) that handles API, auth, and logic | A server that runs Python (Railway, Render, Fly.io, etc.) |
| **PostgreSQL** | Database for users, memories, conversations | Managed DB (Railway, Render, Neon, Supabase) |
| **Qdrant** | Vector database for memory embeddings | Qdrant Cloud (free tier) or a server running Qdrant |

You also need:

- **OpenAI API key** (you already have this for local dev)
- **JWT secret** (a long random string for production)

---

## High-level strategy

Two common setups:

1. **All-in-one**  
   Backend + frontend on one platform (e.g. Railway). Backend serves the built React app and the API. You add PostgreSQL and point to Qdrant Cloud.

2. **Split**  
   Frontend on Vercel/Netlify, backend (and DB) on Railway/Render. Frontend and API have different URLs, so you must set CORS and (if you use cookies) ensure same-site or correct domain/cookie settings.

This guide uses **Option 1 (Railway)** so you only manage one place and the frontend talks to the API on the same domain (no CORS/cookie hassle). You can switch to a split setup later.

---

## Step-by-step (Railway + Qdrant Cloud)

### 1. Create accounts (if needed)

- [Railway](https://railway.app) – backend + Postgres
- [Qdrant Cloud](https://qdrant.tech/product/qdrant-cloud/) – vector DB (free tier)
- [OpenAI](https://platform.openai.com) – you already have an API key

### 2. PostgreSQL on Railway

1. In Railway, **New Project**.
2. **Add service** → **Database** → **PostgreSQL**.
3. After it’s created, open the Postgres service → **Variables** (or **Connect**).
4. Copy the `DATABASE_URL`. It often looks like:
   - `postgresql://postgres:xxx@xxx.railway.app:5432/railway`
   Railway may give a URL with `postgres://`. Your app uses **async** SQLAlchemy, so change the scheme to:
   - `postgresql+asyncpg://postgres:xxx@xxx.railway.app:5432/railway`
   (replace `postgresql://` with `postgresql+asyncpg://`).

Save this; you’ll use it as `DATABASE_URL` for the backend.

### 3. Qdrant Cloud

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io).
2. Create a **cluster** (free tier is enough).
3. In the cluster, find the **API URL** (e.g. `https://xxx-xxx.aws.cloud.qdrant.io:6333`) and, if required, **API key**.
4. Your `QDRANT_URL` will be that URL (and you’ll add the key in the URL or via env if Qdrant Cloud requires it – check their docs).

Save this as `QDRANT_URL` (and `QDRANT_API_KEY` if needed).

### 4. Backend on Railway

1. In the same Railway project, **Add service** → **GitHub repo** (or “Empty” and connect GitHub later).
2. Connect the repo that contains your `memory agent` project.
3. **Settings** for this service:
   - **Root directory**: set to the folder that contains `backend` (e.g. `memory agent` if the repo root is the repo root, or the path to `backend` if you deploy only backend).
   - **Build command**:  
     From the **backend** folder you need Python and dependencies. Example (adjust if you use `pyproject.toml`):
     ```bash
     cd backend && pip install -r requirements.txt
     ```
     If you use `uv`:  
     ```bash
     cd backend && uv sync
     ```
   - **Start command**:  
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
     Railway sets `PORT`; use it so the app listens correctly.
4. **Variables** (env vars) for the backend service – add:

   | Variable | Value |
   |----------|--------|
   | `DATABASE_URL` | `postgresql+asyncpg://...` from step 2 |
   | `QDRANT_URL` | Qdrant Cloud URL from step 3 |
   | `OPENAI_API_KEY` | Your OpenAI API key |
   | `JWT_SECRET` | Long random string (e.g. `openssl rand -hex 32`) |
   | `CORS_ORIGINS` | Your frontend URL (see step 5; if you serve frontend from same app, use `https://your-backend.railway.app`) |
   | `COOKIE_SECURE` | `true` (you’ll be on HTTPS) |

5. Deploy. Railway will build and run the backend. Once it’s up, open **Settings** → **Networking** → **Generate domain**. You’ll get a URL like `https://your-app.railway.app`.  
   This is your **backend (API) URL**.

### 5. Serve the frontend from the same backend (same domain)

To avoid CORS and cookie issues, serve the built React app from FastAPI so the app and API share one origin.

1. **Build the frontend locally** (or in a separate CI step):
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   This creates `frontend/dist`.

2. **Copy the built frontend into the backend** so the backend can serve it:
   - Either copy `frontend/dist` into `backend/static` (or similar) and configure FastAPI to serve that folder at `/`, and add a catch-all route so React Router works.
   - Or add a build step in Railway that builds the frontend then runs the backend (e.g. build: `cd frontend && npm ci && npm run build && cd ../backend && uv sync`; start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`), and mount the built files in FastAPI.

3. **Configure FastAPI to serve static files and fallback to index.html**:
   - Mount `StaticFiles` for the built app (e.g. from `static` or `../frontend/dist`).
   - Add a catch-all route that returns `index.html` for non-API routes so React Router works.

I can provide exact FastAPI code changes and a small script to copy `frontend/dist` into `backend/static` and the exact `main.py` changes if you want to do this next.

Alternatively, you can deploy the frontend to **Vercel** and point it at your Railway backend URL; then set `CORS_ORIGINS` to your Vercel URL (e.g. `https://your-app.vercel.app`) and use that frontend URL when logging in. Cookies will work if the backend sets them with the right domain/SameSite (often same-site is easiest with one domain).

### 6. Set CORS (if frontend and backend are on different domains)

If the frontend is on Vercel (or another domain) and the API on Railway:

- In Railway backend env, set:
  - `CORS_ORIGINS=https://your-vercel-app.vercel.app`
  Use the exact URL (no trailing slash). For multiple origins, use a comma-separated list.

### 7. Test

1. Open your app URL (Railway domain if you serve frontend from backend, or Vercel URL if split).
2. Register a new user.
3. Send a chat message and open Memory Space.
4. Check Railway logs for errors.

---

## Checklist before you go live

- [ ] `DATABASE_URL` uses `postgresql+asyncpg://`
- [ ] `QDRANT_URL` (and key if required) correct
- [ ] `JWT_SECRET` is a new, long random string (not the one from local dev)
- [ ] `COOKIE_SECURE=true` (HTTPS)
- [ ] `CORS_ORIGINS` set to your frontend URL (if frontend and backend are on different domains)
- [ ] Backend listens on `0.0.0.0` and `$PORT`

---

## If something breaks

- **502 / “Application failed”**: Check Railway logs. Often the start command is wrong (wrong path, wrong port) or an env var is missing (e.g. `DATABASE_URL`, `QDRANT_URL`).
- **Login works but then “Unauthorized”**: Cookie not sent or not set. Ensure you’re on HTTPS, `COOKIE_SECURE=true`, and frontend and backend are same-origin or cookie domain/SameSite is correct.
- **CORS errors in the browser**: Add your frontend URL to `CORS_ORIGINS` (exact scheme + host + port).
- **“Connection refused” to DB or Qdrant**: Check URLs and that the DB/Qdrant allow connections from Railway (Railway’s IP or “allow all” for managed services).

---

## Next steps

- Add a **custom domain** (Railway and Vercel both support it).
- Use **environment groups** or **secrets** in Railway so you don’t paste secrets in the UI.
- Optionally add the FastAPI static-serving + catch-all so you can serve the frontend from the same Railway service and keep a single domain.

If you tell me whether you prefer “one domain (frontend served by backend)” or “split (Vercel + Railway)”, I can give you the exact `main.py` changes and commands for that path.
