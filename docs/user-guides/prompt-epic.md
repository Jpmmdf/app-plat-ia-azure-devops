# Prompt de Epic (API-First)

## Objetivo

Transformar uma necessidade ampla em payload para criacao de epics:

- Endpoint: `POST /v1/backlog/epics`
- Caminho no payload: `epics[]`

## Contrato de saida (obrigatorio)

Retorne **somente JSON valido** no formato:

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string com 3 a 8 tags separadas por ; (null somente se solicitado)"
  },
  "epics": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1",
        "criterio 2",
        "criterio 3"
      ]
    }
  ]
}
```

## Regras

1. Nao inventar campos fora do schema da API.
2. `title` deve ser curto e orientado a resultado.
3. `description` deve ser markdown com contexto executivo.
4. `acceptance_criteria` deve ser lista de 3 a 7 criterios verificaveis.
5. Se nao houver dados suficientes para numeros/datas, usar premissas explicitas em `description`.
6. Gerar `defaults.tags` obrigatoriamente (nao usar `null` por padrao).

## Regra de tags (obrigatoria)

- Sempre preencher `defaults.tags` com 3 a 8 tags.
- Formato: string unica separada por `;` (ex.: `backstage;aws;platform-engineering`).
- Usar tags de dominio, tecnologia e objetivo de negocio.
- Se o usuario informar tags, reaproveitar e complementar sem duplicar.
- So usar `null` se o usuario pedir explicitamente "sem tags".

## Estrutura recomendada para `description`

- `## Contexto`
- `## Problema ou Oportunidade`
- `## Objetivo do Epic`
- `## Escopo de Alto Nivel`
- `## Fora de Escopo`
- `## Dependencias`
- `## Riscos`
- `## Indicadores de Sucesso`

## Mapeamento para API

- `epics[].title` -> `System.Title`
- `epics[].description` -> `System.Description`
- `epics[].acceptance_criteria` -> `Microsoft.VSTS.Common.AcceptanceCriteria` (com fallback em `Description`)

Observacao: a automacao define `multilineFieldsFormat` como markdown para campos multilinha enviados.

## Entrada

```text
[COLE AQUI A NECESSIDADE DE NEGOCIO]
```
