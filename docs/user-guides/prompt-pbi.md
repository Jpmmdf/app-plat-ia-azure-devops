# Prompt de PBI (API-First)

## Objetivo

Quebrar uma Feature em itens `PbiIn` compatíveis com a API:

- Endpoint: `POST /v1/scrum/execute`
- Caminho no payload: `epics[n].features[m].pbis[]`

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
    ],
    "tasks": []
  }
]
```

---

## Regras

1. Retornar uma lista de PBIs (mesmo que contenha apenas 1 item).
2. Não incluir campos fora do schema `PbiIn`.
3. Cada PBI deve ser entregável e testável de forma independente.
4. `acceptance_criteria` deve ser objetivo e verificável.
5. `tasks` deve começar vazio quando as tarefas ainda não foram decompostas.

---

## Estrutura recomendada para `description`

- `## User Story`
- `## Contexto Funcional`
- `## Regras de Negocio`
- `## Dependências`
- `## Riscos`
- `## Indicadores de Sucesso`

---

## Mapeamento para API

- `title` -> `PbiIn.title`
- `description` -> `PbiIn.description`
- `acceptance_criteria` -> `PbiIn.acceptance_criteria`
- `tasks` -> `PbiIn.tasks`

---

## Exemplo de saída

```json
[
  {
    "title": "Validar payload do endpoint de execucao",
    "description": "## User Story\\n...",
    "acceptance_criteria": [
      "Payload invalido retorna erro de validacao",
      "Payload valido cria item sem inconsistencias"
    ],
    "tasks": []
  }
]
```

---

## Entrada

```text
[COLE AQUI A FEATURE QUE SERA FATIADA EM PBIS]
```
