# Custom GPT

## Arquivo de prompt para ingestao

Use:

- `prompts/custom-gpt/custom-gpt-system-prompt.md`

Esse prompt foi ajustado para fluxo por contexto de ID existente e para gerar itens com alto nivel de detalhe (description estruturada + criterios de aceite verificaveis).

## URL do OpenAPI para Action

Use diretamente a URL remota do Worker:

- `https://ops-plat-azure-devops-gateway.pedro-milhome.workers.dev/openapi.json`

Alternativa local (arquivo versionado no repo):

- `openapi.json`

## Fluxo recomendado na Action

1. Usuario informa um ID existente (Epic, Feature ou PBI).
2. GPT consulta `GET /v1/backlog/work-items/{work_item_id}`.
3. GPT cria os itens filhos via endpoint nested correspondente:
   - `POST /v1/backlog/epics/{epic_id}/features`
   - `POST /v1/backlog/features/{feature_id}/product-backlog-items`
   - `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

## Configuracao recomendada

1. Copiar o conteudo do prompt para o campo de instrucoes do GPT.
2. Adicionar Action com `https://ops-plat-azure-devops-gateway.pedro-milhome.workers.dev/openapi.json`.
3. Configurar autenticacao com header `X-API-Key`.
4. Testar um caso com Epic criado manualmente e criacao de features a partir do ID.

## Resultado esperado

- GPT consegue consultar contexto do item por ID.
- GPT gera payload correto para criar filhos no endpoint nested.
- Sem necessidade de informar `parent_id` no body quando usar endpoints nested.
