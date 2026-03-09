# Custom GPT

## Arquivo de prompt para ingestão

Use:

- `prompts/custom-gpt/custom-gpt-system-prompt.md`

Esse prompt foi projetado para gerar payloads no schema da API (`PlanIn`) e executar fluxo Epic -> Feature -> PBI -> Task.

## Configuração recomendada no Custom GPT

1. Copiar o conteúdo do arquivo acima para o campo de instruções do GPT.
2. Adicionar Action com o OpenAPI do projeto (`openapi.json`).
3. Configurar autenticação da action com header `X-API-Key`.
4. Testar com payload mínimo e depois com payload completo.

## Resultado esperado

- Saída estritamente em JSON válido para ingestão.
- Compatível com `POST /v1/scrum/execute`.
- Sem campos fora do contrato da API.
