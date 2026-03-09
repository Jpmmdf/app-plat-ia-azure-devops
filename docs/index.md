# ADO Scrum Bootstrap Gateway

Plataforma para criacao automatizada de backlog no Azure DevOps com API, prompts e deploy em Cloudflare Workers.

## O que este projeto resolve

- Padroniza a criacao de Epic, Feature, PBI e Task.
- Reduz criacao manual no board.
- Mantem criterios de aceite e markdown de forma consistente.
- Oferece contratos claros para integracao com IA/Custom GPT.

## Principais componentes

- `src/ops_plat_azure_devops_gateway/app.py`: implementacao principal da API FastAPI.
- `server.py`: entrypoint de compatibilidade (`uvicorn server:app` e deploy Worker).
- `generate_openapi.py`: geracao de `openapi.yaml` e `openapi.json`.
- `requirements.cloudflare.txt`: dependencias Python de runtime para deploy no Worker.
- `scripts/`: scripts auxiliares (ex.: export de diagramas Structurizr).
- `tests/`: testes automatizados.
- `docs/user-guides`: prompts API-first para geracao de payload.
- `prompts/custom-gpt`: prompt pronto para ingestao no Custom GPT.

## Inicio rapido

1. Configure variaveis de ambiente (`.env.example` -> `.env`).
2. Execute a API localmente.
3. Gere os payloads por tipo (`epics`, `features`, `pbis`, `tasks`).
4. Execute chamadas em etapas nas rotas segmentadas.

## Navegacao

- [Visao Geral](visao-geral.md)
- [Arquitetura](arquitetura.md)
- [Arquitetura C4 (Structurizr)](arquitetura-c4.md)
- [API](api.md)
- [Operacao](operacao.md)
- [Seguranca](security.md)
- [Deploy (Cloudflare + GitHub Actions)](deploy-cloudflare-github-actions.md)
- [Custom GPT](custom-gpt.md)
