# Prompt de Task (API-First)

## Objetivo

Gerar payload para criar tasks em um PBI existente.

- Consulta previa: `GET /v1/backlog/work-items/{product_backlog_item_id}`
- Criacao: `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

## Contrato de saida (body)

Retorne somente JSON valido:

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
        "criterio 1",
        "criterio 2"
      ]
    }
  ]
}
```

## Regras

1. Nao incluir `parent_id` no body do endpoint nested.
2. Cada task deve ter escopo pequeno e executavel.
3. `acceptance_criteria` deve ser checklist verificavel.
4. Gerar `defaults.tags` obrigatoriamente (nao usar `null` por padrao).

## Regra de tags (obrigatoria)

- Preencher `defaults.tags` com 3 a 8 tags separadas por `;`.
- Incluir componente/tema tecnico + fase de trabalho (ex.: implementacao, validacao, observabilidade).
- Herdar tags do PBI/Feature quando aplicavel.
- So usar `null` se o usuario pedir explicitamente.

## Entrada

```text
[COLE AQUI O PBI + O ID DO PBI]
```
