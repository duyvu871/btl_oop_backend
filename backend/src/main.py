from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import Theme, get_scalar_api_reference

from src.api.v1.main import api_router
from src.settings.env import settings

# Create FastAPI app
app = FastAPI(
    title="Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Configure CORS middleware
# if len(settings.CORS_ORIGINS) > 0:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=settings.CORS_ORIGINS,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "fastapi-backend", "version": "1.0.0"}


# Include auth router
app.include_router(api_router, prefix=settings.API_PREFIX)


# Scalar UI endpoint
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title + " - Scalar UI",
        theme=Theme.BLUE_PLANET,
    )
