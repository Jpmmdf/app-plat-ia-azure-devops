# app-plat-ia-azure-devops

Gateway/API para criacao automatizada de backlog no Azure DevOps com suporte a Markdown e criterios de aceite.

## O que este projeto resolve

- Padroniza criacao de Epic, Feature, PBI e Task.
- Reduz criacao manual no board.
- Permite continuar backlog a partir de item ja existente no Azure DevOps (via ID).
- Oferece contratos claros para integracao com IA/Custom GPT.

## Estrutura do projeto

```text
.
├── .github/workflows/deploy-cloudflare.yml
├── docs/
├── prompts/custom-gpt/custom-gpt-system-prompt.md
├── examples/create_epics.example.json
├── examples/create_features.example.json
├── examples/create_pbis.example.json
├── examples/create_tasks.example.json
├── server.py
├── create_epic.py
├── create_scrum_tree.py
├── generate_openapi.py
├── openapi.yaml
├── openapi.json
└── wrangler.toml
```

## Requisitos

- Python 3.12+
- Conta no Azure DevOps com PAT (`Work Items Read & write`)
- Conta Cloudflare (para deploy Worker)

## Configuracao local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.local.txt
pip install pyyaml
```

```bash
cp .env.example .env
```

Variaveis necessarias:

- `AZDO_ORG`
- `AZDO_PROJECT`
- `AZDO_PAT`
- `GATEWAY_API_KEY`

## Executar localmente

```bash
source .env
./.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

## Endpoints principais

Consulta:

- `GET /health`
- `GET /v1/backlog/work-items/{work_item_id}`

Criacao nested (recomendado):

- `POST /v1/backlog/epics/{epic_id}/features`
- `POST /v1/backlog/features/{feature_id}/product-backlog-items`
- `POST /v1/backlog/product-backlog-items/{product_backlog_item_id}/tasks`

Criacao direta (bulk):

- `POST /v1/backlog/epics`
- `POST /v1/backlog/features`
- `POST /v1/backlog/product-backlog-items`
- `POST /v1/backlog/tasks`

## Fluxo recomendado com ID existente

1. Usuario informa ID (ex.: Epic criado manualmente).
2. GPT consulta `GET /v1/backlog/work-items/{id}`.
3. GPT cria filhos no endpoint nested correto.

## OpenAPI

```bash
./.venv/bin/python generate_openapi.py --output openapi.yaml
./.venv/bin/python generate_openapi.py --output openapi.json --format json
```

## Documentacao

- [Visao geral](docs/visao-geral.md)
- [Arquitetura](docs/arquitetura.md)
- [Arquitetura C4 (Structurizr)](docs/arquitetura-c4.md)
- [API](docs/api.md)
- [Operacao](docs/operacao.md)
- [Seguranca](docs/security.md)
- [Deploy Cloudflare via GitHub Actions](docs/deploy-cloudflare-github-actions.md)
- [Custom GPT](docs/custom-gpt.md)
