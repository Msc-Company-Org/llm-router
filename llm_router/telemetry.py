"""Telemetria simples: latência (p50/p95), custo e taxa de fallback.

Sem dependências externas. O que você não mede, você não opera — só reza.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Record:
    """Uma observação de execução de provider."""

    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    used_fallback: bool
    ok: bool


class Telemetry:
    """Coletor em memória de métricas de execução."""

    def __init__(self) -> None:
        self._records: list[Record] = []

    def record(self, rec: Record) -> None:
        self._records.append(rec)

    @property
    def count(self) -> int:
        return len(self._records)

    def _latencies(self) -> list[float]:
        return sorted(r.latency_ms for r in self._records if r.ok)

    def percentile(self, p: float) -> float:
        """Percentil ``p`` (0..1) das latências bem-sucedidas, com interpolação."""
        lat = self._latencies()
        if not lat:
            return 0.0
        if len(lat) == 1:
            return lat[0]
        k = (len(lat) - 1) * p
        f = int(k)
        c = min(f + 1, len(lat) - 1)
        return lat[f] + (lat[c] - lat[f]) * (k - f)

    @property
    def p50(self) -> float:
        return self.percentile(0.50)

    @property
    def p95(self) -> float:
        return self.percentile(0.95)

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self._records)

    @property
    def fallback_rate(self) -> float:
        if not self._records:
            return 0.0
        return sum(1 for r in self._records if r.used_fallback) / len(self._records)

    def summary(self) -> dict:
        return {
            "requests": self.count,
            "p50_ms": round(self.p50, 2),
            "p95_ms": round(self.p95, 2),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "fallback_rate": round(self.fallback_rate, 4),
        }
