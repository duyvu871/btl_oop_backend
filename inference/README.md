# OpenAI-compatible Embeddings Server (BKAI)

Một máy chủ embedding văn bản đạt chuẩn OpenAI API, sử dụng mô hình bi-encoder tiếng Việt từ BKAI Foundation Models. Hệ thống được thiết kế với kiến trúc OOP chuẩn, dễ mở rộng và bảo trì.

## 🎯 Tính năng

- **OpenAI-compatible API**: Tương thích với giao diện OpenAI Embeddings API
- **Xử lý văn bản dài**: Tự động chia nhỏ và ghép nối embeddings cho các văn bản vượt quá giới hạn
- **Hỗ trợ GPU/CPU**: Tự động phát hiện và sử dụng GPU nếu có sẵn
- **API Documentation**: Giao diện Scalar UI tương tác cho việc thử nghiệm API
- **Authentication**: Hỗ trợ Bearer token authentication
- **OOP Architecture**: Cấu trúc code sạch với separation of concerns

## 📋 Yêu cầu

- Python >= 3.10
- CUDA 11.8+ (tùy chọn, để sử dụng GPU)

## 🚀 Cài đặt

### 1. Cài đặt Dependencies

Sử dụng `uv` (khuyến nghị):

```bash
cd inference
uv sync
```

Hoặc sử dụng `pip`:

```bash
cd inference
pip install -r requirements.txt
```

### 2. Cài đặt PyTorch (nếu cần)

Cho **GPU (CUDA)**:
```bash
uv pip install torch==2.4.* torchvision==0.19.* torchaudio==2.4.*
```

Cho **CPU only**:
```bash
uv pip install torch==2.4.* --index-url https://download.pytorch.org/whl/cpu
```

## 📦 Cấu trúc Dự án

```
inference/
├── main.py              # Ứng dụng chính (3 classes: Config, EmbeddingModel, EmbeddingAPI)
├── pyproject.toml       # Cấu hình dự án và dependencies
├── README.md           # Tài liệu này
├── Dockerfile          # Docker image cho production
├── Dockerfile.dev      # Docker image cho development
└── resources/          # Tài nguyên (nếu có)
```

## 🏗️ Kiến trúc OOP

Dự án được cấu trúc theo 3 class chính:

### 1. **Config** - Quản lý Cấu hình

```python
class Config:
    """Loads configuration from environment variables"""
    - model_id: Hugging Face model identifier
    - device: 'cuda' hoặc 'cpu'
    - batch_size: Kích thước batch
    - api_key: Bearer token (tùy chọn)
    - max_length: Độ dài max của sequences
```

### 2. **EmbeddingModel** - Xử lý Model

```python
class EmbeddingModel:
    """Manages the embedding model and text encoding"""
    - chunk_by_tokens(): Chia văn bản dài thành chunks
    - embed_long_text(): Encode văn bản dài + mean pooling
    - encode_texts(): Encode danh sách văn bản
```

### 3. **EmbeddingAPI** - API Endpoints

```python
class EmbeddingAPI:
    """FastAPI application with OpenAI-compatible endpoints"""
    - GET /health: Health check
    - GET /v1/models: Danh sách models
    - POST /v1/embeddings: Tạo embeddings
    - GET /scalar: Scalar UI documentation
```

## 🔧 Cấu hình

### Biến Môi trường

| Biến | Mặc định | Mô tả |
|------|----------|-------|
| `MODEL_ID` | `bkai-foundation-models/vietnamese-bi-encoder` | Hugging Face model identifier |
| `DEVICE` | Auto-detect | `cuda` hoặc `cpu` |
| `BATCH_SIZE` | `64` | Kích thước batch encoding |
| `NORMALIZE` | `1` | Chuẩn hóa embeddings (0 hoặc 1) |
| `API_KEY` | `` (empty) | Bearer token (bỏ trống = không auth) |
| `MAX_LENGTH` | `256` | Độ dài max sequence |

### Ví dụ `.env`

```bash
MODEL_ID=bkai-foundation-models/vietnamese-bi-encoder
DEVICE=cuda
BATCH_SIZE=64
NORMALIZE=1
API_KEY=your-secret-key-here
MAX_LENGTH=256
```

## 🚀 Khởi chạy

### 1. Development

```bash
python main.py
```

Server sẽ chạy tại `http://localhost:8000`

### 2. Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Với Docker

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.prod.yml up
```

## 📚 API Endpoints

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "ok": true,
  "device": "cuda",
  "model_id": "bkai-foundation-models/vietnamese-bi-encoder"
}
```

### 2. Danh sách Models

```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your-api-key"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "bkai-foundation-models/vietnamese-bi-encoder",
      "object": "model",
      "created": 1729123456,
      "owned_by": "local"
    }
  ]
}
```

### 3. Tạo Embeddings

