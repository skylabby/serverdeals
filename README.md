# ServerDeals — US eBay Replica

Self-hosted Docker service that finds the best server hardware deals on US eBay, scored against 60-day market prices. Replicates [serverdeals.at](https://serverdeals.at) functionality for the US market.

## Architecture

```
eBay US API → Scraper (Python/cron) → PostgreSQL → FastAPI → React Frontend (Nginx)
```

## Quick Start

```bash
cp .env.example .env
# Edit .env with your eBay API keys
docker compose up -d
```

## Stages

1. **Foundation** — eBay API client + DB schema + scraper cron + seed data
2. **Scoring** — Deal scoring engine + REST API
3. **Frontend** — React SPA with listing cards, price charts, dark theme
4. **Polish** — Email/Telegram alerts, production deploy, docs

## License

MIT
