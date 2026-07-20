# Guía de Uso de Modelos ML - HealthWatch

## Arquitectura General

```
InfluxDB (biometrics)
    │
    ├── app/services/telemetria_service.py
    │   ├── obtener_ultima_ventana()       → HR, SpO2, Temp (30 lecturas)
    │   └── obtener_ultima_ventana_imu()   → ax, ay, az, gx, gy, gz (20 lecturas)
    │
    ├── app/services/ml_services.py        → Módulo A: Clasificación Salud (FeedForward)
    │   └── predecir_ventana(hr, spo2, temp) → "okay" | "warning" | "bad"
    │
    ├── app/services/ml_fall_service.py    → Módulo B: Detección Caídas
    │   └── predecir_caida(ax, ay, az, gx, gy, gz) → (probabilidad, es_caida)
    │
    ├── app/services/alertas_ml.py         → Scheduler automático (c/15s)
    ├── app/services/alertas_caidas.py     → Scheduler automático (c/10s)
    │
    └── app/routers/pacientes.py           → Endpoints on-demand
        ├── GET /api/pacientes/{id}/estado         → Módulo A
        └── GET /api/pacientes/{id}/estado_caida   → Módulo B
```

---

## Módulo A: Clasificación de Salud (Estrés/Fatiga)

### Modelo
- **Tipo:** FeedForward (PyTorch)
- **Archivos:** `app/models/modulo_a/`
  - `modelo_feedforward_health.pth` - pesos del modelo
  - `config_feedforward.pkl` - hiperparámetros (window_size=30, input_size=90, hidden_size=64, num_classes=3)
  - `scaler_feedforward.pkl` - StandardScaler para normalizar features
  - `label_mapping_feedforward.pkl` - mapeo de clases: `{"okay": 0, "warning": 1, "bad": 2}`

### Input esperado
- 3 listas de **exactamente 30 valores** cada una (ventana de 30 lecturas):
  - `hr_vals`: frecuencia cardíaca (BPM)
  - `spo2_vals`: saturación de oxígeno (%)
  - `temp_vals`: temperatura corporal (°C)

### Output
```json
{
    "clasificacion": "okay",    // "okay" | "warning" | "bad"
    "probabilidades": {
        "okay": 0.85,
        "warning": 0.12,
        "bad": 0.03
    }
}
```

### Cómo usarlo desde código
```python
from app.services.ml_services import predecir_ventana

categoria, probs = predecir_ventana(hr_vals, spo2_vals, temp_vals)
# categoria → "okay" | "warning" | "bad"
# probs → {"okay": 0.85, "warning": 0.12, "bad": 0.03}
```

### Endpoint REST
```
GET /api/pacientes/{paciente_id}/estado
Authorization: Bearer <token>

Response:
{
    "paciente_id": "paciente_autorizado_1",
    "clasificacion": "okay",
    "probabilidades": {
        "okay": 0.85,
        "warning": 0.12,
        "bad": 0.03
    },
    "ultima_lectura": { ... }
}
```

---

## Módulo B: Detección de Caídas

### Modelo
- **Tipo:** LSTM binario (PyTorch) con salida sigmoide
- **Archivos:** `app/models/modulo_b/`
  - `fall_model_pytorch.pth` - pesos del modelo
  - `config_fall.pkl` - hiperparámetros (window_size=20, input_size=9, etc.)
  - `scaler_fall.pkl` - StandardScaler

### Input esperado
- 6 listas de **exactamente 20 valores** cada una (ventana de 20 lecturas IMU):
  - `ax_vals`, `ay_vals`, `az_vals`: aceleración (m/s²)
  - `gx_vals`, `gy_vals`, `gz_vals`: velocidad angular (rad/s)

**Procesamiento interno:** El modelo transforma automáticamente los raw values a features de orientación (pitch, roll, yaw) antes de la inferencia.

### Output
```json
{
    "probabilidad_caida": 0.92,    // float entre 0 y 1
    "es_caida": true               // true si prob > 0.5
}
```

