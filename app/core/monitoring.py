from prometheus_client import Counter, Histogram, Info
from prometheus_client.openmetrics.exposition import generate_latest
from fastapi import Response, Request
from time import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import PlainTextResponse

# Metrics
REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

DOCUMENT_PROCESSING = Counter(
    "document_processing_total",
    "Total number of documents processed",
    ["status"]
)

LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["model", "status"]
)

# Middleware for request metrics
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time()
        response = await call_next(request)
        
        REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time() - start_time)
        
        return response

# Metrics endpoint
async def metrics():
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain"
    ) 