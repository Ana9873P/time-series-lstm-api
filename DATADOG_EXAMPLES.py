"""
Exemplos de Integração Avançada com Datadog

Este arquivo demonstra como usar Datadog em cenários comuns
da sua API de ML.
"""

import logging
import time
from functools import wraps
from app.config.datadog_config import get_datadog_tracer
from app.config.datadog_metrics import (
    increment_counter,
    metric,
    record_timing,
    trace_function
)

logger = logging.getLogger(__name__)
tracer = get_datadog_tracer()


# ============================================================================
# EXEMPLO 1: Decorator para Rastreamento Automático de Funções
# ============================================================================

def traced_operation(operation_name: str, tags: dict = None):
    """
    Decorator para rastrear automaticamente uma função.
    
    Uso:
        @traced_operation("data_preprocessing", tags={"ticker": "AAPL"})
        def preprocess_data(df):
            return df.dropna()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Criar span com tags
            span_tags = {"function": func.__name__}
            if tags:
                span_tags.update(tags)
            
            with tracer.trace(operation_name, tags=span_tags):
                try:
                    result = func(*args, **kwargs)
                    
                    # Registrar sucesso
                    duration_ms = (time.time() - start_time) * 1000
                    record_timing(f"{operation_name}.duration", duration_ms)
                    increment_counter(f"{operation_name}.success")
                    
                    return result
                except Exception as e:
                    # Registrar erro
                    increment_counter(f"{operation_name}.error")
                    tracer.current_span().set_tag("error", True)
                    tracer.current_span().set_tag("error.message", str(e))
                    
                    logger.error(f"Erro em {operation_name}: {e}")
                    raise
        
        return wrapper
    
    return decorator


# ============================================================================
# EXEMPLO 2: Rastreamento de Modelo ML
# ============================================================================

@traced_operation("model_inference", tags={"model": "lstm"})
def predict_stock_price(model, data, ticker: str):
    """
    Exemplo de previsão com rastreamento completo.
    
    Métricas registradas:
    - model_inference.duration
    - model_inference.success/error
    - prediction.confidence
    """
    
    # Rastrear etapas internas
    with tracer.trace("data_validation", tags={"ticker": ticker}):
        # Validar dados
        if data is None or len(data) == 0:
            raise ValueError("Dados vazios")
        
        metric("validation.data_points", len(data), tags=[f"ticker:{ticker}"])
    
    # Rastrear inferência
    with tracer.trace("model_forward_pass"):
        prediction = model.predict(data)
        confidence = float(prediction[1])
        
        # Registrar confiança
        metric("prediction.confidence", confidence, tags=[f"ticker:{ticker}"])
    
    return {
        "ticker": ticker,
        "predicted_price": float(prediction[0]),
        "confidence": confidence
    }


# ============================================================================
# EXEMPLO 3: Monitoramento de Performance
# ============================================================================

@traced_operation("data_fetch")
def fetch_historical_data(ticker: str, days: int = 30):
    """
    Exemplo de coleta de dados com monitoramento de performance.
    """
    
    start_time = time.time()
    
    try:
        with tracer.trace("download_data", tags={"ticker": ticker, "days": days}):
            # Simular download
            time.sleep(0.1)
            data_points = days * 5  # 5 pontos por dia útil
            
            metric("data.fetch_points", data_points, tags=[f"ticker:{ticker}"])
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Alerta se muito lento
        if duration_ms > 1000:
            logger.warning(f"Fetch lento para {ticker}: {duration_ms}ms")
            metric("performance.slow_fetch", 1, tags=[f"ticker:{ticker}"])
        
        return {"success": True, "points": data_points}
    
    except Exception as e:
        increment_counter("data.fetch_error", tags=[f"ticker:{ticker}"])
        raise


# ============================================================================
# EXEMPLO 4: Monitoramento de Batch Processing
# ============================================================================

def process_batch_with_metrics(tickers: list, model):
    """
    Exemplo de processamento em lote com métricas agregadas.
    """
    
    with tracer.trace("batch_processing", tags={"batch_size": len(tickers)}):
        results = []
        successful = 0
        failed = 0
        total_duration = 0
        
        for ticker in tickers:
            try:
                start = time.time()
                
                # Executar previsão
                result = predict_stock_price(model, None, ticker)
                
                duration = (time.time() - start) * 1000
                total_duration += duration
                successful += 1
                
                results.append(result)
            
            except Exception as e:
                failed += 1
                logger.error(f"Erro ao processar {ticker}: {e}")
                increment_counter("batch.item_error", tags=[f"ticker:{ticker}"])
        
        # Registrar métricas da batch
        metric("batch.success_count", successful, tags=[f"batch_size:{len(tickers)}"])
        metric("batch.error_count", failed, tags=[f"batch_size:{len(tickers)}"])
        metric("batch.average_duration", total_duration / len(tickers), tags=[f"batch_size:{len(tickers)}"])
        
        return results


# ============================================================================
# EXEMPLO 5: Context Manager para Rastreamento
# ============================================================================

class DatadogTrace:
    """
    Context manager para rastreamento com Datadog.
    
    Uso:
        with DatadogTrace("my_operation", {"ticker": "AAPL"}):
            # seu código
    """
    
    def __init__(self, operation_name: str, tags: dict = None):
        self.operation_name = operation_name
        self.tags = tags or {}
        self.span = None
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.span = tracer.trace(self.operation_name, tags=self.tags).__enter__()
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.span.set_tag("error", True)
            self.span.set_tag("error.type", exc_type.__name__)
            increment_counter(f"{self.operation_name}.error")
        else:
            increment_counter(f"{self.operation_name}.success")
        
        record_timing(f"{self.operation_name}.duration", duration_ms)
        
        return self.span.__exit__(exc_type, exc_val, exc_tb)


# ============================================================================
# EXEMPLO 6: Uso do Context Manager
# ============================================================================

def example_usage():
    """Exemplo de uso do context manager."""
    
    # Rastreamento simples
    with DatadogTrace("database_query", {"table": "prices"}):
        # Executar query
        pass
    
    # Com tratamento de erro
    with DatadogTrace("api_call", {"endpoint": "/predict"}):
        try:
            # Fazer chamada
            pass
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise


# ============================================================================
# EXEMPLO 7: Correlação com Logs
# ============================================================================

def log_with_context(message: str, level: str = "info"):
    """
    Registrar log com contexto do trace Datadog.
    """
    
    # Obter informações do trace atual
    span = tracer.current_span()
    
    if span:
        logger.log(
            getattr(logging, level.upper()),
            f"{message} [trace_id={span.trace_id} span_id={span.span_id}]"
        )
    else:
        logger.log(getattr(logging, level.upper()), message)


# ============================================================================
# EXEMPLO 8: Exemplo Completo - Handler de API
# ============================================================================

def complete_api_handler_example(ticker: str, start_date: str, end_date: str, model):
    """
    Exemplo completo mostrando integração com todos os recursos.
    """
    
    request_id = f"{ticker}_{start_date}_{end_date}"
    
    with DatadogTrace("api_prediction_request", {
        "ticker": ticker,
        "request_id": request_id
    }):
        try:
            # 1. Fetch dados
            with DatadogTrace("data_fetch_step", {"ticker": ticker}):
                data = fetch_historical_data(ticker)
                log_with_context(f"Dados obtidos: {len(data)} pontos")
            
            # 2. Preprocess
            with DatadogTrace("preprocessing_step", {"ticker": ticker}):
                # processed_data = preprocess(data)
                log_with_context("Dados preprocessados")
            
            # 3. Previsão
            with DatadogTrace("prediction_step", {"ticker": ticker}):
                result = predict_stock_price(model, data, ticker)
                metric("final_prediction.confidence", result["confidence"])
            
            # Sucesso
            increment_counter(
                "api_request.success",
                tags=[f"ticker:{ticker}", "status:200"]
            )
            
            log_with_context(f"Previsão concluída para {ticker}", "info")
            
            return result
        
        except Exception as e:
            increment_counter(
                "api_request.error",
                tags=[f"ticker:{ticker}", f"error:{type(e).__name__}"]
            )
            
            log_with_context(
                f"Erro na previsão para {ticker}: {e}",
                "error"
            )
            raise


# ============================================================================
# Notas Importantes
# ============================================================================

"""
1. **Performance**: Datadog tem overhead mínimo (~1-2%)

2. **Tags**: Use tags consistentemente para melhor agregação
   - Evite alta cardinalidade (muitos valores únicos)
   - Use: ticker, status, modelo, versão

3. **Sampling**: Para alto volume, considere sampling
   - `tracer.trace(..., sample_rate=0.1)` para 10%

4. **Async**: Para código async, use context managers

5. **Segurança**: Nunca trace dados sensíveis
   - Evite senhas, tokens, dados PII em tags

6. **Monitoramento**: Visite app.datadoghq.com:
   - APM → Traces
   - Logs → Buscar pelo seu serviço
   - Metrics → Custom metrics
"""
