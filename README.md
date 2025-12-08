# Tech Challenge 4

### API para prever preços da bolsa de valores, treinado sobre o dataset do ITAÚ.

# Como Executar

### Dockerfile (local)

Construir e rodar localmente:

            docker build -t fastapi-example .
            docker run -p 8000:8000 fastapi-example

Acesse:
http://localhost:8000

## Para fazer o deploy e usar na nuvem:

### Pré requisitos:

- ¹ Realize o Login na AWS (Explicado abaixo)
- Tenha instalado o Terraform
- Tenha instalado o AWS Cli
- Tenha instalado o Docker e ativo.

¹ Login na AWS (execute):

            nano ~/.aws/credentials

Substitua por suas credenciais atualizadas, feito.

### Passo 1: Pegue o Login do ECR

Use esse comando substituindo <AWS_ID> pelo seu ID da AWS:

            aws ecr get-login-password --region us-east-1 | \
            docker login --username AWS --password-stdin <AWS_ID>.dkr.ecr.us-east-1.amazonaws.com

### Passo 2: Criar o repositório ECR via Terraform

            cd infra
            terraform init
            terraform apply -auto-approve

Ao executar com sucesso, vai retornar uma saída assim:
ecr_url = "<AWS_ID>.dkr.ecr.us-east-1.amazonaws.com/fastapi-example"

Copie o conteúdo entre aspas e use no passo 3.

### Passo 3: Build + Push da imagem

Dicas:

1. Pegue a saída que você copiou no passo 2 e cole em <ECR_URL>;
2. Para executar, volte a raiz do projeto, onde se encontra o docker;
3. Se estiver executando no Macbook Apple Silicon usar buildx.

**Aviso: O Push pode demorar mais de 1h.**

**Antes do push:** Confirme que o login no ECR funcionou
(substitua <ECR_URL> pelo seu registry, ex: 610520926426.dkr.ecr.us-east-1.amazonaws.com)

            aws ecr get-login-password --region us-east-1 \
            | docker login --username AWS --password-stdin <ECR_URL>

Se você estiver no **Windows** ou Linux (x86_64), execute:

            docker build -t fastapi-example .
            docker tag fastapi-example:latest <ECR_URL>:latest
            docker push <ECR_URL>:latest

Se você estiver no **Mac Apple Silicon** (M1/M2/M3), execute:

            docker buildx build \
            --platform=linux/amd64 \
            -t <ECR_URL>:latest \
            --push \
            .

Necessário para evitar o erro
exec format error
(porque o Fargate só roda imagens AMD64)

### Passo 4 (Último passo): Acessar

No Console AWS: Console AWS > ECS > Clusters > fastapi-cluster > Services > fastapi-service > Tasks > (selecionar task) > Network Interfaces → Public IP

http:<Public_IP>:8000/docs

Exemplo. 13.219.86.170:8000/docs

## Configuração do Datadog (Agent) - Passo a passo

Estas instruções mostram como executar o Datadog Agent localmente como container utilizando o `docker-compose.yml` presente na raiz do projeto. **NÃO** inclua sua `DD_API_KEY` no controle de versão — use variáveis de ambiente ou um arquivo `.env` local.

1) Preparar a variável de ambiente (PowerShell)

```powershell
# Exporte temporariamente a chave na sessão (não commite esse valor)
$env:DD_API_KEY = 'SUA_DD_API_KEY_AQUI'
# Opcional: ajuste o site e o ambiente
$env:DD_SITE = 'us5.datadoghq.com'
$env:DD_ENV = 'prod'
```

2) Subir o Datadog Agent via docker-compose (no diretório raiz do projeto)

```powershell
# Abra um terminal e navegue até a raiz do repositório (onde está o arquivo `docker-compose.yml`).
# Exemplo genérico (substitua pelo caminho do seu projeto):
# cd /caminho/para/time-series-lstm-api
docker compose up -d dd-agent
```

Observação: algumas instalações ainda usam `docker-compose` (com hífen). Experimente `docker compose` (sem hífen) primeiro; se não existir, instale/ative o Docker Desktop ou o plugin Compose.

3) Verificar se o container está rodando

```powershell
docker ps --filter "name=dd-agent"
docker logs -f dd-agent
```

4) Checar o status interno do Agent (dentro do container)

```powershell
docker exec dd-agent datadog-agent status
```

Procure por:
- `Agent (v...)` e `Status: Running`
- Na seção DogStatsD: porta `8125` e pacotes recebidos
- Na seção APM/Trace: porta `8126` (se habilitado)

5) Enviar uma métrica de teste (DogStatsD) diretamente no container

```powershell
docker exec dd-agent bash -lc "echo -n 'test.metric:1|c' > /dev/udp/127.0.0.1/8125"
docker exec dd-agent datadog-agent status
```

Verifique em `datadog-agent status` se houve recepção de pacotes e, em seguida, confirme na UI do Datadog (Metrics Explorer → buscar `test.metric`).

6) Habilitar APM (traces)

Se quiser receber traces (APM), ative as variáveis abaixo no `docker-compose.yml` ou no ambiente e mapeie a porta `8126`:

```yaml
environment:
    - DD_APM_ENABLED=true
    - DD_APM_NON_LOCAL_TRAFFIC=true
ports:
    - "8126:8126/tcp"   # APM
    - "8125:8125/udp"   # DogStatsD
```

Depois configure suas aplicações (Java, Python, Node, etc.) para enviar traces para o Agent (`dd-agent:8126` na mesma rede Docker ou `host.docker.internal:8126` no Windows host).

7) Boas práticas de segurança
- Não versionar `DD_API_KEY`.
- Crie um arquivo `.env` local com a variável e adicione `.env` ao `.gitignore`.
- Inclua um `.env.example` com chaves vazias para referência.

Exemplo de `.env.example`:

```
DD_API_KEY=
DD_SITE=us5.datadoghq.com
DD_ENV=prod
```

8) Remover/atualizar o Agent

```powershell
docker compose down dd-agent
docker rm -f dd-agent
```
