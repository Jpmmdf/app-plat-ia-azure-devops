# Visão Geral

## Fluxo ponta a ponta

1. Usuário descreve demanda de negócio.
2. IA (prompts API-first) gera payload JSON no schema `PlanIn`.
3. Payload é enviado para `POST /v1/scrum/execute`.
4. API cria itens no Azure DevOps em hierarquia:
   - Epic -> Feature -> Product Backlog Item -> Task
5. Resposta retorna IDs e URLs dos itens criados.

## Modos de uso

- **API**: integração de sistemas e automações.
- **CLI**: operação manual, bootstrap e troubleshooting.
- **Custom GPT**: geração guiada de payload e execução assistida.

## Contratos principais

- Entrada da API: `PlanIn`
- Modelos hierárquicos:
  - `EpicIn`
  - `FeatureIn`
  - `PbiIn`
  - `TaskIn`

Campos suportados em todos os níveis:

- `title` (obrigatório)
- `description` (markdown)
- `acceptance_criteria` (string ou lista)

## Persistência no Azure DevOps

- `System.Title`
- `System.Description`
- `Microsoft.VSTS.Common.AcceptanceCriteria` (quando suportado)
- Fallback de critérios para `Description` quando o campo não existir (ex.: Task)
- Formato multiline em markdown via `multilineFieldsFormat`

## Artefatos do projeto

- `openapi.yaml` / `openapi.json`: contrato da API.
- `docs/user-guides`: prompts por nível (epic, feature, pbi, task, orquestração).
- `prompts/custom-gpt/custom-gpt-system-prompt.md`: prompt para Custom GPT.
- `.github/workflows/deploy-cloudflare.yml`: pipeline de deploy.
