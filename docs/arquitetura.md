# Arquitetura

## Visão arquitetural

O projeto adota um modelo C4 baseado em Structurizr para documentar:

- Contexto do sistema (C1)
- Containers (C2)
- Componentes da API (C3)

A modelagem-fonte está em:

- `docs/structurizr/workspace.dsl`

Os diagramas versionados para o MkDocs estão em:

- `docs/diagrams/structurizr/*.mmd`

## Como atualizar diagramas

```bash
./scripts/export_structurizr_diagrams.sh
```

## Páginas relacionadas

- [Arquitetura C4 (Structurizr)](arquitetura-c4.md)
- [API](api.md)
- [Operação](operacao.md)
