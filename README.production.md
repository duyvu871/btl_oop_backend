# Production Deployment Guide

Hướng dẫn triển khai ứng dụng FastAPI lên môi trường production.

## 📋 Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Chuẩn bị môi trường](#chuẩn-bị-môi-trường)
- [Cấu hình](#cấu-hình)
- [Deployment](#deployment)
- [Monitoring và Maintenance](#monitoring-và-maintenance)
- [Backup và Restore](#backup-và-restore)
- [Troubleshooting](#troubleshooting)

## 🖥️ Yêu cầu hệ thống

### Phần cứng tối thiểu
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB SSD
- **Network**: Stable internet connection

### Phần cứng khuyến nghị
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD
- **Network**: High-speed connection

### Phần mềm
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Make (optional, nhưng khuyến nghị)

## 🔧 Chuẩn bị môi trường

### 1. Cài đặt Docker và Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Cài Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Clone repository

```bash
git clone <your-repo-url>
cd BE
```

### 3. Tạo file .env.prod

```bash
cp .env.example .env.prod
```

## ⚙️ Cấu hình

### File .env.prod

Chỉnh sửa file `.env.prod` với các thông tin production:

```env
# App Settings
DEBUG=False
FRONTEND_URL=https://your-domain.com

# Database
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_SERVER=postgres
POSTGRES_DB=prod_db

# Redis
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Qdrant
QDRANT_URL=http://qdrant:6333

# Security
SECRET_KEY=<generate-strong-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (SMTP)
SMTP_TLS=True
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password>
EMAILS_FROM_EMAIL=noreply@your-domain.com
EMAILS_FROM_NAME=Your App Name

# Sentry (Optional - for error tracking)
SENTRY_DSN=https://your-sentry-dsn

# First Superuser
FIRST_SUPERUSER=admin@your-domain.com
FIRST_SUPERUSER_PASSWORD=<strong-admin-password>

# ARQ Worker
ARQ_QUEUE_NAME=arq:queue
ARQ_MAX_JOBS=10
ARQ_JOB_TIMEOUT=300
```

### Tạo SECRET_KEY mạnh

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Cấu hình Nginx (Optional - cho HTTPS)

Nếu bạn muốn sử dụng HTTPS, cần cấu hình SSL certificate. Có thể sử dụng Let's Encrypt:

```bash
# Cài Certbot
sudo apt install certbot

# Tạo SSL certificate
sudo certbot certonly --standalone -d your-domain.com
```

Sau đó uncomment phần HTTPS trong `nginx/nginx.conf` và cập nhật đường dẫn certificate.

## 🚀 Deployment

### Option 1: Sử dụng Makefile (Khuyến nghị)

```bash
# Build và start production
make build-prod
make prod

# Chạy migrations
make migrate-prod

# Tạo superuser
make create-superuser-prod

# Xem logs
make logs-prod
```

### Option 2: Sử dụng Docker Compose trực tiếp

```bash
# Build images
docker-compose -f docker-compose.prod.yml --env-file .env.prod build

# Start services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec fastapi uv run alembic upgrade head

# Create superuser
docker-compose -f docker-compose.prod.yml exec fastapi uv run python -m src.scripts.create_superuser
```

### Kiểm tra deployment

```bash
# Kiểm tra status các services
make status-prod

# Kiểm tra health
curl http://localhost/health

# Hoặc nếu có domain
curl https://your-domain.com/health
```

## 📊 Monitoring và Maintenance

### Xem logs

```bash
# Tất cả services
make logs-prod

# Chỉ FastAPI
make logs-api-prod

# Chỉ Worker
docker-compose -f docker-compose.prod.yml logs -f worker_send_mail
```

### Monitor resource usage

```bash
# Real-time stats
make monitor-prod

# Hoặc
docker stats
```

### Restart services

```bash
# Restart tất cả
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart fastapi
docker-compose -f docker-compose.prod.yml restart worker_send_mail
```

### Update application

```bash
# Sử dụng make deploy-prod (tự động backup)
make deploy-prod

# Hoặc manual
git pull
make build-prod
make migrate-prod
docker-compose -f docker-compose.prod.yml up -d
```

## 💾 Backup và Restore

### Backup database

```bash
# Auto backup with timestamp
make backup-db-prod

# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U prod_user prod_db > backup.sql
```

### Restore database

```bash
# Stop services
make down-prod

# Start only postgres
docker-compose -f docker-compose.prod.yml up -d postgres

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U prod_user -d prod_db < backup.sql

# Start all services
make prod
```

### Backup volumes

```bash
# Backup all volumes
docker run --rm -v btl_oop_be_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v btl_oop_be_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
docker run --rm -v btl_oop_be_qdrant_data:/data -v $(pwd):/backup alpine tar czf /backup/qdrant_backup.tar.gz -C /data .
```

## 🔒 Security Best Practices

### 1. Sử dụng strong passwords
- Database password: Ít nhất 16 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt
- SECRET_KEY: Sử dụng `secrets.token_urlsafe(32)` để generate
- Admin password: Strong và unique

### 2. Firewall configuration

```bash
# Ubuntu/Debian với UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 3. Regular updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Docker images
make pull-prod
make rebuild-prod
```

### 4. Disable debug endpoints in production

Trong `nginx/nginx.conf`, comment out hoặc xóa các location `/docs` và `/redoc` nếu không cần.

### 5. Rate limiting

Nginx configuration đã bao gồm rate limiting. Điều chỉnh theo nhu cầu trong `nginx/nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

## 🐛 Troubleshooting

### Container không start

```bash
# Xem logs chi tiết
docker-compose -f docker-compose.prod.yml logs

# Kiểm tra container status
docker-compose -f docker-compose.prod.yml ps

# Rebuild từ đầu
make clean-prod
make rebuild-prod
```

### Database connection issues

```bash
# Kiểm tra postgres health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Kiểm tra credentials
docker-compose -f docker-compose.prod.yml exec postgres psql -U prod_user -d prod_db -c "SELECT 1;"
```

### Memory issues

```bash
# Kiểm tra memory usage
docker stats

# Tăng memory limits trong docker-compose.prod.yml nếu cần
```

### Permission issues

```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Rebuild với --no-cache
make rebuild-prod
```

## 📈 Scaling

### Horizontal scaling với Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml myapp

# Scale service
docker service scale myapp_fastapi=3
```

### Với Kubernetes

Cần tạo Kubernetes manifests riêng. Tham khảo repository deployment-examples.

## 📞 Support

- **Documentation**: `/docs` endpoint (nếu enabled)
- **Issues**: GitHub Issues
- **Email**: support@your-domain.com

## 📝 Checklist trước khi deploy

- [ ] .env.prod đã được cấu hình đầy đủ
- [ ] SECRET_KEY đã được generate mới (không dùng default)
- [ ] Database password đã được thay đổi
- [ ] SMTP settings đã được test
- [ ] Firewall đã được cấu hình
- [ ] SSL certificate đã được setup (nếu dùng HTTPS)
- [ ] Backup strategy đã được thiết lập
- [ ] Monitoring đã được setup (Sentry, etc.)
- [ ] Domain DNS đã được cấu hình đúng
- [ ] Health check endpoint hoạt động

---

**Good luck với production deployment!** 🚀

