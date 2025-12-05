"""
Smart Model Routing for Optimal Cost/Quality

This module provides intelligent routing of tasks to optimal models
based on complexity, with confidence-based escalation and cost optimization.
"""

from .model_router import ModelRouter, TaskComplexity
from .analytics import RoutingAnalytics
from .ab_testing import ABTestManager

__all__ = ['ModelRouter', 'TaskComplexity', 'RoutingAnalytics', 'ABTestManager']
