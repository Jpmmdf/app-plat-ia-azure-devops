# Prompt de Task (API-First)

## Objetivo

Quebrar um PBI em itens `TaskIn` compatíveis com a API:

- Endpoint: `POST /v1/scrum/execute`
- Caminho no payload: `epics[n].features[m].pbis[k].tasks[]`

---

## Contrato de saída (obrigatório)

Retorne **somente JSON válido** no formato:

```json
[
  {
    "title": "string",
    "description": "string markdown",
    "acceptance_criteria": [
      "criterio 1",
      "criterio 2"
    ]
  }
]
```

---

## Regras

1. Retornar lista de Tasks (mesmo quando houver apenas 1).
2. Não incluir campos fora do schema `TaskIn`.
3. Cada task deve ter escopo pequeno e executável.
4. `acceptance_criteria` deve ser checklist verificável.
5. Evitar tasks genéricas sem resultado observável.

---

## Estrutura recomendada para `description`

- `## Contexto Tecnico`
- `## Escopo`
- `## Implementacao Esperada`
- `## Dependências Tecnicas`
- `## Validacoes e Evidencias`

---

## Mapeamento para API

- `title` -> `TaskIn.title`
- `description` -> `TaskIn.description`
- `acceptance_criteria` -> `TaskIn.acceptance_criteria`  
  (quando o tipo não suporta campo dedicado de critérios, a automação faz fallback para `Description`)

---

## Exemplo de saída

```json
[
  {
    "title": "Implementar validacao de X-API-Key",
    "description": "## Contexto Tecnico\\n...",
    "acceptance_criteria": [
      "Requisicao sem chave retorna erro de autenticacao",
      "Requisicao com chave valida prossegue para execucao"
    ]
  }
]
```

---

## Entrada

```text
[COLE AQUI O PBI QUE SERA QUEBRADO EM TASKS]
```
