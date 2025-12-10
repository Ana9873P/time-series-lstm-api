"""
Exemplo de integração de métricas e tracing customizadas com Datadog.
"""

import logging
from functools import wraps
from app.config.datadog_config import get_datadog_tracer
from statsd import StatsClient
import os

logger = logging.getLogger(__name__)

# Inicializar cliente DogStatsD para métricas customizadas
STATSD_HOST = os.getenv("DD_AGENT_HOST", "localhost")
STATSD_PORT = int(os.getenv("DD_DOGSTATSD_PORT", 8125))

try:
    statsd = StatsClient(host=STATSD_HOST, port=STATSD_PORT, namespace="ml_api")
    logger.info(f"StatsD client conectado em {STATSD_HOST}:{STATSD_PORT}")
except Exception as e:
    logger.warning(f"StatsD client não disponível: {e}")
    statsd = None


def trace_function(name: str = None):
    """
    Decorator para rastrear função com DDTrace.
    
    Uso:
        @trace_function("my_operation")
        def my_function():
            pass
    """
    def decorator(func):
        tracer = get_datadog_tracer()
        operation_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.trace(operation_name):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def metric(name: str, value: float, tags: list = None):
    """
    Enviar métrica customizada para Datadog.
    
    Uso:
        metric("prediction_latency", 0.45, tags=["model:lstm"])
    """
    if statsd:
        try:
            if tags:
                statsd.gauge(name, value, tags=tags)
            else:
                statsd.gauge(name, value)
        except Exception as e:
            logger.error(f"Erro ao enviar métrica '{name}': {e}")


def increment_counter(name: str, value: int = 1, tags: list = None):
    """
    Incrementar contador de métrica.
    
    Uso:
        increment_counter("predictions_total", tags=["status:success"])
    """
    if statsd:
        try:
            if tags:
                statsd.increment(name, value, tags=tags)
            else:
                statsd.increment(name, value)
        except Exception as e:
            logger.error(f"Erro ao incrementar '{name}': {e}")


def record_timing(name: str, duration_ms: float, tags: list = None):
    """
    Registrar duração de operação.
    
    Uso:
        record_timing("model_inference_time", 250.5, tags=["model:lstm"])
    """
    if statsd:
        try:
            if tags:
                statsd.timing(name, duration_ms, tags=tags)
            else:
                statsd.timing(name, duration_ms)
        except Exception as e:
            logger.error(f"Erro ao registrar timing '{name}': {e}")


# Exemplos de uso em handlers

def example_traced_operation():
    """Exemplo de operação com tracing."""
    tracer = get_datadog_tracer()
    
    with tracer.trace("data_processing"):
        # Processar dados
        pass
        
        # Registrar métrica customizada
        metric("processing_status", 1, tags=["status:success"])


def example_handler_with_metrics():
    """Exemplo de handler com métricas."""
    try:
        # Operação
        result = perform_operation()
        
        # Sucesso
        increment_counter("operations_success", tags=["operation:prediction"])
        metric("operation_latency", 0.5, tags=["operation:prediction"])
        
        return result
    except Exception as e:
        # Erro
        increment_counter("operations_error", tags=["operation:prediction"])
        logger.error(f"Erro na operação: {e}")
        raise


def perform_operation():
    """Placeholder para operação."""
    return {"status": "success"}
