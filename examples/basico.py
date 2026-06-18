"""Exemplo mínimo: roteamento com fallback, budget e telemetria.

Usa ``FakeProvider`` (sem rede). Em produção, troque por wrappers de provedores
reais (OpenAI-compatible, Anthropic, vLLM/Ollama...) — basta implementar o
método ``complete``.

    python examples/basico.py
"""
from llm_router import (
    BudgetTracker,
    FakeProvider,
    Message,
    Priority,
    Router,
    TaskType,
    Telemetry,
)


def main() -> None:
    forte = FakeProvider("forte", model="forte-v1", reply="resposta de qualidade", cost_usd=0.02)
    rapido = FakeProvider("rapido", model="rapido-v1", reply="resposta rápida", cost_usd=0.002)
    # 'instavel' simula um primário com rate limit, para demonstrar o fallback:
    instavel = FakeProvider("instavel", model="instavel-v1", fail=True)

    routes = {
        (TaskType.RAG_QA, Priority.HIGH): ["instavel", "forte"],  # primário cai -> fallback
        (TaskType.CHAT, Priority.MEDIUM): ["rapido", "forte"],
        (TaskType.CHAT, Priority.LOW): ["rapido"],
    }

    budget = BudgetTracker(limit_usd=10.0)
    router = Router([forte, rapido, instavel], routes, budget=budget, telemetry=Telemetry())

    perguntas = [
        (TaskType.RAG_QA, Priority.HIGH, "Qual o prazo do processo?"),
        (TaskType.CHAT, Priority.MEDIUM, "Resuma isto em uma frase."),
        (TaskType.CHAT, Priority.MEDIUM, "Obrigado!"),
    ]

    for task, prio, texto in perguntas:
        res = router.complete([Message("user", texto)], task_type=task, priority=prio)
        flag = " (fallback)" if res.used_fallback else ""
        print(f"[{task.value:<7}] {res.provider:<13} {res.latency_ms:6.2f}ms{flag} -> {res.text}")

    print("\nTelemetria:", router.telemetry.summary())
    print(f"Budget gasto: ${budget.spent_usd:.4f} / ${budget.limit_usd:.2f}")


if __name__ == "__main__":
    main()
