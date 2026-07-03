# ServerDeals — US eBay Server Hardware Deal Finder

> **Self-hosted deal discovery engine for refurbished & used server hardware on US eBay.**
> Scores listings against 60-day market medians, surfaces the best deals, and alerts you via email and Telegram.

---

## What is ServerDeals?

ServerDeals is a self-hosted service that continuously scrapes US eBay for server hardware — Dell PowerEdge, HP ProLiant, Supermicro, and more across 25 hardware categories. Each listing is scored against a 60-day rolling market price median, classifying deals as **Hot** (≥40% below market), **Good** (20–39% below), or **Fair** (0–19% below). A React frontend provides a responsive, dark-themed browsing experience with price history charts.

---

## Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────┐
│  eBay US API │────▶│              Backend (Python)             │
│  (Finding)   │     │                                          │
└──────────────┘     │  ┌──────────┐  ┌────────┐  ┌─────────┐  │
                     │  │ Scraper  │  │Scoring │  │ Alerts  │  │
                     │  │ (cron)   │  │ Engine  │  │ Email   │  │
                     │  └────┬─────┘  └───┬────┘  │ Telegram│  │
                     │       │            │       └────┬─────┘  │
                     │  ┌────▼────────────▼───┐       │        │
                     │  │    PostgreSQL 16     │       │        │
                     │  └──────────┬───────────┘       │        │
                     │             │                   │        │
                     │  ┌──────────▼───────────┐       │        │
                     │  │   FastAPI (REST)      │───────┘        │
                     │  └──────────┬───────────┘                │
                     └─────────────┼────────────────────────────┘
                                   │
                     ┌─────────────▼──────────────────────────┐
                     │          Frontend (React + TS)          │
                     │  ┌─────────┐ ┌──────────┐ ┌─────────┐  │
                     │  │ Deals   │ │ Price    │ │Setup    │  │
                     │  │ Browser │ │ Charts   │ │Guides   │  │
                     │  └─────────┘ └──────────┘ └─────────┘  │
                     │           Served by Nginx                │
                     └─────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- eBay Partner Network API credentials (App ID, Dev ID, Cert ID)
- PostgreSQL 16 (included in Compose)

### 1. Clone & Configure

```bash
git clone https://github.com/skylabby/serverdeals.git
cd serverdeals
cp .env.example .env
# Edit .env with your eBay API keys and alert preferences
```

### 2. Start (Docker Compose)

```bash
docker compose up -d --build
```

The stack starts three services:

| Service   | Port | Description                          |
|-----------|------|--------------------------------------|
| postgres  | 5433 | PostgreSQL 16 (data persisted)       |
| backend   | 8183 | FastAPI (scraper + scoring + API)    |
| frontend  | 8182 | Nginx serving React SPA + API proxy  |

### 3. Seed Categories & Trigger Initial Scrape

```bash
# Seed 25 hardware categories
docker compose exec backend python -m backend.db.seed

# Run scraper immediately (also auto-runs on startup via SCRAPE_ON_STARTUP)
docker compose exec backend python -m backend.scraper.scheduler
```

### 4. Access

| Service     | URL                                |
|-------------|------------------------------------|
| Frontend    | http://your-server:8182            |
| API (direct)| http://your-server:8183            |
| API Docs    | http://your-server:8183/docs       |
| Health      | http://your-server:8183/api/health |

> **Note:** The frontend proxies `/api/*` to the backend via Nginx. Set `VITE_API_URL=` (empty) at build time for server deployments — the Dockerfile does this by default.

---

## Environment Variables

| Variable               | Required | Default              | Description                                      |
|------------------------|----------|----------------------|--------------------------------------------------|
| `EBAY_APP_ID`          | Yes      | —                    | eBay Production App ID (OAuth)                   |
| `EBAY_DEV_ID`          | Yes      | —                    | eBay Developer ID                                |
| `EBAY_CERT_ID`         | Yes      | —                    | eBay Certificate ID                              |
| `EBAY_ENV`             | No       | `sandbox`            | `sandbox` or `production`                        |
| `EBAY_CAMPAIGN_ID`     | No       | `YOUR_CAMPAIGN_ID`   | EPN campaign ID for affiliate links              |
| `DATABASE_URL`         | Yes      | —                    | asyncpg DSN (e.g. `postgresql://user:pass@host:5432/db`) |
| `SMTP_HOST`            | No       | `smtp.example.com`   | SMTP server for email alerts                     |
| `SMTP_PORT`            | No       | `587`                | SMTP port                                        |
| `SMTP_USER`            | No       | —                    | SMTP username                                    |
| `SMTP_PASS`            | No       | —                    | SMTP password                                    |
| `EMAIL_FROM`           | No       | `SMTP_USER`          | From address for alert emails                    |
| `TELEGRAM_BOT_TOKEN`   | No       | —                    | Telegram Bot API token (from @BotFather)         |
| `TELEGRAM_CHAT_ID`     | No       | —                    | Default Telegram chat ID for alerts              |
| `SCRAPE_ON_STARTUP`   | No       | `true`               | Run full scraper cycle on container start         |

---

## API Endpoints

### Health

```
GET /api/health
```
Returns service status and database connectivity.

### Deals

| Method | Path                | Description                                      |
|--------|---------------------|--------------------------------------------------|
| GET    | `/api/deals`        | Paginated deals list with filtering and sorting   |
| GET    | `/api/deals/hot`    | Top-scored hot deals (default 20)                 |
| GET    | `/api/deals/{id}`   | Single deal with 60-day price history             |

**Query parameters** for `GET /api/deals`:

