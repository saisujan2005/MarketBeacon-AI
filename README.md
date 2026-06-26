# MarketBeacon AI

> AI-powered portfolio intelligence, market research, smart alerts, and investment analysis platform.

---

## Architecture Overview

```
MarketBeacon-AI/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/routes/       # REST API endpoint handlers
│   │   ├── agents/           # Local NLP agents (FinBERT, spaCy NER, rule-based classifiers)
│   │   ├── db/               # SQLAlchemy database engine, session, and dependency injection
│   │   ├── embeddings/       # Sentence-Transformer embedding service
│   │   ├── evaluation/       # RAG retrieval quality evaluation scripts
│   │   ├── models/           # SQLAlchemy ORM models (20+ tables)
│   │   ├── rag/              # RAG pipeline (retriever, prompt builder, LLM service, verifier, judge)
│   │   ├── retrieval/        # Hybrid search (BM25 + Vector + Cross-Encoder reranker)
│   │   ├── scheduler/        # APScheduler jobs for RSS news and Twitter monitoring
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── scripts/          # Database migrations, ingestion pipelines, backfill utilities
│   │   └── services/         # Core business logic services
│   ├── requirements.txt
│   └── qdrant_data/          # Qdrant vector database storage (local mode)
│
├── frontend/                 # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx           # Main dashboard application (8300+ lines)
│   │   ├── App.css           # Global styles (dark Bloomberg terminal theme)
│   │   ├── components/       # Auth forms, landing page, settings, profile, onboarding
│   │   ├── context/          # React AuthContext with JWT token management
│   │   └── services/         # Axios API client with auto-refresh interceptor
│   ├── index.html
│   └── package.json
│
├── .env                      # Environment variables (DATABASE_URL, GROQ_API_KEY, etc.)
├── .gitignore
└── README.md
```

---

## Tech Stack

| Layer          | Technology                                                    |
|----------------|---------------------------------------------------------------|
| **Backend**    | FastAPI, Python 3.11+, SQLAlchemy ORM                        |
| **Database**   | PostgreSQL 15+                                                |
| **Vector DB**  | Qdrant (local mode, filesystem storage)                       |
| **LLM**       | Groq API (Llama 3.3 70B Versatile)                            |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2)                     |
| **Reranker**   | Cross-Encoder (ms-marco-MiniLM-L-6-v2)                       |
| **Frontend**   | React 19, Vite 8, Recharts, Axios                            |
| **Auth**       | JWT (HS256) with access/refresh token rotation                |
| **NLP**        | FinBERT sentiment, spaCy NER, rule-based sector classification|
| **Scheduler**  | APScheduler (RSS every 10 min, Twitter adaptive polling)      |

---

## Features

### Core Intelligence
- **News Intelligence Dashboard** — Real-time RSS aggregation from 20+ financial sources with AI sentiment analysis, entity extraction, and importance scoring
- **Smart Alerts Engine** — AI-generated alerts with severity classification, filterable KPI cards, and bulk AI summarization
- **Notifications System** — Source-matched notifications with metadata backfilling, severity badges, and summary caching

### Research & Analysis
- **MarketBeacon Copilot** — ChatGPT-style conversational AI with 20-message memory window, 5-source hybrid RAG retrieval, citation engine, and company detection
- **Research Library** — PDF/DOCX/TXT document upload, chunking, vector indexing, and semantic search
- **Company Analysis** — Dynamic scorecards, event timelines, peer comparisons, and executive dossiers with financial data integration
- **AI Research Workspace** — Unified research canvas routing queries across company, sector, macro, event, comparison, and portfolio impact modes

### Portfolio Intelligence
- **Portfolio Dashboard** — Manual holdings ledger with health score, diversification scoring, sector allocation, and attention metrics
- **AI Portfolio Review** — Observational AI analysis (no buy/sell recommendations) with risk monitoring focus points
- **Portfolio Daily Brief** — Bloomberg-style morning narrative summarizing holdings movements, alerts, and upcoming events

### Market Intelligence
- **Sector Heatmap** — Visual sector performance aggregation
- **Event Timeline** — Chronological market event tracking
- **AI Explain Engine** — Context-aware explanations for news, alerts, companies, and events with sliding drawer panel
- **Market Story** — Today's narrative macro summary

### Platform
- **Authentication** — Registration, login, JWT refresh, profile management, preferences, password change, account deletion
- **Global Search (Ctrl+K)** — Command bar searching across companies, watchlist items, portfolio holdings, and saved workspaces
- **RAG Evaluation Dashboard** — Performance metrics for retrieval latency, confidence, citation coverage, and quality

---

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18+ and npm
- **PostgreSQL** 15+ (running locally or via Docker)
- **Qdrant** (runs in local/embedded mode — no separate server required)

---

## Environment Configuration

Create a `.env` file in the project root with:

