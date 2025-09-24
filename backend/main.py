from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from src.api import trending, scripts, media, videos, sessions, tasks, websocket, setup, script_upload, workflow
from src.lib.middleware import setup_middleware
from src.lib.database import DatabaseManager
from src.lib.tasks import task_manager
from src.lib.storage import storage_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Content Creator Workbench API",
    version="1.0.0",
    description="AI-powered content creation platform for YouTube creators"
)

# Setup middleware
setup_middleware(app)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(trending.router, tags=["trending"])
app.include_router(scripts.router, tags=["scripts"])
app.include_router(media.router, tags=["media"])
app.include_router(videos.router, tags=["videos"])
app.include_router(sessions.router, tags=["sessions"])
app.include_router(tasks.router, tags=["tasks"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(setup.router, tags=["setup"])
app.include_router(script_upload.router, tags=["script-upload"])
app.include_router(workflow.router, tags=["workflow"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Content Creator Workbench API...")

    # Initialize database
    try:
        DatabaseManager.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    # Check storage
    try:
        stats = storage_manager.get_storage_stats()
        logger.info(f"Storage initialized - Total files: {stats.get('total', {}).get('file_count', 0)}")
    except Exception as e:
        logger.warning(f"Storage check failed: {e}")

    # Clean up old tasks
    try:
        cleaned = task_manager.cleanup_completed_tasks(max_age_hours=24)
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old tasks")
    except Exception as e:
        logger.warning(f"Task cleanup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Content Creator Workbench API...")

@app.get("/")
async def root():
    return {"message": "Content Creator Workbench API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_healthy = DatabaseManager.health_check()
    storage_stats = storage_manager.get_storage_stats()
    running_tasks = len(task_manager.get_running_tasks())

    status = "healthy" if db_healthy else "unhealthy"

    return {
        "status": status,
        "database": "connected" if db_healthy else "disconnected",
        "storage": {
            "total_files": storage_stats.get("total", {}).get("file_count", 0),
            "total_size_mb": storage_stats.get("total", {}).get("total_size_mb", 0)
        },
        "tasks": {
            "running": running_tasks,
            "total": len(task_manager.get_all_tasks())
        },
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)