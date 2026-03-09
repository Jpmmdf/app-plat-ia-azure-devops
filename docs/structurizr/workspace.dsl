workspace "ADO Scrum Bootstrap Gateway" "C4 model da automação de backlog no Azure DevOps." {

    model {
        user = person "Usuário de Produto/Engenharia" "Solicita criação automatizada de backlog."

        customGpt = softwareSystem "Custom GPT" "Gera payloads segmentados por tipo para execucao."
        azureDevOps = softwareSystem "Azure DevOps Boards" "Sistema alvo para criação de Work Items."
        github = softwareSystem "GitHub" "Repositório e automação de CI/CD."
        cloudflare = softwareSystem "Cloudflare Workers" "Ambiente de execução do gateway."

        gateway = softwareSystem "ADO Scrum Bootstrap Gateway" "Plataforma de automação de backlog (API + Docs)." {
            api = container "API Worker (FastAPI)" "Expoe consulta de item por ID e criacao de backlog por endpoints nested." "Python + FastAPI" {
                auth = component "Auth & Environment Resolver" "Valida API key e resolve variáveis de ambiente."
                validator = component "Payload Validator & Normalizer" "Valida payload por tipo e normaliza acceptance_criteria/tags/defaults."
                orchestrator = component "Batch Creator by Work Item Type" "Cria lotes por endpoint: Epic, Feature, Product Backlog Item e Task."
                reader = component "Work Item Reader" "Consulta Work Item por ID e extrai parent/children."
                adoClient = component "Azure DevOps Client" "Executa chamadas REST para criação de Work Items e links."
                responseBuilder = component "Response Builder" "Monta resposta com IDs e URLs."
            }

            docs = container "Documentação e Prompts" "Guia operacional e prompts API-first para IA." "MkDocs + Markdown"
        }

        user -> customGpt "Solicita geração de backlog"
        user -> api "Executa criação por API"
        user -> docs "Consulta documentação"

        customGpt -> api "GET /v1/backlog/work-items/{id} + POST /v1/backlog/*"
        api -> azureDevOps "Consulta, cria e vincula Work Items"

        github -> cloudflare "Deploy via GitHub Actions + Wrangler"

        auth -> validator "payload autenticado"
        auth -> reader "consulta autenticada"
        validator -> orchestrator "payload válido e normalizado"
        reader -> adoClient "busca item por id"
        orchestrator -> adoClient "operações de criação"
        adoClient -> azureDevOps "REST API 7.1"
        orchestrator -> responseBuilder "estrutura de saída"
    }

    views {
        systemContext gateway "context" {
            include *
            autoLayout lr
            title "C1 - Contexto"
        }

        container gateway "containers" {
            include *
            autoLayout lr
            title "C2 - Containers"
        }

        component api "components" {
            include *
            autoLayout lr
            title "C3 - Componentes da API"
        }

        styles {
            element "Person" {
                background #08427b
                color #ffffff
                shape person
            }

            element "Software System" {
                background #1168bd
                color #ffffff
            }

            element "Container" {
                background #438dd5
                color #ffffff
            }

            element "Component" {
                background #85bbf0
                color #000000
            }
        }
    }
}
