from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import logging
from typing import Callable
import traceback

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.time()

        try:
            # Log incoming request
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Client: {request.client.host if request.client else 'unknown'}"
            )

            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"[{request_id}] Response: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except HTTPException as exc:
            # Handle FastAPI HTTP exceptions
            process_time = time.time() - start_time
            logger.warning(
                f"[{request_id}] HTTP Exception: {exc.status_code} - {exc.detail} - "
                f"Time: {process_time:.3f}s"
            )

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={"X-Request-ID": request_id}
            )

        except Exception as exc:
            # Handle unexpected exceptions
            process_time = time.time() - start_time
            error_trace = traceback.format_exc()

            logger.error(
                f"[{request_id}] Unhandled Exception: {str(exc)} - "
                f"Time: {process_time:.3f}s\n{error_trace}"
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                    "timestamp": time.time()
                },
                headers={"X-Request-ID": request_id}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health check endpoints
        if request.url.path in ["/", "/health", "/metrics"]:
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')

        # Log request details
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read request body for logging (be careful with large payloads)
                body = await request.body()
                if len(body) < 1000:  # Only log small payloads
                    request_body = body.decode()
            except Exception as e:
                logger.warning(f"[{request_id}] Could not read request body: {e}")

        logger.debug(
            f"[{request_id}] Request details - "
            f"Headers: {dict(request.headers)} - "
            f"Body: {request_body[:500] if request_body else 'N/A'}"
        )

        response = await call_next(request)

        # Log response details
        process_time = time.time() - start_time
        logger.debug(
            f"[{request_id}] Response details - "
            f"Status: {response.status_code} - "
            f"Headers: {dict(response.headers)} - "
            f"Time: {process_time:.3f}s"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # In production, use Redis or similar

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old entries (simple cleanup)
        if len(self.requests) > 1000:  # Prevent memory leak
            cutoff_time = current_time - 60
            self.requests = {
                ip: times for ip, times in self.requests.items()
                if any(t > cutoff_time for t in times)
            }

        # Get or create request times for this IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Filter requests within the last minute
        recent_requests = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        if len(recent_requests) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls_per_minute} requests per minute",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add current request time
        recent_requests.append(current_time)
        self.requests[client_ip] = recent_requests

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add CORS headers if not already set
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = "*"
        if "Access-Control-Allow-Methods" not in response.headers:
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        if "Access-Control-Allow-Headers" not in response.headers:
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response


def setup_middleware(app):
    """Setup all middleware for the application"""
    # Order matters - middleware is applied in reverse order
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, calls_per_minute=100)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

    logger.info("Middleware setup completed")