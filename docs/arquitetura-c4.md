# Arquitetura C4 (Structurizr)

Modelagem gerada a partir de `docs/structurizr/workspace.dsl`.

## C1 - Contexto

```mermaid
--8<-- "diagrams/structurizr/structurizr-context.mmd"
```

## C2 - Containers

```mermaid
--8<-- "diagrams/structurizr/structurizr-containers.mmd"
```

## C3 - Componentes da API

```mermaid
--8<-- "diagrams/structurizr/structurizr-components.mmd"
```

## Fonte e regeneração

- DSL: `docs/structurizr/workspace.dsl`
- Script: `scripts/export_structurizr_diagrams.sh`

Regenerar:

```bash
./scripts/export_structurizr_diagrams.sh
```
