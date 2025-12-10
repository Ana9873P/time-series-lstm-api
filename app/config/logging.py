import logging
import sys
import os
import json
from logging import Formatter, StreamHandler


class JSONFormatter(Formatter):
    """Formata logs em JSON para melhor integração com Datadog."""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar info de exceção se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adicionar atributos customizados se houver
        if hasattr(record, "dd_trace_id"):
            log_data["dd_trace_id"] = record.dd_trace_id
        if hasattr(record, "dd_span_id"):
            log_data["dd_span_id"] = record.dd_span_id
            
        return json.dumps(log_data)


def configure_logging():
    """Configure root logger to output to stdout.

    Level is controlled by environment variable LOG_LEVEL (default INFO).
    Outputs JSON format for Datadog integration.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    use_json = os.getenv("LOG_FORMAT", "json").lower() == "json"

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicate logs in some environments
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = StreamHandler(sys.stdout)
    
    if use_json:
        formatter = JSONFormatter()
    else:
        fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        formatter = Formatter(fmt)
    
    handler.setFormatter(formatter)
    root.addHandler(handler)
