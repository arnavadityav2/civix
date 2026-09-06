from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from contextlib import asynccontextmanager

from .database import engine
from .dependencies import get_db_session
from .routers import users, cases, leads, hypotheses, identity, entities, search, ingest, evidence, cctv, spatial, telecom, biometric, assertions
from .services.ml_service import MLService
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup logic
    logging.basicConfig(level=logging.INFO)
    from .safety_gate import verify_demo_environment_safety_gate
    verify_demo_environment_safety_gate()
    try:
        MLService.initialize()
    except Exception as e:
        logging.error(f"Failed to load ML model: {e}")
        raise
    yield
    # Application shutdown logic
    await engine.dispose()
    from .database import neo4j_driver
    if neo4j_driver:
        await neo4j_driver.close()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Civix 2.0 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi import Request
from fastapi.staticfiles import StaticFiles

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/evidence_store") or request.url.path.startswith("/api/v1/evidence"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

from .config import settings
evidence_store_path = os.environ.get("CIVIX_EVIDENCE_STORE_PATH", getattr(settings, "civix_evidence_store_path", r"C:\data\civix_demo\evidence_store"))
if os.path.exists(evidence_store_path):
    app.mount("/evidence_store", StaticFiles(directory=evidence_store_path), name="evidence_store")



app.include_router(users.router)
app.include_router(cases.router)
app.include_router(leads.router)
app.include_router(hypotheses.router)
app.include_router(identity.router)
app.include_router(entities.router)
app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(evidence.router)
app.include_router(evidence.global_router)
app.include_router(cctv.router)
app.include_router(spatial.router)
app.include_router(biometric.router)
app.include_router(telecom.case_router)
app.include_router(telecom.telecom_router)
app.include_router(assertions.router)  # Investigator proposal lifecycle (Graph Workspace Remediation)

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Log the error internally here if needed
    error_msg = str(exc.orig) if exc.orig else str(exc)
    
    # Check if it's a unique constraint violation
    if "duplicate key value violates unique constraint" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "A conflict occurred: Duplicate key value violates unique constraint."}
        )
    
    # Check if it's a foreign key constraint violation
    if "violates foreign key constraint" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "A conflict occurred: Violates foreign key constraint."}
        )
        
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database integrity error occurred."}
    )

@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """
    Health check endpoint verifying API and DB connectivity.
    This safely uses get_db_session() instead of get_rls_session(),
    ensuring we do NOT bypass RLS or impersonate users for a simple check.
    """
    try:
        # Simple query to verify DB is alive
        result = await session.execute(text("SELECT 1"))
        alive = result.scalar() == 1
        if not alive:
            raise HTTPException(status_code=503, detail="Database connectivity verified but returned unexpected result")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connectivity failed: {str(e)}")
