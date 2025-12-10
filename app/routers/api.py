from fastapi import APIRouter, Depends
from app.config.dependencies import get_model
from app.schemas.ticker_request import TickerRequestBetweenDates, TickerRequest
from app.domain.commands.avaluation_prices_commands import handle_ticker_info_specific_date, handle_ticker_info_between_dates
from app.config.datadog_config import get_datadog_tracer
from app.config.datadog_metrics import increment_counter, metric
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)
tracer = get_datadog_tracer()


@router.post("/v1/previsao-entre-datas", response_model=dict, summary="Previsão de preços por ticker")
def ticker_info(payload: TickerRequestBetweenDates, model = Depends(get_model)):
    """
    Recebe data inicial, data final e ticker, retornando a previsão de preços da bolsa para esse período.
    """
    start_time = time.time()
    
    try:
        with tracer.trace("ticker_prediction_between_dates", tags={"ticker": payload.ticker}):
            result = handle_ticker_info_between_dates(payload, model)
        
        duration = (time.time() - start_time) * 1000
        metric("prediction.latency", duration, tags=[f"endpoint:previsao-entre-datas", f"ticker:{payload.ticker}"])
        increment_counter("predictions.total", tags=[f"endpoint:previsao-entre-datas", "status:success"])
        
        return result
    except Exception as e:
        logger.error(f"Erro na previsão entre datas para {payload.ticker}: {e}")
        increment_counter("predictions.total", tags=[f"endpoint:previsao-entre-datas", "status:error"])
        raise


@router.post("/v1/previsao-dia", response_model=dict, summary="Previsão de preço por ticker em um dia específico")
def ticker_info_specific(payload: TickerRequest, model = Depends(get_model)):
    """
    Recebe data e ticker, retornando a previsão de preço da bolsa e se houver, o preço real.
    """
    start_time = time.time()
    
    try:
        with tracer.trace("ticker_prediction_specific_date", tags={"ticker": payload.ticker, "date": str(payload.date)}):
            result = handle_ticker_info_specific_date(payload, model)
        
        duration = (time.time() - start_time) * 1000
        metric("prediction.latency", duration, tags=[f"endpoint:previsao-dia", f"ticker:{payload.ticker}"])
        increment_counter("predictions.total", tags=[f"endpoint:previsao-dia", "status:success"])
        
        return result
    except Exception as e:
        logger.error(f"Erro na previsão para {payload.ticker} em {payload.date}: {e}")
        increment_counter("predictions.total", tags=[f"endpoint:previsao-dia", "status:error"])
        raise
