"""Controle de orçamento: indica quando rebaixar a prioridade por custo."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetTracker:
    """Acompanha o gasto contra um teto e sinaliza quando degradar.

    Regra (inspirada em uso real em produção):

    - até **80%** do teto → roteamento normal;
    - entre **80% e 100%** → rebaixa a prioridade efetiva (modelos mais baratos);
    - em **100%** → força o nível mais econômico.

    O sistema **degrada** a qualidade em vez de **cair**.
    """

    limit_usd: float
    spent_usd: float = 0.0

    @property
    def ratio(self) -> float:
        if self.limit_usd <= 0:
            return 0.0
        return self.spent_usd / self.limit_usd

    def should_downgrade(self) -> bool:
        return self.ratio >= 0.8

    def is_exhausted(self) -> bool:
        return self.ratio >= 1.0

    def add(self, cost_usd: float) -> None:
        self.spent_usd += cost_usd
