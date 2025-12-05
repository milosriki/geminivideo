"""
Market Intelligence Service

Tracks competitor ads, analyzes market trends, and provides actionable insights.
This service replaces fake/hardcoded data with real market intelligence.
"""

from .csv_importer import CSVImporter
from .competitor_tracker import CompetitorTracker

__all__ = ['CSVImporter', 'CompetitorTracker']
