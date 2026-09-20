# 🚢 CargoPulse AI

> **AI-Powered Shipment Risk Intelligence & Decision Platform**

CargoPulse AI is a full-stack, production-grade logistics intelligence platform that combines real-time shipment simulation, machine learning-based delay & ETA prediction, explainable AI (SHAP), and a live WebSocket-driven dashboard — built as a capstone project to demonstrate end-to-end AI/ML engineering skills.

---

## ✨ Features

### 📊 Live Dashboard
- Real-time stat cards: total shipments, in-transit, delayed, delivered
- Shipment status distribution charts (Recharts)
- Risk score distribution charts
- WebSocket-powered live updates every 30 seconds — no page refresh needed

### 🚚 Shipment Management
- Full CRUD for shipments with filtering, search, and pagination
- Status-based tab filtering (In Transit, Delayed, Delivered, etc.)
- Detailed shipment view with live-updating risk & ETA graphs

### 🤖 AI / ML Intelligence
- **Delay Prediction** — XGBoost binary classifier trained on the DataCo Supply Chain dataset; predicts likelihood of late delivery
- **ETA Prediction** — XGBoost regressor that forecasts actual transit days
- **Explainable AI** — SHAP TreeExplainer provides human-readable factor breakdowns (e.g., *"Risk is 81% — primarily due to Heavy Rain (+23%), Port Congestion (+19%)"*)
- **Append-only prediction history** — every simulation tick saves a new prediction row for auditable time-series graphs

### 🔁 Deterministic Simulation Engine
- APScheduler runs simulation ticks every 30 seconds
- Weather states: Clear → Rain → Heavy Rain → Storm → Fog, each with speed modifiers
- Port congestion levels (Low / Medium / High / Critical) adding wait hours
- Mechanical & customs delay events
- Fully deterministic — no random data, scenario-driven timelines

### ⚡ Real-Time WebSocket Updates
- Per-shipment WebSocket channel: `ws://localhost:8000/ws/shipments/{id}`
- Dashboard-level WebSocket: `ws://localhost:8000/ws/dashboard`
- Frontend hooks (`useShipmentHistory`, `useDashboardWebSocket`) merge REST history with live updates
- Live line charts: Risk over time, ETA trend, Speed/Distance dual-axis

### 🧠 AI Recommendation Engine *(In Progress)*
- Generates ranked action recommendations for high-risk shipments (reroute, expedite, carrier switch)
- Multi-objective scoring: cost × delay × risk × downstream impact
- What-If simulator for side-by-side scenario comparison

### 🗣️ AI Logistics Copilot *(Planned)*
- RAG pipeline using LangChain + FAISS over shipment data, events, and predictions
- Chat interface with grounded, non-hallucinated responses
- Compatible with OpenAI, Hugging Face, or local Ollama models

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                      FRONTEND                        │
│   React 19 + TypeScript + Tailwind CSS v4            │
│   Vite · React Router · Recharts · Lucide Icons      │
│   ┌──────────┬──────────┬──────────┬───────────────┐ │
│   │Dashboard │Shipments │Analytics │ Copilot/WhatIf│ │
│   └──────────┴──────────┴──────────┴───────────────┘ │
│         ▲  REST API              ▲  WebSocket        │
└─────────┼────────────────────────┼───────────────────┘
          │                        │
