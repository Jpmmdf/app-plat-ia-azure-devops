# Operação

## Execução local da API

```bash
source .env
./.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

## Execução via API

### Criar epic (payload minimo)

```bash
curl -X POST "http://127.0.0.1:8000/v1/backlog/epics" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${GATEWAY_API_KEY}" \
  -d '{"epics":[{"title":"Epic de teste"}]}'
```

### Criar features para um epic existente

```bash
curl -X POST "http://127.0.0.1:8000/v1/backlog/epics/123/features" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${GATEWAY_API_KEY}" \
  -d '{"features":[{"title":"Feature de teste"}]}'
```

## Troubleshooting rápido

- `401 Unauthorized`: `X-API-Key` ausente ou inválida.
- `500 AZDO_PAT...`: PAT não configurado.
- `HTTP 4xx/5xx - ... Azure DevOps`: erro de integração externa.
- `resposta nao JSON`: credencial/rede/redirect inválido no ADO.