### Cómo usarlo desde código
```python
from app.services.ml_fall_service import predecir_caida

prob, es_caida = predecir_caida(ax_vals, ay_vals, az_vals, gx_vals, gy_vals, gz_vals)
# prob → 0.92 (probabilidad de caída)
# es_caida → True/False (threshold: 0.5)
```

### Endpoint REST
```
GET /api/pacientes/{paciente_id}/estado_caida
Authorization: Bearer <token>

Response:
{
    "paciente_id": "paciente_autorizado_1",
    "probabilidad_caida": 0.92,
    "es_caida": true,
    "ultima_lectura": { ... }
}
```

---

## Schedulers Automáticos (No requieren acción manual)

### 1. Clasificación Salud (`alertas_ml.py`)
- **Intervalo:** cada **15 segundos**
- **Qué hace:** Itera todos los pacientes en Firestore, obtiene sus últimas 30 lecturas de InfluxDB, ejecuta el modelo FeedForward, guarda `ultima_clasificacion` y `ultima_actualizacion_ml` en Firestore
- **Alertas push:** Si detecta `"warning"` o `"bad"`, envía notificación FCM a todos los cuidadores asignados (con cooldown de 5 min por paciente)

### 2. Detección Caídas (`alertas_caidas.py`)
- **Intervalo:** cada **10 segundos**
- **Qué hace:** Itera todos los pacientes, obtiene últimas 20 lecturas IMU, ejecuta modelo de caídas, guarda `ultima_probabilidad_caida` y `ultima_deteccion_caida` en Firestore
- **Alertas push:** Si detecta caída, envía notificación FCM urgente (cooldown 5 min)

### 3. Recordatorio Medicamentos (`notificaciones_service.py`)
- **Intervalo:** cada **1 minuto**
- **Qué hace:** Revisa `collection_group('medicamentos')` por hora programada y envía recordatorios push

### Datos guardados en Firestore automáticamente
Cada documento de paciente se actualiza con:
```json
{
    "ultima_clasificacion": "okay",
    "ultima_actualizacion_ml": "2026-07-04T12:00:00",
    "ultima_probabilidad_caida": 0.05,
    "ultima_deteccion_caida": false,
    "ultima_actualizacion_caida": "2026-07-04T12:00:10"
}
```

---

## Requisitos para que los modelos funcionen

### Datos en InfluxDB
Los modelos necesitan datos en la tabla `biometrics` de InfluxDB con estos campos:

| Campo | Tipo | Requerido por |
|-------|------|---------------|
| `heart_rate` | float | Módulo A |
| `spo2` | int | Módulo A |
| `temp` | float | Módulo A |
| `ax`, `ay`, `az` | float | Módulo B |
| `gx`, `gy`, `gz` | float | Módulo B |
| `id_patient` | tag | Ambos |

### Dependencias Python (ya en requirements.txt)
```
torch
joblib
scikit-learn
numpy
apscheduler
```

### Pipeline de datos
```
ESP32/Mock → MQTT (Mosquitto:1883) → Telegraf → InfluxDB 3 Core
                                                         ↑
                                                FastAPI consulta vía SQL
```

---

## Resumen de Endpoints

| Método | Ruta | Módulo | Descripción |
|--------|------|--------|-------------|
| GET | `/api/pacientes/` | - | Listar pacientes asignados |
| GET | `/api/pacientes/{id}` | - | Perfil del paciente |
| GET | `/api/pacientes/{id}/telemetria` | - | Historial de telemetría |
| **GET** | **`/api/pacientes/{id}/estado`** | **A** | **Clasificación salud (FeedForward)** |
| **GET** | **`/api/pacientes/{id}/estado_caida`** | **B** | **Detección de caídas (LSTM)** |
| GET/POST/PUT/DELETE | `/api/medicamentos/{id}` | - | CRUD medicamentos |
| PUT | `/api/usuarios/fcm-token` | - | Registrar token notificaciones |
| PUT/GET/DELETE | `/api/actividad-fisica/{id}` | - | Objetivos de pasos diarios |
| POST | `/api/auth/login-prueba` | - | Login de prueba (dev) |
