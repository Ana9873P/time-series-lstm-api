import pickle
import torch
import torch.nn as nn
import io
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import yfinance as yf
import traceback

SEQ_LENGTH = 30
DEVICE = "cpu"

# Definição do Modelo LSTM
class SimpleLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, dropout_prob):
        super(SimpleLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # input_size=5 ('Close', 'daily_return', '5-day_volatility', '10-day_volatility', '15-day_volatility')
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)

        # Camanda dropout (desliga neuronios)
        self.dropout = nn.Dropout(dropout_prob)

        # Conecta a saída do LSTM ao output final (previsão de 1 valor)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        """
        Forward pass for the SimpleLSTM.
        Expects input x with shape (batch, seq_len, input_size).
        Returns tensor with shape (batch, output_size).
        """
        # LSTM returns output for all timesteps and the hidden state tuple
        out, (hn, cn) = self.lstm(x)
        # Use the last timestep's output for prediction
        last = out[:, -1, :]
        last = self.dropout(last)
        out = self.fc(last)
        return out


# CPU - Custom Unpickler para forçar o carregamento na CPU
class CpuUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == 'torch.storage' and name == '_load_from_bytes':
            # Retorna uma função lambda que chama torch.load forçando a CPU
            return lambda b: torch.load(io.BytesIO(b), map_location='cpu')
        if module == '__main__':
            # Tenta resolver localmente o nome (por ex. SimpleLSTM)
            if name in globals():
                return globals()[name]

        # Para o resto, usa o comportamento padrão
        return super().find_class(module, name)
        
# Construindo a janela deslizante
def create_sequences_multivariate(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length, :])
        y.append(data[i + seq_length, 0])
    return np.array(X), np.array(y)

def obtemDadosHistoricos(ticker, data_inicial, data_final):
    dados= yf.download(ticker, start=data_inicial, end=data_final)
    colunas= []
    for col in dados.columns:
        colunas.append(col[0])
    dados.columns= colunas
    return dados

# Estratégia 2: Preço de abertura, máxima, mínima, fechamento e volume
def build_features_estrategia2(data):
    columns = ['Close']
    return data[columns]


def obtemX_testeY_teste_Janela_Deslisante(ticker, data_inicial, data_final):
    # 1. Converter string para data real
    dt_inicial = pd.to_datetime(data_inicial)
    
    # 2. Calcular o "Buffer" de segurança.
    # Precisamos de 30 dias ÚTEIS para trás. 
    # Como existem fins de semana, pegamos 60 dias corridos para garantir que sobe.
    buffer_dias = SEQ_LENGTH * 2 
    dt_fetch_start = dt_inicial - pd.Timedelta(days=buffer_dias)
    
    # 3. Baixar dados com margem extra
    print(f"Buscando dados históricos desde {dt_fetch_start.date()} para preencher a janela...")
    dados_brutos = obtemDadosHistoricos(ticker, dt_fetch_start, data_final)
    
    # 4. Encontrar onde começa a data que o usuário pediu
    # O dataframe tem datas no índice. Vamos filtrar para garantir o corte exato.
    # Precisamos garantir que temos exatos SEQ_LENGTH dias ANTES da data_inicial.
    
    # Resetar index para facilitar manipulação se o indice for data
    if isinstance(dados_brutos.index, pd.DatetimeIndex):
        dados_brutos = dados_brutos.reset_index()
        
    # Localizar o índice da primeira data >= data_inicial
    # Coluna 'Date' geralmente é criada pelo reset_index ou yfinance
    mask_start = dados_brutos.iloc[:, 0] >= dt_inicial # Assume data na col 0
    if not mask_start.any():
         raise ValueError("Data inicial não encontrada nos dados baixados.")
         
    idx_start_user = mask_start.idxmax() # Primeiro índice True
    
    # O corte deve começar SEQ_LENGTH posições antes desse índice
    idx_corte = idx_start_user - SEQ_LENGTH
    
    if idx_corte < 0:
        # Se não tiver dados suficientes no passado (ex: IPO recente), avisa
        print("AVISO: Histórico insuficiente para cobrir a janela completa antes da data inicial.")
        idx_corte = 0

    # Cortamos o dataframe para começar exatamente onde precisamos
    dados_validos = dados_brutos.iloc[idx_corte:]
    
    # Voltamos o indice para data se necessário, ou apenas pegamos as features
    # (Seu código espera que build_features receba o DF original do yfinance)
    # Como manipulei o índice, vou reconstruir o DF padrão para manter compatibilidade
    dados_validos = dados_validos.set_index(dados_validos.columns[0])
    
    data = build_features_estrategia2(dados_validos)

    # Construindo a janela deslizante
    data_np = data.to_numpy()
    
    # Verificação de segurança
    if len(data_np) <= SEQ_LENGTH:
         raise ValueError(f"Dados insuficientes ({len(data_np)}) para janela de {SEQ_LENGTH}.")

    X, y = create_sequences_multivariate(data_np, SEQ_LENGTH)

    print(f'X.shape original: {X.shape}, y.shape original: {y.shape}')

    # --- O RESTO SEGUE IGUAL AO SEU CÓDIGO ---
    X_test_reshaped = X.reshape(-1, 1)
    
    # Atenção aqui: o scaler deve ser fitado em X ou y? 
    # Geralmente fitamos no treino e usamos no teste. 
    # Se você está fitando no teste, está vazando informação, mas vou manter sua lógica.
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaler.fit(X_test_reshaped)

    X_test_norm = scaler.transform(X_test_reshaped).reshape(X.shape)
    y_test_norm = scaler.transform(y.reshape(-1, 1))

    # Convertendo para tensores
    X_test = torch.from_numpy(X_test_norm).float().to(DEVICE).unsqueeze(-1)
    y_test = torch.from_numpy(y_test_norm).float().to(DEVICE).unsqueeze(1)

    print(f'Final -> X_test: {X_test.shape} (Esperado ~43 dias)')
    
    return (X_test, y_test, scaler)


def obtemX_para_um_dia(ticker, target_date):
    """Prepara uma única sequência (batch size 1) para prever o dia seguinte ao
    `target_date` usando as últimas SEQ_LENGTH observações úteis disponíveis.

    Retorna: (X_test_tensor, scaler)
    X_test_tensor shape: (1, SEQ_LENGTH, 1) pronto para o modelo.
    """
    # Converter target_date para pandas Timestamp e buscar histórico com folga
    end = pd.to_datetime(target_date)
    # Pedimos um período maior para compensar fins de semana/feriados
    start = end - pd.Timedelta(days=SEQ_LENGTH * 3)

    dados = obtemDadosHistoricos(ticker, start.date().isoformat(), end.date().isoformat())
    data = build_features_estrategia2(dados)

    data = data.to_numpy()
    if data.shape[0] < SEQ_LENGTH:
        # Retornar erro amigável em vez de lançar exceção
        return None, None, {"error": f"Dados históricos insuficientes: {data.shape[0]} linhas (precisa de {SEQ_LENGTH})"}

    # Pega as últimas SEQ_LENGTH observações disponíveis (mais recente primeiro)
    seq = data[-SEQ_LENGTH:, :]

    # Monta array com shape (1, SEQ_LENGTH, n_features)
    X = seq.reshape(1, SEQ_LENGTH, seq.shape[1])

    # Normalização (mesma estratégia usada na preparação em janela deslizante)
    X_reshaped = X.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaler.fit(X_reshaped)
    X_norm = scaler.transform(X_reshaped).reshape(X.shape)

    X_test = torch.from_numpy(X_norm).float().to(DEVICE).unsqueeze(-1)

    return X_test, scaler, None

def executar_previsao(model, dados_tensor):
    """
    Retorna uma tupla (resultado, erro).
    Se houver erro, 'resultado' é None e 'erro' contém o dict pronto para retorno.
    """
    try:
        with torch.no_grad():
            prediction = model(dados_tensor.squeeze(3)).cpu().numpy()
            return prediction, None
            
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Erro interno no PyTorch: {e}")
        
        # FALHA: Monta o objeto de erro aqui mesmo
        error_response = {
            "error": "Erro durante inferência", 
            "details": str(e), 
            "trace": tb
        }
        # Retorna None no dado e o erro preenchido
        return None, error_response


    