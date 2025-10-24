.PHONY: help dev prod up down build rebuild logs shell db-shell redis-shell clean migrate seed test docs

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev           - Start development environment (.env.dev)"
	@echo "  make prod          - Start production environment (.env.prod)"
	@echo "  make up            - Start all services (dev)"
	@echo "  make down          - Stop all services"
	@echo "  make build         - Build all containers"
	@echo "  make rebuild       - Rebuild and restart all containers"
	@echo "  make logs          - Show logs from all services"
	@echo "  make logs-api      - Show logs from FastAPI service"
	@echo "  make logs-fe       - Show logs from Frontend service"
	@echo "  make logs-fe       - Show logs from Frontend service"
	@echo "  make shell-fe      - Open shell in Frontend container"
	@echo "  make logs-fe       - Show logs from Frontend service"
	@echo "  make shell-fe      - Open shell in Frontend container"
	@echo "  make logs-fe       - Show logs from Frontend service"
	@echo "  make shell-fe      - Open shell in Frontend container"
	@echo "  make shell         - Open shell in FastAPI container"
	@echo "  make shell-fe      - Open shell in Frontend container"
	@echo "  make db-shell      - Open PostgreSQL shell"
	@echo "  make test-fe       - Run frontend tests"
	@echo "  make redis-shell   - Open Redis CLI"
	@echo "  make clean         - Remove all containers and volumes"
	@echo "  make lint-fe       - Run frontend linting"
	@echo "  make test-fe       - Run frontend tests"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make lint-fe       - Run frontend linting"
	@echo "  make test-fe       - Run frontend tests"
	@echo "  make seed          - Seed database with initial data"
	@echo "  make test          - Run tests"
	@echo "  make lint-fe       - Run frontend linting"
	@echo "  make test-fe       - Run frontend tests"
	@echo "  make docs          - Start MkDocs server"
	@echo "  make lint          - Run linting"
	@echo "  make lint-fe       - Run frontend linting"
	@echo "  make format        - Format code"

# Development environment
dev:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Production environment
prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Start all services (dev)
up: dev

# Stop all services
down:
	docker-compose -f docker-compose.dev.yml down

# Stop production services
down-prod:
	docker-compose -f docker-compose.prod.yml down

# Build all containers
build:
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build

# Build production containers
build-prod:
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build

# Rebuild and restart
rebuild:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml --env-file .env.dev build --no-cache
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Rebuild and restart production
rebuild-prod:
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml --env-file .env.prod build --no-cache
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Show logs from all services
logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Show logs from FastAPI service only
logs-api:
	docker-compose -f docker-compose.dev.yml logs -f fastapi

# Show logs from Frontend service
logs-fe:
	docker-compose -f docker-compose.dev.yml logs -f frontend

# Show logs from worker service
logs-worker:
	docker-compose -f docker-compose.dev.yml logs -f worker_send_mail

# Show logs from PostgreSQL
logs-db:
	docker-compose -f docker-compose.dev.yml logs -f postgres

# Show logs from Redis
logs-redis:
	docker-compose -f docker-compose.dev.yml logs -f redis
# Open shell in Frontend container
shell-fe:
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh


# Show logs from Qdrant
logs-qdrant:
	docker-compose -f docker-compose.dev.yml logs -f qdrant
# Open shell in Frontend container
shell-fe:
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh


# Show production logs
logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f
# Open shell in Frontend container
shell-fe:
	docker-compose -f docker-compose.dev.yml exec frontend /bin/sh


logs-api-prod:
	docker-compose -f docker-compose.prod.yml logs -f fastapi

# Open shell in FastAPI container
shell:
	docker-compose -f docker-compose.dev.yml exec fastapi /bin/sh

# Open shell in production FastAPI container
shell-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi /bin/sh

# Open PostgreSQL shell
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d fastapi_db

# Open PostgreSQL shell in production
db-shell-prod:
	docker-compose -f docker-compose.prod.yml exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Open Redis CLI
redis-shell:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Open Redis CLI in production
redis-shell-prod:
	docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Clean up containers and volumes
clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Clean production
clean-prod:
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

# Run database migrations
migrate:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic upgrade head

# Run database migrations in production
migrate-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run alembic upgrade head

# Create new migration
migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic revision --autogenerate -m "$$msg"

# Rollback migration
migrate-rollback:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic downgrade -1

# Rollback production migration
migrate-rollback-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run alembic downgrade -1

# Seed database
seed:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python -m src.scripts.seed

# Seed database (production)
seed-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run python -m src.scripts.seed

# Create admin user from environment variables (FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD)
seed-admin:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/seed_admin.py

# Create admin user (production)
seed-admin-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run python scripts/seed_admin.py

# Run tests
test:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run pytest

# Run frontend tests
test-fe:
	cd frontend && npm test

# Run tests with coverage
test-cov:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run pytest --cov=src --cov-report=html

# Start MkDocs documentation server
docs:
	docker-compose -f docker-compose.dev.yml --profile with-docs up -d mkdocs

restart-fe:
	docker-compose -f docker-compose.dev.yml restart frontend

# Run frontend linting
lint-fe:
	cd frontend && npm run lint

# Start with nginx
nginx:
	docker-compose -f docker-compose.dev.yml --profile with-nginx --env-file .env.dev up -d

# Start with nginx (production)
nginx-prod:
	docker-compose -f docker-compose.prod.yml --profile with-nginx --env-file .env.prod up -d

# Run linting
lint:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff check .

# Format code
format:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff format .

# Restart specific service
restart-api:
	docker-compose -f docker-compose.dev.yml restart fastapi

restart-worker:
	docker-compose -f docker-compose.dev.yml restart worker_send_mail

restart-db:
	docker-compose -f docker-compose.dev.yml restart postgres

restart-redis:
	docker-compose -f docker-compose.dev.yml restart redis

restart-qdrant:
	docker-compose -f docker-compose.dev.yml restart qdrant

# Check service status
status:
	docker-compose -f docker-compose.dev.yml ps

# Check service status (production)
status-prod:
	docker-compose -f docker-compose.prod.yml ps

# Pull latest images
pull:
	docker-compose -f docker-compose.dev.yml pull

# Pull latest images (production)
pull-prod:
	docker-compose -f docker-compose.prod.yml pull

# Install dependencies
install:
	docker-compose -f docker-compose.dev.yml exec fastapi uv sync

# Install dependencies (production)
install-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv sync

# Create superuser
create-superuser:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python -m src.scripts.create_superuser

# Create superuser (production)
create-superuser-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run python -m src.scripts.create_superuser

# Deploy to production (with backup)
deploy-prod:
	@echo "Backing up database..."
	docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Pulling latest changes..."
	git pull
	@echo "Building production images..."
	docker-compose -f docker-compose.prod.yml build
	@echo "Running migrations..."
	docker-compose -f docker-compose.prod.yml up -d postgres redis
	sleep 5
	docker-compose -f docker-compose.prod.yml run --rm fastapi uv run alembic upgrade head
	@echo "Restarting services..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Deployment complete!"

# Backup database
backup-db:
	docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$$(date +%Y%m%d_%H%M%S).sql

# Backup production database
backup-db-prod:
	docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_prod_$$(date +%Y%m%d_%H%M%S).sql

# Restore database
restore-db:
	@read -p "Enter backup file path: " file; \
	docker-compose -f docker-compose.dev.yml exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < $$file

# Monitor production services
monitor-prod:
	docker stats

# Check health status
health:
	@echo "Checking services health..."
	@curl -f http://localhost:8000/health || echo "API is not healthy"

# View production environment
env-prod:
	docker-compose -f docker-compose.prod.yml config