```bash
curl http://localhost:8000/v1/embeddings \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "bkai-foundation-models/vietnamese-bi-encoder",
    "input": ["Xin chào", "Bạn khỏe không"]
  }'
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [-0.0234, 0.1245, ...]
    },
    {
      "object": "embedding",
      "index": 1,
      "embedding": [0.0123, -0.0456, ...]
    }
  ],
  "model": "bkai-foundation-models/vietnamese-bi-encoder",
  "usage": {
    "prompt_tokens": 0,
    "total_tokens": 0
  }
}
```

### 4. Scalar UI Documentation

Truy cập giao diện tương tác: `http://localhost:8000/scalar`

Giao diện này cung cấp:
- Danh sách tất cả endpoints
- Thử nghiệm trực tiếp API
- Xem request/response examples
- Tài liệu chi tiết

## 💡 Ví dụ Sử dụng

### Python

```python
import requests

API_URL = "http://localhost:8000/v1/embeddings"
API_KEY = "your-api-key"

texts = [
    "Xin chào, đây là một câu tiếng Việt",
    "Tôi yêu lập trình",
]

response = requests.post(
    API_URL,
    json={"input": texts},
    headers={"Authorization": f"Bearer {API_KEY}"}
)

embeddings = response.json()
for i, emb_data in enumerate(embeddings["data"]):
    print(f"Text {i}: {len(emb_data['embedding'])} dimensions")
```

### JavaScript

```javascript
const API_URL = "http://localhost:8000/v1/embeddings";
const API_KEY = "your-api-key";

const texts = [
    "Xin chào, đây là một câu tiếng Việt",
    "Tôi yêu lập trình",
];

const response = await fetch(API_URL, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({ input: texts }),
});

const embeddings = await response.json();
console.log(embeddings.data);
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "input": ["Xin chào", "Tôi yêu lập trình"]
  }' | jq .
```

## 🔐 Authentication

### Với API Key

1. Đặt `API_KEY` environment variable:
   ```bash
   export API_KEY="your-secret-key"
   ```

2. Gửi token trong header:
   ```bash
   Authorization: Bearer your-secret-key
   ```

### Không có Authentication

Bỏ trống `API_KEY` environment variable (mặc định)

## ⚡ Hiệu Năng

### Xử lý Văn Bản Dài

Model có max length 256 tokens. Hệ thống tự động:
1. **Chia nhỏ** (chunk): Chia văn bản thành 200 tokens/chunk với stride 50
2. **Encode**: Encode từng chunk
3. **Ghép nối** (pooling): Dùng mean pooling để kết hợp embeddings

```python
# Ví dụ: Văn bản 1000 words
# → Tự động chia → Encode chunks → Mean pooling → 1 embedding
```

### Tối ưu hóa GPU

- Tự động sử dụng TensorFloat32 nếu sử dụng GPU
- Batch processing cho throughput cao
- CUDA pinning memory để tăng tốc

## 🧪 Thử Nghiệm

### Unit Tests

```bash
pytest tests/
```

### Performance Benchmark

```bash
python scripts/test_api_embedding.py
```

## 📊 Mô hình

**Model**: `bkai-foundation-models/vietnamese-bi-encoder`

- **Ngôn ngữ**: Tiếng Việt
- **Loại**: Bi-encoder (encoder cả 2 chiều)
- **Output dimension**: 768
- **Max sequence length**: 256 tokens

## 🐛 Troubleshooting

### 1. CUDA Out of Memory

```bash
# Giảm batch size
export BATCH_SIZE=32

# Hoặc sử dụng CPU
export DEVICE=cpu
```

### 2. Model không tải được

```bash
# Kiểm tra kết nối internet
# Hoặc pre-download model:
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')"
```

### 3. Slow response

- Tăng `BATCH_SIZE` (nếu GPU memory cho phép)
- Sử dụng GPU thay vì CPU
- Kiểm tra network latency

## 📝 Logs

Server ghi log chi tiết:

```
using device cuda
model_name: bkai-foundation-models/vietnamese-bi-encoder
```

Để xem chi tiết hơn:

```bash
# Với uvicorn
uvicorn main:app --log-level debug
```

## 🔄 Cập nhật Model

Để sử dụng model khác:

```bash
export MODEL_ID="model-name-on-huggingface"
python main.py
```

## 📦 Docker Deployment

### Dockerfile (Production)

File `Dockerfile` được tối ưu hóa cho production:

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --no-dev

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /app/.venv ./.venv

# Copy application code
COPY main.py ./

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "main.py"]
```

**Tính năng**:
- Multi-stage build: Giảm size image
- Slim base image: Nhẹ và bảo mật
- Non-root user (khuyến nghị): Thêm vào cho production

### Dockerfile.dev (Development)

File `Dockerfile.dev` cho development:

```dockerfile
FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Tính năng**:
- Auto-reload: Phát hiện thay đổi code
- Hot reload: Tiện cho development
- Full development tools

