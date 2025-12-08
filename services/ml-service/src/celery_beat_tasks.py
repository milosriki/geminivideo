"""
Agent 4: Celery Beat Periodic Tasks Configuration
"""
from .celery_app import celery_app

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'monitor-fatigue': {
        'task': 'monitor_fatigue',
        'schedule': 21600.0,  # Every 6 hours
    },
    'auto-index-winners': {
        'task': 'auto_index_winner',
        'schedule': 43200.0,  # Every 12 hours
    },
}

