"""
Alert Triage Service - FastAPI Application
AI-Augmented SOC

Main application entrypoint for LLM-powered security alert triage.
Receives alerts from Shuffle/Wazuh and returns structured analysis.
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from config import settings
from models import SecurityAlert, TriageResponse, HealthResponse
from llm_client import OllamaClient
from worker_pool import WorkerPool
from pii_redaction import redact_alert_pii
from common.security import detect_prompt_injection
from common.rate_limit import RateLimitMiddleware
from common.cache import init_redis, close_redis

import re
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.common.tracing import init_tracing, instrument_app, instrument_httpx

# Security
security = HTTPBearer(auto_error=False)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key_enabled = os.getenv("TRIAGE_API_KEY_ENABLED", "true").lower() == "true"
    if not api_key_enabled:
        return True
    api_key = os.getenv("TRIAGE_API_KEY", "")
    if not credentials or credentials.credentials != api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'triage_requests_total',
    'Total alert triage requests',
    ['status']
)
REQUEST_DURATION = Histogram(
    'triage_request_duration_seconds',
    'Alert triage request duration'
)
ANALYSIS_CONFIDENCE = Histogram(
    'triage_confidence_score',
    'LLM confidence scores'
)

# Global LLM client and worker pool
llm_client: OllamaClient = None
worker_pool: WorkerPool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.

    Initializes Ollama client and validates connectivity.
    """
    global llm_client

    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Ollama host: {settings.ollama_host}")
    logger.info(f"Primary model: {settings.primary_model}")

    # Initialize OpenTelemetry tracing
    init_tracing("alert-triage")
    instrument_app(app, "alert-triage")
    instrument_httpx()

    # Initialize LLM client
    llm_client = OllamaClient()

    # Check Ollama connectivity
    if not await llm_client.check_health():
        logger.warning("Ollama service not reachable at startup")
    else:
        logger.info("Ollama service connected successfully")

    # Initialize async worker pool
    async def _analyze_from_dict(alert_data: dict):
        alert = SecurityAlert(**alert_data)
        return await llm_client.analyze_alert(alert)

    worker_pool = WorkerPool(
        analyze_fn=_analyze_from_dict,
        worker_count=settings.worker_count,
        queue_threshold=settings.queue_threshold,
        circuit_breaker_enabled=settings.circuit_breaker_enabled,
    )
    await worker_pool.start()
    app.state.worker_pool = worker_pool
    logger.info(f"Worker pool started: {settings.worker_count} workers")

    # Initialize Redis cache
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    await init_redis(redis_url)

    yield

    # Shutdown
    logger.info("Shutting down Alert Triage Service")
    await close_redis()
    await worker_pool.stop()


