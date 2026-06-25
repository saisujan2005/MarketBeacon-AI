# MarketBeacon AI Intelligence Upgrade Checklist

## Phase 1: Database Setup
- [x] Create database models: `timeline_event.py`, `daily_briefing.py`, `research_report.py`
- [x] Add columns to `Post` model in `post.py`
- [x] Create and run `upgrade_db_v2.py` migration script

## Phase 2: Foundational LLM Agents
- [x] Implement `sentiment_agent.py`
- [x] Implement `entity_extractor.py`
- [x] Implement `prediction_agent.py`

## Phase 3: Services & Ingestion Integration
- [x] Implement `timeline_service.py`
- [x] Implement `alert_engine.py`
- [x] Implement `watchlist_service.py`
- [x] Implement `sector_intelligence.py`
- [x] Implement `daily_briefing_agent.py`
- [x] Implement `research_report_agent.py`
- [x] Implement `impact_history_service.py`
- [x] Integrate all agents into the ingestion processing script (`score_posts.py` & `news_scheduler.py`)

## Phase 4: API Routes Integration
- [x] Create `sectors.py` router
- [x] Create `timeline.py` router
- [x] Create `daily_briefing.py` router
- [x] Create `research_reports.py` router
- [x] Update `watchlists.py` router
- [x] Update `main.py` router registration

## Phase 5: Frontend Dashboard UI
- [x] Update `App.jsx` sidebar and tabs
- [x] Build News Tab (sentiment, entities, prediction)
- [x] Build Watchlists Tab (news filter)
- [x] Build Sector Heatmap Tab
- [x] Build Timeline Tab
- [x] Build Research Reports Tab
- [x] Build Daily Briefing Tab
- [x] Build Alerts Tab

## Phase 6: Verification & Testing
- [x] Write unit tests for agents
- [x] Manually verify UI and end-to-end flow

## Phase 7: Rate Limit & Stability Fixes
- [x] Fix 1: Handle 429 status code properly with safe neutral fallbacks
- [x] Fix 2: Implement Exponential Backoff (2s, 4s, 8s) on LLM retries
- [x] Fix 3: Limit article processing (skip LLM for rule-based est_score < 70)
- [x] Fix 4: Combine multiple agents (sentiment, entity, prediction) into a single call
- [x] Fix 5: Implement thread-safe 2-second rate limiter throttling
- [x] Fix 6: Implement LLM Circuit Breaker (5 failures triggers 5 mins cooldown)
- [x] Fix 7: Add global in-memory cache for processed articles
- [x] Fix 8: Implement Fail-Fast checks for API responses (non-200 / 429)
- [x] Fix 9: Add detailed logging (article, attempt, duration, status code)
- [x] Fix 10: Process high-priority articles in batches of max 10 items

## Phase 8: Cost & Performance Optimization (90% Groq Reduction)
- [x] Phase 1: Implement local FinBERT sentiment analysis (`finbert_sentiment.py`)
- [x] Phase 2: Implement local spaCy NER entity extraction (`spacy_entity_extractor.py`)
- [x] Phase 3: Implement rule-based local sector classifier (`sector_classifier.py`)
- [x] Phase 4: Implement local rule-based importance scoring (`importance_scorer.py`)
- [x] Phase 5: Integrate local extraction into scoring pipeline (`score_posts.py`)
- [x] Phase 6: Throttling Groq Predictions to high-priority articles ($\ge$ 85 or CRITICAL)
- [x] Phase 7: Add 24-hour database caching to Daily AI Briefings
- [x] Phase 8: Add 6-hour database caching to Research Reports
- [x] Phase 9: Support Telecom and Metals sectors in Heatmap aggregations
- [x] Phase 10: Upgrade frontend optional chaining and render error fallbacks in App.jsx
- [x] Phase 11: Implement local-first unit tests in `test_ai_upgrades.py`

## Phase 9: News Intelligence Dashboard Enhancements
- [x] Task 1: Add News Timestamp
- [x] Task 2 & 3: Fix Dashboard Counters, Neutral Stats, and Sentiment Confidence
- [x] Task 4: Improve Sentiment Classification
- [x] Task 5: Add Debug Visibility
- [x] Task 6: Fix Flat Importance Scoring & False-Positives
- [x] Task 7: Implement Admin Reprocess Endpoint
- [x] Task 8: Verification

