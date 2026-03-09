# API

## Endpoint principal

`POST /v1/scrum/execute`

### Headers

- `X-API-Key`: obrigatório para autenticação.

### Request body

Schema `PlanIn`:

- `defaults`:
  - `area_path`
  - `iteration_path`
  - `tags`
- `epics[]`:
  - `title`
  - `description`
  - `acceptance_criteria`
  - `features[]`

Composição aninhada:

- `features[]` -> `pbis[]` -> `tasks[]`
- Todos os níveis aceitam:
  - `title`
  - `description`
  - `acceptance_criteria`

### Response

- `org`
- `project`
- `created` com IDs e URLs por nível criado.

## Exemplo

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "automation;api"
  },
  "epics": [
    {
      "title": "Automacao de backlog",
      "description": "## Contexto\n...",
      "acceptance_criteria": [
        "Critério 1",
        "Critério 2"
      ],
      "features": []
    }
  ]
}
```

## OpenAPI

- `openapi.yaml`
- `openapi.json`

Regenerar:

```bash
./.venv/bin/python generate_openapi.py --output openapi.yaml
./.venv/bin/python generate_openapi.py --output openapi.json --format json
```
