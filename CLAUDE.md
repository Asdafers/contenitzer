# contentizer Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-22

## Active Technologies
- (002-youtube-api-i)
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, React 18+, Redis, SQLAlchemy, Vite (003-we-now-need)
- SQLite/PostgreSQL (existing), Redis (sessions/tasks) (003-we-now-need)
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, Redis, Celery, React 18+, Vite, SQLAlchemy, WebSockets (004-1-install-redis)
- Redis (sessions/tasks), SQLite/PostgreSQL (persistent data) (004-1-install-redis)
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, React 18+, Redis, SQLAlchemy, Vite, Celery (005-i-need-an)
- SQLite/PostgreSQL (persistent data), Redis (sessions/tasks) (005-i-need-an)

## Project Structure
```
backend/
frontend/
tests/
```

## Commands
- Use `uv` for Python package management and execution (not pip or python3 directly)
- Backend: `uv run` for Python scripts
- Frontend: Standard npm/node commands

## Code Style
: Follow standard conventions

## Recent Changes
- 005-i-need-an: Added Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, React 18+, Redis, SQLAlchemy, Vite, Celery
- 004-1-install-redis: Added Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, Redis, Celery, React 18+, Vite, SQLAlchemy, WebSockets
- 003-we-now-need: Added Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, React 18+, Redis, SQLAlchemy, Vite

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
