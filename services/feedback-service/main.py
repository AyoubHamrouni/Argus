"""
Feedback Service - FastAPI Application
AI-Augmented SOC

Persists all processed alerts and their triage results.
Accepts analyst feedback for the learning flywheel:
- False positive marking
- Severity/category corrections
- Ground truth labels for ML retraining
- Analyst investigation notes
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.common.tracing import init_tracing, instrument_app
from common.rate_limit import RateLimitMiddleware
from common.cache import init_redis, close_redis

from config import Settings
from database import DatabaseManager
from models import (
    StoreAlertRequest,
    FeedbackSubmission,
    FeedbackResponse,
    StoredAlertResponse,
    FeedbackStats,
)

# Configuration
settings = Settings()

# Logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics
ALERTS_STORED = Counter(
    "feedback_alerts_stored_total",
    "Total alerts persisted",
    ["action"],
)
FEEDBACK_RECEIVED = Counter(
    "feedback_received_total",
    "Total feedback submissions",
    ["is_false_positive"],
)
REQUEST_DURATION = Histogram(
    "feedback_request_duration_seconds",
    "Request processing time",
    ["endpoint"],
)

# Database manager (initialized on startup)
db: Optional[DatabaseManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global db
    logger.info("Starting Feedback Service")

    # Initialize OpenTelemetry tracing
    init_tracing("feedback-service")
    instrument_app(app, "feedback-service")

    try:
        db = DatabaseManager(settings.database_url)
        await db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize Redis cache
    import os
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    await init_redis(redis_url)

    yield

    await close_redis()
    logger.info("Shutting down Feedback Service")
    if db:
        await db.close()

# Security
security = HTTPBearer(auto_error=False)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Enforce strict API key authentication if enabled."""
    if not settings.api_key_enabled:
        return True
    if not credentials or credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

app = FastAPI(
    title="Feedback Service",
    description="Alert persistence and analyst feedback for the Argus learning flywheel",
    version=settings.service_version,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

# OpenTelemetry Instrumentation
FastAPIInstrumentor.instrument_app(app)

router = APIRouter(prefix="/api/v1/feedback", tags=["v1"])
app.include_router(router)


# --- Health Check ---


@app.get("/health")
async def health_check():
    """Health check with database connectivity status."""
    db_healthy = await db.check_health() if db else False
    status = "healthy" if db_healthy else "degraded"

    return {
        "status": status,
        "service": settings.service_name,
        "version": settings.service_version,
        "database_connected": db_healthy,
    }


# --- Alert Persistence ---


@router.post("/alerts")
async def store_alert(request: StoreAlertRequest):
    """
    Persist an alert and its triage result.

    Called by alert-triage service after analysis completes.
    Upserts on alert_id (updates if already exists).
    """
    with REQUEST_DURATION.labels(endpoint="store_alert").time():
        try:
            result = await db.store_alert(request.model_dump())
            ALERTS_STORED.labels(action=result["action"]).inc()
            logger.info(f"Alert stored: {request.alert_id} ({result['action']})")
            return result
        except Exception as e:
            logger.error(f"Failed to store alert {request.alert_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts")
async def query_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    source_ip: Optional[str] = None,
    dest_ip: Optional[str] = None,
    has_feedback: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    organization_id: Optional[str] = Query(None, description="Filter by organization/tenant ID"),
):
    """
    Query stored alerts with filtering and pagination.

    Supports filtering by severity, IP addresses, feedback status, time range,
    and organization_id for multi-tenant deployments.
    """
    with REQUEST_DURATION.labels(endpoint="query_alerts").time():
        try:
            return await db.query_alerts(
                limit=limit,
                offset=offset,
                severity=severity,
                source_ip=source_ip,
                dest_ip=dest_ip,
                has_feedback=has_feedback,
                start_time=start_time,
                end_time=end_time,
                organization_id=organization_id,
            )
        except Exception as e:
            logger.error(f"Failed to query alerts: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get a single alert with all its feedback."""
    with REQUEST_DURATION.labels(endpoint="get_alert").time():
        result = await db.get_alert(alert_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        return result


# --- Feedback ---
# IMPORTANT: /feedback/stats must be defined BEFORE /feedback/{alert_id}
# to avoid FastAPI treating "stats" as an alert_id parameter.


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """
    Get aggregated feedback statistics.

    Returns false positive rates, correction rates, confidence calibration,
    and top false-positive source IPs. Used to measure model quality and
    identify systematic detection issues.
    """
    with REQUEST_DURATION.labels(endpoint="feedback_stats").time():
        try:
            return await db.get_feedback_stats()
        except Exception as e:
            logger.error(f"Failed to compute feedback stats: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/feedback/{alert_id}")
async def submit_feedback(alert_id: str, submission: FeedbackSubmission):
    """
    Submit analyst feedback on a triage result.

    This is the core of the learning flywheel:
    - False positive marking improves future detection
    - Severity corrections calibrate the model
    - Ground truth labels (true_label) enable ML retraining
    - Notes capture institutional knowledge
    """
    with REQUEST_DURATION.labels(endpoint="submit_feedback").time():
        result = await db.store_feedback(alert_id, submission.model_dump())
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found. Store the alert first.",
            )

        FEEDBACK_RECEIVED.labels(
            is_false_positive=str(submission.is_false_positive)
        ).inc()

        logger.info(
            f"Feedback received: alert={alert_id}, "
            f"analyst={submission.analyst_id}, "
            f"fp={submission.is_false_positive}"
        )

        return result


@router.get("/feedback/{alert_id}")
async def get_alert_feedback(alert_id: str):
    """Get all feedback for a specific alert."""
    alert = await db.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"alert_id": alert_id, "feedback": alert.get("feedback", [])}


# --- ROI & Business Metrics ---


@router.get("/roi/metrics", tags=["ROI"], summary="Business ROI metrics for the SOC platform")
async def get_roi_metrics(
    organization_id: Optional[str] = Query(None, description="Filter by organization/tenant ID"),
):
    """
    Return quantifiable business ROI metrics for the SOC platform.

    Includes analyst time saved, accuracy rate, throughput by severity,
    and true/false positive counts. Optionally filtered by `organization_id`
    for multi-tenant deployments.
    """
    with REQUEST_DURATION.labels(endpoint="roi_metrics").time():
        try:
            return await db.get_roi_metrics(organization_id=organization_id)
        except Exception as e:
            logger.error(f"Failed to compute ROI metrics: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


# --- Metrics ---


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")


# --- Root ---


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Alert persistence and analyst feedback for the Argus learning flywheel",
        "endpoints": {
            "store_alert": "POST /alerts",
            "query_alerts": "GET /alerts",
            "get_alert": "GET /alerts/{alert_id}",
            "submit_feedback": "POST /feedback/{alert_id}",
            "get_feedback": "GET /feedback/{alert_id}",
            "feedback_stats": "GET /feedback/stats",
            "health": "GET /health",
            "metrics": "GET /metrics",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
