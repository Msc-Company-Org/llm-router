<div align="center">

# 🔀 llm-router

**Roteador multi-modelo para LLMs em produção — fallback em cascata, controle de budget e telemetria. Zero dependências.**

[![Licença: MIT](https://img.shields.io/badge/Licença-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Dependências](https://img.shields.io/badge/dependências-0-brightgreen)
![Tema](https://img.shields.io/badge/LLM·RAG·Agentes-6C3CFF)

*Um único modelo é caro **e** frágil. Roteie por tarefa, caia para o fallback quando o primário falhar, e saiba exatamente quanto custou.*

</div>

---

## Por quê?

Quem coloca LLM em produção descobre rápido que:

- **o provider cai** (rate limit, timeout, 5xx) — e leva seu produto junto;
- **um modelo só não serve para tudo** — classificação curta não precisa do top de linha; raciocínio longo precisa;
- **custo é arquitetura** — a conta da API define qual modelo roteia qual tarefa;
- **sem telemetria, "está lento/caro" vira caça-fantasma.**

`llm-router` resolve isso com uma peça pequena, sem dependências e fácil de auditar.

## Como funciona

Você descreve uma **matriz de roteamento** `(tarefa × prioridade) → [primário, fallback 1, fallback 2, ...]`. O roteador tenta cada provider em ordem; o primeiro que responder vence. Se o budget apertar, a prioridade efetiva é **rebaixada** (degradação graciosa, não queda).

```
   complete(task_type, priority)
              │
   budget > 80%? ── sim ──► rebaixa prioridade efetiva
              │
              ▼
   rota = routes[(task, priority)]  ─►  [ primário ] → falhou? → [ fallback ] → ...
              │                                                         │
              └──────────────► telemetria (latência, custo, fallback) ◄─┘
```

## Instalação

```bash
pip install -e .          # local, a partir do repositório
# requisitos: Python 3.10+ · nenhuma dependência de runtime
```

## Uso em 30 segundos

```python
from llm_router import Router, FakeProvider, Message, TaskType, Priority, BudgetTracker

# Em produção, troque FakeProvider por wrappers de OpenAI-compatible, Anthropic, vLLM...
forte  = FakeProvider("forte",  reply="resposta de qualidade", cost_usd=0.02)
rapido = FakeProvider("rapido", reply="resposta rápida",       cost_usd=0.002)

routes = {
    (TaskType.RAG_QA, Priority.HIGH):   ["forte", "rapido"],   # primário + fallback
    (TaskType.CHAT,   Priority.MEDIUM): ["rapido", "forte"],
}

router = Router([forte, rapido], routes, budget=BudgetTracker(limit_usd=10.0))

res = router.complete(
    [Message("user", "Qual o prazo do processo?")],
    task_type=TaskType.RAG_QA,
    priority=Priority.HIGH,
)
print(res.text, res.provider, f"{res.latency_ms:.1f}ms", f"${res.cost_usd}")
print(router.telemetry.summary())
# {'requests': 1, 'p50_ms': ..., 'p95_ms': ..., 'total_cost_usd': 0.02, 'fallback_rate': 0.0}
```

Rode o exemplo completo:

```bash
python examples/basico.py
```

## Plugando um provider real

Qualquer backend é só uma classe com `name`, `model` e um método `complete`:

```python
from llm_router import Completion, Message

class OpenAICompatible:
    name = "meu-provider"
    model = "gpt-x"

    def __init__(self, client):
        self._client = client

    def complete(self, messages):
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        choice = resp.choices[0].message.content
        usage = resp.usage
        return Completion(
            text=choice,
            model=self.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost_usd=estimar_custo(usage),  # sua tabela de preço
        )
    # Levante llm_router.ProviderError em falhas recuperáveis (rate limit/timeout)
    # para acionar o fallback automaticamente.
```

## O que vem na caixa

| Componente | Função |
|---|---|
| `Router` | Resolve a rota, executa fallback em cascata, registra telemetria |
| `BudgetTracker` | Gasto vs. teto; rebaixa prioridade em 80%, força econômico em 100% |
| `Telemetry` | Latência p50/p95, custo total, taxa de fallback |
| `Provider` (protocolo) | Contrato mínimo para plugar qualquer LLM |
| `FakeProvider` | Provider determinístico para testes/CI, sem rede |

## Testes

```bash
pip install -e ".[dev]"
pytest -q
```

## Licença

MIT © 2026 [Moisés Costa](https://github.com/Finish-Him) / [MSC Company](https://github.com/Msc-Company-Org)

> Destilado de padrões usados em agentes de IA em produção. Conceitos e o "porquê" de cada decisão estão no guia **[IA em Produção](https://github.com/Finish-Him/ia-em-producao)**.
>
> ⭐ Útil pra você? Uma estrela ajuda o projeto a alcançar mais devs.

---

## 🚀 Built by MSC Labs

A public reference from **MSC Labs** — we fine-tune and ship custom LLMs (QLoRA/SFT) with managed inference, benchmarked against frontier-API baselines.

**→ [Train your own model with MSC Labs](https://labs.msccompany.com.br/?utm_source=github&utm_medium=readme&utm_campaign=oss-authority-2026&utm_content=llm-router)**

⭐ *Star this repo if it helps — it keeps the reference models coming.*
