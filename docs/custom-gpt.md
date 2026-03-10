# Custom GPT

## Arquivo de prompt para ingestao

Use:

- `prompts/custom-gpt/custom-gpt-system-prompt.md`

Esse prompt foi ajustado para fluxo por contexto de ID existente e para gerar itens com alto nivel de detalhe (description estruturada + criterios de aceite verificaveis).
Tambem foi ajustado para modo de execucao por padrao: quando o usuario pedir "criar no board", o GPT deve chamar a Action/API (nao apenas devolver JSON).
Agora o fluxo exige previa obrigatoria antes de criar: o GPT primeiro mostra o plano do que sera criado e executa apenas apos confirmacao explicita do usuario.

## URL do OpenAPI para Action

Use diretamente a URL remota do Worker:

- `https://ops-plat-azure-devops-gateway.pedro-milhome.workers.dev/openapi.json`

Alternativa local (arquivo versionado no repo):

- `openapi.json`

## Fluxo recomendado na Action

1. Usuario pede criacao (ou informa um ID existente).
2. GPT mostra previa do plano de criacao (itens por nivel, titulos e escopo).
3. Usuario confirma execucao.
4. GPT consulta contexto quando necessario (`GET /v1/backlog/work-items/{work_item_id}`).
5. Para backlog completo, GPT executa em ordem:
   - `POST /v1/backlog/epics`
   - `POST /v1/backlog/epics/{epic_id}/features`
   - `POST /v1/backlog/features/{feature_id}/product-backlog-items`
   - `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`
6. GPT retorna resumo final com totais, IDs e links criados por nivel.

## Configuracao recomendada

1. Copiar o conteudo do prompt para o campo de instrucoes do GPT.
2. Adicionar Action com `https://ops-plat-azure-devops-gateway.pedro-milhome.workers.dev/openapi.json`.
3. Configurar autenticacao com header `X-API-Key`.
4. Testar um caso com Epic criado manualmente e criacao de features a partir do ID.

## Resultado esperado

- GPT consegue consultar contexto do item por ID.
- GPT gera payload correto para criar filhos no endpoint nested.
- Sem necessidade de informar `parent_id` no body quando usar endpoints nested.