┌─────────┼────────────────────────┼───────────────────┐
│         ▼                        ▼      BACKEND       │
│  FastAPI · SQLAlchemy · Alembic · APScheduler        │
│                                                      │
│  ┌────────────────┐   ┌──────────────────────────┐   │
│  │  REST APIs     │   │  WebSocket Hub           │   │
│  │  /api/...      │   │  ws://.../ws/.../{id}    │   │
│  └───────┬────────┘   └──────────────┬───────────┘   │
│          │                           │               │
│  ┌───────▼───────────────────────────▼───────────┐   │
│  │            Simulation Engine                  │   │
│  │  WeatherSimulator · EventGenerator            │   │
│  │  RouteEngine · ShipmentSimulator              │   │
│  │  APScheduler (30s ticks)                      │   │
│  └───────────────────────┬───────────────────────┘   │
│                          │                           │
│  ┌───────────────────────▼───────────────────────┐   │
│  │              AI / ML Layer                    │   │
│  │  XGBoost Delay Classifier                     │   │
│  │  XGBoost ETA Regressor                        │   │
│  │  SHAP TreeExplainer                           │   │
│  │  Decision Engine · RAG Copilot (LangChain)    │   │
│  └───────────────────────┬───────────────────────┘   │
└──────────────────────────┼────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────┐
│                    PostgreSQL                          │
│  shipments · carriers · routes · shipment_events      │
│  ai_predictions · ai_recommendations · decision_history│
│  simulation_events · users · documents                │
└───────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4 |
| **Charting** | Recharts |
| **Routing** | React Router v7 |
| **Icons** | Lucide React |
| **Backend** | FastAPI, Python 3.11+ |
| **ORM** | SQLAlchemy |
| **Migrations** | Alembic |
| **Scheduler** | APScheduler |
| **Database** | PostgreSQL |
| **ML** | XGBoost, Scikit-learn, SHAP |
| **AI / RAG** | LangChain, FAISS, OpenAI / Ollama |
| **Dataset** | DataCo Supply Chain (~180K records) |
| **Containerization** | Docker, Docker Compose |

---

## 📁 Project Structure

```
cargopulse-ai/
├── backend/
│   ├── app/
│   │   ├── ai/                    # ML models, SHAP, decision engine, RAG
│   │   ├── api/                   # FastAPI route handlers
│   │   │   ├── shipments.py
│   │   │   ├── dashboard.py
│   │   │   ├── ai_predictions.py
│   │   │   ├── ai_recommendations.py
│   │   │   ├── decision_history.py
│   │   │   ├── history.py
│   │   │   ├── simulation.py
│   │   │   └── websocket.py
│   │   ├── core/                  # Config, DB engine, scheduler, security
│   │   ├── db/                    # Session, seed scripts
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response models
│   │   ├── services/              # Business logic layer
│   │   ├── simulation/            # Simulation engine modules
│   │   └── main.py
│   ├── alembic/                   # Database migrations
│   ├── datasets/                  # Raw & processed DataCo dataset
│   ├── models/                    # Saved ML model artifacts
│   ├── notebooks/                 # Jupyter EDA & training notebooks
│   ├── docker/
│   ├── docker-compose.yml
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                   # Axios API client
│       ├── components/            # Reusable UI components
│       ├── hooks/                 # useWebSocket, useShipmentHistory, useDashboardWebSocket
│       ├── layouts/               # MainLayout (sidebar + topbar)
│       ├── pages/                 # Dashboard, Shipments, ShipmentDetails, Analytics, Login
│       ├── routes/                # React Router configuration
│       ├── services/              # API service wrappers
│       ├── store/                 # Global state
│       └── types/                 # TypeScript type definitions
└── docs/
    ├── implementation_plan.md
    ├── github_workflow.md
    └── interview_prep.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/cargopulse-ai.git
cd cargopulse-ai
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, and optional API keys
```

**`.env` configuration:**

```env
APP_NAME=CargoPulse AI
APP_VERSION=0.1.0
DEBUG=true

DATABASE_URL=postgresql://postgres:<password>@localhost:5432/cargopulse_ai

SECRET_KEY=your-secret-key-here

OPENAI_API_KEY=           # Optional — for AI Copilot
HF_TOKEN=                 # Optional — for Hugging Face models
MLFLOW_TRACKING_URI=      # Optional — for experiment tracking
```

```bash
# Run database migrations
alembic upgrade head

# Seed the database with processed DataCo data
python -m app.db.seed

# Start the backend server
python -m uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend: `http://localhost:5173`

---

## 🐳 Docker Setup

Run the full stack (backend + frontend + PostgreSQL) with a single command:

```bash
cd backend
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/shipments` | List shipments (filter, search, paginate) |
| `GET` | `/api/shipments/{id}` | Get shipment by ID |
| `GET` | `/api/shipments/{id}/predictions` | Full ML prediction history |
| `GET` | `/api/shipments/{id}/predictions/latest` | Latest prediction |
| `GET` | `/api/shipments/{id}/explanation` | SHAP factor breakdown |
| `GET` | `/api/shipments/{id}/risk-history` | Risk score over time |
| `GET` | `/api/shipments/{id}/eta-history` | ETA trend over time |
| `GET` | `/api/shipments/{id}/speed-history` | Speed & distance over time |
| `GET` | `/api/shipments/{id}/events` | Shipment event log |
| `GET` | `/api/shipments/{id}/recommendations` | AI action recommendations |
| `POST` | `/api/what-if/simulate` | What-If scenario comparison |
| `GET` | `/api/dashboard/stats` | Aggregated dashboard statistics |
| `POST` | `/api/copilot/ask` | AI Copilot chat query |
| `WS` | `/ws/shipments/{id}` | Live shipment WebSocket stream |
| `WS` | `/ws/dashboard` | Live dashboard WebSocket stream |

