# CI/CD Setup Guide for Monorepo (Backend + Frontend)

## 🏗️ Architecture Overview

Repo này được tổ chức dạng **monorepo** với:
- **Backend**: FastAPI (Python) - Port 8000
- **Frontend**: React + Vite + Mantine - Port 3000

CI/CD được tối ưu hóa để:
- ✅ Chỉ build/test phần có thay đổi (path filtering)
- ✅ Chạy song song backend và frontend jobs
- ✅ Cache Docker layers để build nhanh hơn
- ✅ Multi-stage Docker build cho frontend tối ưu
- ✅ Zero-downtime deployment

---

## 📦 Docker Images

### Backend
- **Repository**: `adc300/btl_oop`
- **Tags**: 
  - `latest` - Latest stable build
  - `sha-{commit}` - Specific commit build

### Frontend
- **Repository**: `adc300/btl_oop_frontend`
- **Tags**:
  - `latest` - Latest stable build
  - `sha-{commit}` - Specific commit build

---

## 🔄 CI Pipeline (.github/workflows/ci.yml)

### Jobs Overview

1. **detect_changes** 
   - Phát hiện thay đổi trong `backend/` hoặc `frontend/`
   - Chỉ chạy jobs liên quan đến phần có thay đổi

2. **test_backend** (chạy nếu backend có thay đổi)
   - Setup Python 3.11 + UV
   - Install dependencies
   - Lint với Ruff
   - Run pytest

3. **test_frontend** (chạy nếu frontend có thay đổi)
   - Setup Node.js 20
   - npm ci (với cache)
   - ESLint
   - TypeScript type check
   - Build test

4. **build_and_push_backend**
   - Build Docker image từ `backend/Dockerfile`
   - Push lên Docker Hub với tags `latest` và `sha-{commit}`
   - Cache Docker layers

5. **build_and_push_frontend**
   - Multi-stage build (node -> build -> nginx)
   - Push lên Docker Hub
   - Cache Docker layers

### Optimization Features

```yaml
# Path filtering - chỉ chạy khi có thay đổi
- uses: dorny/paths-filter@v3
  with:
    filters: |
      backend:
        - 'backend/**'
      frontend:
        - 'frontend/**'

# Node.js cache
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

# Docker layer caching
- uses: docker/build-push-action@v6
  with:
    cache-from: type=registry,ref=${{ env.IMAGE_NAME }}:buildcache
    cache-to: type=registry,ref=${{ env.IMAGE_NAME }}:buildcache,mode=max
```

---

## 🚀 CD Pipeline (.github/workflows/cd-v2.yml)

### Deployment Flow

1. **Trigger**: Tự động chạy khi CI pipeline hoàn thành thành công
2. **Pull images**: Pull cả backend và frontend images từ Docker Hub
3. **Deploy sequence**:
   ```
   Stop containers
   ↓
   Start databases (postgres, redis, qdrant)
   ↓
   Wait for Postgres healthy
   ↓
   Run migrations (alembic upgrade head)
   ↓
   Start all services (backend, frontend, workers)
   ↓
   Health checks
   ```

### Services Deployed

- **fastapi**: Backend API (port 8000)
- **frontend**: React app served by Nginx (port 3000)
- **worker_send_mail**: Background job worker
- **postgres**: Database (port 5432)
- **redis**: Cache & queue (port 6379)
- **qdrant**: Vector database (port 6333)

---

## 🔐 GitHub Secrets Required

### Docker Hub
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

### SSH Deployment
- `SSH_HOST` - Server IP/hostname
- `SSH_USERNAME` - SSH username
- `SSH_PRIVATE_KEY` - SSH private key
- `SSH_PORT` - SSH port (default: 22)
- `DEPLOY_PATH` - Deployment directory path

