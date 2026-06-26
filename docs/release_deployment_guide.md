# MarketBeacon AI v1.0 Beta Release & Deployment Guide

This document contains the official production deployment guidelines, environment configuration, database administration recommendations, rollback procedures, and release summary for **MarketBeacon AI Version 1.0 Beta**.

---

## 1. GitHub Release Readiness Checklist

Follow this checklist prior to executing a commit and pushing the final tag to GitHub. This guarantees local developer databases, configuration secrets, and build logs do not accidentally leak.

### Source Code Exclusions (.gitignore)
- [x] **Verify Ignored Files**: The root [.gitignore](file:///d:/MarketBeacon-AI/.gitignore) has been verified and updated. It correctly excludes the following items:
  - Secrets file: `.env`
  - Virtual Environment: `venv/`, `.venv/`
  - Node modules: `node_modules/`
  - Local Qdrant Storage: `qdrant_data/` and `qdrant_data_backup/`
  - Original Document Uploads: `uploads/`, `backend/uploads/`
  - Static distribution build files: `dist/`, `dist-ssr/`, `build/`, `out/`
  - Development databases: `*.db` (including dev SQLite db files)
  - Logs: `*.log`
- [ ] **Run Code Purge (Safety Check)**: Run the following commands locally in the PowerShell/Command Prompt terminal to list and purge untracked local developer scratch files:
  ```powershell
  # Review what untracked files will be permanently deleted
  git clean -fdn
  # Safely delete them to clean the environment
  git clean -fd
  ```
- [ ] **Verify Dependencies**:
  - Python: Review [requirements.txt](file:///d:/MarketBeacon-AI/backend/requirements.txt) to ensure all packages (including spaCy, PyWebPush, PyPDF, and Sentence-Transformers) are pinned.
  - React SPA: Verify that [package.json](file:///d:/MarketBeacon-AI/frontend/package.json) contains all client-side modules and compiles successfully.

### Tag & Push Commands (Copy-Paste)
Run these commands from the root directory `d:\MarketBeacon-AI` to checkpoint your version code:
```bash
# 1. Stage and commit outstanding configs
git add .gitignore
git commit -m "chore: finalize v1.0.0-beta release configuration"

# 2. Tag the repository with the stable version marker
git tag -a v1.0.0-beta -m "MarketBeacon AI v1.0.0-beta release"

# 3. Push main branch and the release tag to GitHub
git push origin main
git push origin v1.0.0-beta
```

---

## 2. Production Deployment Guide

MarketBeacon AI consists of a FastAPI backend service, a PostgreSQL relational database, an embedded Qdrant vector database (running in local filesystem mode), and a React frontend client configured as a Progressive Web App (PWA).

```mermaid
graph TD
    User([Beta User]) -->|HTTPS| Proxy[Nginx / Caddy Reverse Proxy]
    Proxy -->|Static Assets / PWA| UI[React Static SPA]
    Proxy -->|API Proxy: /api/*| API[FastAPI backend:8000]
    API -->|Ingest Jobs| APS[APScheduler Tasks]
    API -->|Read/Write| DB[(PostgreSQL Database)]
    API -->|Embeddings Search| QDR[(Local Qdrant Filesystem)]
    API -->|Generative RAG| Groq[Groq API: Llama 3.3]
    API -->|System Alerts| Resend[Resend / SendGrid API]
    API -->|Web Push| Push[Browser Push Channels]
```

### 2.1 Database Setup (PostgreSQL)
Install PostgreSQL 15+ on the production instance.
1. Connect to the Postgres server and create the database:
   ```sql
   CREATE DATABASE marketbeacon_prod;
   CREATE USER marketbeacon_user WITH PASSWORD 'ReplaceWithSecureProductionPassword';
   GRANT ALL PRIVILEGES ON DATABASE marketbeacon_prod TO marketbeacon_user;
   ```
2. The FastAPI backend automatically runs migrations on startup via the `lifespan` manager in [main.py](file:///d:/MarketBeacon-AI/backend/app/main.py#L45-L70), creating and backfilling tables for alerts, notifications, chat, portfolios, and workspaces.

### 2.2 Backend Deployment Configuration (FastAPI)
Deploy the FastAPI backend behind an ASGI server like `uvicorn` managed by a process manager (such as `systemd` on Linux) to restart the app automatically in case of crashes.

#### Backend Systemd Service (`/etc/systemd/system/marketbeacon-backend.service`):
```ini
[Unit]
Description=MarketBeacon AI FastAPI Application Server
After=network.target postgresql.service

[Service]
User=marketbeacon
WorkingDirectory=/var/www/MarketBeacon-AI/backend
EnvironmentFile=/var/www/MarketBeacon-AI/.env
ExecStart=/var/www/MarketBeacon-AI/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Apply settings and launch:
```bash
sudo systemctl daemon-reload
sudo systemctl enable marketbeacon-backend
sudo systemctl start marketbeacon-backend
```

### 2.3 Frontend & PWA Deployment (Vite + React)
The frontend should be served as pre-built static assets.
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Compile the production assets:
   ```bash
   npm run build
   ```
   This generates the static code bundle inside `frontend/dist/`, which contains the compiled HTML/JS/CSS assets, the PWA manifest `manifest.json`, and the background service worker `sw.js`.
3. Copy the contents of the `frontend/dist/` directory to the static folder on the web server (e.g. `/var/www/marketbeacon/html/`).

### 2.4 Reverse Proxy Setup (Nginx)
Configure Nginx to serve static files, enable HTTPS/SSL, and proxy API traffic:

```nginx
server {
    listen 80;
    server_name marketbeacon.ai;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name marketbeacon.ai;

    ssl_certificate /etc/letsencrypt/live/marketbeacon.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marketbeacon.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/marketbeacon/html;
    index index.html;

    # React Static Assets & PWA Handlers
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Ensure browser doesn't cache service worker (allows updates)
    location = /sw.js {
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
        expires off;
    }

    # Reverse proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 3. Production Environment Checklist

Validate that the production `.env` configuration contains the following keys, replacing development parameters with production equivalents:

| Env Configuration Key | Production Settings / Requirements | Action / Note |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://marketbeacon_user:SecurePassword@prod-db-ip:5432/marketbeacon_prod` | Connects backend to PG. Do not use local SQLite databases. |
| `GROQ_API_KEY` | Production API token from Groq Console. | Used to synthesize RAG summaries, Copilot reviews, and Dossiers. |
| `APP_ENV` | Set to `production`. | Adjusts security configurations, logs level, and error exposure. |
| `FRONTEND_URL` | Set to the public HTTPS domain (e.g. `https://marketbeacon.ai`). | Essential for JWT cookie boundaries, email links, and CORS mapping. |
| `JWT_SECRET` | Must be a secure, random string (min 64 chars). | Protects session tokens from spoofing. Do not use local defaults. |
| `RESEND_API_KEY` | Resend API Key (`re_...`). | Preferred email notification provider. |
| `SENDGRID_API_KEY` | SendGrid SMTP / API credentials. | Fallback email dispatch handler. |
| `VAPID_PUBLIC_KEY` | Generate a distinct production public key using web-push. | Push notifications browser configuration. |
| `VAPID_PRIVATE_KEY` | Generate a distinct production private key. | Private key to sign Web Push payloads. |
| `VAPID_CLAIMS_EMAIL` | Domain support address (e.g. `admin@marketbeacon.ai`). | Identifies push notification sender. |

> [!IMPORTANT]
> **CORS Security Verification**:
> In [backend/app/main.py](file:///d:/MarketBeacon-AI/backend/app/main.py#L132-L138), the CORS settings default to `http://localhost:5173`. Before starting the production server, update `allow_origins` to pull from `FRONTEND_URL` or list your custom production domain to prevent Cross-Origin request blocks.

---

## 4. Backup and Recovery Recommendations

### 4.1 PostgreSQL Backup
Configure a daily logical database backup via cron to capture system alerts, user portfolios, notes, and preferences.

#### Daily SQL Dump Script (`/opt/marketbeacon/backup_db.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/marketbeacon"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U marketbeacon_user -d marketbeacon_prod | gzip > $BACKUP_FILE

# Maintain a rolling window of 30 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +30 -delete

# Recommended: Sync to offsite storage bucket
# aws s3 cp $BACKUP_FILE s3://production-backups/db/
```

### 4.2 Qdrant Database Backup (Embedded Vectors)
Since Qdrant operates in embedded mode, files are written directly into `backend/qdrant_data/`.
1. **File Locks**: A backup cannot safely copy active DB files while the FastAPI server is running. Stop the backend server first.
2. Run a folder backup:
   ```bash
   cp -r /var/www/MarketBeacon-AI/backend/qdrant_data /var/backups/marketbeacon/qdrant_$(date +%Y%m%d)
   ```
3. Restart the backend service.

### 4.3 Original Document Uploads
User documents uploaded to the Research Library are stored in `backend/uploads/`.
- Set up a daily sync job (using `rsync` or copy commands to back up the folder daily.

---

## 5. Monitoring and Logging Recommendations

### 5.1 System & Logging Level
- Configure systemd logging. Ensure logs write to a dedicated directory and add `/etc/logrotate.d/marketbeacon` to prevent system storage exhaustion:
  ```text
  /var/log/marketbeacon/*.log {
      weekly
      rotate 4
      compress
      delaycompress
      missingok
      notifempty
      copytruncate
  }
  ```
- Backend logging uses standard log output. Keep log levels at `INFO` in production to capture errors, database transaction failures, and scheduler alerts without clogging disks.

### 5.2 Vital Performance Indicators
1. **Health Endpoint**: Configure external monitors to query `GET https://marketbeacon.ai/api/health` every 60 seconds.
2. **Groq API Rate Limits (429 status)**: Monitor uvicorn log files for Groq API throttling warnings.
3. **Database Client Pool**: Keep an eye on active PostgreSQL connections. If the user base expands, adjust connection pool limits inside `db/database.py`.
4. **Ingestion Thread Health**: Monitor that background processes (`news_scheduler`, `twitter_scheduler`) do not block and that data remains fresh.

---

## 6. Rollback Procedure

In the event of a severe deployment failure or outage, utilize this workflow to revert the site to the stable `v1.0.0-beta` tag:

```mermaid
graph TD
    A[Detect Production Defect] --> B{Code or Schema Issue?}
    B -->|Code Bug| C[Checkout Tag v1.0.0-beta]
    B -->|Schema / DB Corruption| D[Restore DB Snapshot]
    C --> E[Build frontend static dist]
    C --> F[Restart backend daemon]
    E & F & D --> G[Run Smoke Test Suite]
```

### Step 1: Revert Code Workspace
Checkout the tag created at release:
```bash
git fetch --tags
git checkout tags/v1.0.0-beta
```

### Step 2: Re-align Backend
1. Reinstate python dependency packages:
   ```bash
   venv/bin/pip install -r requirements.txt
   ```
2. Restart backend app server:
   ```bash
   sudo systemctl restart marketbeacon-backend
   ```

### Step 3: Revert Relational Schema (If Necessary)
If a recent schema patch corrupted user accounts:
1. Shut down backend services to terminate connections.
2. Restore database from the most recent safe daily SQL snapshot:
   ```bash
   dropdb -h localhost -U marketbeacon_user marketbeacon_prod
   createdb -h localhost -U marketbeacon_user marketbeacon_prod
   gunzip -c /var/backups/marketbeacon/db_backup_LASTSAFE.sql.gz | psql -h localhost -U marketbeacon_user -d marketbeacon_prod
   ```
3. Restart backend.

### Step 4: Rebuild Frontend SPA
1. Rebuild the React static distribution:
   ```bash
   cd frontend
   npm run build
   ```
2. Copy `dist/` files to `/var/www/marketbeacon/html/`.
3. In Nginx, trigger a cache purge (if CDN/Cloudflare is active) so that clients receive the updated Service Worker and asset links.

---

## 7. Version 1.0 Beta Release Summary

MarketBeacon AI has completed its stable v1.0 Beta feature cycle. The system has matured from a basic tracker into a Bloomberg-inspired **Unified Market & Portfolio Research Workspace**.

### Key Feature Modules
- **News Intelligence**: Live RSS news pipeline backed by local FinBERT Sentiment and spaCy NER engines, computing hourly sector heatmaps.
- **Smart Alerts Engine**: Tailored alerts with clickable severity cards, advanced sorting, and custom single/bulk LLM summaries.
- **Notification Center Hub**: Unified notifications with timezone alignment, quiet hours, Bloomberg HTML email formatting (using Resend/SendGrid APIs), and browser push alerts.
- **Market Copilot**: Conversational assistant with 20-message memory window, hybrid vector retriever, and citation indexing.
- **Research Library**: Drag-and-drop document uploader parsing PDF, DOCX, and Text files, indexing them into local Qdrant collection vectors.
- **Company Dossiers**: Scorecards, impact milestones, comparative peer grids, and financial details backed by a 30-day cache.
- **Explain Engine**: Contextual analysis explaining tickers, alerts, and text highlight selections via a sliding Bloomberg drawer panel.
- **Portfolio Intelligence**: Ledger CRUD operations, diversification indicators, and Observational AI reviews (strictly non-advisory).
- **AI Research Workspace**: Multi-pane canvas saving custom queries, syncing note logs, and exporting reports to Markdown.
- **Progressive Web App**: Mobile-installable client shell with offline caching and background service worker listeners.

### Stability & Cost Improvements
1. **Local-First NLP Processing**: Reduced API costs by 90% by replacing LLM parsing with local FinBERT sentiment classifiers and spaCy NER.
2. **Circuit Breakers & Backoffs**: Groq integration is throttled with a 2-second queue, exponential backoff (2s, 4s, 8s), and a 5-minute circuit breaker on consecutive errors.
3. **Singleton Vector DB Client**: Integrated thread-safe client connection proxies with automatic file-lock diagnostics.
4. **JWT Auth Resiliency**: Added Axios interceptors with queued JWT token refresh retry loops, preventing session drops on transient network failures.
