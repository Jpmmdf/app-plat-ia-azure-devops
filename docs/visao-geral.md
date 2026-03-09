# Visao Geral

## Fluxo ponta a ponta

1. Usuario descreve demanda de negocio.
2. Se ja existir item no board, GPT consulta `GET /v1/backlog/work-items/{id}`.
3. GPT gera payload do proximo nivel.
4. API cria filhos via endpoint nested com ID no path.

Exemplos de criacao nested:

- `POST /v1/backlog/epics/{epic_id}/features`
- `POST /v1/backlog/features/{feature_id}/product-backlog-items`
- `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

## Modos de uso

- **API**: integracao de sistemas e automacoes.
- **Custom GPT**: geracao guiada de payload e execucao assistida.

## Contratos principais

Consulta:

- `WorkItemOut` em `GET /v1/backlog/work-items/{id}`

Criacao:

- `CreateEpicsIn`
- `CreateFeaturesForEpicIn` (nested)
- `CreatePbisForFeatureIn` (nested)
- `CreateTasksForPbiIn` (nested)
- Endpoints diretos com `parent_id` permanecem disponiveis.

Campos suportados em todos os niveis:

- `title` (obrigatorio)
- `description` (markdown)
- `acceptance_criteria` (string ou lista)
- `area_path` (opcional)
- `iteration_path` (opcional)
- `tags` (opcional)

## Persistencia no Azure DevOps

- `System.Title`
- `System.Description`
- `Microsoft.VSTS.Common.AcceptanceCriteria` (quando suportado)
- Fallback de criterios para `Description` quando o campo nao existir (ex.: Task)
- Formato multiline em markdown via `multilineFieldsFormat`

## Artefatos do projeto

- `openapi.yaml` / `openapi.json`: contrato da API.
- `docs/user-guides`: prompts por nivel (epic, feature, pbi, task, orquestracao).
- `prompts/custom-gpt/custom-gpt-system-prompt.md`: prompt para Custom GPT.
- `.github/workflows/deploy-cloudflare.yml`: pipeline de deploy.
