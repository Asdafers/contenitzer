#!/usr/bin/env python3
from src.lib.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE media_assets ADD COLUMN gemini_model_used VARCHAR(100)"))
        conn.commit()
        print("Successfully added gemini_model_used column to media_assets table")
except Exception as e:
    print(f"Error: {e}")
    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
        print("Column already exists, no action needed")
    else:
        raise