```env
# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/marketbeacon

# ── Groq LLM ─────────────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ── Twitter/X Scraper Auth (optional) ────────────────────────────────────────
TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
TWITTER_EMAIL=your_email

# ── Scheduler ─────────────────────────────────────────────────────────────────
NEWS_INTERVAL_MINUTES=10
TWITTER_MARKET_HOURS_INTERVAL=2
TWITTER_OFF_HOURS_INTERVAL=15
MARKET_OPEN_HOUR=9
MARKET_CLOSE_HOUR=16

# ── Alert Threshold ───────────────────────────────────────────────────────────
ALERT_THRESHOLD=85

# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV=development
FRONTEND_URL=http://localhost:5173
DISABLE_LOCAL_ML=False # Set to True on Render (512MB RAM) to bypass local ML models
```

> **Security Note**: The JWT secret is auto-generated in `auth_service.py`. For production, set `JWT_SECRET` as an environment variable with a cryptographically random 64+ character string.

---

## Setup & Installation

### 1. Database Setup

```bash
# Create the PostgreSQL database
createdb marketbeacon

# Or via psql:
psql -U postgres -c "CREATE DATABASE marketbeacon;"
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install local NLP models for offline sentiment/NER
pip install transformers torch spacy
python -m spacy download en_core_web_sm
```

### 3. Database Migrations

The application runs migrations automatically on startup via the lifespan context manager. For manual initialization:

```bash
# From the backend/ directory (with venv activated)
python -m app.db.init_db
```

If you need to create the `holdings` and `research_workspaces` tables separately:

```bash
# From the project root
python upgrade_workspace.py
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file inside the `frontend/` directory to configure the backend API URL. Refer to `frontend/.env.example` as a template.

#### Deployment Configuration
* **Local development**:
  ```env
  VITE_API_URL=http://127.0.0.1:8000
  ```
* **Production**:
  ```env
  VITE_API_URL=https://<backend-url>
  ```

---

## Running the Application

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (FastAPI auto-generated Swagger UI)

---

## API Catalog

| Route Group        | Prefix                     | Description                                      |
|--------------------|---------------------------|--------------------------------------------------|
| **Health**         | `GET /api/health`          | Service health check                             |
| **Auth**           | `/api/auth/*`              | Register, login, logout, refresh, profile, prefs |
| **Copilot**        | `/api/copilot/*`           | Chat sessions, messages, company research, RAG   |
| **Research**       | `/api/research/*`          | Document upload, search, scorecard, peers, dossier|
| **Portfolio**      | `/api/portfolio/*`         | Holdings CRUD, AI review, brief, timeline, risk  |
| **Workspace**      | `/api/workspace/*`         | Research workspace CRUD, analysis, export        |
| **Watchlists**     | `/api/watchlists/*`        | Company tracking, briefs, analysis               |
| **Alerts**         | `/api/alerts`              | Smart alerts with filtering and AI summaries     |
| **Notifications**  | `/api/notifications`       | System notifications with metadata               |
| **News**           | `/api/market-summary`      | News intelligence and sentiment aggregation      |
| **Sectors**        | `/api/sectors`             | Sector heatmap data                              |
| **Timeline**       | `/api/timeline`            | Event timeline entries                           |
| **Briefing**       | `/api/daily-briefing`      | AI daily market briefings                        |
| **Reports**        | `/api/research-reports`    | Research report generation                       |
| **Explain**        | `/api/explain`             | AI context-aware explanations                    |
| **Admin**          | `/api/admin/*`             | Reprocess pipeline triggers                      |

---

## Database Schema

The application manages 20+ PostgreSQL tables:

| Table                      | Purpose                                        |
|----------------------------|-------------------------------------------------|
| `users`                    | User accounts and authentication                |
| `user_preferences`         | Per-user UI and notification settings           |
| `posts`                    | Ingested news articles with NLP metadata        |
| `alerts`                   | AI-generated smart alerts                       |
| `notifications`            | User notifications with source matching         |
| `notification_summaries`   | Cached AI notification summaries                |
| `watchlists`               | User watchlist companies                        |
| `holdings`                 | Manual portfolio holdings ledger                |
| `research_workspaces`      | Saved AI research workspace sessions            |
| `chat_sessions`            | Copilot conversation sessions                   |
| `chat_messages`            | Individual chat messages with context            |
| `research_documents`       | Uploaded research documents metadata            |
| `research_metrics`         | RAG retrieval quality metrics                   |
| `company_peer_caches`      | Cached peer discovery results (30-day TTL)      |
| `company_research_caches`  | Cached company research data (24-hour TTL)      |
| `timeline_events`          | Market event timeline entries                   |
| `daily_briefings`          | Cached daily AI briefings (24-hour TTL)         |
| `research_reports`         | Generated research reports (6-hour TTL)         |

---

## Known Limitations

1. **Financial Data**: Current prices use a local mock provider (`LocalFinancialDataProvider`). For live prices, implement the `FinancialDataProvider` interface with Yahoo Finance or Alpha Vantage.
2. **Embedded Qdrant**: Vector DB runs in local filesystem mode. For production scale, deploy Qdrant as a standalone service.
3. **CORS**: Currently configured for `localhost:5173` only. Update `allow_origins` in `main.py` for production domains.
4. **Rate Limiting**: Groq API has rate limits. The system includes exponential backoff and circuit breaker patterns, but sustained high load may trigger 429 errors.
5. **Local NLP Models**: FinBERT and spaCy are optional. Without them, the system falls back to rule-based sentiment and entity extraction.

---

## License

Private — All rights reserved.
