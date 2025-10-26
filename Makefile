.PHONY: help dev prod up down build rebuild logs shell db-shell redis-shell clean migrate seed load-recipes load-recipes-prod compress-resources load-vector-store test docs lint format deploy-prod deploy-dev

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
	@echo "  make logs-worker   - Show logs from worker service"
	@echo "  make shell         - Open shell in FastAPI container"
	@echo "  make shell-fe      - Open shell in Frontend container"
	@echo "  make db-shell      - Open PostgreSQL shell"
	@echo "  make redis-shell   - Open Redis CLI"
	@echo "  make clean         - Remove all containers and volumes"
	@echo "  make migrate       - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make seed          - Seed database with initial data"
	@echo "  make load-recipes   - Load recipes from JSON file"
	@echo "  make load-recipes-prod - Load recipes from JSON file (production)"
	@echo "  make compress-resources - Compress resources file to gzip"
	@echo "  make load-vector-store   - Load recipes to vector store (Qdrant)"
	@echo "  make search        - Run similarity search test"
	@echo "  make test          - Run tests"
	@echo "  make docs          - Start MkDocs server"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make deploy-dev    - Deploy to development environment"
	@echo "  make deploy-prod   - Deploy to production environment"

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

# Open shell in FastAPI container
shell:
	docker-compose -f docker-compose.dev.yml exec fastapi bash

# Open shell in Frontend container
shell-fe:
	docker-compose -f docker-compose.dev.yml exec frontend sh

# Open PostgreSQL shell
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U $$(grep POSTGRES_USER .env.dev | cut -d '=' -f2) -d $$(grep POSTGRES_DB .env.dev | cut -d '=' -f2)

# Open Redis CLI
redis-shell:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Remove all containers and volumes
clean:
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -f

# Database migrations
migrate:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker-compose -f docker-compose.dev.yml exec fastapi uv run alembic revision --autogenerate -m "$$msg"

# Seed database
seed:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/seed_admin.py

# Load recipes (development)
load-recipes:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/load_recipe_to_db.py

# Load recipes (production)
load-recipes-prod:
	docker-compose -f docker-compose.prod.yml exec fastapi uv run python scripts/load_recipe_to_db.py

# Compress resources
compress-resources:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/compress_resources_file.py

# Load vector store
load-vector-store:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/load_recipe_to_vector_store.py

# Run similarity search test
search:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run python scripts/search_recipe_similarity.py

# Run tests
test:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run pytest

# Start documentation server
docs:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run mkdocs serve -f mkdocs.yml

# Run linting
lint:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff check .
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint

# Format code
format:
	docker-compose -f docker-compose.dev.yml exec fastapi uv run ruff format .
	docker-compose -f docker-compose.dev.yml exec frontend npm run format

# Deploy to development (placeholder)
deploy-dev:
	@echo "🚀 Deploying to development environment..."
	@echo "This would trigger the development deployment workflow"
	# Add your dev deployment commands here

# Deploy to production (triggers GitHub Actions)
deploy-prod:
	@echo "🚀 Deploying to production environment..."
	@echo "This will trigger the CD pipeline on GitHub Actions"
	git add .
	git commit -m "Deploy to production" || echo "No changes to commit"
