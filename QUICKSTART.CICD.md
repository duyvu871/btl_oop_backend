# Quick Start - Frontend CI/CD

## 🚀 Quick Setup

### 1. Thêm GitHub Secrets

Vào **Settings → Secrets and variables → Actions** và thêm:

#### Docker Hub (Bắt buộc)
```
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token
```

#### Frontend Specific
```
VITE_API_BASE_URL=https://api.yourdomain.com
```

### 2. Tạo Docker Hub Repositories

Tạo 2 repositories trên Docker Hub:
- `adc300/btl_oop` (Backend - có sẵn)
- `adc300/btl_oop_frontend` (Frontend - mới)

### 3. Test Local Build

```bash
# Test frontend Docker build
cd frontend
docker build -t test-frontend .

# Test với environment variable
docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t test-frontend .

# Run local
docker run -p 3000:80 test-frontend
```

### 4. Push Code

```bash
git add .
git commit -m "feat(frontend): setup CI/CD"
git push origin main
```

CI sẽ tự động:
- ✅ Detect changes (backend hoặc frontend)
- ✅ Run tests (ESLint, TypeScript, Build)
- ✅ Build Docker image
- ✅ Push lên Docker Hub
- ✅ Deploy lên server (nếu có CD setup)

---

## 📊 CI/CD Status

### Check Progress
1. Vào **Actions** tab trên GitHub
2. Xem workflow "CI Pipeline"
3. Nếu thành công → "CD Pipeline" sẽ tự động chạy

### Expected Timeline
- Frontend CI: **2-4 phút**
- Backend CI: **3-5 phút** 
- Deploy CD: **2-3 phút**
- **Total: ~7-10 phút** (lần đầu, sau đó nhanh hơn nhờ cache)

---

## 🎯 What You Get

### Development
```bash
make dev          # Start cả backend + frontend
make logs-fe      # Xem logs frontend
make shell-fe     # Vào container frontend
make lint-fe      # Lint frontend code
make test-fe      # Test frontend
```

### Production Services
- **Frontend**: http://server:3000 (Nginx serving React)
- **Backend**: http://server:8000 (FastAPI)
- **Docs**: http://server:8000/docs

### Optimization Features
✅ **Path filtering** - Chỉ build phần có thay đổi  
✅ **Docker cache** - Build nhanh hơn 50%  
✅ **Multi-stage build** - Image size chỉ ~20MB  
✅ **Parallel jobs** - Backend + Frontend chạy song song  
✅ **Zero-downtime** - Rolling deployment  

---

## 🔍 Verify Deployment

### Check Services
```bash
# On server
docker compose -f docker-compose.prod.yml ps

# Should see:
# - fastapi (running)
# - frontend (running)
# - worker_send_mail (running)
# - postgres (running)
# - redis (running)
# - qdrant (running)
```

### Health Checks
```bash
curl http://localhost:8000/health  # Backend
curl http://localhost:3000/health  # Frontend
```

---

## 📝 Common Tasks

### Update Frontend Code
```bash
# Edit code in frontend/src/
git add frontend/
git commit -m "feat(frontend): new feature"
git push

# CI sẽ:
# 1. Skip backend tests (no changes)
# 2. Run frontend tests
# 3. Build & push frontend image
# 4. Deploy
```

### Update Backend Code
```bash
git add backend/
git commit -m "fix(backend): bug fix"
git push

# CI sẽ:
# 1. Run backend tests
# 2. Skip frontend tests (no changes)
# 3. Build & push backend image
# 4. Deploy
```

### Update Both
```bash
git add .
git commit -m "feat: full stack feature"
git push

# CI sẽ:
# 1. Run cả backend và frontend tests (parallel)
# 2. Build cả 2 images (parallel)
# 3. Deploy cả 2
```

---

## 🐛 Troubleshooting

### CI Fails on Frontend Build
```bash
# Check locally first
cd frontend
npm ci
npm run lint
npm run build
```

### Image Not Found on Deploy
```bash
# Wait 1-2 minutes cho Docker Hub
# Hoặc check Docker Hub dashboard
```

### Frontend Shows Wrong API URL
```bash
# Check GitHub Secret: VITE_API_BASE_URL
# Rebuild image sau khi update secret
```

---

## 📚 Full Documentation

Xem **README.CICD.md** cho chi tiết đầy đủ về:
- Architecture overview
- Deployment flow
- All GitHub Secrets
- Performance optimizations
- Advanced troubleshooting

