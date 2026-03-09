# Operação

## Execução local da API

```bash
source .env
./.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

## Execução via CLI

### Criar item único

```bash
source .env
./.venv/bin/python create_scrum_tree.py \
  --type "Feature" \
  --title "Minha feature" \
  --parent-id 123
```

### Criar árvore completa por arquivo

```bash
source .env
./.venv/bin/python create_scrum_tree.py path/plan.json
```

### Criar epic unitário

```bash
source .env
./.venv/bin/python create_epic.py --title "Meu epic"
```

## Troubleshooting rápido

- `401 Unauthorized`: `X-API-Key` ausente ou inválida.
- `500 AZDO_PAT...`: PAT não configurado.
- `HTTP 4xx/5xx - ... Azure DevOps`: erro de integração externa.
- `resposta nao JSON`: credencial/rede/redirect inválido no ADO.
