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
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, Celery, Redis, SQLAlchemy, React 18+, ffmpeg-python (006-implement-the-real)
- SQLite/PostgreSQL (persistent data), Redis (sessions/tasks), File system (media files) (006-implement-the-real)
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, Celery, Redis, SQLAlchemy, React 18+, google-generativeai library (007-https-aistudio-google)
- TypeScript 5+ (frontend), JavaScript ES2020+ + React 18+, axios, React Router DOM, Tailwind CSS, Headless UI, React Hook Form (008-make-changes-required)
- Browser localStorage for user preferences, session storage for UI state (008-make-changes-required)
- Python 3.11+ (backend), TypeScript 5.2+ (frontend) + FastAPI, google-generativeai, Celery, Redis, SQLAlchemy, React 18, Vite (009-problem-identified-the)
- SQLite/PostgreSQL (persistent data), Redis (sessions/tasks), File system (generated media) (009-problem-identified-the)

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
- 009-problem-identified-the: Added Python 3.11+ (backend), TypeScript 5.2+ (frontend) + FastAPI, google-generativeai, Celery, Redis, SQLAlchemy, React 18, Vite
- 008-make-changes-required: Added TypeScript 5+ (frontend), JavaScript ES2020+ + React 18+, axios, React Router DOM, Tailwind CSS, Headless UI, React Hook Form
- 007-https-aistudio-google: Added Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI, Celery, Redis, SQLAlchemy, React 18+, google-generativeai library

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
