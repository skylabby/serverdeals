# ──────────────────────────────────────────────────────────────────────────────
# ServerDeals — Makefile
# ──────────────────────────────────────────────────────────────────────────────

.PHONY: up down build logs db-reset seed dev-frontend dev-backend clean

# ── Compose files ────────────────────────────────────────────────────────────
COMPOSE := docker compose
COMPOSE_PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml

# ── Stack ────────────────────────────────────────────────────────────────────

up:	    ## Start the full stack (development)
	$(COMPOSE) up -d

up-prod:       ## Start the full stack (production)
	$(COMPOSE_PROD) up -d

down:	  ## Stop and remove all containers
	$(COMPOSE) down

down-prod:     ## Stop and remove all containers (production)
	$(COMPOSE_PROD) down

# ── Build ────────────────────────────────────────────────────────────────────

build:	 ## Build all Docker images
	$(COMPOSE) build

build-backend: ## Build only the backend image
	$(COMPOSE) build backend

build-frontend:## Build only the frontend image
	$(COMPOSE) build frontend

# ── Logs ─────────────────────────────────────────────────────────────────────

logs:	  ## Tail logs for all services
	$(COMPOSE) logs -f

logs-backend:  ## Tail backend logs
	$(COMPOSE) logs -f backend

logs-frontend: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

logs-db:       ## Tail PostgreSQL logs
	$(COMPOSE) logs -f postgres

# ── Database ─────────────────────────────────────────────────────────────────

db-reset:      ## Drop all data, recreate DB, run migrations + seed
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres
	@echo "Waiting for PostgreSQL to become ready …"
	@sleep 8
	$(COMPOSE) run --rm backend alembic upgrade head
	$(COMPOSE) run --rm backend python -m backend.db.seed

seed:	  ## Seed the categories table
	$(COMPOSE) run --rm backend python -m backend.db.seed

migrate:       ## Run Alembic migrations
	$(COMPOSE) run --rm backend alembic upgrade head

migrate-new:   ## Generate a new Alembic migration (usage: make migrate-new MSG="description")
	$(COMPOSE) run --rm backend alembic revision --autogenerate -m "$(MSG)"

# ── Development ──────────────────────────────────────────────────────────────

dev-backend:   ## Start only postgres + backend
	$(COMPOSE) up -d postgres backend

dev-frontend:  ## Start only postgres + backend + frontend (alias for 'up')
	$(COMPOSE) up -d

# ── Maintenance ──────────────────────────────────────────────────────────────

clean:	 ## Stop containers and remove images + volumes
	$(COMPOSE) down -v --rmi local

status:	## Show running container status
	$(COMPOSE) ps

shell-backend: ## Open a shell in the backend container
	$(COMPOSE) exec backend /bin/bash

shell-db:      ## Open psql in the PostgreSQL container
	$(COMPOSE) exec postgres psql -U serverdeals -d serverdeals

# ── Help ─────────────────────────────────────────────────────────────────────

help:	  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
