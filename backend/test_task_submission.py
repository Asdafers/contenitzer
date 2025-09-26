#!/usr/bin/env python3
import sys
sys.path.append('.')

# Test task submission from the API server environment
from src.tasks.media_tasks import generate_media_from_script

print("Testing task submission from API server environment...")

try:
    result = generate_media_from_script.apply_async(
        args=['test-session-api', '509b250a-8844-4eaa-9001-164d5b17a719', {'model': 'gemini-2.5-flash'}],
        task_id='api-test-task'
    )
    print(f"✅ Task submitted successfully: {result.id}")
    print(f"Task ready: {result.ready()}")
    print(f"Task state: {result.state}")
except Exception as e:
    print(f"❌ Task submission failed: {e}")
    import traceback
    traceback.print_exc()