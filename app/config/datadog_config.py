"""
Configuração do Datadog para monitoramento e tracing da aplicação.
"""

import os
import logging
from datadog import initialize, api
from ddtrace import tracer
from ddtrace.contrib.fastapi import patch_all

logger = logging.getLogger(__name__)


def configure_datadog():
    """
    Configura o Datadog com base em variáveis de ambiente.
    
    Variáveis esperadas:
    - DD_API_KEY: Chave de API do Datadog (obrigatória)
    - DD_APP_KEY: Chave de aplicação do Datadog (obrigatória)
    - DD_AGENT_HOST: Host do agent Datadog (padrão: localhost)
    - DD_AGENT_PORT: Porta do agent Datadog (padrão: 8126)
    - DD_SERVICE: Nome do serviço (padrão: ml-microservice)
    - DD_ENV: Ambiente (padrão: development)
    - DD_TRACE_ENABLED: Habilitar tracing (padrão: true)
    """
    
    # Ler variáveis de ambiente
    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")
    agent_host = os.getenv("DD_AGENT_HOST", "localhost")
    agent_port = int(os.getenv("DD_AGENT_PORT", 8126))
    service_name = os.getenv("DD_SERVICE", "ml-microservice")
    env = os.getenv("DD_ENV", "development")
    trace_enabled = os.getenv("DD_TRACE_ENABLED", "true").lower() == "true"
    
    # Se não houver chaves, apenas log de aviso
    if not api_key or not app_key:
        logger.warning(
            "Datadog API/APP keys não configuradas. "
            "Defina DD_API_KEY e DD_APP_KEY para ativar o monitoramento."
        )
        return
    
    # Configurar cliente de API do Datadog
    options = {
        "api_key": api_key,
        "app_key": app_key,
    }
    
    try:
        initialize(**options)
        logger.info("Cliente Datadog API inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar cliente Datadog API: {e}")
    
    # Configurar tracer distribuído (DDTrace)
    if trace_enabled:
        try:
            tracer.configure(
                hostname=agent_host,
                port=agent_port,
                service=service_name,
                env=env,
                analytics_enabled=True,
            )
            logger.info(
                f"Tracer Datadog configurado: "
                f"host={agent_host}, port={agent_port}, "
                f"service={service_name}, env={env}"
            )
        except Exception as e:
            logger.error(f"Erro ao configurar tracer Datadog: {e}")


def get_datadog_tracer():
    """Retorna a instância global do tracer do Datadog."""
    return tracer
