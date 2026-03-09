# Prompt de PBI (API-First)

## Objetivo

Gerar payload para criar PBIs em uma Feature existente.

- Consulta previa: `GET /v1/backlog/work-items/{feature_id}`
- Criacao: `POST /v1/backlog/features/{feature_id}/product-backlog-items`

## Contrato de saida (body)

Retorne somente JSON valido:

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string ou null"
  },
  "product_backlog_items": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1",
        "criterio 2"
      ]
    }
  ]
}
```

## Regras

1. Nao incluir `parent_id` no body do endpoint nested.
2. Cada PBI deve ser entregavel e testavel.
3. `acceptance_criteria` verificavel.

## Entrada

```text
[COLE AQUI A FEATURE + O ID DA FEATURE]
```
