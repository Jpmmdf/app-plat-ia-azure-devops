# app-plat-ia-azure-devops

Gateway/API para criação automatizada de backlog no Azure DevOps (Epic -> Feature -> PBI -> Task), com suporte a:

- execução via API FastAPI (`/v1/scrum/execute`)
- execução via CLI (`create_epic.py` e `create_scrum_tree.py`)
- critérios de aceite por item
- persistência de campos multilinha em Markdown
- documentação e prompts para uso com IA/Custom GPT
- deploy em Cloudflare Workers

## Estrutura do projeto

```text
.
├── .github/workflows/deploy-cloudflare.yml
├── docs/
│   ├── index.md
│   ├── visao-geral.md
│   ├── arquitetura.md
│   ├── api.md
│   ├── operacao.md
│   ├── security.md
│   ├── deploy-cloudflare-github-actions.md
│   ├── custom-gpt.md
│   ├── prompts/
│   └── user-guides/
├── prompts/custom-gpt/custom-gpt-system-prompt.md
├── examples/planin.example.json
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

## Configuração local

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.local.txt
pip install pyyaml
```

2. Criar arquivo `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

3. Preencher variáveis:

- `AZDO_ORG`
- `AZDO_PROJECT`
- `AZDO_PAT`
- `GATEWAY_API_KEY`

## Executar localmente

```bash
source .env
./.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health`
- `POST /v1/scrum/execute`

## Exemplo de payload da API

Arquivo de exemplo: [`examples/planin.example.json`](examples/planin.example.json)

```bash
curl -X POST "http://127.0.0.1:8000/v1/scrum/execute" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $GATEWAY_API_KEY" \
  --data @examples/planin.example.json
```

## Uso via CLI

Criar item único:

```bash
./.venv/bin/python create_scrum_tree.py \
  --type "Product Backlog Item" \
  --title "Meu PBI" \
  --parent-id 123
```

Criar epic unitário:

```bash
./.venv/bin/python create_epic.py \
  --title "Meu Epic" \
  --description "## Contexto\n..."
```

## OpenAPI

Gerar especificações:

```bash
./.venv/bin/python generate_openapi.py --output openapi.yaml
./.venv/bin/python generate_openapi.py --output openapi.json --format json
```

## Deploy Cloudflare (GitHub Actions)

Workflow: [`.github/workflows/deploy-cloudflare.yml`](.github/workflows/deploy-cloudflare.yml)

Secrets necessários no GitHub:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `AZDO_ORG`
- `AZDO_PROJECT`
- `AZDO_PAT`
- `GATEWAY_API_KEY`

## Segurança e boas práticas

- Não versionar `.env`, `.dev.vars` e caches locais.
- Não hardcodar credenciais no código ou `wrangler.toml`.
- Usar secrets no GitHub Actions/Cloudflare.
- Revisar e regenerar OpenAPI após mudanças de contrato.

## Documentação completa

- [Visão geral](docs/visao-geral.md)
- [Arquitetura](docs/arquitetura.md)
- [API](docs/api.md)
- [Operação](docs/operacao.md)
- [Segurança](docs/security.md)
- [Deploy Cloudflare via GitHub Actions](docs/deploy-cloudflare-github-actions.md)
- [Custom GPT](docs/custom-gpt.md)
