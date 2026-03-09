# Prompt de Feature (API-First)

## Objetivo

Transformar uma necessidade de negócio em um objeto `FeatureIn` compatível com a API:

- Endpoint: `POST /v1/scrum/execute`
- Caminho no payload: `epics[n].features[]`

---

## Contrato de saída (obrigatório)

Retorne **somente JSON válido** no formato:

```json
{
  "title": "string",
  "description": "string markdown",
  "acceptance_criteria": [
    "criterio 1",
    "criterio 2"
  ],
  "pbis": []
}
```

---

## Regras

1. Não usar campos fora do schema `FeatureIn`.
2. `title` direto e orientado a valor.
3. `description` em markdown, com contexto de produto + impacto técnico relevante.
4. `acceptance_criteria` como lista objetiva e testável.
5. Retornar `pbis` vazio quando a decomposição em PBIs ainda não tiver sido feita.

---

## Estrutura recomendada para `description`

- `## Contexto`
- `## Problema a Resolver`
- `## Objetivo da Feature`
- `## Escopo Funcional`
- `## Requisitos Nao Funcionais`
- `## Dependências`
- `## Riscos`
- `## Indicadores de Sucesso`

---

## Mapeamento para API

- `title` -> `FeatureIn.title`
- `description` -> `FeatureIn.description` (`System.Description`)
- `acceptance_criteria` -> `FeatureIn.acceptance_criteria` (campo de critérios quando suportado, fallback em `Description`)
- `pbis` -> `FeatureIn.pbis`

---

## Exemplo para inserir no payload

```json
{
  "title": "Padronizar criacao de Work Items via API",
  "description": "## Contexto\\n...",
  "acceptance_criteria": [
    "Fluxo de criacao suportado para Epic, Feature, PBI e Task",
    "Erros retornados com mensagens operacionais claras"
  ],
  "pbis": []
}
```

---

## Entrada

```text
[COLE AQUI A NECESSIDADE DA FEATURE]
```
