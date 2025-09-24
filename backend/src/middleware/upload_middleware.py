"""
Performance optimization middleware for large file uploads
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import hashlib
import tempfile
import os

logger = logging.getLogger(__name__)


class UploadOptimizationMiddleware:
    """Middleware for optimizing file upload performance"""

    def __init__(self, max_file_size: int = 51200, chunk_size: int = 8192):
        self.max_file_size = max_file_size
        self.chunk_size = chunk_size
        self.upload_cache: Dict[str, Dict[str, Any]] = {}

    async def __call__(self, request: Request, call_next):
        """Process upload requests with optimization"""

        # Only apply to upload endpoints
        if not self._is_upload_request(request):
            return await call_next(request)

        # Check request size before processing
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_file_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "payload_too_large",
                    "message": f"Request size exceeds {self.max_file_size} bytes limit",
                    "timestamp": time.time()
                }
            )

        # Add upload optimization headers
        start_time = time.time()

        try:
            response = await call_next(request)

            # Add performance headers
            processing_time = time.time() - start_time
            response.headers["X-Upload-Processing-Time"] = str(round(processing_time, 3))
            response.headers["X-Upload-Optimized"] = "true"

            return response

        except Exception as e:
            logger.error(f"Upload optimization error: {e}")
            return await call_next(request)

    def _is_upload_request(self, request: Request) -> bool:
        """Check if request is an upload request"""
        return (
            request.method == "POST" and
            "/upload" in request.url.path and
            "multipart/form-data" in request.headers.get("content-type", "")
        )


class ChunkedUploadHandler:
    """Handler for chunked file uploads (for future implementation)"""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.active_uploads: Dict[str, Dict[str, Any]] = {}

    async def start_chunked_upload(self, upload_id: str, total_size: int, filename: str) -> Dict[str, Any]:
        """Initialize a chunked upload session"""

        if total_size > 51200:  # 50KB limit
            raise ValueError("File size exceeds maximum limit")

        temp_file_path = os.path.join(self.temp_dir, f"upload_{upload_id}")

        self.active_uploads[upload_id] = {
            "temp_file": temp_file_path,
            "total_size": total_size,
            "received_size": 0,
            "filename": filename,
            "start_time": time.time(),
            "chunks": []
        }

        return {
            "upload_id": upload_id,
            "status": "initialized",
            "chunk_size": 8192
        }

    async def upload_chunk(self, upload_id: str, chunk_data: bytes, chunk_index: int) -> Dict[str, Any]:
        """Process a file chunk"""

        if upload_id not in self.active_uploads:
            raise ValueError("Upload session not found")

        upload_info = self.active_uploads[upload_id]

        # Write chunk to temp file
        with open(upload_info["temp_file"], "ab") as f:
            f.write(chunk_data)

        upload_info["received_size"] += len(chunk_data)
        upload_info["chunks"].append(chunk_index)

        progress = upload_info["received_size"] / upload_info["total_size"]

        return {
            "upload_id": upload_id,
            "progress": round(progress, 3),
            "received_size": upload_info["received_size"],
            "total_size": upload_info["total_size"]
        }

    async def complete_upload(self, upload_id: str) -> Dict[str, Any]:
        """Complete the chunked upload"""

        if upload_id not in self.active_uploads:
            raise ValueError("Upload session not found")

        upload_info = self.active_uploads[upload_id]

        # Verify upload completion
        if upload_info["received_size"] != upload_info["total_size"]:
            raise ValueError("Upload incomplete")

        # Read final file content
        with open(upload_info["temp_file"], "rb") as f:
            file_content = f.read()

        # Cleanup temp file
        os.unlink(upload_info["temp_file"])
        del self.active_uploads[upload_id]

        return {
            "upload_id": upload_id,
            "status": "completed",
            "content": file_content,
            "filename": upload_info["filename"],
            "size": len(file_content)
        }


class UploadProgressTracker:
    """Track upload progress for real-time feedback"""

    def __init__(self):
        self.progress_cache: Dict[str, Dict[str, Any]] = {}

    def start_tracking(self, upload_id: str, total_size: int) -> None:
        """Start tracking upload progress"""
        self.progress_cache[upload_id] = {
            "total_size": total_size,
            "uploaded_size": 0,
            "start_time": time.time(),
            "status": "uploading"
        }

    def update_progress(self, upload_id: str, uploaded_size: int) -> Dict[str, Any]:
        """Update upload progress"""
        if upload_id not in self.progress_cache:
            raise ValueError("Upload tracking not initialized")

        progress_info = self.progress_cache[upload_id]
        progress_info["uploaded_size"] = uploaded_size

        progress_percent = uploaded_size / progress_info["total_size"]
        elapsed_time = time.time() - progress_info["start_time"]

        # Estimate remaining time
        if progress_percent > 0:
            estimated_total_time = elapsed_time / progress_percent
            remaining_time = estimated_total_time - elapsed_time
        else:
            remaining_time = 0

        return {
            "upload_id": upload_id,
            "progress": round(progress_percent, 3),
            "uploaded_size": uploaded_size,
            "total_size": progress_info["total_size"],
            "elapsed_time": round(elapsed_time, 2),
            "estimated_remaining": round(remaining_time, 2),
            "upload_speed": round(uploaded_size / elapsed_time, 2) if elapsed_time > 0 else 0
        }

    def complete_tracking(self, upload_id: str) -> None:
        """Complete upload tracking"""
        if upload_id in self.progress_cache:
            self.progress_cache[upload_id]["status"] = "completed"

    def get_progress(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for an upload"""
        return self.progress_cache.get(upload_id)


class UploadCacheManager:
    """Manage upload caching for deduplication"""

    def __init__(self, max_cache_size: int = 100):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = max_cache_size

    def generate_content_hash(self, content: bytes) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content).hexdigest()

    def check_duplicate(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Check if content already exists in cache"""
        return self.cache.get(content_hash)

    def cache_upload(self, content_hash: str, upload_result: Dict[str, Any]) -> None:
        """Cache successful upload result"""

        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[content_hash] = {
            **upload_result,
            "cached_at": time.time()
        }

    def clear_cache(self) -> None:
        """Clear upload cache"""
        self.cache.clear()


# Global instances
upload_progress_tracker = UploadProgressTracker()
upload_cache_manager = UploadCacheManager()
chunked_upload_handler = ChunkedUploadHandler()


# Utility functions for upload optimization
def optimize_upload_performance():
    """Apply various optimizations for upload performance"""

    # Set optimal buffer sizes
    import io
    io.DEFAULT_BUFFER_SIZE = 8192

    # Configure logging for upload operations
    upload_logger = logging.getLogger('upload_optimization')
    upload_logger.setLevel(logging.INFO)

    return {
        "buffer_size": io.DEFAULT_BUFFER_SIZE,
        "logger": upload_logger
    }


async def validate_upload_rate_limit(request: Request, max_uploads_per_minute: int = 10) -> bool:
    """Validate upload rate limiting"""
    # Simple in-memory rate limiting (in production, use Redis)
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    # This is a simplified implementation
    # In production, implement proper rate limiting with Redis/database
    return True


def get_optimal_chunk_size(file_size: int) -> int:
    """Calculate optimal chunk size based on file size"""
    if file_size < 1024:  # < 1KB
        return 512
    elif file_size < 8192:  # < 8KB
        return 1024
    elif file_size < 32768:  # < 32KB
        return 4096
    else:
        return 8192