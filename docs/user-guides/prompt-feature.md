# Prompt de Feature (API-First)

## Objetivo

Gerar payload para criar features em um Epic existente.

- Consulta previa: `GET /v1/backlog/work-items/{epic_id}`
- Criacao: `POST /v1/backlog/epics/{epic_id}/features`

## Contrato de saida (body)

Retorne somente JSON valido:

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
        "criterio 1",
        "criterio 2"
      ]
    }
  ]
}
```

## Regras

1. Nao incluir `parent_id` no body do endpoint nested.
2. `title` orientado a valor.
3. `description` em markdown.
4. `acceptance_criteria` objetiva e testavel.
5. Gerar `defaults.tags` obrigatoriamente (nao usar `null` por padrao).

## Regra de tags (obrigatoria)

- Preencher `defaults.tags` com 3 a 8 tags separadas por `;`.
- Incluir contexto funcional + tecnologia + objetivo.
- Se o usuario informar tags, priorizar essas tags e complementar sem duplicidade.
- So usar `null` se o usuario pedir explicitamente.

## Entrada

```text
[COLE AQUI A NECESSIDADE DA FEATURE + O ID DO EPIC]
```
