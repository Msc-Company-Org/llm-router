"""Tipos centrais do roteador: tarefa, prioridade, mensagem e resultado."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(str, Enum):
    """Tipo de tarefa — uma das dimensões da matriz de roteamento."""

    CHAT = "chat"
    RAG_QA = "rag_qa"
    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    RERANK = "rerank"


class Priority(str, Enum):
    """Prioridade da requisição.

    Define qual rota da matriz é escolhida e interage com o budget: quando o
    orçamento aperta, a prioridade efetiva é rebaixada (degradação graciosa).
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def downgrade(self) -> "Priority":
        """Retorna a prioridade um nível abaixo (LOW é o piso)."""
        order = [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
        i = order.index(self)
        return order[min(i + 1, len(order) - 1)]


@dataclass
class Message:
    """Mensagem de um turno de conversa."""

    role: str
    content: str


@dataclass
class Completion:
    """Resposta crua devolvida por um provider."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class RouteResult:
    """Resultado de uma rota: resposta + metadados de execução."""

    text: str
    model: str
    provider: str
    cost_usd: float
    latency_ms: float
    attempts: int          # quantos providers foram tentados (1 = primário de primeira)
    used_fallback: bool    # True se algum primário falhou antes deste responder
    degraded: bool         # True se a prioridade foi rebaixada por budget


class ProviderError(Exception):
    """Falha recuperável de provider (rate limit, timeout, 5xx) — dispara fallback."""
