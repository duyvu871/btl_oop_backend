# BTL OOP Backend

Backend cho dự án BTL OOP, xây dựng bằng FastAPI, tích hợp với LangChain, Qdrant, Postgres, Redis, và Nginx.

## Mô tả

Dự án này cung cấp một backend API sử dụng FastAPI để xử lý các yêu cầu, với các thành phần hỗ trợ:

- **FastAPI**: Framework web cho API.
- **LangChain**: Framework cho ứng dụng LLM.
- **Qdrant**: Cơ sở dữ liệu vector cho embeddings.
- **Postgres**: Cơ sở dữ liệu quan hệ.
- **Redis**: Bộ nhớ cache.
- **Nginx**: Máy chủ web và reverse proxy.
- **MkDocs**: Tài liệu dự án.

## Cài đặt

1. Clone repository:
   ```bash
   git clone <repository-url>
   cd btl_oop/BE/backend
   ```

2. Đảm bảo có Docker và Docker Compose cài đặt.

3. Tạo file `.env` trong thư mục `src/` với các biến môi trường cần thiết (xem `src/settings/env.py`).

## Chạy

Để chạy tất cả dịch vụ:

```bash
docker-compose -f ../docker-compose.dev.yml up --build
```

- FastAPI sẽ chạy trên http://localhost:8000
- MkDocs (nếu bật profile) trên http://localhost:8001
- Nginx trên http://localhost:80

Để chạy chỉ docs:

```bash
docker-compose -f ../docker-compose.dev.yml --profile with-docs up mkdocs --build
```

## Cấu trúc dự án

```
backend/
├── src/
│   ├── app/
│   ├── settings/
│   │   └── env.py
│   └── ...
├── pyproject.toml
├── Dockerfile.dev
├── README.md
└── ...
```

## API Documentation

Khi server chạy, truy cập:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Phát triển

Sử dụng uv để quản lý dependencies:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## License

MIT License. Xem LICENSE file để biết thêm chi tiết.

## Tác giả

Bùi An Du - dubuicp123@gmail.com
