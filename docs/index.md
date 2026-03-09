# ADO Scrum Bootstrap Gateway

Plataforma para criação automatizada de backlog no Azure DevOps com API, CLI, prompts e deploy em Cloudflare Workers.

## O que este projeto resolve

- Padroniza a criação de Epic, Feature, PBI e Task.
- Reduz criação manual no board.
- Mantém critérios de aceite e formatação markdown de forma consistente.
- Oferece contratos claros para integração com IA/Custom GPT.

## Principais componentes

- `server.py`: API FastAPI (`/v1/scrum/execute`).
- `create_scrum_tree.py`: CLI para criação hierárquica e itens independentes.
- `create_epic.py`: CLI para criação unitária.
- `generate_openapi.py`: geração de `openapi.yaml` e `openapi.json`.
- `docs/user-guides`: prompts API-first para geração de payload.
- `prompts/custom-gpt`: prompt pronto para ingestão no Custom GPT.

## Início rápido

1. Configure variáveis de ambiente (`.env.example` -> `.env`).
2. Execute a API localmente.
3. Gere e valide o payload no formato `PlanIn`.
4. Envie para `/v1/scrum/execute`.

## Navegação

- [Visão Geral](visao-geral.md)
- [Arquitetura](arquitetura.md)
- [API](api.md)
- [Operação](operacao.md)
- [Segurança](security.md)
- [Deploy (Cloudflare + GitHub Actions)](deploy-cloudflare-github-actions.md)
- [Custom GPT](custom-gpt.md)
