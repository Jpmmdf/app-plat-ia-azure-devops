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

## Permissões do token Cloudflare

Para o `CLOUDFLARE_API_TOKEN`, usar no mínimo:

- `Account -> Workers Scripts: Edit`
- `Account -> Account Settings: Read`
- `User -> User Details: Read`
- `User -> User Memberships: Read`

Se usar rotas customizadas, adicionar:

- `Zone -> Workers Routes: Edit`

## Comportamento do deploy

1. Faz checkout do repositório.
2. Configura Python 3.12 no runner.
3. Gera `python_modules` para runtime do Worker com:
   - `pip install --target python_modules -r requirements.cloudflare.txt`
4. Remove extensões nativas (`*.so`) não suportadas pelo runtime Python do Workers.
5. Executa `cloudflare/wrangler-action@v3` com `wranglerVersion` fixado.
6. Publica bindings sensíveis como secrets no Worker:
   - `AZDO_ORG`
   - `AZDO_PROJECT`
   - `AZDO_PAT`
   - `GATEWAY_API_KEY`

## Observações

- Mantenha `wrangler.toml` sem credenciais.
- O arquivo de dependências usado no deploy é `requirements.cloudflare.txt`.
- Não usar `cf-requirements.txt` neste projeto.
- Use rotação periódica de tokens.
- Sempre valide o endpoint `/health` após deploy.