# FastAPI app
app = FastAPI(
    title="Alert Triage Service",
    description="LLM-powered security alert analysis for SOC automation",
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

router = APIRouter(prefix="/api/v1/triage", tags=["v1"])
app.include_router(router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status, Ollama connectivity, and ML API status.
    """
    ollama_connected = await llm_client.check_health()
    ml_connected = await llm_client.ml_client.check_health() if settings.ml_enabled else False

    status = "healthy"
    if not ollama_connected:
        status = "degraded"
    elif settings.ml_enabled and not ml_connected:
        status = "partial"  # LLM works but ML is down

    return HealthResponse(
        status=status,
        service=settings.service_name,
        version=settings.service_version,
        ollama_connected=ollama_connected,
        ml_api_connected=ml_connected
    )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes service metrics for monitoring.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_alert(alert: SecurityAlert):
    """
    Submit alert for async triage using the high-throughput worker pool.
    Instantly returns a 202 Accepted status and a job_id.
    """
    try:
        logger.info(f"Received alert for async triage: {alert.alert_id}")

        # Guardrails: Detect prompt injection
        is_injection, attack_type = detect_prompt_injection(alert.rule_description)
        is_injection2, attack_type2 = detect_prompt_injection(alert.raw_log)
        if is_injection or is_injection2:
            logger.warning(f"Prompt injection detected in alert {alert.alert_id}")
            REQUEST_COUNT.labels(status="rejected").inc()
            raise HTTPException(
                status_code=400,
                detail="Invalid input: Prompt injection pattern detected in alert data"
            )

        # Sanitize PII
        alert_dict = alert.model_dump(mode="json")
        sanitized_alert_dict = redact_alert_pii(alert_dict)

        # Submit to worker pool
        pool = app.state.worker_pool
        job_id = pool.submit(sanitized_alert_dict)
        
        REQUEST_COUNT.labels(status="queued").inc()
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Alert {alert.alert_id} queued for async analysis"
        }

    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT.labels(status="error").inc()
        logger.error(f"Unexpected error queuing alert {alert.alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _persist_alert(alert: SecurityAlert, result: TriageResponse):
    """Fire-and-forget: persist alert + triage result to feedback service."""
    try:
        payload = {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
            "source_ip": alert.source_ip,
            "dest_ip": alert.dest_ip,
            "rule_id": alert.rule_id,
            "rule_description": alert.rule_description,
            "rule_level": alert.rule_level,
            "raw_alert": alert.model_dump(mode="json"),
            "triage_result": result.model_dump(mode="json"),
            "ai_severity": result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
            "ai_category": result.category.value if hasattr(result.category, 'value') else str(result.category),
            "ai_confidence": result.confidence,
            "ai_is_true_positive": result.is_true_positive,
            "ml_prediction": result.ml_prediction,
            "ml_confidence": result.ml_confidence,
            "organization_id": alert.organization_id,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{settings.feedback_service_url}/alerts", json=payload)
        logger.debug(f"Alert {alert.alert_id} persisted to feedback service")
    except Exception as e:
        logger.warning(f"Failed to persist alert {alert.alert_id}: {e}")


@router.post("/batch", response_model=Dict[str, Any])
async def batch_analyze(alerts: list[SecurityAlert]):
    """
    Batch analyze multiple alerts concurrently.

    Uses asyncio.gather() for parallel processing with error handling.

    **Args:**
        alerts: List of SecurityAlert objects

    **Returns:**
        Dict with results and statistics
    """
    import asyncio

    if not alerts:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "errors": []
        }

    start_time = time.time()
    logger.info(f"Starting batch analysis of {len(alerts)} alerts")

    # Process alerts concurrently
    tasks = [llm_client.analyze_alert(alert) for alert in alerts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Categorize results
    successful = []
    failed = []
    errors = []

    for idx, result in enumerate(results):
        alert_id = alerts[idx].alert_id

        if isinstance(result, Exception):
            failed.append(alert_id)
            errors.append({
                "alert_id": alert_id,
                "error": str(result)
            })
            logger.error(f"Batch analysis failed for {alert_id}: {result}")
        elif result is None:
            failed.append(alert_id)
            errors.append({
                "alert_id": alert_id,
                "error": "LLM analysis returned None"
            })
        else:
            successful.append(result.dict())

    duration = time.time() - start_time

    logger.info(
        f"Batch analysis complete: {len(successful)}/{len(alerts)} successful "
        f"in {duration:.2f}s"
    )

    return {
        "total": len(alerts),
        "successful": len(successful),
        "failed": len(failed),
        "processing_time_seconds": round(duration, 2),
        "results": successful,
        "errors": errors
    }


@router.post("/analyze/async")
async def analyze_async(alert: SecurityAlert, callback_url: str = None):
    """
    Submit alert for async triage (Legacy endpoint mapping to /analyze logic).
    """
    # Guardrails: Detect prompt injection
    is_injection, attack_type = detect_prompt_injection(alert.rule_description)
    is_injection2, attack_type2 = detect_prompt_injection(alert.raw_log)
    if is_injection or is_injection2:
        raise HTTPException(status_code=400, detail="Invalid input: Prompt injection pattern detected")
        
    # Sanitize PII
    alert_dict = alert.model_dump(mode="json")
    sanitized_alert_dict = redact_alert_pii(alert_dict)

    pool = app.state.worker_pool
    job_id = pool.submit(sanitized_alert_dict, callback_url=callback_url)
    return {
        "job_id": job_id,
        "status": "queued",
        "queue_depth": pool.queue_depth,
        "message": f"Alert {alert.alert_id} queued for async analysis",
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Get the status and result of an async triage job.

    Returns job status (queued/processing/completed/failed) and
    result when complete.
    """
    pool = app.state.worker_pool
    result = pool.get_job(job_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {
        "job_id": result.job_id,
        "status": result.status,
        "alert_id": result.alert_id,
        "result": result.result,
        "error": result.error,
        "created_at": result.created_at,
        "completed_at": result.completed_at,
        "processing_time_ms": result.processing_time_ms,
        "circuit_breaker_applied": result.circuit_breaker_applied,
    }


@router.get("/workers/stats")
async def worker_stats():
    """Get worker pool statistics."""
    pool = app.state.worker_pool
    return pool.stats


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "operational",
        "endpoints": {
            "analyze": "/analyze",
            "analyze_async": "/analyze/async",
            "jobs": "/jobs/{job_id}",
            "batch": "/batch",
            "workers": "/workers/stats",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "models": {
            "primary": settings.primary_model,
            "fallback": settings.fallback_model
        }
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development only
        log_level=settings.log_level.lower()
    )
