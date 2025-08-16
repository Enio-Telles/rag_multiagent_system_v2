"""
Módulo de database
"""

from .models import Base, ClassificacaoRevisao, GoldenSetEntry, MetricasQualidade
from .connection import get_db, create_tables, test_connection, SessionLocal

__all__ = [
    "Base",
    "ClassificacaoRevisao", 
    "GoldenSetEntry",
    "MetricasQualidade",
    "get_db",
    "create_tables",
    "test_connection",
    "SessionLocal"
]
