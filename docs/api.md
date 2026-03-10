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

## Modo performance (backlog grande)

Para reduzir tempo total de execucao em backlog volumoso:

1. Criar epics em lote: `POST /v1/backlog/epics`.
2. Criar features por epic: `POST /v1/backlog/epics/{epic_id}/features`.
3. Criar PBIs em blocos usando endpoint direto:
   - `POST /v1/backlog/product-backlog-items`
   - cada item com `parent_id` da feature correspondente.
4. Criar Tasks em blocos usando endpoint direto:
   - `POST /v1/backlog/tasks`
   - cada item com `parent_id` do PBI correspondente.

Recomendacao de chunk:

- 10 a 25 itens por chamada para PBIs e Tasks.
- Em timeout/falha por volume, reduzir tamanho do bloco.
- A API valida limite por requisicao para PBIs/Tasks e retorna `400` se exceder.

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
- `failed[]` com falhas parciais por item:
  - `type`
  - `title`
  - `parent_id` (quando aplicavel)
  - `error`

## OpenAPI

- `openapi.yaml`
- `openapi.json`

Regenerar:

```bash
./.venv/bin/python generate_openapi.py --output openapi.yaml
./.venv/bin/python generate_openapi.py --output openapi.json --format json
```