### Application Config
- `FRONTEND_URL` - Frontend URL (e.g., https://example.com)
- `VITE_API_BASE_URL` - API URL cho frontend (e.g., https://api.example.com)

### Database
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

### Security
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 30)

### Email/SMTP
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_TLS`
- `EMAILS_FROM_EMAIL`
- `EMAILS_FROM_NAME`

### Optional
- `SENTRY_DSN` - Error tracking
- `FIRST_SUPERUSER` - Initial admin email
- `FIRST_SUPERUSER_PASSWORD` - Initial admin password

---

## 🏃 Local Development

### Backend
```bash
cd backend
uv sync --dev
uv run uvicorn src.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full Stack (Docker)
```bash
# Development
make dev
# hoặc
docker-compose -f docker-compose.dev.yml up

# Production
make prod
# hoặc
docker-compose -f docker-compose.prod.yml up
```

---

## 📊 CI/CD Flow Diagram

```
┌─────────────────┐
│  Push to main   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Detect Changes         │
│  - backend/             │
│  - frontend/            │
└──────────┬──────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐  ┌──────────┐
│ Backend │  │ Frontend │
│  Tests  │  │  Tests   │
└────┬────┘  └────┬─────┘
     │            │
     ▼            ▼
┌─────────┐  ┌──────────┐
│ Build & │  │ Build &  │
│  Push   │  │  Push    │
└────┬────┘  └────┬─────┘
     │            │
     └─────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   Deploy    │
    │ to Server   │
    └─────────────┘
```

---

## 🎯 Performance Optimizations

### 1. Path Filtering
Chỉ build phần có thay đổi:
- Commit chỉ sửa backend → Skip frontend build
- Commit chỉ sửa frontend → Skip backend build
- Tiết kiệm ~50% thời gian build

### 2. Docker Layer Caching
```dockerfile
# Backend: UV cache được tái sử dụng
# Frontend: node_modules cache được tái sử dụng
```

### 3. Multi-stage Build (Frontend)
```dockerfile
FROM node:20-alpine AS deps     # Install deps
FROM base AS builder             # Build app
FROM nginx:alpine AS runner      # Serve static files
```
Kết quả: Image size ~20MB (thay vì ~500MB với node)

### 4. Parallel Jobs
Backend và Frontend test/build chạy song song → Tiết kiệm thời gian

### 5. npm ci vs npm install
`npm ci` nhanh hơn và deterministic cho CI/CD

---

## 🔧 Troubleshooting

### Image not found
Nếu CD fails với "image not found":
```bash
# Kiểm tra images trên Docker Hub
# Đảm bảo CI đã push thành công
```

### Frontend build fails
```bash
# Check environment variables
VITE_API_BASE_URL must be set in GitHub Secrets
```

### Migration fails
```bash
# SSH vào server và check logs
docker compose -f docker-compose.prod.yml logs fastapi
```

### Service unhealthy
```bash
# Check health endpoints
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/health  # Frontend
```

---

## 📝 Best Practices

1. **Always test locally first**
   ```bash
   docker build -t test-backend ./backend
   docker build -t test-frontend ./frontend
   ```

2. **Use semantic commits**
   - `feat(frontend):` → Triggers frontend build
   - `fix(backend):` → Triggers backend build
   - `chore:` → May skip builds

3. **Monitor deployment**
   - Check GitHub Actions tab
   - Watch server logs during deployment

4. **Rollback strategy**
   ```bash
   # On server, use previous image tag
   export IMAGE_SHA=adc300/btl_oop:sha-previous_commit
   docker compose -f docker-compose.prod.yml up -d
   ```

---

## 🚦 Status Checks

### Backend Health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # API documentation
```

### Frontend Health
```bash
curl http://localhost:3000/health
```

### Database
```bash
docker compose exec postgres pg_isready
```

### Redis
```bash
docker compose exec redis redis-cli ping
```

---

## 📈 Metrics

Thời gian build ước tính:
- Backend test + build: ~3-5 phút
- Frontend test + build: ~2-4 phút
- Total CI: ~5-7 phút (parallel)
- CD deployment: ~2-3 phút

Với cache hits:
- Backend: ~2-3 phút
- Frontend: ~1-2 phút