Full interactive docs available at `http://localhost:8000/docs`.

---

## 🧪 ML Models

### Delay Prediction Model

| Property | Detail |
|----------|--------|
| **Type** | Binary Classification |
| **Algorithm** | XGBoost Classifier |
| **Dataset** | DataCo Supply Chain (~180K records) |
| **Target** | `Late_delivery_risk` (0 or 1) |
| **Features** | Shipping mode, scheduled days, product price, customer segment, market, distance, order quantity |
| **Explainability** | SHAP TreeExplainer |
| **Metrics** | Accuracy, Precision, Recall, F1, AUC-ROC |

### ETA Prediction Model

| Property | Detail |
|----------|--------|
| **Type** | Regression |
| **Algorithm** | XGBoost Regressor |
| **Target** | Actual transit days |
| **Features** | Shipping mode, distance, carrier reliability, weather, congestion, current speed, distance remaining |
| **Metrics** | MAE, RMSE, R² |

---

## 🔁 Simulation Data Flow

```
APScheduler Tick (every 30 seconds)
        │
        ▼
Read deterministic scenario for current timestamp
        │
        ▼
Apply weather / congestion / events to shipment
        │
        ▼
Update shipment state (position, speed, distance remaining)
        │
        ▼
Run XGBoost Delay Model  → delay_probability
Run XGBoost ETA Model    → predicted_eta
Run SHAP Explainer       → contributing factors
        │
        ▼
Append new row to ai_predictions (never overwrite)
        │
        ▼
Broadcast update via WebSocket
        │
        ▼
React appends to chart data arrays → live graphs re-render
```

---

## 🗄️ Database Schema

```
shipments          — core shipment entity with live position & risk scores
carriers           — carrier profiles with reliability scores
routes             — origin/destination routes with waypoint JSON
shipment_events    — append-only event log (weather, port, mechanical, customs)
simulation_events  — tick-level simulation state records
ai_predictions     — append-only ML prediction history (delay + ETA + SHAP)
ai_recommendations — AI-generated ranked action recommendations
decision_history   — manager accept/reject/modify audit trail
users              — authentication & RBAC roles
documents          — uploaded shipping documents with OCR extraction
dependency_graph   — supply chain upstream/downstream impact graph
```

---

## 📖 Documentation

| File | Description |
|------|-------------|
| [`docs/implementation_plan.md`](./docs/implementation_plan.md) | Detailed 3-week build plan with architecture decisions |
| [`docs/github_workflow.md`](./docs/github_workflow.md) | Git branching strategy and workflow guide |
| [`docs/interview_prep.md`](./docs/interview_prep.md) | Technical Q&A for capstone viva preparation |

---

## 🗺️ Roadmap

- [x] Backend: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- [x] Deterministic simulation engine with weather & congestion scenarios
- [x] APScheduler background ticks (30s interval)
- [x] WebSocket real-time push to frontend
- [x] Frontend: React 19 + TypeScript + Tailwind CSS v4
- [x] Live dashboard with stat cards and charts
- [x] Shipments list with filtering, search, pagination
- [x] Shipment detail page with live graphs and event timeline
- [x] XGBoost delay & ETA prediction models
- [x] SHAP explainability layer
- [ ] AI Recommendation Engine
- [ ] What-If Simulator UI
- [ ] Multi-objective Decision Optimizer
- [ ] Supply Chain Dependency Graph visualization
- [ ] RAG AI Copilot (LangChain + FAISS)
- [ ] JWT Authentication & protected routes
- [ ] Docker multi-container deployment
- [ ] Decision Memory & outcome tracking

---

## 📄 License

This project is licensed under the terms in the [`LICENSE`](./backend/LICENSE) file.

---

<div align="center">
  <sub>Built with ❤️ as an AI/ML Engineering Capstone Project</sub>
</div>
