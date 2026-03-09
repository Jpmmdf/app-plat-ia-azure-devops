# Prompt de Orquestracao (API-First)

## Objetivo

Gerar um payload completo e pronto para ingestao pela API:

- Endpoint: `POST /v1/scrum/execute`
- Schema alvo: `PlanIn`

---

## Contrato de saída (obrigatório)

Retorne **somente JSON válido** no formato:

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "string ou null"
  },
  "epics": [
    {
      "title": "string",
      "description": "string markdown",
      "acceptance_criteria": [
        "criterio 1"
      ],
      "features": [
        {
          "title": "string",
          "description": "string markdown",
          "acceptance_criteria": [
            "criterio 1"
          ],
          "pbis": [
            {
              "title": "string",
              "description": "string markdown",
              "acceptance_criteria": [
                "criterio 1"
              ],
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
          ]
        }
      ]
    }
  ]
}
```

---

## Regras

1. Não usar campos fora do schema `PlanIn`.
2. Todos os objetos devem conter `title`.
3. `description` sempre em markdown.
4. `acceptance_criteria` sempre como lista de strings verificáveis.
5. Se um nível não estiver detalhado, retornar lista vazia (`[]`) no nó correspondente.
6. Não retornar texto explicativo fora do JSON.

---

## Estratégia de uso com os demais prompts

1. Gerar `EpicIn` com `prompt-epic.md`.
2. Gerar `FeatureIn` e anexar em `epics[].features`.
3. Gerar lista de `PbiIn` e anexar em `features[].pbis`.
4. Gerar lista de `TaskIn` e anexar em `pbis[].tasks`.
5. Consolidar tudo em `PlanIn` e enviar para `/v1/scrum/execute`.

---

## Exemplo mínimo válido

```json
{
  "defaults": {
    "area_path": null,
    "iteration_path": null,
    "tags": "automation;api"
  },
  "epics": [
    {
      "title": "Automacao de Backlog",
      "description": "## Contexto\\n...",
      "acceptance_criteria": [
        "Epic aprovado pelas areas envolvidas"
      ],
      "features": []
    }
  ]
}
```

---

## Entrada

```text
[COLE AQUI A NECESSIDADE DE NEGOCIO E O NIVEL DE DETALHE ESPERADO]
```
