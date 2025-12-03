"""
Titan Knowledge Base Module

Provides versioned knowledge management with hot-reload capability.
Agent 14: Knowledge Base Hot-Reload Engineer
"""
from .manager import (
    KnowledgeBaseManager,
    get_manager,
    VersionInfo,
    StorageBackend,
    LocalFileSystemBackend,
    GCSBackend,
)
from .core import TitanKnowledge, titan_knowledge

__all__ = [
    'KnowledgeBaseManager',
    'get_manager',
    'VersionInfo',
    'StorageBackend',
    'LocalFileSystemBackend',
    'GCSBackend',
    'TitanKnowledge',
    'titan_knowledge',
]