### Build Images

**Production Image**:
```bash
docker build -f Dockerfile -t bkai-embedding:latest .
docker tag bkai-embedding:latest bkai-embedding:0.1.0
```

**Development Image**:
```bash
docker build -f Dockerfile.dev -t bkai-embedding:dev .
```

### Run Container

**Production Mode**:
```bash
docker run -p 8000:8000 \
  -e DEVICE=cuda \
  -e API_KEY=your-secret-key \
  -e MODEL_ID=bkai-foundation-models/vietnamese-bi-encoder \
  --gpus all \
  --name embedding-server \
  bkai-embedding:latest
```

**Development Mode**:
```bash
docker run -it -p 8000:8000 \
  -e DEVICE=cuda \
  -e API_KEY=dev-key \
  -v $(pwd):/app \
  --gpus all \
  --name embedding-dev \
  bkai-embedding:dev
```

**CPU Only**:
```bash
docker run -p 8000:8000 \
  -e DEVICE=cpu \
  -e API_KEY=your-secret-key \
  bkai-embedding:latest
```

### Docker Compose

#### docker-compose.dev.yml

```yaml
services:
  embedding-service:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DEVICE=cuda
      - BATCH_SIZE=64
      - API_KEY=dev-key
      - MODEL_ID=bkai-foundation-models/vietnamese-bi-encoder
      - MAX_LENGTH=256
    volumes:
      - .:/app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - embedding-network

networks:
  embedding-network:
    driver: bridge
```

**Khởi chạy**:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

#### docker-compose.prod.yml

```yaml
version: '3.9'

services:
  embedding-service:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DEVICE=cuda
      - BATCH_SIZE=64
      - API_KEY=${API_KEY}
      - MODEL_ID=bkai-foundation-models/vietnamese-bi-encoder
      - MAX_LENGTH=256
      - CUDA_LAUNCH_BLOCKING=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - embedding-network
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"

networks:
  embedding-network:
    driver: bridge
```

**Khởi chạy**:
```bash
export API_KEY="your-production-key"
docker-compose -f docker-compose.prod.yml up -d
```

### Docker Commands

**View logs**:
```bash
docker logs embedding-server
docker logs -f embedding-server  # Follow logs
```

**Stop container**:
```bash
docker stop embedding-server
docker rm embedding-server
```

**Check status**:
```bash
docker ps
docker inspect embedding-server
```

**Execute command in container**:
```bash
docker exec embedding-server python -c "import torch; print(torch.cuda.is_available())"
```

### Docker Network

Nếu cần kết nối với các service khác:

```yaml
services:
  embedding-service:
    networks:
      - backend-network
  
  backend:
    networks:
      - backend-network

networks:
  backend-network:
    driver: bridge
```

Từ backend service, có thể gọi:
```python
response = requests.post("http://embedding-service:8000/v1/embeddings", ...)
```

### Docker Registry (Push to Docker Hub)

```bash
# Login
docker login

# Tag image
docker tag bkai-embedding:latest username/bkai-embedding:latest
docker tag bkai-embedding:latest username/bkai-embedding:0.1.0

# Push
docker push username/bkai-embedding:latest
docker push username/bkai-embedding:0.1.0

# Pull
docker pull username/bkai-embedding:latest
```

### Kubernetes Deployment (Optional)

Nếu sử dụng Kubernetes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: embedding-server
spec:
  containers:
  - name: embedding
    image: bkai-embedding:latest
    ports:
    - containerPort: 8000
    env:
    - name: DEVICE
      value: "cuda"
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: api-secrets
          key: embedding-key
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: "16Gi"
      requests:
        memory: "8Gi"
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 60
      periodSeconds: 30
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 20
      periodSeconds: 10
```

## 🤝 Đóng Góp

Để cải tiến:

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

MIT License

## 📧 Support

Có vấn đề? Liên hệ hoặc mở issue trên repository.

## 🗂️ Cấu Trúc Mã

```python
# main.py

# 1. Config Class
class Config:
    """Quản lý cấu hình từ environment variables"""
    
# 2. EmbeddingModel Class
class EmbeddingModel:
    """Quản lý model encoding"""
    
# 3. EmbeddingAPI Class
class EmbeddingAPI:
    """FastAPI application"""
    
# 4. EmbeddingRequest Schema
class EmbeddingRequest(BaseModel):
    """Request schema cho API"""
    
# 5. Main Entry Point
if __name__ == "__main__":
    config = Config()
    model = EmbeddingModel(config)
    api = EmbeddingAPI(config, model)
    uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

## ✨ Tính năng Tương Lai

- [ ] Caching embeddings
- [ ] Batch processing optimization
- [ ] Metrics/Monitoring
- [ ] Multi-model support
- [ ] Async processing queue
- [ ] Database integration

---

**Version**: 0.1.0  
**Last Updated**: October 2025

