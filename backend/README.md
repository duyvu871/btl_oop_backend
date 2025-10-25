# Cấu trúc thư mục Backend

Dưới đây là mô tả chi tiết về cấu trúc thư mục của dự án backend, giúp bạn hiểu rõ vai trò của từng thành phần.

## Tổng quan

```
backend/
├── alembic/              # Chứa các script migration cho database
├── docs/                 # Tài liệu dự án (nếu có)
├── playground/           # Các script Python để test nhanh các endpoint
├── scripts/              # Các script tiện ích (ví dụ: tạo admin, seed data)
├── src/                  # Toàn bộ source code của ứng dụng
│   ├── ai/               # Các module liên quan đến AI (LangChain, Qdrant)
│   ├── api/              # Nơi định nghĩa các API endpoint
│   ├── core/             # Các thành phần cốt lõi của ứng dụng
│   ├── domains/          # Logic nghiệp vụ và domain model
│   ├── schemas/          # Pydantic schema để validate và serialize dữ liệu
│   ├── settings/         # Cấu hình và biến môi trường
│   └── workers/          # Các background worker (ví dụ: gửi email)
├── templates/            # Chứa các template (ví dụ: email HTML)
├── tests/                # Chứa các test case cho ứng dụng
├── alembic.ini           # File cấu hình cho Alembic
├── Dockerfile            # Dockerfile cho môi trường production
├── Dockerfile.dev        # Dockerfile cho môi trường development
├── mkdocs.yml            # File cấu hình cho MkDocs (nếu dùng)
├── pyproject.toml        # File quản lý project và dependencies (dùng với Hatch và Ruff)
└── README.md             # File bạn đang đọc
```

## Chi tiết các thư mục

### `src/`

Đây là thư mục quan trọng nhất, chứa toàn bộ mã nguồn của ứng dụng FastAPI.

#### `src/main.py`

File khởi tạo và cấu hình chính cho ứng dụng FastAPI. Đây là điểm bắt đầu (entrypoint) của ứng dụng.

#### `src/api/`

Thư mục này chứa các router và endpoint của API. Code được tổ chức theo phiên bản để dễ dàng quản lý và nâng cấp.

- **`api/v1/`**: Chứa các endpoint cho API phiên bản 1. Mỗi file trong này thường tương ứng với một nhóm chức năng (ví dụ: `auth.py`, `users.py`).

#### `src/core/`

Chứa các thành phần cốt lõi, dùng chung cho toàn bộ ứng dụng.

- **`core/database/`**: Thiết lập kết nối đến database (PostgreSQL), định nghĩa Base model cho SQLAlchemy.
- **`core/redis/`**: Thiết lập kết nối đến Redis.
- **`core/security.py`**: Xử lý các vấn đề bảo mật như hashing password, tạo và xác thực JWT.
- **`core/verification.py`**: Cung cấp service để tạo và xác thực mã OTP, dùng cho các luồng như xác thực email, reset password.
- **`core/log.py`**: Cấu hình logging cho ứng dụng.

#### `src/domains/`

Nơi triển khai logic nghiệp vụ (business logic) của ứng dụng.

- **`domains/user/`**: Chứa các model SQLAlchemy (ví dụ: `User`) và các service liên quan đến người dùng.
- **`domains/ai/`**: Các logic liên quan đến AI, ví dụ như xử lý embedding, tương tác với Qdrant.

#### `src/schemas/`

Chứa các Pydantic model (schema) được dùng để:
- Validate dữ liệu đầu vào của API request.
- Serialize dữ liệu đầu ra của API response.
- Tách biệt giữa model database và model API.

Ví dụ: `schemas/user.py` chứa các schema như `UserCreate`, `UserRead`, `UserUpdate`.

#### `src/settings/`

Quản lý cấu hình của ứng dụng thông qua các biến môi trường.

- **`settings/env.py`**: Sử dụng `pydantic-settings` để đọc các biến từ file `.env` và parse chúng vào một class Settings.

#### `src/workers/`

Chứa code cho các background worker, thường được chạy bởi một hệ thống queue như ARQ hoặc Celery.

- **`workers/send_mail.py`**: Worker để xử lý việc gửi email bất đồng bộ (ví dụ: email xác thực, email reset password).
- **`workers/helpers.py`**: Các hàm tiện ích để đưa job vào queue một cách dễ dàng từ API.

#### `src/ai/`

Tập trung các thành phần liên quan đến trí tuệ nhân tạo.

- **`ai/embeddings/`**: Module để tạo vector embedding từ văn bản.
- **`ai/llm/`**: Cấu hình và tương tác với các mô hình ngôn ngữ lớn (LLM).
- **`ai/chains/`**: Xây dựng các LangChain chain để thực hiện các tác vụ phức tạp.

### `alembic/`

Quản lý việc thay đổi schema của database (database migrations).

- **`alembic/versions/`**: Chứa các file migration được tạo tự động hoặc thủ công. Mỗi file tương ứng với một sự thay đổi trong cấu trúc database.
- Lệnh `make migrate-create` để tạo migration mới và `make migrate` để áp dụng chúng.

### `tests/`

Chứa các bài test cho ứng dụng, sử dụng `pytest`.

- Các test được viết để đảm bảo các endpoint và logic nghiệp vụ hoạt động đúng như mong đợi.
- Lệnh `make test` để chạy toàn bộ test suite.

### `templates/`

Chứa các file template, thường là HTML.

- **`templates/emails/`**: Các template email (định dạng Jinja2) được worker sử dụng để tạo nội dung email trước khi gửi.

### `scripts/`

Các script Python độc lập để thực hiện các tác vụ quản trị.

- **`scripts/create_admin.py`**: Script để tạo một tài khoản admin mới từ dòng lệnh.
- **`scripts/seed_admin.py`**: Script để tạo dữ liệu mẫu cho database.

## Các file cấu hình quan trọng

- **`pyproject.toml`**: Định nghĩa metadata của project, danh sách các dependency, và cấu hình cho các công cụ như `ruff` (linter/formatter) và `hatch` (build system). Đây là file tiêu chuẩn cho các dự án Python hiện đại.
- **`alembic.ini`**: File cấu hình cho Alembic, chỉ định đường dẫn đến database và thư mục chứa script migration.
- **`Dockerfile` và `Dockerfile.dev`**: Các chỉ dẫn để build Docker image cho môi trường production và development.
- **`docker-compose.dev.yml` và `docker-compose.prod.yml`**: Các file để định nghĩa và chạy các service của ứng dụng (API, database, Redis) bằng Docker Compose.

