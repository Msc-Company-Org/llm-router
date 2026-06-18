"""llm-router — roteador multi-modelo com fallback, budget e telemetria.

Sem dependências externas. Plugue qualquer provider implementando o protocolo
``Provider`` e descreva sua matriz de roteamento ``(tarefa × prioridade)``.
"""
from .budget import BudgetTracker
from .providers import FakeProvider, Provider
from .router import Router
from .telemetry import Record, Telemetry
from .types import (
    Completion,
    Message,
    Priority,
    ProviderError,
    RouteResult,
    TaskType,
)

__all__ = [
    "Router",
    "Provider",
    "FakeProvider",
    "BudgetTracker",
    "Telemetry",
    "Record",
    "Message",
    "Completion",
    "TaskType",
    "Priority",
    "RouteResult",
    "ProviderError",
]
__version__ = "0.1.0"
