"""FastAPI Middleware Entrypoint for Autonomous ML Research Agent."""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import chat, data, auth, cache
from .cache import app_cache, apply_edge_cache_headers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agentic Middleware orchestrating arXiv, Kaggle, and FastMCP tools with Cloudflare Edge Caching.",
)

# Enable CORS strictly for configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(data.router)
app.include_router(cache.router)


@app.get("/api/health")
async def health_check(response: Response):
    """Service health probe with Cloudflare Edge and In-Memory Caching."""
    cache_key = "system:health_status"
    cached, hit, age = app_cache.get(cache_key)
    if hit and cached:
        apply_edge_cache_headers(response, ttl_seconds=5, is_hit=True, age_seconds=age)
        return cached

    payload = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "configured_provider": settings.MODEL_PROVIDER,
        "auth_enabled": settings.AUTH_ENABLED,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_groq_key": bool(settings.GROQ_API_KEY),
        "cache_tier": "Active: In-Memory RAM + Cloudflare Edge",
    }
    app_cache.set(cache_key, payload, ttl=5)
    apply_edge_cache_headers(response, ttl_seconds=5, is_hit=False)
    return payload


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
