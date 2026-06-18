"""Roteador multi-modelo com fallback em cascata, budget e telemetria."""
from __future__ import annotations

import time
from typing import Mapping, Sequence

from .budget import BudgetTracker
from .providers import Provider
from .telemetry import Record, Telemetry
from .types import Message, Priority, ProviderError, RouteResult, TaskType

RouteKey = tuple[TaskType, Priority]


class Router:
    """Escolhe o modelo certo por ``(tarefa × prioridade)`` e tenta fallbacks.

    - ``routes`` mapeia ``(TaskType, Priority)`` → lista de nomes de provider em
      ordem de preferência: ``[primário, fallback 1, fallback 2, ...]``.
    - Se o budget passar de 80%, a prioridade efetiva é **rebaixada** antes de
      resolver a rota (degradação graciosa em vez de queda).
    - Os providers da cadeia são tentados em ordem; o primeiro a responder vence.
      Se todos falharem, levanta ``RuntimeError``.
    """

    def __init__(
        self,
        providers: Sequence[Provider],
        routes: Mapping[RouteKey, Sequence[str]],
        *,
        budget: BudgetTracker | None = None,
        telemetry: Telemetry | None = None,
    ) -> None:
        self._providers = {p.name: p for p in providers}
        self._routes = dict(routes)
        self.budget = budget
        self.telemetry = telemetry or Telemetry()
        self._validate()

    def _validate(self) -> None:
        for key, chain in self._routes.items():
            if not chain:
                raise ValueError(f"rota {key} não tem providers")
            for name in chain:
                if name not in self._providers:
                    raise ValueError(
                        f"rota {key} referencia provider desconhecido: {name!r}"
                    )

    def _resolve_priority(self, priority: Priority) -> tuple[Priority, bool]:
        """Aplica a regra de budget. Retorna (prioridade_efetiva, foi_rebaixada)."""
        if self.budget and self.budget.should_downgrade():
            if self.budget.is_exhausted():
                return Priority.LOW, True
            return priority.downgrade(), True
        return priority, False

    def complete(
        self,
        messages: Sequence[Message],
        *,
        task_type: TaskType,
        priority: Priority = Priority.MEDIUM,
    ) -> RouteResult:
        eff_priority, degraded = self._resolve_priority(priority)
        key = (task_type, eff_priority)
        if key not in self._routes:
            raise KeyError(f"sem rota definida para {key}")
        chain = self._routes[key]

        last_error: Exception | None = None
        for attempt, name in enumerate(chain, start=1):
            provider = self._providers[name]
            used_fallback = attempt > 1
            t0 = time.perf_counter()
            try:
                completion = provider.complete(messages)
            except ProviderError as exc:
                latency_ms = (time.perf_counter() - t0) * 1000
                self.telemetry.record(
                    Record(
                        provider=name,
                        model=provider.model,
                        latency_ms=latency_ms,
                        cost_usd=0.0,
                        used_fallback=used_fallback,
                        ok=False,
                    )
                )
                last_error = exc
                continue

            latency_ms = (time.perf_counter() - t0) * 1000
            if self.budget:
                self.budget.add(completion.cost_usd)
            self.telemetry.record(
                Record(
                    provider=name,
                    model=completion.model,
                    latency_ms=latency_ms,
                    cost_usd=completion.cost_usd,
                    used_fallback=used_fallback,
                    ok=True,
                )
            )
            return RouteResult(
                text=completion.text,
                model=completion.model,
                provider=name,
                cost_usd=completion.cost_usd,
                latency_ms=latency_ms,
                attempts=attempt,
                used_fallback=used_fallback,
                degraded=degraded,
            )

        raise RuntimeError(
            f"todos os providers falharam para {key}: {list(chain)}"
        ) from last_error
