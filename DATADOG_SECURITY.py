"""
Guia de Segurança e Boas Práticas - Datadog

Este arquivo documenta como configurar Datadog de forma segura
em produção.
"""

# ============================================================================
# 1. PROTEÇÃO DE CREDENCIAIS
# ============================================================================

# Adicione ao seu .gitignore:
gitignore_entries = """
# Datadog
.env
.env.local
.env.*.local

# Secrets
*.key
*.secret
/secrets/
"""


# ============================================================================
# 2. BOAS PRÁTICAS DE TAGS
# ============================================================================

"""
Tags ajudam a organizar dados no Datadog.
Use-as consistentemente para melhor monitoramento.
"""

recommended_tags = {
    "deployment": ["service:ml-microservice", "env:production"],
    "technical": ["model:lstm", "version:1.0.0"],
    "business": ["ticker:AAPL", "prediction_type:daily"],
    "operations": ["region:us-east-1", "cluster:prod"],
}


# ============================================================================
# 3. PROTEÇÃO DE DADOS SENSÍVEIS
# ============================================================================

"""
Datadog armazena dados em seus servidores.
Algumas informações devem ser mascaradas.
Evite enviar PII (Personally Identifiable Information)
"""

# Exemplo de mascaramento:
import hashlib

def safe_tag_user_id(user_id: str) -> str:
    """Cria tag segura a partir de ID de usuário."""
    # Hash em lugar de ID real
    hashed = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    return f"user_segment:{hashed}"

def safe_tag_price(price: float) -> str:
    """Cria tag de faixa de preço em lugar de preço exato."""
    if price < 10:
        return "price_range:under_10"
    elif price < 100:
        return "price_range:10_to_100"
    else:
        return "price_range:over_100"


# ============================================================================
# 4. CONFIGURAÇÃO SEGURA EM PRODUÇÃO
# ============================================================================

"""
Para produção, use variáveis de ambiente de forma segura.
"""

# Configuração recomendada para produção:
production_env_setup = """
# 1. Use secrets manager (AWS Secrets Manager, HashiCorp Vault, etc)
# 2. Defina variáveis via CI/CD (GitHub Actions, GitLab CI, etc)
# 3. Não armazene .env em produção
# 4. Use IAM roles/policies para acesso
# 5. Rotacione credenciais regularmente

# Exemplo com Docker Swarm/Kubernetes:
apiVersion: v1
kind: Secret
metadata:
  name: datadog-secrets
type: Opaque
stringData:
  DD_API_KEY: ${DD_API_KEY}  # Injetado via CI/CD
  DD_APP_KEY: ${DD_APP_KEY}  # Injetado via CI/CD
"""


# ============================================================================
# 5. POLÍTICA DE RETENÇÃO DE DADOS
# ============================================================================

"""
Datadog cobra por retenção de dados.
Configure retention policies apropriadas.

Padrão:
- Traces: 15 dias (pode aumentar)
- Logs: 30 dias (configurável)
- Metrics: 15 meses
- Custom metrics: conforme plano

Para reduzir custos:
- Use sampling de traces
- Archive logs para S3
- Configure exclusão de logs muito verbosos
"""

# Configurar sampling em código:
from ddtrace import tracer

# 50% de sampling para operações de alto volume
@tracer.wrap("high_volume_operation", sample_rate=0.5)
def high_volume_function():
    pass


# ============================================================================
# 6. CONFORMIDADE E REGULAMENTAÇÕES
# ============================================================================

"""
Se você processa dados sob regulamentações, observe:

GDPR (Europa):
- Datadog oferece Data Processing Agreement (DPA)
- Direito ao apagamento em Datadog
- Dados pessoais devem ser minimizados

HIPAA (Saúde - EUA):
- Datadog pode ser HIPAA compliant com BAA
- Criptografia de dados em trânsito e em repouso

PCI-DSS (Pagamentos):
- Não envie dados de cartão para Datadog
- Use hashing para dados sensíveis

SOC 2 Type II:
- Datadog é certificado SOC 2

CCPA (Califórnia):
- Similiar a GDPR, direitos do consumidor
"""


# ============================================================================
# 7. AUDITORIA E COMPLIANCE
# ============================================================================

"""
Monitore quem acessa suas credenciais e dados:

1. Audit Logs:
   - Settings → Audit Trail
   - Ver quem criou/modificou monitors
   - Ver quem acessou dashboards

2. Access Control:
   - Use roles e permissions
   - Princípio de least privilege
   - MFA para contas admin

3. Data Access:
   - Restrinja acesso a dashboards sensíveis
   - Use restricções de role para logs/traces
   - Audit trail de downloads
"""


# ============================================================================
# 8. SEGURANÇA DE NETWORK
# ============================================================================

"""
Comunicação com Datadog é cifrada.

Configuração segura:
- TLS 1.2+ para todos os dados
- Certificados auto-assinados verificados
- Firewall rules para agent Datadog
- Private Link disponível em EUs premium
"""

# Verificar TLS:
# curl https://api.datadoghq.com/ -v
# Deve mostrar TLS 1.2 ou superior


# ============================================================================
# 9. ROTEIRO DE SEGURANÇA - CHECKLIST
# ============================================================================

security_checklist = """
□ Credenciais em .env, não commitadas
□ .env no .gitignore
□ Usar variáveis de ambiente em produção
□ Não incluir PII em logs/tags
□ Mascarar dados sensíveis
□ Rotação regular de API keys
□ MFA habilitado em conta Datadog
□ Audit logs revisados regularmente
□ Retention policies configuradas
□ Role-based access control (RBAC) ativado
□ TLS/HTTPS em todas as comunicações
□ Alertas para atividade suspeita
□ Backup de configurações
□ Disaster recovery plan
□ Documentação de security policies
"""


# ============================================================================
# 10. INCIDENT RESPONSE
# ============================================================================

"""
Se suas credenciais forem comprometidas:

1. IMEDIATO:
   - Revogar keys em https://app.datadoghq.com
   - Criar novas keys
   - Atualizar em todos os lugares

2. CURTO PRAZO:
   - Investigar em Audit Trail o que foi acessado
   - Rodar compliance check
   - Rotear senhas/tokens do Datadog

3. LONGO PRAZO:
   - Implementar secrets rotation automática
   - Revisar políticas de acesso
   - Treinar equipe em segurança
   - Atualizar documentação
"""


# ============================================================================
# CONTATO E SUPORTE
# ============================================================================

"""
Para questões de segurança:

Datadog Security Team:
- Email: security@datadoghq.com
- Vulnerability Disclosure: https://app.datadoghq.com/security/disclosure

Documentação Oficial:
- https://docs.datadoghq.com/security/
- https://docs.datadoghq.com/account_management/rbac/
"""

print(__doc__)
