#!/usr/bin/env bash
# Script rápido para configurar Datadog

set -e

echo "=== Configuração Rápida do Datadog ==="
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env
    echo "✓ Arquivo .env criado"
    echo ""
else
    echo "ℹ Arquivo .env já existe"
    echo ""
fi

# Solicitar credenciais
echo "Você precisa de suas credenciais Datadog:"
echo "1. Acesse: https://app.datadoghq.com"
echo "2. Settings → API Keys (copie DD_API_KEY)"
echo "3. Settings → Application Keys (copie DD_APP_KEY)"
echo ""

read -p "Digite sua DD_API_KEY: " api_key
read -p "Digite sua DD_APP_KEY: " app_key
read -p "Digite seu DD_SITE (padrão: datadoghq.com): " site
site=${site:-datadoghq.com}

# Atualizar .env
echo ""
echo "Atualizando .env..."

# Usando sed para substituir valores
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|^DD_API_KEY=.*|DD_API_KEY=$api_key|" .env
    sed -i '' "s|^DD_APP_KEY=.*|DD_APP_KEY=$app_key|" .env
    sed -i '' "s|^DD_SITE=.*|DD_SITE=$site|" .env
else
    # Linux
    sed -i "s|^DD_API_KEY=.*|DD_API_KEY=$api_key|" .env
    sed -i "s|^DD_APP_KEY=.*|DD_APP_KEY=$app_key|" .env
    sed -i "s|^DD_SITE=.*|DD_SITE=$site|" .env
fi

echo "✓ Variáveis de ambiente atualizadas"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado"
    exit 1
fi

echo "Docker encontrado: $(docker --version)"
echo ""

# Iniciar containers
echo "Iniciando containers..."
docker-compose up -d

echo ""
echo "=== Configuração Completa ==="
echo ""
echo "✓ Agent Datadog iniciado"
echo "✓ API iniciada em http://localhost:8000"
echo ""
echo "Próximos passos:"
echo "1. Aguarde 30 segundos para o agent ficar pronto"
echo "2. Acesse: https://app.datadoghq.com/apm/traces"
echo "3. Gere tráfego: curl -X POST http://localhost:8000/api/v1/previsao-dia -H 'Content-Type: application/json' -d '{\"ticker\":\"AAPL\",\"date\":\"2024-01-01\"}'"
echo ""
echo "Ver logs:"
echo "  docker logs -f dd-agent     # Agent Datadog"
echo "  docker logs -f ml-api       # API"
echo ""
