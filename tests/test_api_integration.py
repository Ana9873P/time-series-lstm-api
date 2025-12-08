'''
Teste de integração das rotas da API em app.routers.api com handlers monkeypatched.
Passos principais:
Define a função
        make_app_with_monkeypatched_handlers()
        Define duas funções dummy:
        dummy_between_dates(req, model) — retorna um dict simples com keys: "ticker", "predictions" e "type": "between_dates".
        dummy_single_day(req, model) — retorna um dict com "ticker", "prediction" e "type": "single_day".
        Substitui (monkeypatch) as funções originais importadas no módulo app.routers.api:
        api_module.handle_ticker_info_between_dates = dummy_between_dates
        api_module.handle_ticker_info_specific_date = dummy_single_day
        Isso faz com que, quando as rotas chamarem os handlers, os dummies sejam executados em vez da lógica real.
        Cria uma instância FastAPI(), define app.state.model = object() (um modelo dummy no estado, para que a dependência get_model não falhe)
        e inclui o router do módulo (app.include_router(api_module.router, prefix="/api")).
        Retorna essa app preparada para testes.

Motivação do monkeypatch:

Evita tocar código pesado ou externo (como carregar modelo PyTorch, acessar yfinance, ou executar lógica longa).
Permite testar apenas o comportamento das rotas (validação de payloads e wiring do endpoint) de forma rápida e isolada.

test_previsao_dia_endpoint_returns_expected
    Cria a app com make_app_with_monkeypatched_handlers() e um TestClient.
    Monta um payload JSON com target_date e ticker.
    Faz POST em /api/v1/previsao-dia.
    Verifica:
    Status HTTP 200.
    Que o JSON retornado tem type == "single_day".
    Que o campo ticker do retorno coincide com o ticker enviado.
'''

import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.api as api_module


def make_app_with_monkeypatched_handlers():
    def dummy_between_dates(req, model):
        return {"ticker": req.ticker, "predictions": [1.23, 1.45], "type": "between_dates"}

    def dummy_single_day(req, model):
        return {"ticker": req.ticker, "prediction": 2.34, "type": "single_day"}

    api_module.handle_ticker_info_between_dates = dummy_between_dates
    api_module.handle_ticker_info_specific_date = dummy_single_day

    app = FastAPI()
    
    app.state.model = object()
    app.include_router(api_module.router, prefix="/api")
    return app


def test_previsao_dia_endpoint_returns_expected():
    app = make_app_with_monkeypatched_handlers()
    client = TestClient(app)

    payload = {
        "target_date": "2025-06-01",
        "ticker": "ITUB4.SA"
    }

    resp = client.post("/api/v1/previsao-dia", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("type") == "single_day"
    assert data.get("ticker") == payload["ticker"]


def test_previsao_entre_datas_endpoint_returns_expected():
    app = make_app_with_monkeypatched_handlers()
    client = TestClient(app)

    payload = {
        "init_date": "2025-06-01",
        "end_date": "2025-06-10",
        "ticker": "ITUB4.SA"
    }

    resp = client.post("/api/v1/previsao-entre-datas", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("type") == "between_dates"
    assert data.get("ticker") == payload["ticker"]
