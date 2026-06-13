import torch
import torch.nn as nn
import numpy as np
import joblib
import os
import math

# --- Definir la misma arquitectura LSTM usada en el entrenamiento ---
class FallLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(FallLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

# --- Rutas a los artefactos ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models', 'modulo_b')

# --- Cargar configuración, modelo y scaler ---
config = joblib.load(os.path.join(MODELS_DIR, 'config_fall.pkl'))
model = FallLSTM(
    input_size=config['input_size'],
    hidden_size=config['hidden_size'],
    num_layers=config['num_layers']
)
model.load_state_dict(torch.load(os.path.join(MODELS_DIR, 'fall_model_pytorch.pth'), map_location=torch.device('cpu')))
model.eval()
scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler_fall.pkl'))

# --- Función para calcular orientación (pitch, roll, yaw) a partir de datos brutos ---
# Esta es una simplificación; en un sistema real necesitarías integrar el giroscopio.
# Para las caídas, los cambios bruscos en aceleración y giroscopio pueden ser suficientes.
def calcular_orientacion(ax, ay, az, gx, gy, gz):
    """
    Calcula pitch, roll y yaw (en radianes) a partir de los datos brutos.
    ax, ay, az: aceleraciones en m/s^2 (asumimos que ya incluyen gravedad)
    gx, gy, gz: velocidades angulares en rad/s (no se usan directamente aquí)
    """
    # Convertir a unidades de g (dividir por 9.81) para fórmulas estándar
    ax_g = ax / 9.81
    ay_g = ay / 9.81
    az_g = az / 9.81
    
    # Pitch (inclinación hacia adelante/atrás)
    pitch = math.atan2(-ax_g, math.sqrt(ay_g**2 + az_g**2))
    # Roll (inclinación lateral)
    roll = math.atan2(ay_g, az_g)
    # Yaw (orientación horizontal) – simplificado, en producción se integraría gz
    yaw = 0.0
    return pitch, roll, yaw

def transformar_ventana_imu(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals):
    """
    Convierte una ventana de datos brutos (listas de longitud WINDOW_SIZE)
    en la matriz de características esperada por el modelo: (1, WINDOW_SIZE, input_size)
    """
    window_size = config['window_size']
    features_list = []
    for i in range(window_size):
        ax, ay, az = ax_vals[i], ay_vals[i], az_vals[i]
        gx, gy, gz = gx_vals[i], gy_vals[i], gz_vals[i]
        pitch, roll, yaw = calcular_orientacion(ax, ay, az, gx, gy, gz)
        # Características en el orden usado en el entrenamiento
        feature_vector = [
            pitch, roll, yaw,
            gx, gy, gz,
            az, ax, ay   # Nota: en el script original es 'accz', 'accx', 'accy'
        ]
        features_list.append(feature_vector)
    # Escalar usando el scaler guardado
    features_array = np.array(features_list)  # (window_size, 9)
    features_scaled = scaler.transform(features_array)
    # Añadir dimensión de batch
    features_scaled = features_scaled.reshape(1, window_size, -1)
    return features_scaled

def predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals):
    """
    ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals: listas de 20 valores cada una.
    Retorna: (probabilidad_caida, es_caida_booleana)
    """
    if len(ax_vals) != config['window_size']:
        raise ValueError(f"Se requieren {config['window_size']} lecturas por ventana, recibidas {len(ax_vals)}")
    input_tensor = torch.FloatTensor(transformar_ventana_imu(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals))
    with torch.no_grad():
        output = model(input_tensor)
        prob = output.item()  # probabilidad de caída (entre 0 y 1)
    es_caida = prob > 0.5
    return prob, es_caida