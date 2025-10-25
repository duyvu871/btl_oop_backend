# Backend — Hướng dẫn dùng Makefile

Đây là hướng dẫn cách dùng `Makefile` để chạy và quản lý backend trong project này.

Mục đích chính: Giúp bạn chạy Docker (dev hoặc production), migrate database, test, build docs... tất cả chỉ bằng vài lệnh `make` đơn giản.

---

## Yêu cầu trước khi bắt đầu

- Đã cài Docker & Docker Compose trên máy
- Có sẵn file môi trường `.env.dev` (cho dev) và `.env.prod` (cho production). Makefile sẽ dùng `--env-file` để load các biến môi trường từ đây

File Makefile nằm ở root của repo (`./Makefile`). Các lệnh `make` sẽ tự động chọn file compose phù hợp (`docker-compose.dev.yml` hoặc `docker-compose.yml`) tùy vào môi trường.

---

## Các lệnh hay dùng

### Khởi động services

Chạy dev (chạy ngầm):
```bash
make dev
```

Tương đương với:
```bash
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

Chạy production:
```bash
make prod
```

Tương đương với:
```bash
docker-compose -f docker-compose.yml --env-file .env.prod up -d
```

### Dừng và xem logs

Dừng tất cả services (dev):
```bash
make down
```

Xem logs của toàn bộ stack:
```bash
make logs
```

Xem logs riêng FastAPI:
```bash
make logs-api
```

### Vào trong container

Mở shell trong container FastAPI (dev):
```bash
make shell
```

Mở psql để truy cập PostgreSQL:
```bash
make db-shell
```

Mở redis-cli:
```bash
make redis-shell
```

### Build và rebuild

Rebuild containers từ đầu (dev):
```bash
make rebuild
```

Build images:
```bash
make build
```

### Database migrations

Chạy migrations (upgrade to head):
```bash
make migrate
```

Lệnh này gọi `uv run alembic upgrade head` trong container.

Tạo migration mới (autogenerate):
```bash
make migrate-create
```

Lệnh sẽ hỏi bạn nhập message cho migration, sau đó chạy `alembic revision --autogenerate -m "message"`.

### ARQ Email Worker

Chạy ARQ worker để xử lý email queue (local):
```bash
arq src.workers.send_mail.WorkerSettings
```

Hoặc trong Docker container:
```bash
make shell
# Trong container:
arq src.workers.send_mail.WorkerSettings
```

Queue email từ code (ví dụ trong API endpoint):
```python
from src.workers.helpers import queue_verification_email

# Queue use_cases email
job_id = await queue_verification_email(
    email="user@example.com",
    verification_token="token_abc123"
)
```

Các loại email hỗ trợ:
- **Verification email**: `queue_verification_email(email, verification_token)`
- **Password reset email**: `queue_password_reset_email(email, reset_token)`
- **Custom email**: `queue_custom_email(email, subject, html_content, text_content)`

Xem ví dụ chi tiết tại: `backend/src/workers/example_usage.py`

### Khác

Seed dữ liệu:
```bash
make seed
```

Chạy test:
```bash
make test
```

Khởi động mkdocs server (xem docs):
```bash
make docs
```

Cài đặt dependencies:
```bash
make install
```

**Lưu ý:** Lệnh này chạy `docker-compose ... exec fastapi uv sync`. Nếu image của bạn không có CLI `uv` thì sẽ báo lỗi. Xem phần Troubleshooting bên dưới để biết c��ch fix.

---

## Về file môi trường (.env)

Makefile mặc định dùng `.env.dev` và `.env.prod` ở thư mục root. Nếu muốn dùng file khác (ví dụ `.env.local`), bạn có thể:

- Sửa Makefile
- Hoặc tự gọi docker-compose trực tiếp:
  ```bash
  docker-compose -f docker-compose.dev.yml --env-file .env.local up -d
  ```

Trong file `.env.{ENV}` thường có các biến như:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `API_URL`
- `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- `JWT_SECRET`, `JWT_ALGORITHM`
- `QDRANT_HOST`, `QDRANT_PORT`
- `ARQ_QUEUE_NAME`, `ARQ_MAX_JOBS`, `ARQ_JOB_TIMEOUT`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TLS`
- `EMAILS_FROM_EMAIL`, `EMAILS_FROM_NAME`
- `FRONTEND_URL`
- `SENTRY_DSN` (nếu dùng Sentry)

---

## Verification Service

### Tổng quan

Verification Service giúp bạn tạo và xác thực mã OTP (One-Time Password) cho các luồng như:
- Email verification
- Password reset
- 2FA authentication
- Custom verification flows

### Tính năng chính

- ✅ Generate mã số ngẫu nhiên (cryptographically secure)
- ✅ Hash mã với Argon2 trước khi lưu Redis
- ✅ Rate limiting để chống spam
- ✅ Attempt tracking để ch���ng brute force
- ✅ One-time use (tự động xóa sau khi verify thành công)
- ✅ TTL tự động hết hạn
- ✅ Pipeline Redis cho atomic operations

### Cách sử dụng

**1. Khởi tạo service:**
```python
from redis.asyncio import from_url
from src.core.verification import VerificationService, VerificationOptions

