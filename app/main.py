from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from prometheus_client import (
	Counter,
	Histogram,
	CONTENT_TYPE_LATEST,
	generate_latest,
)

app = FastAPI(
	title = "AIOps Infrastructure Monitoring API",
	description = "A containerized application for AIOps monitoring experiments",
	version = "0.1.0",
)

# Total HTTP requests, grouped by method, endpoint and status.
REQUEST_COUNT = Counter(
	"http_requests_total",
	"Total number of HTTP requests",
	["method", "endpoint", "status_code"],
)

# Http request processing duration.
REQUEST_LATENCY = Histogram(
	"http_request_duration_seconds",
	"HTTP request processing duration in seconds",
	["method", "endpoint"],
)


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
	if request.url.path == "/metrics":
		return await call_next(request)

	start_time = datetime.now(timezone.utc)

	response = await call_next(request)

	duration = (
		datetime.now(timezone.utc) - start_time
	).total_seconds()

	REQUEST_COUNT.labels(
		method=request.method,
		endpoint=request.url.path,
		status_code=str(response.status_code),
	).inc()

	REQUEST_LATENCY.labels(
		method=request.method,
		endpoint=request.url.path,
	).observe(duration)

	return response


@app.get("/")
def root():
	return {
		"message" : "AIOps monitoring application is running",
		"timestamp" : datetime.now(timezone.utc).isoformat(),
	}

@app.get("/health")
def health():
	return {
		"status" : "healthy",
		"service" : "aiops-monitoring-api",
	}

@app.get("/metrics")
def metrics():
	return Response(
		content = generate_latest(),
		media_type = CONTENT_TYPE_LATEST,
	)
