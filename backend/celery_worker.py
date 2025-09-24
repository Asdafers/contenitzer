"""
Celery worker configuration for background task processing.
"""
import os
from celery import Celery
from src.lib.database import DatabaseManager

# Redis connection configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery instance
celery_app = Celery(
    "contentizer_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "src.tasks.trending_tasks",
        "src.tasks.script_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task routing and queues
    task_routes={
        'src.tasks.trending_tasks.*': {'queue': 'trending'},
        'src.tasks.script_tasks.*': {'queue': 'script'},
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'visibility_timeout': 300,  # 5 minutes
        'retry_policy': {
            'timeout': 5.0
        }
    },

    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Task time limits
    task_soft_time_limit=600,  # 10 minutes
    task_time_limit=900,       # 15 minutes
)

# Task failure callback
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing worker connectivity"""
    print(f'Request: {self.request!r}')
    return {'status': 'success', 'worker_id': self.request.id}

# Worker startup event
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic cleanup tasks"""
    # Clean up expired task results every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour
        cleanup_expired_tasks.s(),
        name='cleanup expired tasks'
    )

@celery_app.task
def cleanup_expired_tasks():
    """Clean up expired task results and session data"""
    try:
        # This will be implemented when Redis service is ready
        return {'cleaned': 0, 'status': 'not_implemented'}
    except Exception as e:
        return {'error': str(e), 'status': 'failed'}

if __name__ == '__main__':
    # Run worker
    celery_app.start()