## Phase 10: Enhance Notifications Module
- [x] Subtask 10.1: Database Schema Modifications & Migration Script (Add fields to `Notification`, `Alert`, and create `NotificationSummary` model and table)
- [x] Subtask 10.2: Update Alert Engine (`alert_engine.py` - store post_id, post_url)
- [x] Subtask 10.3: Update Notification Generation (`generate_notifications.py` - implement robust matching with confidence logging and populate new metadata fields)
- [x] Subtask 10.4: Update Backend API Routes (`routes/notifications.py` - sort notifications, return new metadata, query and store in `notification_summaries` cache table with timeout/error safety)
- [x] Subtask 10.5: Register `NotificationSummary` model in `init_db.py`
- [x] Subtask 10.6: Update Frontend React Dashboard (`App.jsx` - periodic timer for auto-updating ages, visual source badges mapping emojis, severity badges mapping ranges, original article click-through links, summary modal, loading state, empty/error stateRetry)
- [x] Subtask 10.7: Run migration, run reprocess pipeline, and verify frontend rendering

## Phase 11: Smart Alerts Dashboard Upgrade
- [x] Task 11.1: Enhance `/api/alerts` backend route to support parameters (`severity`, `source`, `importance_min`, `direction`, `sort`), filtering, sorting, ISO timestamps, and `direction` key.
- [x] Task 11.2: Upgrade frontend state management and API integration in `App.jsx` (add state variables and `useEffect` to fetch from `/api/alerts` with active parameters).
- [x] Task 11.3: Update KPI Cards to act as toggleable filters with premium glow, border, and scale animation styles.
- [x] Task 11.4: Implement Active Filter Chips above the alerts grid to display and remove individual active filters.
- [x] Task 11.5: Implement Sort Dropdown for Latest, Oldest, Highest Importance, and Highest Confidence.
- [x] Task 11.6: Implement empty state with "Clear Filters" button.
- [x] Task 11.7: Format alert timestamp (relative age + hover tooltip).
- [x] Task 11.8: Perform verification and test features.

## Phase 12: AI Summarization & Unified Filtering
- [x] Feature 1: Single AI summary for alerts (including Key Takeaways, Suggested Watchlist, caching logic, and right side Bloomberg terminal analysis drawer UI)
- [x] Feature 2: Bulk AI summaries of alerts (including checkbox state selections and "Summarize Selected" triggers)
- [x] Feature 3: Notifications filtering (incorporating unified KPI cards, timeframe, and source selectors)
- [x] Feature 4: News Intelligence filtering (incorporating clickable sentiment KPI cards and unified dropdowns)
- [x] Feature 5: Reusable layout filter components (incorporating dynamic props in FilterBar, ActiveFilterChips, and SortDropdown)
- [x] Feature 6: Daily AI briefings generator (incorporating top-right catalyst briefings from alerts/posts/notifications)
- [x] Feature 7: Database-backed 24h summary caching
- [x] Feature 8: Loading states, disabled button visual cues, and toasts
- [x] Feature 9: Optimized react effect dependency routing to prevent extraneous API calls

## Phase 13: Transform Ask AI into MarketBeacon Copilot
- [x] Task 13.1: Define database models `ChatSession` and `ChatMessage` in `chat.py`
- [x] Task 13.2: Implement 20-message memory window context and 24h rolling context summarizer in `copilot_agent.py`
- [x] Task 13.3: Implement automatic company detection research mode and dossier generation templates in `copilot_agent.py`
- [x] Task 13.4: Integrate 5-source hybrid retriever (News, Alerts, Notifications, Briefs, Reports) using BM25 + Vector Search + Reranker in `hybrid_retriever.py`
- [x] Task 13.5: Implement citation engine and 24h company report database caching in `copilot_agent.py`
- [x] Task 13.6: Add REST endpoints for sessions, messages, history, company research, and deep research in routes `copilot.py` and register in `main.py`
- [x] Task 13.7: Implement frontend chat history sidebar with session switching and deletion in `App.jsx`
- [x] Task 13.8: Implement ChatGPT-style conversation view with copy, regenerate, suggested follow-ups, and watchlist button in `App.jsx`
- [x] Task 13.9: Add Deep Research Mode UI toggle and streaming loading spinner state transitions in `App.jsx`
- [x] Task 13.10: Perform schema migrations and verify overall compilation stability

