import torch
import torch.nn as nn
import numpy as np
import joblib
import os

# Definir la misma arquitectura LSTM usada en entrenamiento
class HealthLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(HealthLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out

# Obtener la ruta absoluta a la carpeta models (asumiendo que este script está en app/services)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # directorio app
MODELS_DIR = os.path.join(BASE_DIR, 'models', 'modulo_a')

def _cargar_modelo():
    config = joblib.load(os.path.join(MODELS_DIR, 'config_lstm.pkl'))
    model = HealthLSTM(
        input_size=config['input_size'],
        hidden_size=config['hidden_size'],
        num_layers=config['num_layers'],
        num_classes=config['num_classes']
    )
    model.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'modelo_lstm_health.pth'), map_location=torch.device('cpu')))
    model.eval()
    scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler_lstm.pkl'))
    label_mapping = joblib.load(os.path.join(MODELS_DIR, 'label_mapping_lstm.pkl'))
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
    # Construir array (1, 30, 3)
    seq = np.stack([hr_vals, spo2_vals, temp_vals], axis=1)  # (30,3)
    seq_reshaped = seq.reshape(-1, 3)
    seq_scaled = SCALER.transform(seq_reshaped)
    seq_scaled = seq_scaled.reshape(1, CONFIG['window_size'], 3)
    seq_tensor = torch.FloatTensor(seq_scaled)
    with torch.no_grad():
        output = MODEL(seq_tensor)
        probs = torch.softmax(output, dim=1).cpu().numpy()[0]
        pred_class = int(np.argmax(probs))
    categoria = INV_MAP[pred_class]
    probabilidades = {INV_MAP[i]: float(probs[i]) for i in range(3)}
    return categoria, probabilidades