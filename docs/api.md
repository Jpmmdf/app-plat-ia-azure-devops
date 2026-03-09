# API

## Endpoints

Consulta:

- `GET /v1/backlog/work-items/{work_item_id}`

Criacao recomendada (nested por pai):

- `POST /v1/backlog/epics/{epic_id}/features`
- `POST /v1/backlog/features/{feature_id}/product-backlog-items`
- `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

Criacao direta (bulk):

- `POST /v1/backlog/epics`
- `POST /v1/backlog/features`
- `POST /v1/backlog/product-backlog-items`
- `POST /v1/backlog/tasks`

### Headers

- `X-API-Key`: obrigatorio para autenticacao.

## Fluxo recomendado para Custom GPT

1. Receber o ID de item existente do usuario.
2. Consultar `GET /v1/backlog/work-items/{work_item_id}`.
3. Criar proximo nivel com endpoint nested correspondente.
4. Repetir para os niveis seguintes.

## Exemplo: usuario passou ID de Epic

### 1) Consultar o epic

`GET /v1/backlog/work-items/12345`

Response (exemplo):

```json
{
  "org": "minha-org",
  "project": "meu-projeto",
  "id": 12345,
  "type": "Epic",
  "title": "Automacao de backlog",
  "url": "https://dev.azure.com/...",
  "parent_id": null,
  "child_ids": []
}
```

### 2) Criar features nesse epic

`POST /v1/backlog/epics/12345/features`

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "automation;api"
  },
  "features": [
    {
      "title": "API de orquestracao",
      "description": "## Contexto\n...",
      "acceptance_criteria": [
        "Criar features via endpoint nested"
      ]
    }
  ]
}
```

## Schemas de criacao

Todos os endpoints de criacao aceitam `defaults`:

- `area_path`
- `iteration_path`
- `tags`

Em endpoints nested, o pai vem no path.
Em endpoints diretos de filhos, `parent_id` e obrigatorio no body.

## Response de criacao

- `org`
- `project`
- `created[]` com:
  - `id`
  - `type`
  - `title`
  - `url`
  - `parent_id` (quando aplicavel)

## OpenAPI

- `openapi.yaml`
- `openapi.json`

Regenerar:

```bash
./.venv/bin/python generate_openapi.py --output openapi.yaml
./.venv/bin/python generate_openapi.py --output openapi.json --format json
```
