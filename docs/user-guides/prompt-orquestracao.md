# Prompt de Orquestracao (API-First)

## Objetivo

Gerar payloads para criacao de backlog por etapas, com suporte a ID existente.

Endpoints usados:

- Consulta: `GET /v1/backlog/work-items/{work_item_id}`
- Criacao nested:
  - `POST /v1/backlog/epics/{epic_id}/features`
  - `POST /v1/backlog/features/{feature_id}/product-backlog-items`
  - `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

## Regras

1. Retornar somente JSON valido para body.
2. Nao usar campos fora dos schemas da API.
3. `description` em markdown.
4. `acceptance_criteria` como lista verificavel.
5. Em endpoints nested, nao incluir `parent_id` no body.
6. Gerar `defaults.tags` obrigatoriamente (nao usar `null` por padrao).

## Regra de tags (obrigatoria)

- Em cada payload gerado, preencher `defaults.tags` com 3 a 8 tags separadas por `;`.
- Manter coerencia de tags ao longo da hierarquia (Epic -> Feature -> PBI -> Task).
- Reutilizar tags centrais do item pai e acrescentar tags do nivel atual.
- So usar `null` se o usuario pedir explicitamente "sem tags".

## Fluxo quando o usuario fornece ID

1. Consultar o item por ID.
2. Validar o tipo retornado.
3. Gerar payload para o endpoint nested correspondente.

## Contrato de body: features para epic

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string com 3 a 8 tags separadas por ; (null somente se solicitado)"
  },
  "features": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1"
      ]
    }
  ]
}
```

## Contrato de body: pbis para feature

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string com 3 a 8 tags separadas por ; (null somente se solicitado)"
  },
  "product_backlog_items": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1"
      ]
    }
  ]
}
```

## Contrato de body: tasks para pbi

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string com 3 a 8 tags separadas por ; (null somente se solicitado)"
  },
  "tasks": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1"
      ]
    }
  ]
}
```

## Entrada

```text
[COLE AQUI A NECESSIDADE, O ITEM BASE E O ID DO ITEM]
```
