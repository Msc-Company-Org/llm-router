"""Contrato de provider e um provider falso para testes/exemplos.

Qualquer backend — OpenAI-compatible, Anthropic, vLLM, Ollama — é apenas uma
implementação do protocolo ``Provider`` (um atributo ``name``, ``model`` e um
método ``complete``). O roteador não conhece detalhes de nenhum provider.
"""
from __future__ import annotations

import time
from typing import Protocol, Sequence, runtime_checkable

from .types import Completion, Message, ProviderError


@runtime_checkable
class Provider(Protocol):
    """Contrato mínimo de um provider de LLM."""

    name: str
    model: str

    def complete(self, messages: Sequence[Message]) -> Completion:
        ...


class FakeProvider:
    """Provider determinístico, sem rede — para testes, exemplos e CI.

    Pode simular falha (``fail=True``) para exercitar o caminho de fallback, e
    custo/latência fixos para validar budget e telemetria.
    """

    def __init__(
        self,
        name: str,
        model: str = "fake-1",
        *,
        reply: str = "ok",
        cost_usd: float = 0.001,
        latency_ms: float = 0.0,
        fail: bool = False,
    ) -> None:
        self.name = name
        self.model = model
        self._reply = reply
        self._cost = cost_usd
        self._latency = latency_ms
        self._fail = fail

    def complete(self, messages: Sequence[Message]) -> Completion:
        if self._latency:
            time.sleep(self._latency / 1000.0)
        if self._fail:
            raise ProviderError(f"{self.name}: falha simulada")
        prompt = " ".join(m.content for m in messages)
        return Completion(
            text=self._reply,
            model=self.model,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(self._reply.split()),
            cost_usd=self._cost,
        )
