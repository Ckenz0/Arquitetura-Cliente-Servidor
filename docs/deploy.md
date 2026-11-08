# Deploy na Azure

O frontend usa Azure Static Web Apps e o backend usa Azure App Service
Linux. O navegador recebe os arquivos estáticos de uma origem e acessa
diretamente a API Flask em outra, por HTTPS/JSON. Não há Azure Functions
nem proxy no frontend.

## Recursos

| Parte | Recurso | Plano | Região |
| --- | --- | --- | --- |
| Frontend | `entrelinhas-front-ckenz0` | Static Web Apps Free | Central US |
| Backend | `entrelinhas-api-ckenz0` | App Service Linux F1 | Brazil South |

Grupo de recursos: `livraria-entrelinhas`.

Domínio atribuído ao frontend:
`https://purple-rock-035da0010.3.azurestaticapps.net`.

## Consultar os domínios

Comandos em Bash no Azure Cloud Shell, já autenticado:

```bash
az account set --subscription a8e0c9f2-aebe-415a-8afa-629c61ea8bce
API_HOST=$(az webapp show -g livraria-entrelinhas -n entrelinhas-api-ckenz0 --query defaultHostName -o tsv)
FRONT_HOST=$(az staticwebapp show -g livraria-entrelinhas -n entrelinhas-front-ckenz0 --query defaultHostname -o tsv)
printf 'API: https://%s\nFrontend: https://%s\n' "$API_HOST" "$FRONT_HOST"
```

O App Service usa um hostname com sufixo gerado. Consulte `defaultHostName`
em vez de derivar a URL do nome do recurso.

## Regiões permitidas

A assinatura restringe a criação de recursos por região. Consulte a
interseção entre as regiões permitidas e as suportadas pelo serviço:

```bash
az policy assignment list --scope /subscriptions/a8e0c9f2-aebe-415a-8afa-629c61ea8bce --query '[].{politica:displayName,parametros:parameters}' -o json
az provider show --namespace Microsoft.Web --query "resourceTypes[?resourceType=='staticSites'].locations | [0]" -o json
```

Na criação deste frontend, a interseção encontrada foi Central US.

## Configurar a API

| Configuração | Valor |
| --- | --- |
| Runtime | Python 3.12, Linux |
| Startup command | `bash startup.sh` |
| `APP_ENV` | `production` |
| `SECRET_KEY` | Chave aleatória estável, com pelo menos 32 caracteres, apenas no backend |
| `ALLOWED_ORIGINS` | `https://purple-rock-035da0010.3.azurestaticapps.net` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

Ative HTTPS only. Use uma única instância e o único processo Waitress com
quatro threads definido em `startup.sh`. Os dados ficam em memória;
reinícios apagam alterações. Uma chave estável não recupera dados perdidos.
Não configure múltiplos workers ou réplicas.

Gere o pacote de execução:

```bash
python scripts/package_backend.py --output dist/backend-azure.zip
```

O ZIP contém `requirements.txt`, `startup.sh` e `server/` na raiz, sem
frontend, documentação, caches ou arquivos locais. Habilite o build remoto
para que a Azure instale as dependências Python.

## Configurar GitHub Actions

No repositório, abra **Settings → Secrets and variables → Actions**:

| Tipo | Nome | Valor |
| --- | --- | --- |
| Variable | `AZURE_API_BASE_URL` | Origem HTTPS real da API, sem `/api` |
| Secret | `AZURE_CLIENT_ID` | Client ID da identidade com acesso ao App Service |
| Secret | `AZURE_TENANT_ID` | Tenant ID |
| Secret | `AZURE_SUBSCRIPTION_ID` | ID da assinatura |
| Secret | `AZURE_STATIC_WEB_APPS_API_TOKEN` | Token do Static Web App, em Manage deployment token |

Configure a identidade federada OIDC do backend com:

- Issuer: `https://token.actions.githubusercontent.com`.
- Audience: `api://AzureADTokenExchange`.
- Subject: `repo:Ckenz0/Arquitetura-Cliente-Servidor:ref:refs/heads/main`.
- Permissão de publicação no App Service, por exemplo **Website Contributor**
  no escopo desse recurso.

O workflow já solicita `id-token: write`; OIDC não precisa de client secret.
O token do Static Web Apps pertence somente aos secrets do GitHub.
Não coloque tokens ou `SECRET_KEY` no JavaScript ou em arquivos rastreados.

## Publicação

- `main_entrelinhas-api-ckenz0.yml` valida e empacota a API, autentica via
  OIDC, publica o ZIP e verifica `/api/health`.
- `azure-static-web-apps.yml` valida o empacotamento e a sintaxe JS, prepara
  os assets e publica apenas `dist/client/`.

Os workflows estão em `.github/workflows/`, publicam a branch `main` e
aceitam execução manual em **Actions → Run workflow**. Pull requests
executam validações sem publicar. A falta de configuração causa falha
explícita na etapa de deploy.

O frontend gera `dist/client/config.js` com `AZURE_API_BASE_URL`.
`client/config.js` preserva localhost para desenvolvimento. Variáveis do
painel do Static Web Apps não alteram JavaScript estático automaticamente.
`api_location` fica vazio: a API Flask executa no App Service separado.

Para preparar os assets localmente:

```bash
python scripts/package_frontend.py --api-url "https://$API_HOST"
```

## Verificar a aplicação

1. A API deve responder 200 com `{"status":"ok"}` em `/api/health`.
2. Abra o frontend e confira catálogo, busca e detalhes.
3. Reserve um exemplar, altere o prazo e cancele; confira o estoque.
4. Publique uma avaliação e confira sua visibilidade em outra sessão,
   mantendo o isolamento das reservas.
5. Salve preferências e recarregue.
6. Em Network, confira assets no domínio do Static Web Apps e chamadas
   `/api/` no domínio do App Service, com Bearer e sem erros de CORS ou
   conteúdo misto.

Criar os recursos não comprova que a aplicação foi publicada.

## Referências

- [Static Web Apps: configuração de build](https://learn.microsoft.com/en-us/azure/static-web-apps/build-configuration).
- [App Service: deploy ZIP e build remoto](https://learn.microsoft.com/en-us/azure/app-service/deploy-zip).
- [App Service: GitHub Actions e OIDC](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions).
- [Diagnóstico de bloqueio por política](https://learn.microsoft.com/en-us/azure/azure-resource-manager/troubleshooting/error-policy-requestdisallowedbypolicy).