## Phase 14: Phase B: Research Library & Ingestion Pipeline
- [x] Task 14.1: Define database model `ResearchDocument` in `research_document.py`
- [x] Task 14.2: Import and register new models in database initialization scripts (`init_db.py`, `upgrade_notifications.py`)
- [x] Task 14.3: Implement document text extraction routines for PDF, DOCX, and TXT with fallbacks in `document_parser.py`
- [x] Task 14.4: Implement word-based sliding-window token chunker (800-1000 tokens, 100-150 tokens overlap) in `document_parser.py`
- [x] Task 14.5: Create `research_documents` Qdrant collection for index isolation in `qdrant_service.py`
- [x] Task 14.6: Implement files uploader endpoint `/api/research/upload` converting and indexing text chunks in Qdrant in `copilot.py`
- [x] Task 14.7: Implement documents metadata retrieval `/api/research/documents` and document deletion `/api/research/document/{id}` in `copilot.py`
- [x] Task 14.8: Implement semantic vector search sandbox query endpoint `/api/research/search` in `copilot.py`
- [x] Task 14.9: Design and build dedicated Research Library interface tab in `App.jsx`
- [x] Task 14.10: Implement drag-and-drop file inputs, file directories, custom metadata tags, status indicators, and vector search widgets in `App.jsx`
- [x] Task 14.11: Create automated mock ingestion tests in `test_research_agent.py`

## Phase 15: Phase C: Hybrid RAG Retrieval & Deep Research Mode
- [x] Task 15.1: Create database model `ResearchMetric` in `research_metric.py`
- [x] Task 15.2: Register `ResearchMetric` in migration and initialization scripts (`init_db.py`, `upgrade_notifications.py`)
- [x] Task 15.3: Upgrade Cross-Encoder reranker to evaluate query matches against document text content in `reranker.py`
- [x] Task 15.4: Modify `hybrid_search` retriever to conditionally query the `research_documents` collection and merge results with BM25 in `hybrid_retriever.py`
- [x] Task 15.5: Attach full attribution metadata fields (`document_id`, `source_file`, `company_name`, `document_type`, `chunk_index`, `similarity_score`, `text`) to all retrieved contexts in `hybrid_retriever.py`
- [x] Task 15.6: Track RAG query latency, prompt token estimates, matching quality, and log metrics inside `research_metrics` in `copilot_agent.py`
- [x] Task 15.7: Create evaluation logging endpoint `/api/research/evaluate` returning retrieval statistics in `copilot.py`
- [x] Task 15.8: Instruct LLM to format responses with strict Markdown headings (Summary, Evidence, Sources, Confidence Score, Suggested Follow-Ups) in `copilot_agent.py`
- [x] Task 15.9: Render "View Evidence 📖" buttons next to references in the Copilot chat history log in `App.jsx`
- [x] Task 15.10: Implement `Evidence Viewer Modal` overlay to display retrieved document chunk text contents in `App.jsx`

## Phase 16: Phase D: Scorecards, Timeline Generation, and Dynamic Peer Comparison
- [x] Task 16.1: Define SQLAlchemy models `CompanyPeerCache` and `CompanyResearchCache` in `research_cache.py`
- [x] Task 16.2: Register research cache models in `init_db.py` and `upgrade_notifications.py` for automated database table creation
- [x] Task 16.3: Implement dynamic peer discovery service using LLM classification cached for 30 days in `research_agent.py`
- [x] Task 16.4: Implement orchestrator compiling evidence-backed scorecards, milestones event timelines, comparative peer grids, and executive dossiers cached for 24 hours in `research_agent.py`
- [x] Task 16.5: Create REST API endpoints `POST /api/research/scorecard`, `POST /api/research/timeline`, `POST /api/research/peers`, and `POST /api/research/dossier` in `copilot.py`
- [x] Task 16.6: Add company research state variables and fetch trigger triggers inside `App.jsx`
- [x] Task 16.7: Build auto-detection of companies from history session switching inside `App.jsx`
- [x] Task 16.8: Design and implement dynamic 3-column layout rendering chat alongside the Company Analysis side panel in `App.jsx`
- [x] Task 16.9: Build interactive sub-tabs inside the Company Analysis panel displaying Scorecard progress bars, Event Timelines with impact badges, Peer Comparison Tables, and Dossier textual breakdowns in `App.jsx`
- [x] Task 16.10: Render Research Confidence Score meter with verified details inside the dashboard in `App.jsx`

