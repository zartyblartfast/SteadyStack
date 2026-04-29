"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.comparison import router as comparison_router
from app.api.decisions import router as decisions_router
from app.api.health import router as health_router
from app.config import settings

app = FastAPI(
    title="SteadyStack",
    description="Smart, self-custodial Bitcoin DCA engine",
    version="0.1.0",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(decisions_router)
app.include_router(comparison_router)
