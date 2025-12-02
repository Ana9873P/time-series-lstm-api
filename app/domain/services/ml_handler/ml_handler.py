import io
import pickle
import torch
import logging
from app.domain.services.avaluation_model_service import SimpleLSTM

logger = logging.getLogger(__name__)

# Sua classe customizada para converter de GPU para CPU
class CpuUnpickler(pickle.Unpickler):
    def find_class(self, module, name):

        if module == '__main__' and name == 'SimpleLSTM':
            return SimpleLSTM
        
        if module == 'torch.storage' and name == '_load_from_bytes':
            return lambda b: torch.load(io.BytesIO(b), map_location='cpu')

        return super().find_class(module, name)

# Variável global que guardará o modelo
_modelo_carregado = None

def carregar_modelo_global(model_path: str = None):
    """
    Carrega o modelo do disco para a memória global.
    Deve ser chamado apenas UMA VEZ ao iniciar o app.
    """
    global _modelo_carregado
    arquivo_modelo = model_path

    try:
        logger.info("Carregando modelo %s para a memória...", arquivo_modelo)
        with open(arquivo_modelo, 'rb') as f:
            _modelo_carregado = CpuUnpickler(f).load()

        if hasattr(_modelo_carregado, 'eval'):
            _modelo_carregado.eval()
            
        logger.info("Modelo carregado com sucesso!")
        return _modelo_carregado

    except Exception as e:
        logger.exception("FATAL: Erro ao carregar modelo: %s", e)
        return None

def obter_modelo():
    """
    Retorna a instância do modelo já carregado.
    Se por acaso não estiver carregado, tenta carregar (Lazy Loading).
    """
    global _modelo_carregado
    if _modelo_carregado is None:
        return carregar_modelo_global()
    return _modelo_carregado