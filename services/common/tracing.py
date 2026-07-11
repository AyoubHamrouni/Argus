"""OpenTelemetry distributed tracing for AI-SOC services."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import StatusCode, Status

logger = logging.getLogger(__name__)


def init_tracing(
    service_name: str,
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
) -> TracerProvider:
    """Initialize OpenTelemetry tracing for a service.

    Args:
        service_name: Name of the service (e.g., "alert-triage")
        otlp_endpoint: OTLP collector endpoint (e.g., "http://otel-collector:4317")
        console_export: Whether to also export to console (debug mode)
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("DEPLOY_ENV", "development"),
    })

    provider = TracerProvider(resource=resource)

    # OTLP exporter (sends to collector)
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {endpoint}")
    except Exception as e:
        logger.warning(f"OTLP exporter unavailable: {e}")

    # Console exporter (debug mode)
    if console_export or os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true":
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for a specific component."""
    return trace.get_tracer(name)


def instrument_app(app, service_name: str):
    """Instrument a FastAPI app with OpenTelemetry.

    This automatically creates spans for every HTTP request.
    """
    FastAPIInstrumentor.instrument_app(app, service_name=service_name)
    logger.info(f"FastAPI instrumented: {service_name}")


def instrument_httpx():
    """Instrument httpx HTTP client for outgoing requests."""
    HTTPXClientInstrumentor().instrument()
    logger.info("httpx client instrumented")


def instrument_sqlalchemy(engine):
    """Instrument SQLAlchemy engine for DB query tracing."""
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy engine instrumented")
    except Exception as e:
        logger.warning(f"SQLAlchemy instrumentation failed: {e}")


@asynccontextmanager
async def traced_span(tracer_name: str, span_name: str, attributes: Optional[dict] = None):
    """Context manager for creating traced spans.

    Usage:
        async with traced_span("alert-triage", "analyze_alert", {"alert.id": alert_id}):
            result = await analyze(alert)
    """
    tracer = get_tracer(tracer_name)
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
