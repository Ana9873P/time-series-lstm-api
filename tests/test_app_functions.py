'''
Teste unitário das funções em app.domain.services.avaluation_model_service.py.
Este arquivo
contém uma suíte de testes unitários que verificam funções da camada de serviço/modelo sem acessar rede ou arquivos grandes.
'''


import numpy as np
import pandas as pd
import torch

from app.domain.services.avaluation_model_service import (
    create_sequences_multivariate,
    build_features_estrategia2,
    SimpleLSTM,
    run_forecast,
    generate_recursive_forecast,
)


def test_create_sequences_multivariate_shapes():
    # Create artificial data: 40 rows, 3 features
    data = np.arange(40 * 3).reshape(40, 3).astype(float)
    seq_length = 5
    X, y = create_sequences_multivariate(data, seq_length)
    # Expect len(data) - seq_length sequences
    assert X.shape[0] == 40 - seq_length
    assert X.shape[1] == seq_length
    assert X.shape[2] == 3
    assert y.shape[0] == 40 - seq_length


def test_build_features_estrategia2_returns_close_column():
    # Build dataframe with standard yfinance columns
    idx = pd.date_range('2025-01-01', periods=3, freq='D')
    df = pd.DataFrame(
        data={
            ('Close', ''): [10.0, 11.0, 12.0],
            ('Open', ''): [9.0, 10.0, 11.0],
        },
        index=idx,
    )
    # pandas MultiIndex columns can be simplified by renaming in the function; test expects 'Close' column available
    df.columns = pd.MultiIndex.from_tuples([('Close', ''), ('Open', '')])
    # The function expects a DataFrame with column names, and returns only the 'Close' column
    result = build_features_estrategia2(df)
    assert 'Close' in result.columns
    assert list(result['Close'].values) == [10.0, 11.0, 12.0]


def test_simplest_lstm_forward_shape():
    # Create a SimpleLSTM and pass a small tensor
    model = SimpleLSTM(input_size=1, hidden_size=4, num_layers=1, output_size=1, dropout_prob=0.0)
    x = torch.randn(2, 6, 1)  # batch=2, seq_len=6, input_size=1
    out = model(x)
    assert out.shape == (2, 1)


def test_run_forecast_with_dummy_model_returns_numpy_and_no_error():
    class DummyModel:
        def __call__(self, x):
            # Return a tensor of shape (batch, 1)
            return torch.tensor([[0.42]])

    dummy = DummyModel()
    # Create a dummy tensor shaped like the model expects: batch x seq_len x features x 1 removed by code
    data = torch.randn(1, 6, 1, 1)
    preds, err = run_forecast(dummy, data)
    assert err is None
    assert isinstance(preds, np.ndarray)


def test_generate_recursive_forecast_creates_future_dates_and_preds():
    # Dummy model that returns a single-element tensor
    class DummyModel:
        def eval(self):
            return None

        def __call__(self, x):
            # Always predict 0.1 as normalized value
            return torch.tensor(0.1)

    class DummyScaler:
        def inverse_transform(self, arr):
            # return the same numeric values in a 2D numpy array
            return np.array(arr, dtype=float)

    seq_len = 5
    # last_window_tensor should be shape [seq_len, 1] or [seq_len, 1, 1]; use [seq_len,1]
    last_window = torch.zeros(seq_len, 1)
    last_val_norm = 0.2
    last_date = '2025-12-01'
    target_end_date = '2025-12-05'

    dates, preds = generate_recursive_forecast(
        model=DummyModel(),
        scaler=DummyScaler(),
        last_window_tensor=last_window,
        last_val_norm=last_val_norm,
        last_date=last_date,
        target_end_date=target_end_date,
    )

    # There should be at least one business day in the range
    assert isinstance(dates, list)
    assert isinstance(preds, list)
    # lengths must match
    assert len(dates) == len(preds)