| Parameter       | Type   | Description                                     |
|-----------------|--------|-------------------------------------------------|
| `page`          | int    | Page number, 1-indexed (default 1)              |
| `per_page`      | int    | Items per page (1–200, default 50)              |
| `category`      | str    | Filter by category key (e.g. `dell-poweredge`)   |
| `group`         | str    | Filter by category group (e.g. `servers`)       |
| `classification`| str    | Filter: `hot`, `good`, `fair`                    |
| `sort`          | str    | Sort: `price`, `score`, `date`                   |

### Categories

```
GET /api/categories
```
All hardware categories with listing counts and median prices.

### Stats

```
GET /api/stats
```
Live counters: total listings, categories, hot/good deal counts, last updated.

---

## Project Structure

```
serverdeals/
├── backend/
│   ├── alerts/                 # Stage 4: Alert notifications
│   │   ├── __init__.py         #   Exports send_deal_alert, send_telegram_alert
│   │   ├── email.py            #   Async SMTP client (HTML emails)
│   │   └── telegram.py         #   Telegram Bot API (rate-limited)
│   ├── api/                    # FastAPI REST layer
│   │   ├── main.py             #   App factory, CORS, health check
│   │   ├── dependencies.py     #   DB session dependency
│   │   ├── models/
│   │   │   └── schemas.py      #   Pydantic response models
│   │   └── routes/
│   │       ├── deals.py        #   GET /api/deals, /hot, /{id}
│   │       ├── categories.py   #   GET /api/categories
│   │       └── stats.py        #   GET /api/stats
│   ├── db/
│   │   ├── database.py         #   asyncpg engine + session factory
│   │   ├── models.py           #   SQLAlchemy 2.0 ORM models
│   │   ├── seed.py             #   Category seeder (25 categories)
│   │   └── migrations/         #   Alembic migrations
│   ├── scoring/
│   │   ├── engine.py           #   Deal scoring engine (60-day median)
│   │   └── affiliate.py        #   eBay EPN affiliate URL tagging
│   ├── scraper/
│   │   ├── config.py           #   eBay API credential helpers
│   │   ├── ebay_client.py      #   eBay Finding API XML client
│   │   ├── categories.py       #   Category definitions + search queries
│   │   └── scheduler.py        #   APScheduler cron jobs
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── CategorySidebar.tsx
│   │   │   ├── DealBadge.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorState.tsx
│   │   │   ├── ListingCard.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── PriceChart.tsx
│   │   ├── pages/              # Route pages
│   │   │   ├── Home.tsx        #   Landing page with stats
│   │   │   ├── Deals.tsx       #   Deal browser with filters
│   │   │   ├── ModelPage.tsx   #   Single deal detail
│   │   │   └── SetupGuides.tsx #   Hardware setup guides
│   │   ├── lib/
│   │   │   └── api.ts          #   API client
│   │   ├── types.ts            #   TypeScript type definitions
│   │   ├── App.tsx             #   Router setup
│   │   └── index.css           #   Tailwind + dark theme
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   └── test_scoring_smoke.py   # Scoring engine smoke tests
├── .env.example                # Environment variables template
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Multi-service Compose config
└── README.md
```

---

## Stage Progress

| Stage | Name          | Status      | Description                                       |
|-------|---------------|-------------|---------------------------------------------------|
| 1     | Foundation    | ✅ Complete | eBay API client, DB schema, scraper, seed data    |
| 2     | Scoring       | ✅ Complete | Deal scoring engine, REST API, categories/stats   |
| 3     | Frontend      | ✅ Complete | React SPA, listing cards, price charts, dark theme|
| 4     | Alerts & Docs | ✅ Complete | Email alerts (SMTP), Telegram bot, README          |

---

## Alert System

ServerDeals can notify you about top deals via two channels:

### Email Alerts

```python
from backend.alerts import send_deal_alert

deals = [{"title": "Dell R740", "price": 899.99, "score": 45.2, ...}]
await send_deal_alert("you@example.com", deals)
```

- Uses **aiosmtplib** for async SMTP
- Sends **HTML emails** with deal images, prices, scores, and eBay links
- Dark-themed responsive template
- Configure via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`

### Telegram Alerts

```python
from backend.alerts import send_telegram_alert

await send_telegram_alert(chat_id=123456789, deals=deals)
```

- Uses the **Telegram Bot API** via httpx
- Formats deals with **MarkdownV2** (bold titles, emoji badges, inline links)
- **Rate-limited** to 10 messages per minute (Telegram API limit)
- Configure via `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

---

## Server Deployment

For deploying to a remote server (VPS, homelab, Proxmox VM):

```bash
# On the target server
git clone https://github.com/skylabby/serverdeals.git /opt/serverdeals
cd /opt/serverdeals

# Configure
cp .env.example .env
# Set your eBay API keys and DATABASE_URL in .env

# Start the stack
docker compose up -d --build

# Seed categories + trigger first scrape
docker compose exec backend python -m backend.db.seed
docker compose exec backend python -m backend.scraper.scheduler
```

The frontend will be available at `http://<server-ip>:8182`. For production, place it behind a reverse proxy (nginx/Caddy) with SSL.

---

## Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Links

- **GitHub**: [github.com/skylabby/serverdeals](https://github.com/skylabby/serverdeals)
- **Gitea**: [gitea.skylabshome.net/skylab/serverdeals](https://gitea.skylabshome.net/skylab/serverdeals)
- **Live demo**: [deals.skylabshome.net](https://deals.skylabshome.net) (coming soon)

---

## License

MIT
