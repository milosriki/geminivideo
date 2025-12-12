"""
Agent 4: Celery Beat Periodic Tasks Configuration
Agent 6: Precomputation Tasks Added
Agent 10: Drift Detection Tasks Added
"""
from celery.schedules import crontab
from .celery_app import celery_app

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Existing tasks
    'monitor-fatigue': {
        'task': 'monitor_fatigue',
        'schedule': 21600.0,  # Every 6 hours
    },
    'auto-index-winners': {
        'task': 'auto_index_winner',
        'schedule': 43200.0,  # Every 12 hours
    },

    # Agent 6: Precomputation Tasks
    # Run daily at 2am (off-peak) to precompute top 1000 ads
    'precompute-daily-predictions': {
        'task': 'precompute_daily_predictions',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
        'kwargs': {'limit': 1000, 'force': False}
    },

    # Analyze query patterns hourly for optimization
    'analyze-query-patterns': {
        'task': 'analyze_query_patterns',
        'schedule': 3600.0,  # Every hour
    },

    # Warm cache for campaigns launching in next 4 hours (runs every 2 hours)
    'precompute-scheduled-campaigns': {
        'task': 'precompute_scheduled_campaigns',
        'schedule': 7200.0,  # Every 2 hours
        'kwargs': {'hours_ahead': 4}
    },

    # Clean up old query logs daily at 3am
    'cleanup-old-query-logs': {
        'task': 'cleanup_old_query_logs',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM daily
        'kwargs': {'days_to_keep': 7}
    },

    # Agent 10: Drift Detection Tasks
    # Daily drift check at 4am (after precomputation)
    'check-drift-daily': {
        'task': 'check_drift_daily',
        'schedule': crontab(hour=4, minute=0),  # 4:00 AM daily
    },

    # Weekly comprehensive drift analysis on Mondays at 5am
    'check-drift-weekly': {
        'task': 'check_drift_weekly',
        'schedule': crontab(hour=5, minute=0, day_of_week=1),  # Mondays at 5:00 AM
    },

    # Hourly prediction monitoring
    'monitor-predictions-hourly': {
        'task': 'monitor_predictions_hourly',
        'schedule': 3600.0,  # Every hour
    },
}

