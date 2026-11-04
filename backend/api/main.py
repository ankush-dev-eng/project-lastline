"""PROJECT LASTLINE: FastAPI Application Entrypoint.

Provides REST operations endpoints, real-time WebSocket live streaming,
and sandboxed advisory control boundary enforcement.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import router
from backend.api.state import get_system_state
from backend.api.websocket import handle_live_stream


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Warm up shared system state singleton
    get_system_state()
    yield


app = FastAPI(
    title="PROJECT LASTLINE: AI Cyber-Resilience for Critical Water Infrastructure",
    description="Fail-operational situational intelligence, state reconstruction, and advisory fallback playbooks.",
    version="0.7.0",
    lifespan=lifespan,
)

# CORS configuration for control-room frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Safety-Mode"] = "SANDBOX_ADVISORY_ONLY"
    return response


# Mount REST Routes
app.include_router(router)


# Mount WebSocket Live Stream
@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    """Real-time streaming WebSocket broadcasting operational state frames <= 1.0s."""
    await handle_live_stream(websocket)


@app.get("/")
def root():
    return JSONResponse(
        {
            "system": "PROJECT LASTLINE",
            "description": "AI-Driven Cyber-Resilience for Critical Water Infrastructure",
            "status": "OPERATIONAL",
            "safety_mode": "SANDBOX_ADVISORY_ONLY",
            "docs_url": "/docs",
        }
    )
