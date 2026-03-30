# Plan 07 — Web App & Repo Restructure: Handoff

## Context

This document captures all decisions made about converting the auction tool into a
commercial web app and restructuring the codebase into multiple repos. Use it to
resume planning in a new session.

---

## What We're Building

A rotisserie fantasy baseball valuation tool as a multi-user web app. The existing
Python codebase (SGP engine, projection pipeline, MSP targeting) becomes the backend
model layer. A FastAPI backend and Next.js frontend wrap it for public use.

**Product shape:**
- Users create accounts and store their own league configurations
- Configurable per league: # teams, scoring categories, budget, roster sizes
- Supports third-party projections (ATC, THE BAT X) and custom projection upload
- Monetization TBD (one-time or subscription)
- Target audience: serious rotisserie players; niche to start, built to scale

---

## Competitive Advantage

The auction tool was originally built for personal use (an edge in the Moonlight Graham
league). Making it public removes that edge. The plan to preserve the edge:

- The **valuation engine** (SGP model) becomes public — it's not the moat
- The **projection system** (`baseball-projections`) stays **private** — this is the moat
- The public app supports **custom projection upload** (CSV), so the private projections
  can be fed into the app without exposing them
- Other users get ATC / THE BAT X; we get our own projections run through the same engine

---

## Stack Decisions

| Layer | Technology | Hosting |
|---|---|---|
| Frontend | Next.js (React) | Vercel |
| Backend | FastAPI (Python) | Render |
| Database | PostgreSQL | Render (managed) |
| Auth | fastapi-users (JWT bearer) | — |

**Rationale:** Vercel is purpose-built for Next.js. Render handles Python + managed
Postgres cleanly. The existing scipy/pandas/numpy ecosystem has no viable equivalent
in other languages — no rewrite.

---

## Repo Structure (Decided)

### Three repos, one dependency chain

```
baseball-projections  ──┐
                         ├──► roto-models  ──► roto-auction-app
    (future, private)    │    (library)         (product)
```

---

### `roto-models` (rename of `baseball-models`)

**Purpose:** Personal research environment + installable Python library.
**Visibility:** Public.

**Contents (no changes from current):**
- `sgp/` — SGP valuation engine
- `projections/` — FanGraphs ingestion, transform, valuate
- `targeting/` — MSP targeting model
- `scrapers/` — OnRoto scrapers
- `data/` — historical standings, rosters, CSVs
- `auction/app.py` — Streamlit draft-day tool (local use until web app replaces it)
- `plans/`, `research/`, `reports/`, `plots/` — existing docs and diagnostics

**To add:**
- `pyproject.toml` — exposes `sgp`, `projections`, `targeting` as an installable package

**To remove (when roto-auction-app is created):**
- `backend/` — moves to `roto-auction-app`
- `render.yaml` — moves to `roto-auction-app`

---

### `roto-auction-app` (new)

**Purpose:** Deployed multi-user web product.
**Visibility:** Private to start.

**High-level structure:**
```
roto-auction-app/
  backend/       ← FastAPI
  frontend/      ← Next.js
  render.yaml    ← Render deployment config
```

**Key constraint:** Never reads `data/` CSVs directly. All model access goes through
the `roto-models` package. The `roto-models` git dependency is pinned to a tag:
```
git+https://github.com/jdenn0514/roto-models.git@<tag>
```

**Detailed specs still to write:**
- Product spec (user flows, feature list, monetization)
- Backend spec (data model, API endpoints, auth flows)
- Frontend spec (pages, components, state management)

---

### `baseball-projections` (new, private)

**Purpose:** Research project to build a from-scratch projection system (à la ATC,
ZiPS, Steamer, THE BAT X).
**Visibility:** Private.

Entirely independent of the other repos to start. If projections mature, they feed
into `roto-auction-app` via CSV upload (custom projection feature) or eventually as
a second pip dependency.

Scope of this project is its own separate planning effort.

---

## Migration Steps (when ready to act)

1. Add `pyproject.toml` to `baseball-models`, rename repo to `roto-models`
2. Create `roto-auction-app`, move `backend/` and `render.yaml` into it
3. Update `roto-auction-app/backend/requirements.txt` to install `roto-models` from GitHub
4. Create `baseball-projections` as a fresh private repo

---

## What Was Already Built (but not yet in the right repo)

A FastAPI backend scaffold exists on branch `claude/scaffold-fastapi-backend-bt3RO`
in the current `baseball-models` repo. It is a starting point only — a full spec
sheet will be written before the backend is properly built. Contents:

- `backend/db.py` — async SQLAlchemy engine (asyncpg), handles Render's connection string
- `backend/models.py` — ORM models: `User`, `LeagueConfig`, `SavedValuation`
- `backend/schemas.py` — Pydantic schemas for all request/response types
- `backend/auth.py` — JWT bearer auth via fastapi-users
- `backend/main.py` — FastAPI app: CORS, lifespan, routers
- `backend/routes/leagues.py` — CRUD for per-user league configs
- `backend/routes/valuate.py` — `POST /valuate` wraps the projection pipeline in a
  threadpool; `GET /valuate` and `GET /valuate/{id}` retrieve saved results
- `backend/requirements.txt` — all deps for Render deployment
- `render.yaml` — Render Blueprint: web service + managed Postgres

This scaffold should be reviewed against the backend spec before use.

---

## Immediate Next Steps

1. Write product spec for `roto-auction-app` (user flows, feature list, monetization model)
2. Write backend spec (data model, full API surface, auth flows, custom projection upload)
3. Write frontend spec (pages, components, Next.js structure)
4. Create the new GitHub repos (`roto-auction-app`, `baseball-projections`)
5. Add `pyproject.toml` to `roto-models` and rename the repo