redis = await from_url(settings.REDIS_URL, decode_responses=False)
service = VerificationService(redis)
```

**2. Generate verification code:**
```python
# Tạo mã xác thực email
result = await service.generate(
    VerificationOptions(
        namespace="email-verify",
        subject="user@example.com",
        ttl_sec=600,  # 10 phút
        max_attempts=5,  # Tối đa 5 lần thử
        length=6,  # Mã 6 chữ số
        rate_limit_window_sec=60,  # Cửa sổ 60 giây
        rate_limit_max=3  # Tối đa 3 mã trong 60 giây
    )
)

print(f"Mã: {result.code}")  # Gửi mã này qua email
print(f"Hết hạn lúc: {result.expires_at}")
```

**3. Verify code (không xóa):**
```python
valid = await service.verify(
    VerificationOptions(namespace="email-verify", subject="user@example.com"),
    code="123456"
)

if valid:
    print("Mã hợp lệ!")
else:
    # Số lần thử còn lại tự động giảm
    attempts = await service.get_remaining_attempts("email-verify", "user@example.com")
    print(f"Mã không đúng. Còn {attempts} lần thử.")
```

**4. Verify và consume (one-time use):**
```python
valid = await service.verify_and_consume(
    VerificationOptions(namespace="email-verify", subject="user@example.com"),
    code="123456"
)

if valid:
    # Mã đúng và đã bị xóa, không thể dùng lại
    print("Xác thực thành công!")
```

**5. Sử dụng helper functions (tích hợp với email worker):**
```python
from src.core.verification_helpers import (
    generate_and_send_email_verification,
    verify_email_code
)

# Tạo mã và gửi email tự động
job_id = await generate_and_send_email_verification(
    verification_service=service,
    email="user@example.com",
    ttl_sec=600
)

# Sau khi user nhập mã từ email
valid = await verify_email_code(
    verification_service=service,
    email="user@example.com",
    code=user_input_code
)
```

**6. Password reset flow:**
```python
from src.core.verification_helpers import (
    generate_and_send_password_reset,
    verify_password_reset_code
)

# Gửi email reset password
job_id = await generate_and_send_password_reset(
    verification_service=service,
    email="user@example.com",
    ttl_sec=1800  # 30 phút
)

# Verify reset code
valid = await verify_password_reset_code(
    verification_service=service,
    email="user@example.com",
    code=reset_code
)

if valid:
    # Cho phép user đặt lại password
    pass
```

### Sử dụng như FastAPI Dependency

```python
from fastapi import Depends
from src.core.verification import get_verification_service, VerificationService

@app.post("/auth/send-verification")
async def send_verification(
    email: EmailStr,
    service: VerificationService = Depends(get_verification_service)
):
    try:
        result = await service.generate(
            VerificationOptions(
                namespace="email-verify",
                subject=email
            )
        )
        # Queue email to send the code
        await queue_verification_email(email, result.code)
        return {"message": "Verification code sent"}
    except Exception as e:
        if "Too many requests" in str(e):
            raise HTTPException(status_code=429, detail=str(e))
        raise

@app.post("/auth/verify-email")
async def verify_email(
    email: EmailStr,
    code: str,
    service: VerificationService = Depends(get_verification_service)
):
    valid = await service.verify_and_consume(
        VerificationOptions(namespace="email-verify", subject=email),
        code=code
    )
    
    if not valid:
        attempts = await service.get_remaining_attempts("email-verify", email)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid code. {attempts} attempts remaining."
        )
    
    # Update user verified status in database
    return {"message": "Email verified successfully"}
