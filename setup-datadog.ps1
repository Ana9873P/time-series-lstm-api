#!/usr/bin/env powershell
# Script de configuração rápida do Datadog para Windows

Write-Host "=== Configuração Rápida do Datadog ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se .env existe
if (-not (Test-Path ".env")) {
    Write-Host "Criando arquivo .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Arquivo .env criado" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "ℹ Arquivo .env já existe" -ForegroundColor Blue
    Write-Host ""
}

# Solicitar credenciais
Write-Host "Você precisa de suas credenciais Datadog:" -ForegroundColor Yellow
Write-Host "1. Acesse: https://app.datadoghq.com"
Write-Host "2. Settings → API Keys (copie DD_API_KEY)"
Write-Host "3. Settings → Application Keys (copie DD_APP_KEY)"
Write-Host ""

$api_key = Read-Host "Digite sua DD_API_KEY"
$app_key = Read-Host "Digite sua DD_APP_KEY"
$site = Read-Host "Digite seu DD_SITE (padrão: datadoghq.com)"

if ([string]::IsNullOrWhiteSpace($site)) {
    $site = "datadoghq.com"
}

# Atualizar .env
Write-Host ""
Write-Host "Atualizando .env..." -ForegroundColor Yellow

# Ler o conteúdo do .env
$env_content = Get-Content ".env"

# Substituir valores
$env_content = $env_content -replace "^DD_API_KEY=.*", "DD_API_KEY=$api_key"
$env_content = $env_content -replace "^DD_APP_KEY=.*", "DD_APP_KEY=$app_key"
$env_content = $env_content -replace "^DD_SITE=.*", "DD_SITE=$site"

# Salvar de volta
$env_content | Set-Content ".env"

Write-Host "✓ Variáveis de ambiente atualizadas" -ForegroundColor Green
Write-Host ""

# Verificar Docker
try {
    $docker_version = docker --version
    Write-Host "Docker encontrado: $docker_version" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está instalado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Iniciar containers
Write-Host "Iniciando containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "=== Configuração Completa ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ Agent Datadog iniciado" -ForegroundColor Green
Write-Host "✓ API iniciada em http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Aguarde 30 segundos para o agent ficar pronto"
Write-Host "2. Acesse: https://app.datadoghq.com/apm/traces"
Write-Host "3. Gere tráfego com curl ou Postman"
Write-Host ""
Write-Host "Ver logs:" -ForegroundColor Yellow
Write-Host "  docker logs -f dd-agent     # Agent Datadog"
Write-Host "  docker logs -f ml-api       # API"
Write-Host ""
