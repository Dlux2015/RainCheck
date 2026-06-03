# Skill: readme-audit

Audit README.md against the actual repository and update it to match reality.

## Trigger

`/readme-audit`

## What this skill does

1. Read README.md in full
2. Walk the real repo: files, directories, stack, endpoints, env vars, workflows, deployment config
3. Produce a findings table — what's stale, missing, or wrong
4. Apply every fix directly to README.md
5. Confirm what changed

---

## Step 1 — Read the README

Read `README.md` top to bottom. Note every factual claim:
- Tech stack table
- Architecture diagram / description
- How It Works steps
- Data sources
- Environment variables table
- GitHub Actions secrets table
- Local setup commands
- Deployment instructions
- Any URLs, file paths, or version numbers

---

## Step 2 — Ground-truth the repo

Run these checks in parallel:

**Stack**
- `package.json` (frontend deps + devDeps) — confirm framework, chart lib, map lib, versions
- `requirements.txt` or `pyproject.toml` — Python deps and versions
- `src/api/main.py` — framework (FastAPI), routers, CORS config
- `src/ingestion/*.py` — data sources actually used
- `src/ml/train.py` — ML library, model name constant
- `src/transforms/*.py` — PySpark usage, Delta Lake paths

**Architecture**
- Delta Lake paths: `grep -r "delta/" src/` — what volume/path is actually used
- MLflow model name: grep for `MODEL_NAME` and `MODEL_ALIAS` in `src/ml/`
- Supabase tables: `supabase/migrations/*.sql` — what tables actually exist
- API endpoints: read all `src/api/routers/*.py` — list every route

**Automation**
- `.github/workflows/*.yml` — cron schedules, what each workflow does, what secrets it uses
- Check for `Procfile`, `railway.toml`, `frontend/vercel.json` — deployment config that exists

**Environment variables**
- `.env.example` — canonical list
- Search all `os.getenv(` calls in `src/` for any vars not in `.env.example`

**Frontend**
- `frontend/src/App.jsx` — what API endpoints it calls, what components are rendered
- `frontend/src/components/` — list all components and what they do
- `frontend/vite.config.js` — proxy target, build config

---

## Step 3 — Diff README vs reality

For each README claim, mark it:

| Claim | Status | Evidence |
|-------|--------|----------|
| ... | ✅ Correct / ❌ Wrong / ⚠️ Outdated / ➕ Missing | file:line |

Categories to check:
- **Stack table rows** — is every technology listed? Are any wrong?
- **Data sources** — correct API names (EIA not Zyla?)
- **How It Works** — does each step match the actual workflow files?
- **Delta paths** — do the documented paths match the code?
- **MLflow model name** — matches `MODEL_NAME` constant?
- **Environment variables** — every var in `.env.example` and any undocumented ones
- **GitHub Actions secrets** — every secret referenced in `.yml` files
- **Deployment** — `railway.toml`, `vercel.json`, `Procfile` existence and content
- **Local setup commands** — do they actually work with the real project structure?
- **Component list / features** — does README mention the weather background? 3-grade chart? city selector?

---

## Step 4 — Apply all fixes

Edit `README.md` directly. Do not ask for confirmation on individual fixes — apply everything and summarise at the end.

Fixes to apply:
- Wrong API names → correct them
- Missing components/features → add them
- Wrong paths → update
- Missing env vars → add to table
- Missing secrets → add to GitHub Actions secrets table
- Outdated architecture description → rewrite to match actual code
- Wrong local setup commands → fix
- Missing deployment files → document them

Do NOT:
- Add marketing fluff
- Invent features that don't exist
- Change the writing style

---

## Step 5 — Report

List every change made as a one-liner:
- `[FIXED]` Wrong data source name: Zyla → EIA Open Data API
- `[ADDED]` Missing component: WeatherBackground + city selector
- `[ADDED]` Missing env var: NHC_RSS_URL
- `[UPDATED]` Delta paths: dbfs:/delta → /Volumes/workspace/default/raincheck/delta
- etc.
