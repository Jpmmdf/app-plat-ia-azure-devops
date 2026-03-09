# Prompt de Epic (API-First)

## Objetivo

Transformar uma necessidade ampla em um objeto `EpicIn` compatível com a API:

- Endpoint: `POST /v1/scrum/execute`
- Caminho no payload: `epics[]`

---

## Contrato de saída (obrigatório)

Retorne **somente JSON válido** (sem markdown fora do JSON) no formato:

```json
{
  "title": "string",
  "description": "string markdown",
  "acceptance_criteria": [
    "criterio 1",
    "criterio 2",
    "criterio 3"
  ],
  "features": []
}
```

---

## Regras

1. Não inventar campos fora do schema da API.
2. `title` deve ser curto e orientado a resultado.
3. `description` deve ser markdown com contexto executivo.
4. `acceptance_criteria` deve ser lista de 3 a 7 critérios verificáveis.
5. Se não houver dados suficientes para números/datas, usar premissas explícitas em `description`.
6. Manter `features` como lista vazia quando a quebra ainda não for feita.

---

## Estrutura recomendada para `description`

- `## Contexto`
- `## Problema ou Oportunidade`
- `## Objetivo do Epic`
- `## Escopo de Alto Nível`
- `## Fora de Escopo`
- `## Dependências`
- `## Riscos`
- `## Indicadores de Sucesso`

---

## Mapeamento para API

- `title` -> `EpicIn.title`
- `description` -> `EpicIn.description` (`System.Description`)
- `acceptance_criteria` -> `EpicIn.acceptance_criteria` (`Microsoft.VSTS.Common.AcceptanceCriteria`, com fallback em `Description`)
- `features` -> `EpicIn.features`

Observação: a automação define `multilineFieldsFormat` como markdown para campos multilinha enviados.

---

## Exemplo de uso no payload final

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "automation;platform"
  },
  "epics": [
    {
      "title": "Automacao de Backlog no Azure DevOps",
      "description": "## Contexto\\n...",
      "acceptance_criteria": [
        "Criterio 1",
        "Criterio 2",
        "Criterio 3"
      ],
      "features": []
    }
  ]
}
```

---

## Entrada

```text
[COLE AQUI A NECESSIDADE DE NEGOCIO]
```
