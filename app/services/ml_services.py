import torch
import torch.nn as nn
import numpy as np
import joblib
import os

# Definir la arquitectura FeedForward del modelo actualizado
class HealthFeedForward(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, num_classes),
        )

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.network(x)

# Obtener la ruta absoluta a la carpeta models (asumiendo que este script está en app/services)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # directorio app
MODELS_DIR = os.path.join(BASE_DIR, 'models', 'modulo_a')

def _cargar_modelo():
    config = joblib.load(os.path.join(MODELS_DIR, 'config_feedforward.pkl'))
    model = HealthFeedForward(
        input_size=config['input_size'],
        hidden_size=config['hidden_size'],
        num_classes=config['num_classes']
    )
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'modelo_feedforward_health.pth'), map_location=torch.device('cpu')))
    model.eval()
    scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler_feedforward.pkl'))
    label_mapping = joblib.load(os.path.join(MODELS_DIR, 'label_mapping_feedforward.pkl'))
    inv_map = {v: k for k, v in label_mapping.items()}  # {0:'okay',1:'warning',2:'bad'}
    return model, scaler, inv_map, config

MODEL, SCALER, INV_MAP, CONFIG = _cargar_modelo()

def predecir_ventana(hr_vals, spo2_vals, temp_vals):
    """
    hr_vals, spo2_vals, temp_vals: listas de 30 valores (float)
    Retorna: (categoria_str, dict_probabilidades)
    """
    if len(hr_vals) != CONFIG['window_size']:
        raise ValueError(f"Se requieren {CONFIG['window_size']} lecturas, se recibieron {len(hr_vals)}")
    # Construir array (30, 3)
    seq = np.column_stack([hr_vals, spo2_vals, temp_vals]).astype(float)
    # Normalizar: reshape para aplicar scaler
    seq_scaled = SCALER.transform(seq.reshape(-1, 3)).reshape(1, -1)
    # Convertir a tensor
    seq_tensor = torch.FloatTensor(seq_scaled)
    with torch.no_grad():
        output = MODEL(seq_tensor)
        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
        pred_class = int(np.argmax(probs))
    categoria = INV_MAP[pred_class]
    probabilidades = {INV_MAP[i]: float(probs[i]) for i in range(3)}
    return categoria, probabilidades