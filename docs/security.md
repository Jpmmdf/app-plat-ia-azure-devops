# Segurança

## Variáveis sensíveis

Nunca versionar:

- `AZDO_PAT`
- `GATEWAY_API_KEY`
- arquivos `.env`, `.dev.vars` e derivados

## Práticas aplicadas

- `.gitignore` bloqueia arquivos de ambiente e caches.
- `wrangler.toml` sem credenciais hardcoded.
- Pipeline de deploy usa GitHub Secrets.
- API valida `X-API-Key` antes de processar payload.

## Checklist antes de publicar

1. Validar que `.env` não está versionado.
2. Rodar scan de tokens/chaves no repositório.
3. Confirmar que não há PAT em docs, exemplos ou logs.
4. Revisar permissões mínimas do PAT no Azure DevOps.
