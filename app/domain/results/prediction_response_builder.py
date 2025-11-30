from typing import List, Optional, Dict, Any
import pandas as pd
from itertools import zip_longest

class PredictionResponseBuilder:
    def __init__(self):
        self._ticker: str = ""
        self._metadata: Dict[str, Any] = {}
        self._data: List[Dict[str, Any]] = []

    def set_ticker(self, ticker: str) -> 'PredictionResponseBuilder':
        self._ticker = ticker
        return self

    def set_metadata(self, model_version: str, period_type: str, **kwargs) -> 'PredictionResponseBuilder':
        """
        Define metadados padrão e aceita extras via kwargs.
        """
        self._metadata = {
            "model_version": model_version,
            "period": period_type,
            **kwargs
        }
        return self

    def add_prediction(self, date: Any, prediction: float, actual: Optional[float] = None) -> 'PredictionResponseBuilder':
        """
        Adiciona um ponto de dado. Calcula automaticamente o diff e formata a data.
        """
        p_val = round(float(prediction), 2)
        
        item = {
            "date": pd.to_datetime(date).strftime('%Y-%m-%d'),
            "prediction": p_val,
            "actual": None,
            "diff": None
        }

        if actual is not None:
            a_val = round(float(actual), 2)
            item["actual"] = a_val
            item["diff"] = round(p_val - a_val, 2)

        self._data.append(item)
        return self

    def add_batch_predictions(self, dates: list, predictions: list, actuals: list) -> 'PredictionResponseBuilder':
        """
        Utilitário para adicionar múltiplos dados de uma vez (ideal para o loop).
        """
        for date_val, pred_val, actual_val in zip_longest(dates, predictions, actuals, fillvalue=None):
            
            if date_val is None: continue 
            
            self.add_prediction(date_val, pred_val, actual_val)
            
        return self

    def build(self) -> Dict[str, Any]:
        """
        Finaliza a construção e retorna o dicionário formatado.
        Atuaiza metadados dependentes dos dados (como count ou type).
        """
        # Regra dinâmica: Se temos 'actual', é backtest, senão é forecast (para single day)
        if "type" not in self._metadata:
            has_actual = any(d["actual"] is not None for d in self._data)
            self._metadata["type"] = "backtest" if has_actual else "forecast"

        # Atualiza count se não tiver sido passado
        if "count" not in self._metadata:
            self._metadata["count"] = len(self._data)

        return {
            "ticker": self._ticker,
            "metadata": self._metadata,
            "data": self._data
        }