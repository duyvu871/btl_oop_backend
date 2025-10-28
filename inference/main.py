from __future__ import annotations

import os
import time
from typing import List, Union

import torch
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from scalar_fastapi import Theme, get_scalar_api_reference


class Config:
    def __init__(self):
        os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "1")
        self.model_id = os.getenv("MODEL_ID", "bkai-foundation-models/vietnamese-bi-encoder")
        self.device = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = int(os.getenv("BATCH_SIZE", "64"))
        self.normalize = os.getenv("NORMALIZE", "1") == "1"
        self.api_key = os.getenv("API_KEY", "")
        self.max_length = int(os.getenv("MAX_LENGTH", "256"))


class EmbeddingModel:
    def __init__(self, conf: Config):
        self.config = conf
        self.device = conf.device
        self.batch_size = conf.batch_size
        self.max_length = conf.max_length

        if torch.cuda.is_available():
            torch.set_float32_matmul_precision("high")
            try:
                torch.backends.cudnn.conv.fp32_precision = "tf32"
            except Exception:
                pass

        self.model: SentenceTransformer = SentenceTransformer(
            conf.model_id,
            device=self.device,
        )
        self.model.max_seq_length = self.max_length
        self.tokenizer = self.model.tokenizer

    def chunk_by_tokens(self, text: str, max_tokens: int = 200, stride: int = 50) -> List[str]:
        ids = self.tokenizer(text, add_special_tokens=True, return_attention_mask=False)["input_ids"]
        chunks = []
        start = 0
        while start < len(ids):
            end = min(start + max_tokens, len(ids))
            chunk_ids = ids[start:end]
            chunk = self.tokenizer.decode(chunk_ids, skip_special_tokens=True)
            chunks.append(chunk)
            if end == len(ids):
                break
            start += (max_tokens - stride)
        return chunks or [" "]

    def embed_long_text(self, text: str) -> np.ndarray:
        parts = self.chunk_by_tokens(text, max_tokens=200, stride=50)
        vecs = self.model.encode(
            parts,
            batch_size=self.batch_size,
            device=self.device,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return vecs.mean(axis=0)  # mean pooling

    def encode_texts(self, inputs: List[str]) -> List[np.ndarray]:
        vectors = []
        for s in inputs:
            if len(self.tokenizer.encode(s)) > 256:
                v = self.embed_long_text(s)
            else:
                v = self.model.encode(
                    [s],
                    batch_size=8,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )[0]
            vectors.append(v)
        return vectors


class EmbeddingAPI:
    def __init__(self, conf: Config, emodel: EmbeddingModel):
        self.config = conf
        self.model = emodel
        self.app = FastAPI(
            title="OpenAI-compatible Embeddings (BKAI)",
            version="1.0.0",
            openapi_url="/openapi.json",
        )
        print(f"using device {self.config.device}")

        # Add routes
        self.app.add_api_route("/health", self.health, methods=["GET"])
        self.app.add_api_route("/v1/models", self.list_models, methods=["GET"])
        self.app.add_api_route("/v1/embeddings", self.create_embeddings, methods=["POST"])
        self.app.add_api_route("/scalar", self.scalar_ui, methods=["GET"], include_in_schema=False)

    def _check_api_key(self, req: Request):
        if self.config.api_key:
            auth = req.headers.get("authorization", "")
            if not auth.lower().startswith("bearer "):
                raise HTTPException(status_code=401, detail="Missing bearer token")
            key = auth.split(" ", 1)[1].strip()
            if key != self.config.api_key:
                raise HTTPException(status_code=403, detail="Invalid API key")

    async def scalar_ui(self):
        """Scalar API documentation UI endpoint.

        Returns:
            Scalar API reference HTML interface.
        """
        return get_scalar_api_reference(
            openapi_url=self.app.openapi_url,
            title=self.app.title + " - Scalar UI",
            theme=Theme.BLUE_PLANET,
        )

    async def health(self):
        ok = torch.cuda.is_available() if self.config.device.startswith("cuda") else True
        return {"ok": ok, "device": self.config.device, "model_id": self.config.model_id}

    async def list_models(self, request: Request):
        self._check_api_key(request)
        return {
            "object": "list",
            "data": [
                {
                    "id": self.config.model_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local",
                }
            ],
        }

    async def create_embeddings(self, req: Request, body: EmbeddingRequest):
        self._check_api_key(req)
        inputs = self._ensure_list(body.input)
        model_name = body.model or self.config.model_id
        print(f"model_name: {model_name}")

        with torch.no_grad():
            try:
                vectors = self.model.encode_texts(inputs)
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

    @staticmethod
    def _ensure_list(x: Union[str, List[str]]) -> List[str]:
        return [x] if isinstance(x, str) else list(x)


# ====== Schemas ======
class EmbeddingRequest(BaseModel):
    model: str | None = None
    input: Union[str, List[str]]


# ====== Main ======
if __name__ == "__main__":
    config = Config()
    model = EmbeddingModel(config)
    api = EmbeddingAPI(config, model)
    import uvicorn
    uvicorn.run(api.app, host="0.0.0.0", port=8000)
