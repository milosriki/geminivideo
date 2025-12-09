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
}

# Import tasks (will be created by Agent 4)
celery_app.autodiscover_tasks(['src.celery_tasks'])

