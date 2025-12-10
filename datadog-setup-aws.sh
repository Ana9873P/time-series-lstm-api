#!/bin/bash
# 🚀 SCRIPT RÁPIDO: Conectar AWS EC2 ao Datadog
# 
# Copie e cole EXATAMENTE os comandos abaixo em sua instância EC2
# Substitua SEU_API_KEY_AQUI e SEU_APP_KEY_AQUI pelas suas chaves reais
#
# Credenciais obtidas em:
# DD_API_KEY: https://app.datadoghq.com/organization/settings/api-keys
# DD_APP_KEY: https://app.datadoghq.com/organization/settings/application-keys

set -e

echo "════════════════════════════════════════════════════════════"
echo "  CONFIGURAÇÃO RÁPIDA: AWS EC2 + DATADOG"
echo "════════════════════════════════════════════════════════════"
echo ""

# PASSO 1: Instalar Docker
echo "📦 Passo 1: Instalando Docker..."
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

echo "✅ Docker instalado"
echo ""

# PASSO 2: Instalar Docker Compose
echo "📦 Passo 2: Instalando Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "✅ Docker Compose instalado"
echo ""

# PASSO 3: Clonar repositório
echo "📦 Passo 3: Clonando repositório..."
cd /home/ec2-user
git clone https://github.com/Ana9873P/time-series-lstm-api.git
cd time-series-lstm-api

echo "✅ Repositório clonado"
echo ""

# PASSO 4: Criar arquivo .env
echo "📦 Passo 4: Criando arquivo .env..."
echo ""
echo "⚠️  IMPORTANTE: Você precisa de suas credenciais Datadog!"
echo ""
echo "Obtém em:"
echo "  DD_API_KEY: https://app.datadoghq.com/organization/settings/api-keys"
echo "  DD_APP_KEY: https://app.datadoghq.com/organization/settings/application-keys"
echo ""

read -p "Digite sua DD_API_KEY: " DD_API_KEY
read -p "Digite sua DD_APP_KEY: " DD_APP_KEY
read -p "Digite seu DD_SITE (padrão: datadoghq.com): " DD_SITE
DD_SITE=${DD_SITE:-datadoghq.com}

cat > .env << EOF
DD_API_KEY=$DD_API_KEY
DD_APP_KEY=$DD_APP_KEY
DD_SITE=$DD_SITE
DD_ENV=production
DD_SERVICE=ml-microservice
DD_VERSION=1.0.0
DD_TRACE_ENABLED=true
LOG_LEVEL=INFO
EOF

echo "✅ Arquivo .env criado"
echo ""

# PASSO 5: Iniciar containers
echo "📦 Passo 5: Iniciando containers..."
docker-compose up -d

echo "✅ Containers iniciados"
echo ""

# PASSO 6: Esperar agent ficar pronto
echo "⏳ Aguardando Agent Datadog ficar pronto (30 segundos)..."
sleep 30

# PASSO 7: Verificar status
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  STATUS"
echo "════════════════════════════════════════════════════════════"
echo ""

docker-compose ps

echo ""
echo "✅ Verificando logs..."
echo ""

echo "Logs do Agent Datadog:"
docker logs dd-agent 2>&1 | head -10

echo ""
echo "Logs da API:"
docker logs ml-api 2>&1 | head -10

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  ✨ PRONTO! Agora gere tráfego..."
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Teste simples:"
echo "  curl http://44.203.108.19:8000/docs"
echo ""

echo "Gerar tráfego para Datadog rastrear:"
echo "  curl -X POST http://44.203.108.19:8000/api/v1/previsao-dia \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"ticker\":\"AAPL\",\"date\":\"2024-01-01\"}'"
echo ""

echo "Ver em Datadog:"
echo "  1. Acesse: https://app.datadoghq.com"
echo "  2. Vá para: APM → Traces"
echo "  3. Procure por: service:ml-microservice"
echo "  4. Você verá seus requests rastreados!"
echo ""

echo "Ver logs em tempo real:"
echo "  docker logs -f dd-agent"
echo "  docker logs -f ml-api"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "  ✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "════════════════════════════════════════════════════════════"
