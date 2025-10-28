# CUDA 12.1 + cuDNN runtime
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface \
    UV_LINK_MODE=copy \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    # tối ưu alloc GPU tránh phân mảnh

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-dev \
    git ca-certificates curl wget build-essential && \
    rm -rf /var/lib/apt/lists/*

# ---- Install uv (Astral) ----
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# ---- Install Python deps via uv ----
# 1) Torch/cu121 (dùng index PyTorch chính thức)
ARG TORCH_INDEX_URL="https://download.pytorch.org/whl/cu121"
RUN uv pip install --system --index-url ${TORCH_INDEX_URL} \
    torch torchvision torchaudio

# 2) Các thư viện còn lại
RUN uv pip install --system \
    fastapi uvicorn[standard] sentence-transformers transformers tokenizers \
    numpy accelerate

# ---- Copy app ----
# (Đảm bảo có app.py trong context)
COPY app.py /app/app.py

# ---- Runtime env an toàn cho attention (tránh SDPA/flash) ----
ENV CUDA_LAUNCH_BLOCKING=0

EXPOSE 8000

# ---- Start (Uvicorn) ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