## Phase 17: Phase E: Research Quality, Reliability, and Financial Data Integration
- [x] Task 17.1: Implement `FinancialDataProvider` abstract base class and `LocalFinancialDataProvider` default offline database with normalized aliases mapping (`tcs`/`hdfcbank` -> `TCS`/`HDFC Bank`) in `financial_data.py`
- [x] Task 17.2: Create numerical source reliability mapping defining 4 tiers (Tiers 1 to 4 with weights 1.0 to 0.4) in `reliability_layer.py`
- [x] Task 17.3: Modify hybrid search retrieval to adjust cross-encoder scores based on source weights and rerank documents in `hybrid_retriever.py`
- [x] Task 17.4: Implement confidence-based multi-factor evidence scoring (averaging similarity and source weights) and clamp confidence to 10% on hallucination guard trigger in `copilot_agent.py`
- [x] Task 17.5: Restructure dossier text blocks to return structured citations including source, document, date, and exact evidence text in `research_agent.py`
- [x] Task 17.6: Add database migrations for `citation_coverage` in `ResearchMetric` model and register in `upgrade_notifications.py`
- [x] Task 17.7: Create aggregated RAG evaluation metrics endpoint `/api/research/metrics/aggregate` in `copilot.py`
- [x] Task 17.8: Implement thread-safe background preloading task inside application lifespan setup in `main.py`
- [x] Task 17.9: Upgrade frontend React UI in `App.jsx` to render confidence badges, evidence detail cards, and full interactive RAG Evaluation dashboard
- [x] Task 17.10: Create integration and dossier quality test suite `test_dossier_quality.py`

## Phase 18: Phase J: Watchlist Intelligence - Personal Briefs
- [x] Extend the Watchlist database model with priority, sector, and industry columns
- [x] Build Watchlist morning brief generator engine with RAG retrieval
- [x] Create backend API routes for watchlist analysis caching
- [x] Update frontend dashboard to support customized P1-P5 Watchlist cards
- [x] Implement the interactive Morning Brief dashboard widget

## Phase 19: Phase K: Market Intelligence Engine
- [x] Create Market Health Dashboard calculations and endpoints
- [x] Build Sector Intelligence heatmap data provider
- [x] Implement Opportunities & Risks rank tracker
- [x] Build keyboard Ctrl + K Command Bar with global search
- [x] Implement frontend Bloomberg Terminal layout enhancements

## Phase 20: Phase L: AI Explain Engine
- [x] Create FastAPI endpoint `/api/explain` supporting news, alert, company, event, and text types
- [x] Create FastAPI endpoint `/api/market-intelligence/story` for Today's Market Story narrative
- [x] Implement 30-minute global in-memory caching logic in `explain_service.py`
- [x] Build structured prompts with RAG context integration in `explain_service.py`
- [x] Build dynamic related entities extraction via hybrid search engine
- [x] Update `App.jsx` sliding drawer panel layout with visual impact map, timeline, and citations
- [x] Add floating selection bubble "✨ Explain" for highlighted text
- [x] Add click triggers on News, Alerts, Companies, and macro Events
- [x] Verify frontend syntax and finalize code repair

## Phase 21: Phase M: Portfolio Intelligence Platform
- [x] Define manual portfolio holdings `Holding` database model mapping exchange, average buy price, current price, tags, and notes.
- [x] Register new models in DB initialization and write upgrade migration script.
- [x] Implement portfolio service calculating Net Valuation, Today's change, Health Score, Diversification Score, alert/news risk penalties.
- [x] Implement Observational AI Portfolio Review prompt strictly excluding buying/selling recommendations.
- [x] Implement Today's Portfolio Daily Brief narrative generator detailing earnings, macro calendar alerts, and warnings.
- [x] Implement REST router exposing CRUD operations on holdings, AI reviews, Daily Briefs, timeline histories, risk centers.
- [x] Implement 30-minute user-specific in-memory TTL caching with evictions on portfolio updates or alerts ingestion.
- [x] Extend smart global command search (Ctrl+K) to match holdings, notes, and metadata.
- [x] Design premium dark-themed Portfolio dashboard widgets with sector allocation bars and holding ledger cards.
- [x] Implement side-by-side holdings comparison scorecard detailing peer timelines.
- [x] Integrate macro event impact simulations reusing Explain Engine.
- [x] Verify overall compilation and system stability.

