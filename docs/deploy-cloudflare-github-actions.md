# Deploy Cloudflare com GitHub Actions

## Workflow

Arquivo: `.github/workflows/deploy-cloudflare.yml`

Trigger:

- `push` na branch `main`
- `workflow_dispatch`

## Secrets obrigatórios no GitHub

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `AZDO_ORG`
- `AZDO_PROJECT`
- `AZDO_PAT`
- `GATEWAY_API_KEY`

## Comportamento do deploy

1. Faz checkout do repositório.
2. Executa `wrangler deploy`.
3. Publica bindings sensíveis como secrets no Worker:
   - `AZDO_ORG`
   - `AZDO_PROJECT`
   - `AZDO_PAT`
   - `GATEWAY_API_KEY`

## Observações

- Mantenha `wrangler.toml` sem credenciais.
- Use rotação periódica de tokens.
- Sempre valide o endpoint `/health` após deploy.
