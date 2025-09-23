# Quickstart Guide

## Setup
1. Install dependencies: `uv sync`
2. Set YouTube API key in config (optional - can provide via API)
3. Start backend: `uv run python main.py`
4. Start frontend: `npm run dev` (when implemented)

## Environment Variables
```bash
export DATABASE_URL="sqlite:///./contentizer.db"  # Optional
export STORAGE_PATH="/tmp/contentizer"           # Optional
export AUTO_CREATE_TABLES="true"                # Optional
```

## Basic Workflow
1. **Analyze Trends**: POST `/api/trending/analyze` with timeframe
2. **Generate Script**: POST `/api/scripts/generate` with theme_id
3. **Create Media**: POST `/api/media/generate` with script_id
4. **Compose Video**: POST `/api/videos/compose` with project_id
5. **Upload**: POST `/api/videos/upload` with project_id

## Manual Input Fallback
- Use `input_type: "manual_subject"` with topic text
- Use `input_type: "manual_script"` with complete script

## Test Scenarios
1. Full automated: API → theme → script → media → video → upload
2. Manual subject: Manual topic → script → media → video → upload
3. Manual script: Complete script → media → video → upload