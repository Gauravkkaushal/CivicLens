<div align="center">

# 🏙️ CivicLens

**Test the street. Know if your shop will work, before you sign the lease.**

An AI-powered geospatial market simulator: describe any local business, pick any place in India, and watch
10,000 synthetic customers — each with a 615-parameter genome grounded in official data — choose between you,
your real competitors, and not buying at all.

[![CI](https://github.com/Gauravkkaushal/CivicLens/actions/workflows/ci.yml/badge.svg)](https://github.com/Gauravkkaushal/CivicLens/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![PostgreSQL PostGIS](https://img.shields.io/badge/PostgreSQL-PostGIS-336791.svg)](https://postgis.net/)

[**Live Demo**](https://civiclens-vbuo.onrender.com) · [Methodology](docs/MODEL.md) · [Data Sources](docs/DATA_SOURCES.md) · [Architecture](docs/ARCHITECTURE.md) · [Demo Script](docs/DEMO.md)

<br/>

![CivicLens landing page](docs/screenshots/landing.jpg)

</div>

> **Notice:** Model outputs are estimates under stated assumptions — not predictions, guarantees, or financial advice.
> Every number on screen is labelled as **observed**, **official aggregate**, **derived**, **assumed**, or **simulated**.

---

## 📌 The Problem

Small entrepreneurs bet their life savings on a location with almost no evidence. A map shows *some* competitors, a spreadsheet shows margins, a chatbot gives generic advice — none of them explains how **location, affordability, competition, and price interact** for the people who actually live around the shop. 

CivicLens connects all four in one unified workflow and remains rigorous and honest about what it doesn't know.

---

## ⚡ How It Works

| 1. Define | 2. Discover | 3. Simulate | 4. Decide |
|---|---|---|---|
| Any business in plain words ("gym", "pizza shop", "dental clinic") with price, capacity, and costs | Live competitors, buildings, roads, and population for any searched place | 10,000 synthetic agents choose with a calibrated logit model; Monte Carlo for risk | Ranked scenarios, break-even, P(loss), and clear recommendations on what to verify next |

---

## 📸 Screenshots & Visual Walkthrough

### Live market — 10,000 agents at real population density
Every red dot is a synthetic customer placed on real WorldPop density. Press play: awareness spreads and agents travel to you or to real OpenStreetMap competitors.

![Live market simulation](docs/screenshots/live-agents.jpg)

### Agent X-ray — why *this* customer chose a competitor
Click any agent to inspect its genome, the utility of each option split into channels, and the exact parameters that cost you the sale.

![Agent X-ray](docs/screenshots/agent-xray.jpg)

<table>
<tr>
<td width="50%"><b>Simulation Lab</b> — change price, marketing, hours or capacity and rerun the real engine<br><img src="docs/screenshots/simulation-lab.jpg" alt="Simulation lab"></td>
<td width="50%"><b>Sensitivity</b> — tornado of the assumptions your profit actually depends on<br><img src="docs/screenshots/sensitivity.jpg" alt="Sensitivity analysis"></td>
</tr>
<tr>
<td><b>Market DNA</b> — agents × 615 parameters, and what separates your customers from your competitors'<br><img src="docs/screenshots/market-dna.jpg" alt="Market DNA"></td>
<td><b>Factor Intelligence Engine</b> — 615 factors across 10 domains, each tagged with where its value comes from<br><img src="docs/screenshots/factor-engine.jpg" alt="Factor engine"></td>
</tr>
<tr>
<td><b>Live competitors</b> — real businesses with observed vs unknown fields and provenance<br><img src="docs/screenshots/live-competitors.jpg" alt="Live competitors"></td>
<td><b>Decisions</b> — verdict, recommendations, and "what could make this result wrong?"<br><img src="docs/screenshots/decisions.jpg" alt="Decisions page"></td>
</tr>
<tr>
<td><b>New analysis</b> — any searchable place, radius or travel-time catchment<br><img src="docs/screenshots/wizard-location.jpg" alt="Location step"></td>
<td><b>Feasibility report</b> — shareable, with sources, assumptions and limits<br><img src="docs/screenshots/report.jpg" alt="Report"></td>
</tr>
</table>

---

## 🔬 What Makes It Different

- **Real spending power, not guesses.** Each agent's monthly spend comes from MoSPI **HCES 2023-24** consumption deciles for its state × rural/urban, placed tile by tile with Meta's **Relative Wealth Index** (weighted by WorldPop) through percentile rank matching. The area's real rich/poor mix drives willingness to pay and participation. ([Details](docs/research/REAL_DATA_SOURCES.md))
- **Real road distance.** Every population zone is routed to the site and competitors over OpenStreetMap roads (OSRM). If routing fails, the run reports it transparently and falls back to straight-line × circuity.
- **615-parameter Agent Genome.** 16 correlated latent traits conditioned on age and income, 46 real-geometry measurements, and 553 generated parameters — every one consumed by the model and audited in tests. ([GENOME.md](docs/GENOME.md))
- **A defensible model.** Vectorised multinomial logit with an outside option (Huff gravity is a special case), lognormal affordability by segment, distance decay, marketing awareness, capacity limits, seeded Monte Carlo → P10/P50/P90 profit and P(loss). ([MODEL.md](docs/MODEL.md))
- **Honest about gaps.** Unknown competitor prices stay unknown. Add a competitor you saw on the street, rerun, and see the delta. When data is missing, **field research** sends a mobile survey to someone on the ground; answers flow straight back into the agents.
- **Voice analyst in Hinglish.** Press **V** anywhere and run the whole app by talking — it navigates, changes the plan, and runs the real engine. It never speaks a number that isn't in the project facts or a model run.
- **LLM never fabricates numbers.** All money and demand figures come directly from the tested Python engine; AI text containing a number not present in the model output is discarded.

---

## 🏗️ Architecture

```
Browser ── Next.js 15 (frontend/) ── /api/* proxy ──► FastAPI (backend/)
                                                      ├─ engine/      choice model, ABM, population synthesis, finance,
                                                      │               Monte Carlo, sensitivity, recommendations, field research
                                                      ├─ factors/     615-factor intelligence engine with evidence mapping
                                                      ├─ categories/  open business taxonomy and resolver
                                                      ├─ providers/   Nominatim, Overpass, Foursquare, WorldPop, OSRM/openrouteservice
                                                      ├─ data/        HCES 2023-24 tables, India wealth grid
                                                      └─ PostgreSQL + PostGIS (geography columns, GIST indexes)
```

**Stack:** Next.js 15, React 19, TypeScript, Tailwind 4, MapLibre GL + deck.gl (3D) · FastAPI, NumPy/SciPy, SQLAlchemy, Alembic · PostgreSQL + PostGIS · Playwright e2e · GitHub Actions CI.

---

## 🚀 Run Locally

### Quick Start with Docker (Recommended)

```bash
# Clone the repository
git clone git@github.com:Gauravkkaushal/CivicLens.git
cd CivicLens

# Setup environment variables (all keys have sane defaults or are optional)
cp .env.example .env

# Spin up PostGIS + Backend API + Frontend Next.js app
docker compose up --build

# Open the app
open http://localhost:3000
```

<details>
<summary><b>Running Without Docker (Manual Development Servers)</b></summary>

```bash
# 1. Start the PostGIS database
docker compose up -d db

# 2. Setup and run Backend
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements-dev.txt
export DATABASE_URL=postgresql://civiclens:civiclens@localhost:5432/civiclens
alembic upgrade head
python dev.py                             # auto-reload dev server; Swagger UI at http://localhost:8000/docs

# 3. Setup and run Frontend
cd ../frontend
npm install
API_URL=http://localhost:8000 npm run dev  # Web app at http://localhost:3000
```
</details>

---

## 🧪 Tests

```bash
cd backend
pytest                        # engine, providers, genome, factors, API (with PostGIS)
RUN_LIVE=1 pytest -m live -s  # real OpenStreetMap / WorldPop calls
```

CI runs:
- Linting with Ruff
- Alembic migrations up/down/up verification
- Comprehensive test suite against PostGIS
- Live-data verification job
- Frontend typecheck (`tsc --noEmit`) and production build (`npm run build`)
- Playwright end-to-end journey tests

---

## 🌐 Deployment

Frontend and API can run on Render's free tier:
- `frontend/` as a Node web service (`npm start`, with `API_URL` pointing to the API).
- `backend/` as a Docker web service using `backend/Dockerfile` (applies Alembic migrations on startup).
- Database: Postgres + PostGIS (e.g. Neon project).
- Vercel is also supported for serverless deployments (`backend/` as a Python function with `SERVERLESS=1`, `AUTO_MIGRATE=1`).

Refer to `.env.example` for optional integrations (OpenRouteService, Speko Voice, LLM API keys).

---

## 📊 Data and Licences

- **Map data:** © OpenStreetMap contributors (ODbL)
- **Population:** © WorldPop, University of Southampton (CC BY 4.0)
- **Consumption:** © MoSPI HCES 2023-24
- **Relative Wealth Index:** © Meta Data for Good / Chi et al. 2022 (CC BY-NC 4.0, non-commercial)
- **State boundaries:** © geoBoundaries (CC BY 4.0)
- **Routing:** © OSRM / FOSSGIS, openrouteservice by HeiGIT
- **Map Tiles:** © OpenFreeMap / OpenMapTiles

Distributed under the [MIT License](LICENSE).