## Phase 22: Phase N: AI Research Workspace
- [x] Create saved workspaces `ResearchWorkspace` database model mapping query, title, notes, is_favorite, and analysis.
- [x] Register new models in DB initialization and write upgrade migration script.
- [x] Implement backend service `workspace_service.py` to route queries (company, sector, macro, event, comparison, portfolio impact) and compile canvas details.
- [x] Implement REST endpoints for workspace analysis, Saved Workspaces CRUD operations, duplication, favoriting, and Markdown report export.
- [x] Extend global search to query saved workspaces and notes.
- [x] Build three-pane premium dark-themed Research Workspace dashboard UI in `App.jsx`.
- [x] Implement Analyst Notes panel linking notes to active workspaces.
- [x] Implement follow-up prompts extending query analysis in-place.
- [x] Verify overall compilation and system stability.

## Phase 23: v1.0 Stabilization & Production Readiness
- [x] Audit codebase for TODO, FIXME, HACK comments — none found
- [x] Audit codebase for console.log in frontend — clean
- [x] Audit codebase for debug print() in production paths — found and fixed in `main.py` and `market_agent.py`
- [x] Fix CRITICAL: Register `Holding` and `ResearchWorkspace` models in `upgrade_notifications.py`
- [x] Fix CRITICAL: Register `Holding` and `ResearchWorkspace` models in `upgrade_auth_db.py`
- [x] Fix CRITICAL: Update `requirements.txt` with all actual runtime dependencies
- [x] Fix HIGH: Remove dead code (unreachable double return) in `market_agent.py`
- [x] Fix HIGH: Replace hardcoded absolute path in `main.py` with `os.path`-based relative path
- [x] Fix HIGH: Correct health endpoint service name from "AlgoAI" to "MarketBeacon AI"
- [x] Fix MEDIUM: Replace debug `print()` with `logger.info()` in `main.py` and `market_agent.py`
- [x] Fix MEDIUM: Update `index.html` title from "frontend" to "MarketBeacon AI" and add meta description
- [x] Fix MEDIUM: Update `.gitignore` to cover `node_modules/`, `*.log`, `*.db`, `dist/`
- [x] Security audit: JWT, CORS, SQL injection, password hashing, input validation — documented
- [x] Performance audit: caching TTLs, rate limiting, circuit breaker — verified operational
- [x] Database migration verification: all 18 tables registered across all entry points
- [x] Write comprehensive production `README.md` with architecture, setup, API catalog, and deployment checklist
- [x] Write comprehensive `docs/bug_audit_report.md` with all findings, fixes, and recommendations

## Phase 24: Robust Token Refresh and Auth Stabilization
- [x] Subtask 24.1: Add temporary debug logging in backend `dependencies.py`, `auth_service.py`, and `auth.py`
- [x] Subtask 24.2: Enhance frontend Axios response interceptor in `api.js` (implement refresh queue and transient error resiliency)
- [x] Subtask 24.3: Add temporary debug logging in frontend `api.js`
- [x] Subtask 24.4: Upgrade frontend startup authentication validation in `AuthContext.jsx` (retry on 401 and load from cache on 500/network error)
- [x] Subtask 24.5: Verify protected routes call the API with correct credentials
- [x] Subtask 24.6: Run end-to-end verification (login, token refresh, multiple 401s, 500 resilience, invalid refresh token logout, navigation)
- [x] Subtask 24.7: Clean up temporary debug logging statements and finalize code

## Phase 25: Singleton Qdrant Client Integration
- [x] Subtask 25.1: Implement `QdrantClientProxy` and lazy initialization in `qdrant_service.py`
- [x] Subtask 25.2: Integrate client shutdown handle in FastAPI lifespan in `main.py`
- [x] Subtask 25.3: Verify single instance constraints, startup, search, indexing, and retrieval
- [x] Subtask 25.4: Document walkthrough and finalize verification results

