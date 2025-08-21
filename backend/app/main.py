"""Main FastAPI application."""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_runs, routes_workflows
from app.core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    # You could initialize resources here
    
    yield
    
    # Shutdown
    # You could cleanup resources here


# Create FastAPI app
app = FastAPI(
    title="Workflow Backend",
    description="Workflow engine with FastAPI and LangGraph",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(routes_runs.router, prefix="/runs", tags=["runs"])


def run() -> None:
    """Run the application using uvicorn.
    
    This function is called by the Poetry script entry point.
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if "--reload" in sys.argv else False
    )


if __name__ == "__main__":
    run()