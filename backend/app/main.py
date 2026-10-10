"""
AgentBreak FastAPI application entry point.

Lifespan context initialises the database tables on startup.
CORS middleware is configured for the React frontend development server.
Includes all REST routes and SSE streaming channels.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.security.headers import SecurityHeadersMiddleware
from app.security.rate_limit import setup_rate_limiting
from app.security.redaction import setup_log_redaction

from app.config import get_settings
from app.db import init_db
from app.api.campaigns import router as campaigns_router
from app.api.attacks import router as attacks_router
from app.api.traces import router as traces_router
from app.api.defenses import router as defenses_router
from app.api.eval import router as eval_router
from app.api.metrics import router as metrics_router
from app.api.reports import router as reports_router
from app.api.demo import router as demo_router
from app.api.stream import router as stream_router
from app.api.users import router as users_router
from app.api.findings import router as findings_router
from app.api.validation import router as validation_router
from app.api.approvals import router as approvals_router
from app.api.scenarios import router as scenarios_router
from app.api.inventory import router as inventory_router
from app.api.governance import router as governance_router
from app.api.killswitch import router as killswitch_router
from app.api.integrity import router as integrity_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    # Ensure all SQLite database tables exist
    await init_db()
    yield


settings = get_settings()

app = FastAPI(
    title="AgentBreak API",
    description="Defensive AI Red-Team Sandbox Platform",
    version="0.1.0",
    lifespan=lifespan,
)

setup_log_redaction()
setup_rate_limiting(app)

# ── CORS Middleware ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# ── Register API Routers ────────────────────────────────────────
app.include_router(campaigns_router)
app.include_router(attacks_router)
app.include_router(traces_router)
app.include_router(defenses_router)
app.include_router(eval_router)
app.include_router(metrics_router)
app.include_router(reports_router)
app.include_router(demo_router)
app.include_router(stream_router)
app.include_router(users_router)
app.include_router(findings_router)
app.include_router(validation_router)
app.include_router(approvals_router)
app.include_router(scenarios_router)
app.include_router(inventory_router)
app.include_router(governance_router)
app.include_router(killswitch_router)
app.include_router(integrity_router)


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "app": "AgentBreak",
        "victim_model": settings.victim_model,
        "attacker_model": settings.attacker_model,
        "demo_mode": str(settings.demo_mode),
    }
