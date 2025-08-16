"""
Módulo de feedback e aprendizagem contínua
Implementa as Fases 4 e 5 do sistema de classificação fiscal
"""

# Fase 4: Interface de Revisão Humana
from .review_service import ReviewService
from .metrics_service import MetricsService

# Fase 5: Aprendizagem Contínua
try:
    from .continuous_learning import GoldenSetManager, AugmentedRetrieval, ContinuousLearningScheduler
    CONTINUOUS_LEARNING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Aprendizagem contínua não disponível: {e}")
    CONTINUOUS_LEARNING_AVAILABLE = False

__all__ = [
    "ReviewService",
    "MetricsService",
]

if CONTINUOUS_LEARNING_AVAILABLE:
    __all__.extend([
        "GoldenSetManager",
        "AugmentedRetrieval", 
        "ContinuousLearningScheduler"
    ])
