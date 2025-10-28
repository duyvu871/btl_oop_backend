from __future__ import annotations

import logging
import os
import time
import uuid
from typing import List, Union

import torch
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

# ====== Config ======
os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "1")
# os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
MODEL_ID = os.getenv("MODEL_ID", "bkai-foundation-models/vietnamese-bi-encoder")
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))
NORMALIZE = os.getenv("NORMALIZE", "1") == "1"
API_KEY = os.getenv("API_KEY", "")
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "256"))

# ====== App ======
app = FastAPI(title="OpenAI-compatible Embeddings (BKAI)")
print("app oke")
print(f"device {DEVICE}")
# ====== Model load ======
if torch.cuda.is_available():

    torch.set_float32_matmul_precision("high")
    try:
        torch.backends.cudnn.conv.fp32_precision = "tf32"
    except Exception:
        pass

model: SentenceTransformer = SentenceTransformer(
    MODEL_ID,
    device=DEVICE,
)
model.max_seq_length = MAX_LENGTH

tok = model._first_module().tokenizer


# ====== Schemas ======
class EmbeddingRequest(BaseModel):
    model: str | None = None
    input: Union[str, List[str]]


def _ensure_list(x: Union[str, List[str]]) -> List[str]:
    return [x] if isinstance(x, str) else list(x)


def _check_api_key(req: Request):
    if API_KEY:
        auth = req.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        key = auth.split(" ", 1)[1].strip()
        if key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")


def chunk_by_tokens(text, max_tokens=200, stride=50):
    ids = tok(text, add_special_tokens=True, return_attention_mask=False)["input_ids"]
    chunks = []
    start = 0
    while start < len(ids):
        end = min(start + max_tokens, len(ids))
        chunk_ids = ids[start:end]
        chunk = tok.decode(chunk_ids, skip_special_tokens=True)
        chunks.append(chunk)
        if end == len(ids): break
        start += (max_tokens - stride)
    return chunks or [" "]


def embed_long_text(text):
    parts = chunk_by_tokens(text, max_tokens=200, stride=50)
    vecs = model.encode(parts, batch_size=BATCH_SIZE, device=DEVICE, convert_to_numpy=True, normalize_embeddings=True,
                        show_progress_bar=False)
    return vecs.mean(axis=0)  # mean pooling


@app.get("/health")
async def health():
    ok = torch.cuda.is_available() if DEVICE.startswith("cuda") else True
    return {"ok": ok, "device": DEVICE, "model_id": MODEL_ID}


@app.get("/v1/models")
async def list_models(request: Request):
    _check_api_key(request)
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            }
        ],
    }


@app.post("/v1/embeddings")
async def create_embeddings(req: Request, body: EmbeddingRequest):
    _check_api_key(req)
    inputs = _ensure_list(body.input)
    model_name = body.model or MODEL_ID
    print(f"model_name: {model_name}")
    # Batch encode
    with torch.no_grad():
        try:
            vectors = []
            for s in inputs:
                if len(tok.encode(s)) > 256:
                    v = embed_long_text(s)
                    vectors.append(v)
                else:
                    v = model.encode([s], batch_size=8, convert_to_numpy=True,
                                     normalize_embeddings=True, show_progress_bar=False)[0]
                    vectors.append(v)
        except Exception as e:

            raise HTTPException(status_code=502, detail=f"Embedding failed: {type(e).__name__}")

    data = []
    for i, vec in enumerate(vectors):
        data.append({
            "object": "embedding",
            "index": i,
            "embedding": vec.astype(float).tolist(),
        })

    resp = {
        "object": "list",
        "data": data,
        "model": model_name,
        "usage": {
            "prompt_tokens": 0,
            "total_tokens": 0
        }
    }
    return JSONResponse(resp)