FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Adicionar início do tracer Datadog
ENV DD_TRACE_STARTUP_LOGS=true
ENV DD_TRACE_DEBUG=false

CMD ["ddtrace-run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