```

### Chạy examples

```bash
cd backend
python -m src.core.verification_example
```

### Redis Keys Structure

Verification Service lưu trữ dữ liệu trong Redis với các keys:

- `verify:{namespace}:{subject}:code` - Hash của mã (Argon2)
- `verify:{namespace}:{subject}:attempts` - Số lần thử còn lại
- `verify:{namespace}:{subject}:rate` - Counter cho rate limiting

Ví dụ:
```
verify:email-verify:user@example.com:code = "$argon2id$v=19$m=65536..."
verify:email-verify:user@example.com:attempts = "5"
verify:email-verify:user@example.com:rate = "1"
```

### Rate Limiting

Rate limiting hoạt động như sau:

1. **Mỗi lần generate code**, counter tăng lên
2. **Counter tự động expire** sau `rate_limit_window_sec`
3. **Nếu counter > rate_limit_max**, throw exception "Too many requests"

Ví dụ với `rate_limit_window_sec=60` và `rate_limit_max=3`:
- User có thể generate tối đa 3 mã trong 60 giây
- Sau 60 giây, counter reset về 0

### Security Best Practices

✅ **Dùng namespace khác nhau** cho các mục đích khác nhau:
- `email-verify` - Xác thực email
- `password-reset` - Reset password
- `2fa` - Two-factor authentication

✅ **TTL phù hợp**:
- Email verification: 10-15 phút
- Password reset: 30-60 phút
- 2FA: 2-5 phút

✅ **Max attempts**:
- Email verification: 5 lần
- Password reset: 3 lần (nghiêm ngặt hơn)
- 2FA: 3 lần

✅ **Rate limiting**:
- Ngăn spam generate codes
- Chống DoS attacks

---

## Test nhanh endpoint register

Nếu muốn test endpoint register, bạn có thể dùng script Python:

```bash
python backend/playground/test_register.py --env-file .env.dev --email you@example.com --password secret
```

Hoặc dùng curl:

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}'
```

---

## Troubleshooting

### Lỗi "uv: not found"

Đây là lỗi phổ biến khi build image hoặc chạy `make install`.

**Nguyên nhân:** Makefile đang gọi `uv sync` hoặc `uv run ...` nhưng image Docker không có CLI `uv`.

**Cách fix:**

**Option 1:** Thêm `uv` vào Dockerfile

Thêm dòng này vào Dockerfile trước khi gọi `uv sync`:
```dockerfile
RUN pip install uv
```

**Option 2:** Bỏ `uv` hoàn toàn

Thay các lệnh `uv sync` / `uv run` trong Makefile và Dockerfile bằng lệnh thông thường:
- `uv sync` → `pip install -r requirements.txt`
- `uv run alembic ...` → `alembic ...` hoặc `python -m alembic ...`
- `uv run pytest` → `pytest`

Cách này đơn giản hơn và không phụ thuộc vào tool bên ngoài.

### Lỗi import khi uvicorn không tìm thấy app

Kiểm tra biến môi trường `UV_APP` hoặc command trong Dockerfile/docker-compose. Đảm bảo đúng module path, ví dụ `src.main:app`.

### ARQ Worker không chạy

**Lỗi:** `ModuleNotFoundError` hoặc worker không nhận jobs.

**Cách fix:**
1. Đảm bảo Redis đang chạy: `docker ps | grep redis`
2. Kiểm tra `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` trong `.env`
3. Chạy worker trong đúng thư mục: `cd backend && arq src.workers.send_mail.WorkerSettings`
4. Xem logs của worker để debug

**Kiểm tra Redis connection:**
```bash
redis-cli -h localhost -p 6379 ping
# Nên trả về: PONG
```

### Debug thủ công

Nếu muốn vào container và chạy lệnh tự do:

```bash
make shell
# Trong container:
python -m pip install -r requirements.txt
alembic upgrade head
arq src.workers.send_mail.WorkerSettings
```

---

## Tổng kết

- Dùng `make dev` hoặc `make prod` để khởi động nhanh
- Sửa `--env-file` nếu muốn dùng file `.env` khác
- Gặp lỗi "uv: not found" thì fix Dockerfile hoặc thay lệnh `uv` bằng lệnh pip/alembic trực tiếp
- Chạy ARQ worker riêng để xử lý email queue: `arq src.workers.send_mail.WorkerSettings`

[docs](backend/docs)
