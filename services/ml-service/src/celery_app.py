"""
Agent 3: Celery Worker Setup
"""
import os
from celery import Celery

# Create Celery app
celery_app = Celery('ml-service')

# Configuration
celery_app.conf.broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app.conf.task_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.result_serializer = 'json'
celery_app.conf.timezone = 'UTC'
celery_app.conf.enable_utc = True

# Task routes
celery_app.conf.task_routes = {
    'process_hubspot_webhook': {'queue': 'hubspot-webhook-events'},
    'monitor_fatigue': {'queue': 'fatigue-monitoring'},
    'auto_index_winner': {'queue': 'budget-optimization'},
    'process_budget_optimization': {'queue': 'budget-optimization'},
    # Agent 6: Precomputation tasks
    'precompute_daily_predictions': {'queue': 'precomputation'},
    'warm_cache_for_campaigns': {'queue': 'precomputation'},
    'analyze_query_patterns': {'queue': 'precomputation'},
    'precompute_top_campaigns': {'queue': 'precomputation'},
    'precompute_scheduled_campaigns': {'queue': 'precomputation'},
    'cleanup_old_query_logs': {'queue': 'precomputation'},
    # Agent 10: Drift detection tasks
    'check_drift_daily': {'queue': 'drift-monitoring'},
    'check_drift_weekly': {'queue': 'drift-monitoring'},
    'alert_on_drift': {'queue': 'drift-monitoring'},
    'monitor_predictions_hourly': {'queue': 'drift-monitoring'},
}

# Import tasks (Agent 3, 4, 6, and 10)
celery_app.autodiscover_tasks(['src.celery_tasks', 'src.precompute.tasks', 'src.drift.drift_tasks'])

