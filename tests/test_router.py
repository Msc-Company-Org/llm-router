from llm_router import (
    BudgetTracker,
    FakeProvider,
    Message,
    Priority,
    Router,
    TaskType,
)


def msgs(text="oi"):
    return [Message(role="user", content=text)]


def test_roteia_para_primario():
    primary = FakeProvider("primary", reply="resposta-primaria")
    fb = FakeProvider("fb", reply="resposta-fb")
    r = Router([primary, fb], {(TaskType.CHAT, Priority.MEDIUM): ["primary", "fb"]})

    res = r.complete(msgs(), task_type=TaskType.CHAT)

    assert res.text == "resposta-primaria"
    assert res.provider == "primary"
    assert res.attempts == 1
    assert res.used_fallback is False


def test_cai_para_fallback_quando_primario_falha():
    primary = FakeProvider("primary", fail=True)
    fb = FakeProvider("fb", reply="salvo-pelo-fb")
    r = Router([primary, fb], {(TaskType.CHAT, Priority.MEDIUM): ["primary", "fb"]})

    res = r.complete(msgs(), task_type=TaskType.CHAT)

    assert res.text == "salvo-pelo-fb"
    assert res.provider == "fb"
    assert res.attempts == 2
    assert res.used_fallback is True


def test_erro_quando_todos_falham():
    p1 = FakeProvider("p1", fail=True)
    p2 = FakeProvider("p2", fail=True)
    r = Router([p1, p2], {(TaskType.CHAT, Priority.HIGH): ["p1", "p2"]})

    try:
        r.complete(msgs(), task_type=TaskType.CHAT, priority=Priority.HIGH)
        assert False, "deveria ter levantado RuntimeError"
    except RuntimeError:
        pass


def test_budget_rebaixa_prioridade():
    forte = FakeProvider("forte", reply="forte", cost_usd=1.0)
    barato = FakeProvider("barato", reply="barato", cost_usd=0.01)
    budget = BudgetTracker(limit_usd=1.0, spent_usd=0.9)  # 90% -> deve rebaixar
    routes = {
        (TaskType.CHAT, Priority.HIGH): ["forte"],
        (TaskType.CHAT, Priority.MEDIUM): ["barato"],
    }
    r = Router([forte, barato], routes, budget=budget)

    res = r.complete(msgs(), task_type=TaskType.CHAT, priority=Priority.HIGH)

    assert res.degraded is True
    assert res.provider == "barato"


def test_rota_invalida_falha_na_construcao():
    p = FakeProvider("p")
    try:
        Router([p], {(TaskType.CHAT, Priority.LOW): ["inexistente"]})
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


def test_telemetria_acumula():
    p = FakeProvider("p", reply="ok")
    r = Router([p], {(TaskType.CHAT, Priority.MEDIUM): ["p"]})

    for _ in range(5):
        r.complete(msgs(), task_type=TaskType.CHAT)

    s = r.telemetry.summary()
    assert s["requests"] == 5
    assert s["p50_ms"] >= 0
    assert s["total_cost_usd"] > 0
