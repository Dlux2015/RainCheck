---
name: serve-api
description: Start the FastAPI server and verify storm, signal, and price endpoints respond correctly
---

## Serve API

Launches the FastAPI application with Uvicorn and verifies all endpoints.

### Steps
1. Ensure `.env` is configured (copy from `.env.example` and fill in keys)
2. Run: `uvicorn src.api.main:app --reload --port 8000`
3. Verify health check: `GET http://localhost:8000/health` → `{"status": "ok"}`
4. Test endpoints:
   - `GET /storm/active`
   - `GET /signal/latest`
   - `GET /prices/history?region=gulf-coast&days=14`
5. Run `pytest` before marking complete

### Rules
- All Supabase credentials must come from `os.getenv()` — never hardcoded
- CORS is open (`allow_origins=["*"]`) for local dev; restrict in production via env config
- The frontend dev server proxies `/api/*` to `http://localhost:8000` via `vite.config.js`
